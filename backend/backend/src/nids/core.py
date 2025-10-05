"""
Core real-time NIDS implementation.
Orchestrates the complete pipeline from capture to alert.
"""

import time
import yaml
from typing import Dict, Optional, Any
from pathlib import Path
from threading import Thread, Event
import queue
from loguru import logger

from .capture import PacketCapture, OfflineCapture
from .features import FeatureExtractor
from .models import MATLABModelAdapter, SimpleModelAdapter
from .alerts import AlertManager
from .schemas import PacketInfo, FeatureVector, ModelPrediction, ProcessingStats


class RealTimeNIDS:
    """
    Real-time Network Intrusion Detection System.
    Orchestrates the complete pipeline: Capture → Parse → Features → Model → Alert
    """
    
    def __init__(self, config_path: str):
        """
        Initialize NIDS with configuration.
        
        Args:
            config_path: Path to YAML configuration file
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
        # Initialize components
        self.capture: Optional[PacketCapture] = None
        self.feature_extractor: Optional[FeatureExtractor] = None
        self.model_adapter: Optional[Any] = None
        self.alert_manager: Optional[AlertManager] = None
        
        # Processing state
        self._running = False
        self._stop_event = Event()
        self._processing_thread: Optional[Thread] = None
        
        # Statistics
        self.stats = {
            'packets_processed': 0,
            'alerts_generated': 0,
            'start_time': None,
            'processing_times': []
        }
        
        self._initialize_components()
        
        logger.info("Real-time NIDS initialized")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Configuration loaded from {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
    
    def _initialize_components(self):
        """Initialize all NIDS components."""
        # Initialize packet capture
        capture_config = self.config.get('capture', {})
        self.capture = PacketCapture(
            interface=capture_config.get('interface'),
            bpf_filter=capture_config.get('filter', 'tcp or udp'),
            promiscuous=capture_config.get('promiscuous', False),
            buffer_size=capture_config.get('buffer_size', 2048),
            timeout=capture_config.get('timeout', 1.0)
        )
        
        # Initialize feature extractor
        features_config = self.config.get('features', {})
        performance_config = self.config.get('performance', {})
        
        self.feature_extractor = FeatureExtractor(
            window_size=features_config.get('window_size', 10),
            window_overlap=features_config.get('window_overlap', 0.5),
            session_timeout=features_config.get('session_timeout', 300.0),
            max_payload_bytes=features_config.get('max_payload_bytes', 1500),
            use_numba=performance_config.get('use_numba', True)
        )
        
        # Initialize model adapter
        self._initialize_models()
        
        # Initialize alert manager
        alerts_config = self.config.get('alerts', {})
        self.alert_manager = AlertManager(
            toast_enabled=alerts_config.get('toast_enabled', True),
            toast_duration=alerts_config.get('toast_duration', 5),
            toast_sound=alerts_config.get('toast_sound', True),
            log_file=alerts_config.get('log_file', 'logs/alerts.jsonl'),
            min_confidence=alerts_config.get('min_confidence', 0.7),
            cooldown_seconds=alerts_config.get('cooldown_seconds', 30)
        )
    
    def _initialize_models(self):
        """Initialize model adapter based on configuration."""
        models_config = self.config.get('models', {})
        
        # For now, always use SimpleModelAdapter for demo purposes
        # The MATLAB model loading needs to be properly implemented
        logger.info("Using simple model adapter for demo")
        self.model_adapter = SimpleModelAdapter()
        
        # Set threshold if specified in config
        threshold = models_config.get('binary_classifier', {}).get('threshold', 0.5)
        self.model_adapter.set_threshold(threshold)
    
    def _process_packet(self, packet: PacketInfo) -> Optional[ModelPrediction]:
        """
        Process a single packet through the complete pipeline.
        
        Args:
            packet: Input packet information
            
        Returns:
            Model prediction if successful, None otherwise
        """
        try:
            start_time = time.time()
            
            # Extract features
            features = self.feature_extractor.extract_features(packet)
            
            # Get model prediction
            prediction = self.model_adapter.predict(features)
            
            # Track processing time
            processing_time = (time.time() - start_time) * 1000
            self.stats['processing_times'].append(processing_time)
            
            # Keep only recent processing times for statistics
            if len(self.stats['processing_times']) > 1000:
                self.stats['processing_times'] = self.stats['processing_times'][-1000:]
            
            return prediction
            
        except Exception as e:
            logger.error(f"Failed to process packet: {e}")
            return None
    
    def _processing_loop(self):
        """Main processing loop running in separate thread."""
        logger.info("Starting packet processing loop")
        
        try:
            while not self._stop_event.is_set():
                # Get packet from capture
                packet = self.capture.get_packet_nowait()
                if packet is None:
                    time.sleep(0.001)  # Small sleep to prevent busy waiting
                    continue
                
                # Process packet
                prediction = self._process_packet(packet)
                if prediction is None:
                    continue
                
                self.stats['packets_processed'] += 1
                
                # Generate alert if needed
                if prediction.is_attack:
                    alert = self.alert_manager.generate_alert(prediction)
                    if alert:
                        self.stats['alerts_generated'] += 1
                
                # Log processing statistics periodically
                if self.stats['packets_processed'] % 1000 == 0:
                    self._log_statistics()
                
        except Exception as e:
            logger.error(f"Processing loop error: {e}")
        finally:
            logger.info("Packet processing loop stopped")
    
    def _log_statistics(self):
        """Log current processing statistics."""
        if not self.stats['processing_times']:
            return
        
        current_time = time.time()
        uptime = current_time - self.stats['start_time'] if self.stats['start_time'] else 0
        
        # Calculate throughput
        pps = self.stats['packets_processed'] / max(uptime, 1)
        
        # Calculate latency statistics
        processing_times = self.stats['processing_times']
        avg_latency = sum(processing_times) / len(processing_times)
        p95_latency = sorted(processing_times)[int(0.95 * len(processing_times))]
        
        logger.info(
            f"Stats: {self.stats['packets_processed']} packets, "
            f"{pps:.1f} pps, "
            f"avg latency: {avg_latency:.1f}ms, "
            f"p95 latency: {p95_latency:.1f}ms, "
            f"alerts: {self.stats['alerts_generated']}, "
            f"flows: {self.feature_extractor.get_flow_count()}"
        )
    
    def start_detection(self):
        """Start real-time detection."""
        if self._running:
            logger.warning("Detection already running")
            return
        
        logger.info("Starting real-time network intrusion detection")
        
        # Start packet capture
        self.capture.start()
        
        # Start processing thread
        self._stop_event.clear()
        self._running = True
        self.stats['start_time'] = time.time()
        
        self._processing_thread = Thread(target=self._processing_loop, daemon=True)
        self._processing_thread.start()
        
        logger.info("Real-time detection started")
    
    def stop_detection(self):
        """Stop real-time detection."""
        if not self._running:
            logger.warning("Detection not running")
            return
        
        logger.info("Stopping real-time detection")
        
        # Stop processing
        self._stop_event.set()
        self._running = False
        
        # Stop capture
        self.capture.stop()
        
        # Wait for processing thread
        if self._processing_thread:
            self._processing_thread.join(timeout=5.0)
        
        # Final statistics
        self._log_statistics()
        
        logger.info("Real-time detection stopped")
    
    def process_offline(self, pcap_file: str, replay_speed: float = 1.0) -> Dict[str, Any]:
        """
        Process offline PCAP file for evaluation.
        
        Args:
            pcap_file: Path to PCAP file
            replay_speed: Replay speed multiplier
            
        Returns:
            Processing results and statistics
        """
        logger.info(f"Processing offline PCAP: {pcap_file}")
        
        # Initialize offline capture
        offline_capture = OfflineCapture(pcap_file, replay_speed)
        
        # Reset statistics
        self.stats = {
            'packets_processed': 0,
            'alerts_generated': 0,
            'start_time': time.time(),
            'processing_times': []
        }
        
        # Process packets
        predictions = []
        alerts = []
        
        try:
            for packet in offline_capture.replay():
                prediction = self._process_packet(packet)
                if prediction:
                    predictions.append(prediction)
                    self.stats['packets_processed'] += 1
                    
                    if prediction.is_attack:
                        alert = self.alert_manager.generate_alert(prediction)
                        if alert:
                            alerts.append(alert)
                            self.stats['alerts_generated'] += 1
                
                # Log progress
                if self.stats['packets_processed'] % 1000 == 0:
                    logger.info(f"Processed {self.stats['packets_processed']} packets")
        
        except KeyboardInterrupt:
            logger.info("Offline processing interrupted")
        
        # Calculate final statistics
        total_time = time.time() - self.stats['start_time']
        
        results = {
            'packets_processed': self.stats['packets_processed'],
            'alerts_generated': self.stats['alerts_generated'],
            'processing_time_seconds': total_time,
            'packets_per_second': self.stats['packets_processed'] / max(total_time, 1),
            'predictions': predictions,
            'alerts': alerts
        }
        
        if self.stats['processing_times']:
            results['avg_latency_ms'] = sum(self.stats['processing_times']) / len(self.stats['processing_times'])
            results['p95_latency_ms'] = sorted(self.stats['processing_times'])[int(0.95 * len(self.stats['processing_times']))]
        
        logger.info(f"Offline processing complete: {results['packets_processed']} packets, {results['alerts_generated']} alerts")
        
        return results
    
    def get_status(self) -> Dict[str, Any]:
        """Get current system status."""
        current_time = time.time()
        uptime = current_time - self.stats['start_time'] if self.stats['start_time'] else 0
        
        status = {
            'running': self._running,
            'uptime_seconds': uptime,
            'packets_processed': self.stats['packets_processed'],
            'alerts_generated': self.stats['alerts_generated'],
            'active_flows': self.feature_extractor.get_flow_count() if self.feature_extractor else 0,
            'capture_queue_size': self.capture.queue_size if self.capture else 0
        }
        
        if self.stats['processing_times']:
            recent_times = self.stats['processing_times'][-100:]  # Last 100 packets
            status['avg_latency_ms'] = sum(recent_times) / len(recent_times)
            status['packets_per_second'] = self.stats['packets_processed'] / max(uptime, 1)
        
        return status
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self._running:
            self.stop_detection()