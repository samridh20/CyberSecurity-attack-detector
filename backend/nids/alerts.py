"""
Alert management system with Windows toast notifications and logging.
"""

import time
import json
import uuid
from typing import Dict, Optional, List
from pathlib import Path
from datetime import datetime
from loguru import logger

# Windows toast notification imports
try:
    import sys
    if sys.platform == "win32":
        try:
            # Try winrt first (preferred)
            from winrt.windows.ui.notifications import ToastNotificationManager, ToastNotification
            from winrt.windows.data.xml.dom import XmlDocument
            WINRT_AVAILABLE = True
            WIN10TOAST_AVAILABLE = False
        except ImportError:
            # Fallback to win10toast
            try:
                from win10toast import ToastNotifier
                WINRT_AVAILABLE = False
                WIN10TOAST_AVAILABLE = True
            except ImportError:
                WINRT_AVAILABLE = False
                WIN10TOAST_AVAILABLE = False
    else:
        WINRT_AVAILABLE = False
        WIN10TOAST_AVAILABLE = False
except ImportError:
    WINRT_AVAILABLE = False
    WIN10TOAST_AVAILABLE = False

from .schemas import Alert, ModelPrediction, FlowKey


class AlertManager:
    """
    Manages security alerts with Windows toast notifications and structured logging.
    """
    
    def __init__(self,
                 toast_enabled: bool = True,
                 toast_duration: int = 5,
                 toast_sound: bool = True,
                 log_file: str = "logs/alerts.jsonl",
                 min_confidence: float = 0.7,
                 cooldown_seconds: int = 30):
        """
        Initialize alert manager.
        
        Args:
            toast_enabled: Enable Windows toast notifications
            toast_duration: Toast display duration in seconds
            toast_sound: Enable notification sound
            log_file: Path to alert log file
            min_confidence: Minimum confidence for alerts
            cooldown_seconds: Cooldown period between similar alerts
        """
        self.toast_enabled = toast_enabled and (WINRT_AVAILABLE or WIN10TOAST_AVAILABLE)
        self.toast_duration = toast_duration
        self.toast_sound = toast_sound
        self.log_file = Path(log_file)
        self.min_confidence = min_confidence
        self.cooldown_seconds = cooldown_seconds
        
        # Alert tracking for cooldown
        self.recent_alerts: Dict[str, float] = {}
        
        # In-memory storage for recent alerts (for API access)
        self._recent_alerts: List[Dict] = []
        
        # Initialize toast notifier
        self.toast_notifier = None
        if self.toast_enabled:
            self._init_toast_notifier()
        
        # Ensure log directory exists
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Alert manager initialized (toast={'enabled' if self.toast_enabled else 'disabled'})")
    
    def _init_toast_notifier(self):
        """Initialize Windows toast notification system."""
        try:
            if WINRT_AVAILABLE:
                # Using WinRT (preferred)
                self.toast_notifier = ToastNotificationManager.create_toast_notifier("NIDS")
                logger.info("Using WinRT for toast notifications")
            elif WIN10TOAST_AVAILABLE:
                # Using win10toast (fallback)
                self.toast_notifier = ToastNotifier()
                logger.info("Using win10toast for notifications")
            else:
                logger.warning("No toast notification library available")
                self.toast_enabled = False
        except Exception as e:
            logger.error(f"Failed to initialize toast notifications: {e}")
            self.toast_enabled = False
    
    def _create_alert_key(self, prediction: ModelPrediction) -> str:
        """Create unique key for alert cooldown tracking."""
        return f"{prediction.flow_key.src_ip}:{prediction.flow_key.dst_ip}:{prediction.attack_class or 'attack'}"
    
    def _should_alert(self, prediction: ModelPrediction) -> bool:
        """Check if alert should be generated based on confidence and cooldown."""
        # Check confidence threshold
        if prediction.attack_probability < self.min_confidence:
            return False
        
        # Check cooldown
        alert_key = self._create_alert_key(prediction)
        current_time = time.time()
        
        if alert_key in self.recent_alerts:
            time_since_last = current_time - self.recent_alerts[alert_key]
            if time_since_last < self.cooldown_seconds:
                return False
        
        # Update cooldown tracking
        self.recent_alerts[alert_key] = current_time
        
        return True
    
    def _determine_severity(self, prediction: ModelPrediction) -> str:
        """Determine alert severity based on prediction."""
        confidence = prediction.attack_probability
        attack_class = prediction.attack_class
        
        # Critical attacks
        if attack_class in ['DoS', 'Exploits'] and confidence > 0.9:
            return 'critical'
        
        # High severity
        if confidence > 0.85:
            return 'high'
        
        # Medium severity
        if confidence > 0.75:
            return 'medium'
        
        # Low severity
        return 'low'
    
    def _create_alert_description(self, prediction: ModelPrediction) -> str:
        """Create human-readable alert description."""
        attack_type = prediction.attack_class or "Unknown Attack"
        confidence = prediction.attack_probability * 100
        
        return (f"{attack_type} detected from {prediction.flow_key.src_ip} "
                f"to {prediction.flow_key.dst_ip}:{prediction.flow_key.dst_port} "
                f"(confidence: {confidence:.1f}%)")
    
    def _get_recommended_action(self, prediction: ModelPrediction) -> str:
        """Get recommended action based on attack type."""
        attack_class = prediction.attack_class
        
        if attack_class == "DoS":
            return "Consider rate limiting or blocking source IP"
        elif attack_class == "Exploits":
            return "Investigate payload and consider blocking connection"
        elif attack_class == "Reconnaissance":
            return "Monitor for follow-up attacks from this source"
        elif attack_class == "Fuzzers":
            return "Check application logs for errors or crashes"
        else:
            return "Monitor connection and investigate if persistent"
    
    def _send_toast_notification(self, alert: Alert):
        """Send Windows toast notification."""
        if not self.toast_enabled or not self.toast_notifier:
            return
        
        try:
            title = f"Security Alert - {alert.severity.upper()}"
            message = alert.description
            
            if WINRT_AVAILABLE:
                # Create toast using WinRT
                toast_xml = f"""
                <toast duration="{'long' if self.toast_duration > 5 else 'short'}">
                    <visual>
                        <binding template="ToastGeneric">
                            <text>{title}</text>
                            <text>{message}</text>
                        </binding>
                    </visual>
                    {'<audio src="ms-winsoundevent:Notification.Default" />' if self.toast_sound else '<audio silent="true" />'}
                </toast>
                """
                
                xml_doc = XmlDocument()
                xml_doc.load_xml(toast_xml)
                toast = ToastNotification(xml_doc)
                self.toast_notifier.show(toast)
                
            elif WIN10TOAST_AVAILABLE:
                # Use win10toast
                self.toast_notifier.show_toast(
                    title=title,
                    msg=message,
                    duration=self.toast_duration,
                    threaded=True
                )
            
            logger.debug(f"Toast notification sent: {title}")
            
        except Exception as e:
            logger.error(f"Failed to send toast notification: {e}")
    
    def _log_alert(self, alert: Alert):
        """Log alert to structured JSON log file."""
        try:
            alert_data = {
                'timestamp': alert.timestamp,
                'alert_id': alert.alert_id,
                'severity': alert.severity,
                'attack_type': alert.attack_type,
                'confidence': alert.confidence,
                'source_ip': alert.source_ip,
                'destination_ip': alert.destination_ip,
                'destination_port': alert.flow_key.dst_port,
                'protocol': alert.flow_key.protocol,
                'description': alert.description,
                'recommended_action': alert.recommended_action,
                'processing_time_ms': alert.prediction.processing_time_ms
            }
            
            # Append to JSONL file
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(alert_data) + '\n')
            
            logger.info(f"Alert logged: {alert.alert_id}")
            
        except Exception as e:
            logger.error(f"Failed to log alert: {e}")
    
    def generate_alert(self, prediction: ModelPrediction) -> Optional[Alert]:
        """
        Generate alert from model prediction.
        
        Args:
            prediction: Model prediction result
            
        Returns:
            Alert object if alert should be generated, None otherwise
        """
        # Check if alert should be generated
        if not prediction.is_attack or not self._should_alert(prediction):
            return None
        
        # Create alert
        alert = Alert(
            timestamp=prediction.timestamp,
            alert_id=str(uuid.uuid4()),
            severity=self._determine_severity(prediction),
            attack_type=prediction.attack_class or "Unknown",
            confidence=prediction.attack_probability,
            source_ip=prediction.flow_key.src_ip,
            destination_ip=prediction.flow_key.dst_ip,
            flow_key=prediction.flow_key,
            prediction=prediction,
            description=self._create_alert_description(prediction),
            recommended_action=self._get_recommended_action(prediction)
        )
        
        # Send notifications
        self._send_toast_notification(alert)
        self._log_alert(alert)
        
        # Store in memory for API access
        alert_dict = {
            'id': alert.alert_id,
            'timestamp': alert.timestamp,
            'attack_type': alert.attack_type,
            'attack_class': alert.attack_type,  # Frontend compatibility
            'severity': alert.severity,
            'confidence': alert.confidence,
            'probability': alert.confidence,  # Frontend compatibility
            'src_ip': alert.source_ip,
            'dst_ip': alert.destination_ip,
            'src_port': alert.flow_key.src_port,
            'dst_port': alert.flow_key.dst_port,
            'protocol': alert.flow_key.protocol,
            'description': alert.description,
            'recommended_action': alert.recommended_action,
            'packet_length': getattr(alert.prediction, 'packet_size', 0),
            'interface': 'auto',
            'flags': 'SYN'  # Default for demo
        }
        
        # Add to in-memory storage (keep last 1000)
        self._recent_alerts.insert(0, alert_dict)
        self._recent_alerts = self._recent_alerts[:1000]
        
        logger.warning(f"SECURITY ALERT: {alert.description}")
        
        return alert
    
    def cleanup_old_alerts(self, max_age_seconds: int = 3600):
        """Clean up old alert tracking data."""
        current_time = time.time()
        expired_keys = []
        
        for alert_key, timestamp in self.recent_alerts.items():
            if current_time - timestamp > max_age_seconds:
                expired_keys.append(alert_key)
        
        for key in expired_keys:
            del self.recent_alerts[key]
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} old alert entries")
    
    def get_recent_alerts(self, limit: int = 100) -> List[Dict]:
        """
        Get recent alerts from in-memory storage and log file.
        
        Args:
            limit: Maximum number of alerts to return
            
        Returns:
            List of recent alert dictionaries
        """
        # First try in-memory storage (faster and more reliable)
        if self._recent_alerts:
            return self._recent_alerts[:limit]
        
        # Fallback to log file
        alerts = []
        
        try:
            if self.log_file.exists():
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # Get last N lines
                recent_lines = lines[-limit:] if len(lines) > limit else lines
                
                for line in recent_lines:
                    try:
                        alert_data = json.loads(line.strip())
                        # Convert to frontend format
                        formatted_alert = {
                            'id': alert_data.get('alert_id', str(uuid.uuid4())),
                            'timestamp': alert_data.get('timestamp', time.time()),
                            'attack_type': alert_data.get('attack_type', 'Unknown'),
                            'attack_class': alert_data.get('attack_type', 'Unknown'),
                            'severity': alert_data.get('severity', 'medium'),
                            'confidence': alert_data.get('confidence', 0.5),
                            'probability': alert_data.get('confidence', 0.5),
                            'src_ip': alert_data.get('source_ip', 'unknown'),
                            'dst_ip': alert_data.get('destination_ip', 'unknown'),
                            'src_port': alert_data.get('src_port', 0),
                            'dst_port': alert_data.get('destination_port', 0),
                            'protocol': alert_data.get('protocol', 'unknown'),
                            'description': alert_data.get('description', ''),
                            'recommended_action': alert_data.get('recommended_action', ''),
                            'packet_length': 0,
                            'interface': 'auto',
                            'flags': 'SYN'
                        }
                        alerts.append(formatted_alert)
                    except json.JSONDecodeError:
                        continue
        
        except Exception as e:
            logger.error(f"Failed to read alert log: {e}")
        
        return alerts
    
    def get_alert_stats(self) -> Dict:
        """Get alert statistics."""
        alerts = self.get_recent_alerts(1000)  # Last 1000 alerts
        
        if not alerts:
            return {
                'total_alerts': 0,
                'by_severity': {},
                'by_attack_type': {},
                'recent_sources': []
            }
        
        # Count by severity
        severity_counts = {}
        attack_type_counts = {}
        source_ips = set()
        
        for alert in alerts:
            severity = alert.get('severity', 'unknown')
            attack_type = alert.get('attack_type', 'unknown')
            source_ip = alert.get('source_ip', 'unknown')
            
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            attack_type_counts[attack_type] = attack_type_counts.get(attack_type, 0) + 1
            source_ips.add(source_ip)
        
        return {
            'total_alerts': len(alerts),
            'by_severity': severity_counts,
            'by_attack_type': attack_type_counts,
            'unique_sources': len(source_ips),
            'recent_sources': list(source_ips)[-10:]  # Last 10 unique sources
        }