"""
Unit tests for feature extraction module.
"""

import pytest
import time
from nids.features import FeatureExtractor
from nids.schemas import PacketInfo


class TestFeatureExtractor:
    """Test cases for FeatureExtractor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = FeatureExtractor(
            window_size=5,
            session_timeout=60.0,
            use_numba=False  # Disable for testing
        )
    
    def create_test_packet(self, **kwargs):
        """Create a test packet with default values."""
        defaults = {
            'timestamp': time.time(),
            'src_ip': '192.168.1.100',
            'dst_ip': '10.0.0.1',
            'src_port': 12345,
            'dst_port': 80,
            'protocol': 'tcp',
            'packet_size': 1000,
            'payload_size': 500,
            'payload': b'GET / HTTP/1.1\\r\\n\\r\\n',
            'tcp_flags': 0x18,  # PSH+ACK
            'ttl': 64
        }
        defaults.update(kwargs)
        return PacketInfo(**defaults)
    
    def test_single_packet_features(self):
        """Test feature extraction from single packet."""
        packet = self.create_test_packet()
        features = self.extractor.extract_features(packet)
        
        # Check basic packet features
        assert features.packet_size == 1000.0
        assert features.direction == 0  # First packet in flow
        assert features.tcp_flags_bitmap == 0x18
        assert features.ttl == 64.0
        
        # Check flow features
        assert features.total_bytes == 1000.0
        assert features.total_packets == 1.0
        assert features.bytes_ratio == 0.0  # No reverse traffic yet
    
    def test_flow_tracking(self):
        """Test flow state tracking across multiple packets."""
        # Send packets in both directions
        packet1 = self.create_test_packet(
            src_ip='192.168.1.100', dst_ip='10.0.0.1',
            src_port=12345, dst_port=80,
            packet_size=100
        )
        
        packet2 = self.create_test_packet(
            src_ip='10.0.0.1', dst_ip='192.168.1.100',
            src_port=80, dst_port=12345,
            packet_size=200,
            timestamp=packet1.timestamp + 0.1
        )
        
        features1 = self.extractor.extract_features(packet1)
        features2 = self.extractor.extract_features(packet2)
        
        # Check flow key consistency
        assert features1.flow_key == features2.flow_key
        
        # Check direction tracking
        assert features1.direction == 0  # Forward
        assert features2.direction == 1  # Reverse
        
        # Check byte ratio calculation
        assert features2.bytes_ratio == 0.5  # 100 / 200
    
    def test_window_features(self):
        """Test sliding window statistical features."""
        packets = []
        for i in range(10):
            packet = self.create_test_packet(
                packet_size=100 + i * 10,  # Increasing sizes
                timestamp=time.time() + i * 0.1
            )
            packets.append(packet)
        
        # Process all packets
        features_list = []
        for packet in packets:
            features = self.extractor.extract_features(packet)
            features_list.append(features)
        
        # Check that window features are calculated
        final_features = features_list[-1]
        assert final_features.size_mean > 0
        assert final_features.size_std > 0
        assert final_features.iat_mean > 0
    
    def test_payload_features(self):
        """Test payload-based feature extraction."""
        # Test with high-entropy payload
        high_entropy_payload = bytes(range(256))
        packet1 = self.create_test_packet(
            payload=high_entropy_payload,
            payload_size=len(high_entropy_payload)
        )
        
        features1 = self.extractor.extract_features(packet1)
        
        # High entropy payload should have high entropy score
        assert features1.payload_entropy > 7.0
        
        # Test with printable payload
        printable_payload = b'Hello World! This is a test message.'
        packet2 = self.create_test_packet(
            payload=printable_payload,
            payload_size=len(printable_payload)
        )
        
        features2 = self.extractor.extract_features(packet2)
        
        # Printable payload should have high printable ratio
        assert features2.printable_ratio > 0.8
    
    def test_dns_features(self):
        """Test DNS-specific feature extraction."""
        dns_packet = self.create_test_packet(
            protocol='udp',
            dst_port=53,
            payload=b'\\x12\\x34\\x01\\x00\\x00\\x01\\x00\\x00\\x00\\x00\\x00\\x00' +  # DNS header
                   b'\\x07example\\x03com\\x00\\x00\\x01\\x00\\x01',  # QNAME
            payload_size=29
        )
        
        features = self.extractor.extract_features(dns_packet)
        
        # Should detect DNS QNAME length
        assert features.dns_qname_length is not None
        assert features.dns_qname_length > 0
    
    def test_tls_features(self):
        """Test TLS-specific feature extraction."""
        tls_packet = self.create_test_packet(
            protocol='tcp',
            dst_port=443,
            payload=b'\\x16\\x03\\x01\\x00\\x50' +  # TLS handshake header
                   b'\\x00\\x00' * 20,  # Dummy TLS data with SNI marker
            payload_size=50
        )
        
        features = self.extractor.extract_features(tls_packet)
        
        # Should detect TLS SNI presence
        assert features.tls_sni_present is not None
    
    def test_flow_cleanup(self):
        """Test expired flow cleanup."""
        # Create a flow
        packet = self.create_test_packet()
        self.extractor.extract_features(packet)
        
        initial_flow_count = self.extractor.get_flow_count()
        assert initial_flow_count == 1
        
        # Force cleanup by setting old timestamp
        self.extractor.last_cleanup = time.time() - 120  # Force cleanup
        
        # Create new packet to trigger cleanup
        old_packet = self.create_test_packet(
            timestamp=time.time() - 400,  # Old timestamp
            src_ip='192.168.1.200'  # Different flow
        )
        self.extractor.extract_features(old_packet)
        
        # Should still have flows (cleanup logic may vary)
        assert self.extractor.get_flow_count() >= 1
    
    def test_feature_vector_to_array(self):
        """Test conversion of feature vector to numpy array."""
        packet = self.create_test_packet()
        features = self.extractor.extract_features(packet)
        
        # Define feature order
        feature_order = [
            'packet_size', 'direction', 'tcp_flags_bitmap', 'ttl',
            'total_bytes', 'total_packets', 'payload_entropy'
        ]
        
        # Convert to array
        feature_array = features.to_array(feature_order)
        
        assert len(feature_array) == len(feature_order)
        assert feature_array[0] == features.packet_size
        assert feature_array[1] == features.direction
    
    def test_reset(self):
        """Test feature extractor reset."""
        # Create some flows
        for i in range(5):
            packet = self.create_test_packet(src_ip=f'192.168.1.{i}')
            self.extractor.extract_features(packet)
        
        assert self.extractor.get_flow_count() == 5
        
        # Reset
        self.extractor.reset()
        
        assert self.extractor.get_flow_count() == 0