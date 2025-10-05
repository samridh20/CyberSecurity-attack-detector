"""
Unit tests for alert management module.
"""

import pytest
import time
import tempfile
import json
from pathlib import Path
from nids.alerts import AlertManager
from nids.schemas import ModelPrediction, FlowKey


class TestAlertManager:
    """Test cases for AlertManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Use temporary directory for test logs
        self.temp_dir = tempfile.mkdtemp()
        self.log_file = Path(self.temp_dir) / "test_alerts.jsonl"
        
        self.alert_manager = AlertManager(
            toast_enabled=False,  # Disable for testing
            log_file=str(self.log_file),
            min_confidence=0.7,
            cooldown_seconds=5
        )
    
    def create_test_prediction(self, **kwargs):
        """Create test model prediction."""
        defaults = {
            'timestamp': time.time(),
            'flow_key': FlowKey(
                src_ip='192.168.1.100',
                dst_ip='10.0.0.1',
                src_port=12345,
                dst_port=80,
                protocol='tcp'
            ),
            'is_attack': True,
            'attack_probability': 0.8,
            'attack_class': 'DoS',
            'class_probabilities': {'DoS': 0.8, 'Normal': 0.2},
            'model_version': '1.0',
            'threshold_used': 0.5,
            'processing_time_ms': 10.0
        }
        defaults.update(kwargs)
        return ModelPrediction(**defaults)
    
    def test_alert_generation(self):
        """Test basic alert generation."""
        prediction = self.create_test_prediction()
        
        alert = self.alert_manager.generate_alert(prediction)
        
        # Should generate alert for high-confidence attack
        assert alert is not None
        assert alert.attack_type == 'DoS'
        assert alert.confidence == 0.8
        assert alert.source_ip == '192.168.1.100'
        assert alert.destination_ip == '10.0.0.1'
        assert alert.severity in ['low', 'medium', 'high', 'critical']
    
    def test_confidence_threshold(self):
        """Test confidence threshold filtering."""
        # Low confidence prediction
        low_conf_prediction = self.create_test_prediction(attack_probability=0.5)
        
        alert = self.alert_manager.generate_alert(low_conf_prediction)
        
        # Should not generate alert below threshold
        assert alert is None
        
        # High confidence prediction
        high_conf_prediction = self.create_test_prediction(attack_probability=0.9)
        
        alert = self.alert_manager.generate_alert(high_conf_prediction)
        
        # Should generate alert above threshold
        assert alert is not None
    
    def test_cooldown_mechanism(self):
        """Test alert cooldown to prevent spam."""
        prediction = self.create_test_prediction()
        
        # Generate first alert
        alert1 = self.alert_manager.generate_alert(prediction)
        assert alert1 is not None
        
        # Generate second alert immediately (same source/destination)
        alert2 = self.alert_manager.generate_alert(prediction)
        assert alert2 is None  # Should be blocked by cooldown
        
        # Wait for cooldown to expire
        time.sleep(6)  # Cooldown is 5 seconds
        
        # Generate third alert
        alert3 = self.alert_manager.generate_alert(prediction)
        assert alert3 is not None  # Should be allowed after cooldown
    
    def test_severity_determination(self):
        """Test alert severity classification."""
        # Critical severity
        critical_prediction = self.create_test_prediction(
            attack_class='DoS',
            attack_probability=0.95
        )
        
        alert = self.alert_manager.generate_alert(critical_prediction)
        assert alert.severity == 'critical'
        
        # High severity
        high_prediction = self.create_test_prediction(
            attack_class='Generic',
            attack_probability=0.9
        )
        
        alert = self.alert_manager.generate_alert(high_prediction)
        assert alert.severity == 'high'
        
        # Medium severity
        medium_prediction = self.create_test_prediction(
            attack_class='Reconnaissance',
            attack_probability=0.8,
            flow_key=FlowKey(
                src_ip='192.168.1.101',  # Different IP to avoid cooldown
                dst_ip='10.0.0.1',
                src_port=12346,
                dst_port=80,
                protocol='tcp'
            )
        )
        
        alert = self.alert_manager.generate_alert(medium_prediction)
        assert alert.severity == 'medium'
        
        # Low severity
        low_prediction = self.create_test_prediction(
            attack_class='Generic',
            attack_probability=0.72,  # Just above min_confidence but below medium threshold
            flow_key=FlowKey(
                src_ip='192.168.1.102',  # Different IP to avoid cooldown
                dst_ip='10.0.0.1',
                src_port=12347,
                dst_port=80,
                protocol='tcp'
            )
        )
        
        alert = self.alert_manager.generate_alert(low_prediction)
        assert alert.severity == 'low'
    
    def test_alert_logging(self):
        """Test alert logging to file."""
        prediction = self.create_test_prediction()
        
        alert = self.alert_manager.generate_alert(prediction)
        assert alert is not None
        
        # Check that log file was created and contains alert
        assert self.log_file.exists()
        
        with open(self.log_file, 'r') as f:
            log_line = f.readline().strip()
            alert_data = json.loads(log_line)
        
        assert alert_data['alert_id'] == alert.alert_id
        assert alert_data['attack_type'] == 'DoS'
        assert alert_data['confidence'] == 0.8
        assert alert_data['source_ip'] == '192.168.1.100'
    
    def test_recommended_actions(self):
        """Test recommended action generation."""
        # DoS attack
        dos_prediction = self.create_test_prediction(attack_class='DoS')
        alert = self.alert_manager.generate_alert(dos_prediction)
        assert 'rate limiting' in alert.recommended_action.lower()
        
        # Exploit attack
        exploit_prediction = self.create_test_prediction(attack_class='Exploits')
        alert = self.alert_manager.generate_alert(exploit_prediction)
        assert 'payload' in alert.recommended_action.lower()
        
        # Reconnaissance
        recon_prediction = self.create_test_prediction(attack_class='Reconnaissance')
        alert = self.alert_manager.generate_alert(recon_prediction)
        assert 'monitor' in alert.recommended_action.lower()
    
    def test_normal_traffic_no_alert(self):
        """Test that normal traffic doesn't generate alerts."""
        normal_prediction = self.create_test_prediction(
            is_attack=False,
            attack_probability=0.2,
            attack_class=None
        )
        
        alert = self.alert_manager.generate_alert(normal_prediction)
        assert alert is None
    
    def test_get_recent_alerts(self):
        """Test retrieval of recent alerts."""
        # Generate multiple alerts
        predictions = []
        for i in range(5):
            prediction = self.create_test_prediction(
                flow_key=FlowKey(
                    src_ip=f'192.168.1.{100+i}',
                    dst_ip='10.0.0.1',
                    src_port=12345+i,
                    dst_port=80,
                    protocol='tcp'
                )
            )
            predictions.append(prediction)
            
            # Wait to avoid cooldown
            time.sleep(0.1)
        
        # Generate alerts
        alerts = []
        for prediction in predictions:
            alert = self.alert_manager.generate_alert(prediction)
            if alert:
                alerts.append(alert)
        
        # Retrieve recent alerts
        recent_alerts = self.alert_manager.get_recent_alerts(limit=10)
        
        assert len(recent_alerts) == len(alerts)
        assert all('alert_id' in alert for alert in recent_alerts)
    
    def test_alert_statistics(self):
        """Test alert statistics generation."""
        # Generate alerts of different types
        attack_types = ['DoS', 'Exploits', 'Reconnaissance']
        severities = ['high', 'medium', 'low']
        
        for i, (attack_type, severity) in enumerate(zip(attack_types, severities)):
            confidence = 0.9 if severity == 'high' else 0.8 if severity == 'medium' else 0.75
            
            prediction = self.create_test_prediction(
                attack_class=attack_type,
                attack_probability=confidence,
                flow_key=FlowKey(
                    src_ip=f'192.168.1.{200+i}',
                    dst_ip='10.0.0.1',
                    src_port=12345+i,
                    dst_port=80,
                    protocol='tcp'
                )
            )
            
            self.alert_manager.generate_alert(prediction)
            time.sleep(0.1)  # Avoid cooldown
        
        # Get statistics
        stats = self.alert_manager.get_alert_stats()
        
        assert stats['total_alerts'] == 3
        assert 'by_severity' in stats
        assert 'by_attack_type' in stats
        assert 'unique_sources' in stats
        
        # Check attack type distribution
        assert stats['by_attack_type']['DoS'] == 1
        assert stats['by_attack_type']['Exploits'] == 1
        assert stats['by_attack_type']['Reconnaissance'] == 1
    
    def test_cleanup_old_alerts(self):
        """Test cleanup of old alert tracking data."""
        prediction = self.create_test_prediction()
        
        # Generate alert
        alert = self.alert_manager.generate_alert(prediction)
        assert alert is not None
        
        # Check that tracking data exists
        assert len(self.alert_manager.recent_alerts) > 0
        
        # Cleanup with very short max age
        self.alert_manager.cleanup_old_alerts(max_age_seconds=0)
        
        # Should have cleaned up tracking data
        assert len(self.alert_manager.recent_alerts) == 0