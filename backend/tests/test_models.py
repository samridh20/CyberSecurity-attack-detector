"""
Unit tests for model adapter module.
"""

import pytest
import time
from nids.models import SimpleModelAdapter
from nids.schemas import PacketInfo, FeatureVector, FlowKey


class TestSimpleModelAdapter:
    """Test cases for SimpleModelAdapter class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.adapter = SimpleModelAdapter()
    
    def create_test_features(self, **kwargs):
        """Create test feature vector."""
        defaults = {
            'timestamp': time.time(),
            'flow_key': FlowKey(
                src_ip='192.168.1.100',
                dst_ip='10.0.0.1',
                src_port=12345,
                dst_port=80,
                protocol='tcp'
            ),
            'packet_size': 1000.0,
            'direction': 0,
            'inter_arrival_delta': 0.1,
            'tcp_flags_bitmap': 0x18,
            'ttl': 64.0,
            'total_bytes': 1000.0,
            'total_packets': 1.0,
            'bytes_ratio': 0.5,
            'packets_per_second': 10.0,
            'syn_fin_ratio': 1.0,
            'size_mean': 1000.0,
            'size_std': 100.0,
            'iat_mean': 0.1,
            'iat_std': 0.01,
            'burstiness': 0.1,
            'payload_entropy': 4.0,
            'printable_ratio': 0.8
        }
        defaults.update(kwargs)
        return FeatureVector(**defaults)
    
    def test_normal_traffic_prediction(self):
        """Test prediction for normal traffic."""
        features = self.create_test_features(
            packets_per_second=10.0,
            packet_size=1000.0,
            payload_entropy=4.0,
            burstiness=0.5
        )
        
        prediction = self.adapter.predict(features)
        
        # Check prediction structure
        assert prediction.timestamp == features.timestamp
        assert prediction.flow_key == features.flow_key
        assert isinstance(prediction.is_attack, bool)
        assert 0.0 <= prediction.attack_probability <= 1.0
        assert prediction.processing_time_ms > 0
        
        # Normal traffic should have low attack probability
        assert prediction.attack_probability < 0.7
    
    def test_dos_attack_prediction(self):
        """Test prediction for DoS attack patterns."""
        features = self.create_test_features(
            packets_per_second=500.0,  # High packet rate
            packet_size=64.0,          # Small packets
            burstiness=5.0             # High burstiness
        )
        
        prediction = self.adapter.predict(features)
        
        # DoS patterns should increase attack probability
        assert prediction.attack_probability > 0.3
        
        # If classified as attack, should be DoS
        if prediction.is_attack:
            assert prediction.attack_class == "DoS"
    
    def test_exploit_attack_prediction(self):
        """Test prediction for exploit patterns."""
        features = self.create_test_features(
            payload_entropy=7.9,       # High entropy (encrypted/obfuscated)
            packet_size=1400.0,        # Large packets
            packets_per_second=50.0
        )
        
        prediction = self.adapter.predict(features)
        
        # High entropy should increase attack probability
        assert prediction.attack_probability > 0.2
        
        # If classified as attack, should be Exploits
        if prediction.is_attack and prediction.attack_class:
            assert prediction.attack_class == "Exploits"
    
    def test_threshold_setting(self):
        """Test threshold adjustment."""
        features = self.create_test_features(packets_per_second=150.0)
        
        # Test with default threshold
        prediction1 = self.adapter.predict(features)
        
        # Lower threshold
        self.adapter.set_threshold(0.3)
        prediction2 = self.adapter.predict(features)
        
        # Higher threshold
        self.adapter.set_threshold(0.8)
        prediction3 = self.adapter.predict(features)
        
        # Same probability, different classifications
        assert prediction1.attack_probability == prediction2.attack_probability == prediction3.attack_probability
        
        # But potentially different attack classifications
        # (depends on the specific probability value)
    
    def test_multiclass_prediction(self):
        """Test multi-class attack classification."""
        # Create features that should trigger attack detection
        features = self.create_test_features(
            packets_per_second=300.0,
            payload_entropy=8.0,
            burstiness=4.0
        )
        
        prediction = self.adapter.predict(features)
        
        if prediction.is_attack:
            # Should have attack class
            assert prediction.attack_class is not None
            assert prediction.attack_class in self.adapter.class_names
            
            # Should have class probabilities
            assert prediction.class_probabilities is not None
            assert isinstance(prediction.class_probabilities, dict)
            
            # Probabilities should sum to approximately 1.0
            total_prob = sum(prediction.class_probabilities.values())
            assert 0.8 <= total_prob <= 1.2  # Allow some tolerance
            
            # Predicted class should have highest probability
            max_prob_class = max(prediction.class_probabilities.items(), key=lambda x: x[1])[0]
            assert max_prob_class == prediction.attack_class
    
    def test_processing_time_tracking(self):
        """Test processing time measurement."""
        features = self.create_test_features()
        
        prediction = self.adapter.predict(features)
        
        # Should track processing time
        assert prediction.processing_time_ms > 0
        assert prediction.processing_time_ms < 1000  # Should be fast for simple model
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Test with zero values
        features = self.create_test_features(
            packets_per_second=0.0,
            packet_size=0.0,
            payload_entropy=0.0,
            burstiness=0.0
        )
        
        prediction = self.adapter.predict(features)
        
        # Should handle gracefully
        assert 0.0 <= prediction.attack_probability <= 1.0
        assert isinstance(prediction.is_attack, bool)
        
        # Test with extreme values
        features_extreme = self.create_test_features(
            packets_per_second=10000.0,
            packet_size=65535.0,
            payload_entropy=8.0,
            burstiness=100.0
        )
        
        prediction_extreme = self.adapter.predict(features_extreme)
        
        # Should handle extreme values
        assert 0.0 <= prediction_extreme.attack_probability <= 1.0
    
    def test_consistency(self):
        """Test prediction consistency."""
        features = self.create_test_features()
        
        # Make multiple predictions with same features
        predictions = []
        for _ in range(10):
            prediction = self.adapter.predict(features)
            predictions.append(prediction)
        
        # Should be consistent (allowing for small random variation)
        probabilities = [p.attack_probability for p in predictions]
        prob_std = sum((p - probabilities[0])**2 for p in probabilities) ** 0.5
        
        # Standard deviation should be small (allowing for randomness in simple model)
        assert prob_std < 0.2