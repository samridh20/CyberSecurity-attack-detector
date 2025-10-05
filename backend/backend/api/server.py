"""
NIDS Backend REST API Server
Provides HTTP endpoints for frontend integration
"""

import json
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nids import RealTimeNIDS
from loguru import logger

try:
    from flask import Flask, jsonify, request, Response
    from flask_cors import CORS
    FLASK_AVAILABLE = True
except ImportError:
    logger.warning("Flask not available. Install with: pip install flask flask-cors")
    FLASK_AVAILABLE = False


@dataclass
class AlertData:
    """Alert data structure for API responses."""
    id: str
    timestamp: float
    severity: str
    description: str
    source_ip: str
    destination_ip: str
    attack_type: str
    confidence: float


@dataclass
class SystemStatus:
    """System status data structure."""
    running: bool
    uptime_seconds: float
    packets_processed: int
    alerts_generated: int
    active_flows: int
    packets_per_second: float
    avg_latency_ms: float


class NIDSAPIServer:
    """NIDS Backend API Server."""
    
    def __init__(self, config_path: str):
        """Initialize API server."""
        self.config_path = config_path
        self.nids: Optional[RealTimeNIDS] = None
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS for frontend
        
        # Data storage
        self.alerts_history: List[AlertData] = []
        self.status_history: List[Dict] = []
        self.max_history_size = 1000
        
        # Threading
        self.nids_thread: Optional[threading.Thread] = None
        self.monitoring_thread: Optional[threading.Thread] = None
        self.running = False
        
        self._setup_routes()
        
    def _setup_routes(self):
        """Setup API routes."""
        
        @self.app.route('/api/status', methods=['GET'])
        def get_status():
            """Get current system status."""
            if not self.nids:
                return jsonify({
                    'running': False,
                    'error': 'NIDS not initialized'
                }), 503
            
            status = self.nids.get_status()
            return jsonify(status)
        
        @self.app.route('/api/alerts', methods=['GET'])
        def get_alerts():
            """Get recent alerts."""
            limit = request.args.get('limit', 100, type=int)
            offset = request.args.get('offset', 0, type=int)
            
            # Get recent alerts
            alerts = self.alerts_history[offset:offset + limit]
            
            return jsonify({
                'alerts': [asdict(alert) for alert in alerts],
                'total': len(self.alerts_history),
                'limit': limit,
                'offset': offset
            })
        
        @self.app.route('/api/alerts/stream', methods=['GET'])
        def stream_alerts():
            """Stream alerts in real-time using Server-Sent Events."""
            def generate():
                last_alert_count = len(self.alerts_history)
                while True:
                    current_count = len(self.alerts_history)
                    if current_count > last_alert_count:
                        # New alerts available
                        new_alerts = self.alerts_history[last_alert_count:]
                        for alert in new_alerts:
                            yield f"data: {json.dumps(asdict(alert))}\\n\\n"
                        last_alert_count = current_count
                    time.sleep(1)
            
            return Response(generate(), mimetype='text/plain')
        
        @self.app.route('/api/start', methods=['POST'])
        def start_detection():
            """Start NIDS detection."""
            if not self.nids:
                try:
                    self.nids = RealTimeNIDS(self.config_path)
                except Exception as e:
                    return jsonify({'error': f'Failed to initialize NIDS: {e}'}), 500
            
            if self.running:
                return jsonify({'message': 'NIDS already running'}), 200
            
            try:
                self.nids.start_detection()
                self.running = True
                
                # Start monitoring thread
                self.monitoring_thread = threading.Thread(target=self._monitor_alerts, daemon=True)
                self.monitoring_thread.start()
                
                return jsonify({'message': 'NIDS detection started'})
            except Exception as e:
                return jsonify({'error': f'Failed to start detection: {e}'}), 500
        
        @self.app.route('/api/stop', methods=['POST'])
        def stop_detection():
            """Stop NIDS detection."""
            if not self.nids or not self.running:
                return jsonify({'message': 'NIDS not running'}), 200
            
            try:
                self.nids.stop_detection()
                self.running = False
                return jsonify({'message': 'NIDS detection stopped'})
            except Exception as e:
                return jsonify({'error': f'Failed to stop detection: {e}'}), 500
        
        @self.app.route('/api/config', methods=['GET'])
        def get_config():
            """Get current configuration."""
            try:
                with open(self.config_path, 'r') as f:
                    import yaml
                    config = yaml.safe_load(f)
                return jsonify(config)
            except Exception as e:
                return jsonify({'error': f'Failed to load config: {e}'}), 500
        
        @self.app.route('/api/stats/history', methods=['GET'])
        def get_stats_history():
            """Get historical statistics."""
            hours = request.args.get('hours', 1, type=int)
            
            # Filter status history by time
            cutoff_time = time.time() - (hours * 3600)
            recent_stats = [
                stat for stat in self.status_history 
                if stat.get('timestamp', 0) > cutoff_time
            ]
            
            return jsonify({
                'stats': recent_stats,
                'hours': hours
            })
        
        @self.app.route('/api/demo/start', methods=['POST'])
        def start_demo():
            """Start synthetic demo."""
            duration = request.json.get('duration', 60) if request.json else 60
            
            try:
                if not self.nids:
                    self.nids = RealTimeNIDS(self.config_path)
                
                # Run demo in background thread
                def run_demo():
                    from scripts.demo import run_synthetic_demo
                    run_synthetic_demo(self.nids, duration=duration)
                
                demo_thread = threading.Thread(target=run_demo, daemon=True)
                demo_thread.start()
                
                return jsonify({'message': f'Demo started for {duration} seconds'})
            except Exception as e:
                return jsonify({'error': f'Failed to start demo: {e}'}), 500
        
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            """Health check endpoint."""
            return jsonify({
                'status': 'healthy',
                'timestamp': time.time(),
                'version': '1.0.0'
            })
    
    def _monitor_alerts(self):
        """Monitor for new alerts in background thread."""
        logger.info("Starting alert monitoring thread")
        
        while self.running and self.nids:
            try:
                # This is a simplified approach - in a real implementation,
                # you'd want to hook into the alert manager's callback system
                time.sleep(1)
                
                # Get current status and store in history
                status = self.nids.get_status()
                status['timestamp'] = time.time()
                
                self.status_history.append(status)
                
                # Keep history size manageable
                if len(self.status_history) > self.max_history_size:
                    self.status_history = self.status_history[-self.max_history_size:]
                
            except Exception as e:
                logger.error(f"Error in alert monitoring: {e}")
                time.sleep(5)
        
        logger.info("Alert monitoring thread stopped")
    
    def add_alert(self, alert_data: AlertData):
        """Add new alert to history."""
        self.alerts_history.append(alert_data)
        
        # Keep history size manageable
        if len(self.alerts_history) > self.max_history_size:
            self.alerts_history = self.alerts_history[-self.max_history_size:]
    
    def run(self, host='0.0.0.0', port=8000, debug=False):
        """Run the API server."""
        logger.info(f"Starting NIDS API server on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug, threaded=True)


def start_api_server(port: int = 8000, config_path: str = "config/config.yaml"):
    """Start the NIDS API server."""
    if not FLASK_AVAILABLE:
        logger.error("Flask is required for API server. Install with: pip install flask flask-cors")
        return
    
    server = NIDSAPIServer(config_path)
    server.run(port=port)


if __name__ == "__main__":
    start_api_server()