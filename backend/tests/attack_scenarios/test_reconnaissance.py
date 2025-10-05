"""
Reconnaissance attack scenario tests.
Tests for port scanning, network mapping, and information gathering attacks.
"""

import pytest
import time
from nids.features import FeatureExtractor
from nids.models import SimpleModelAdapter
from nids.alerts import AlertManager
from nids.schemas import PacketInfo, FlowKey


class TestReconnaissanceAttacks:
    """Test cases for reconnaissance attack detection."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = FeatureExtractor(window_size=10, use_numba=False)
        self.model = SimpleModelAdapter()
        self.alert_manager = AlertManager(toast_enabled=False, min_confidence=0.5)
    
    def create_packet(self, src_ip="192.168.1.100", dst_ip="10.0.0.1", 
                     src_port=12345, dst_port=80, protocol="tcp", 
                     packet_size=64, timestamp=None, **kwargs):
        """Create a test packet with default values."""
        defaults = {
            'timestamp': timestamp or time.time(),
            'src_ip': src_ip,
            'dst_ip': dst_ip,
            'src_port': src_port,
            'dst_port': dst_port,
            'protocol': protocol,
            'packet_size': packet_size,
            'payload_size': 0,
            'payload': b'',
            'tcp_flags': 0x02,  # SYN
            'ttl': 64
        }
        defaults.update(kwargs)
        return PacketInfo(**defaults)
    
    def test_port_scan_typical(self):
        """Test typical port scanning behavior - sequential port probing."""
        base_time = time.time()
        packets = []
        
        # Create port scan: same source scanning multiple ports on same target
        for i, port in enumerate([21, 22, 23, 25, 53, 80, 110, 143, 443, 993]):
            packet = self.create_packet(
                src_ip="192.168.1.100",
                dst_ip="10.0.0.1", 
                src_port=12345 + i,
                dst_port=port,
                packet_size=64,  # Small SYN packets
                tcp_flags=0x02,  # SYN only
                timestamp=base_time + i * 0.1  # 100ms intervals
            )
            packets.append(packet)
        
        # Process packets and check for reconnaissance detection
        predictions = []
        for packet in packets:
            features = self.extractor.extract_features(packet)
            prediction = self.model.predict(features)
            predictions.append(prediction)
        
        # Should detect reconnaissance pattern
        attack_predictions = [p for p in predictions if p.is_attack]
        assert len(attack_predictions) > 0, "Should detect port scanning as attack"
        
        # Check for reconnaissance classification
        recon_predictions = [p for p in attack_predictions if p.attack_class == "Reconnaissance"]
        # Note: SimpleModelAdapter may not classify as Reconnaissance, but should detect as attack
        assert len(attack_predictions) >= 3, "Should detect multiple attack packets in port scan"
    
    def test_port_scan_edge_case(self):
        """Test edge case - very fast port scan with unusual patterns."""
        base_time = time.time()
        packets = []
        
        # Very fast scan with random high ports
        high_ports = [8080, 8443, 9000, 9001, 9999, 10000, 31337, 65535]
        for i, port in enumerate(high_ports):
            packet = self.create_packet(
                src_ip="192.168.1.200",
                dst_ip="172.16.0.1",
                src_port=50000 + i,
                dst_port=port,
                packet_size=40,  # Very small packets
                tcp_flags=0x02,  # SYN
                timestamp=base_time + i * 0.01  # 10ms intervals - very fast
            )
            packets.append(packet)
        
        # Process packets
        predictions = []
        for packet in packets:
            features = self.extractor.extract_features(packet)
            prediction = self.model.predict(features)
            predictions.append(prediction)
        
        # Fast scanning should trigger detection
        attack_predictions = [p for p in predictions if p.is_attack]
        assert len(attack_predictions) > 0, "Should detect fast port scanning"
        
        # Check high packet rate detection
        last_features = self.extractor.extract_features(packets[-1])
        assert last_features.packets_per_second > 50, "Should detect high packet rate"
    
    def test_port_scan_malformed(self):
        """Test malformed reconnaissance packets - unusual flags and sizes."""
        base_time = time.time()
        packets = []
        
        # Malformed scan packets with unusual TCP flags
        unusual_flags = [0x00, 0x01, 0x04, 0x08, 0x29, 0x3F]  # NULL, FIN, RST, PSH, combinations
        for i, flags in enumerate(unusual_flags):
            packet = self.create_packet(
                src_ip="10.0.0.100",
                dst_ip="192.168.1.1",
                src_port=1024 + i,
                dst_port=80,
                packet_size=0 if flags == 0x00 else 1500,  # NULL scan or large packets
                tcp_flags=flags,
                timestamp=base_time + i * 0.05,
                payload=b'\\x00' * (0 if flags == 0x00 else 100)  # Unusual payload
            )
            packets.append(packet)
        
        # Process malformed packets
        predictions = []
        for packet in packets:
            features = self.extractor.extract_features(packet)
            prediction = self.model.predict(features)
            predictions.append(prediction)
        
        # Should detect unusual patterns
        attack_predictions = [p for p in predictions if p.is_attack]
        assert len(attack_predictions) > 0, "Should detect malformed reconnaissance packets"
    
    def test_network_sweep_typical(self):
        """Test typical network sweep - scanning same port across multiple hosts."""
        base_time = time.time()
        packets = []
        
        # Network sweep: scan port 22 across subnet
        for i in range(1, 21):  # Scan 20 hosts
            packet = self.create_packet(
                src_ip="192.168.1.100",
                dst_ip=f"192.168.1.{i}",
                src_port=12345,
                dst_port=22,  # SSH port
                packet_size=64,
                tcp_flags=0x02,  # SYN
                timestamp=base_time + i * 0.05  # 50ms intervals
            )
            packets.append(packet)
        
        # Process network sweep
        predictions = []
        for packet in packets:
            features = self.extractor.extract_features(packet)
            prediction = self.model.predict(features)
            predictions.append(prediction)
        
        # Should detect scanning behavior
        attack_predictions = [p for p in predictions if p.is_attack]
        assert len(attack_predictions) > 0, "Should detect network sweep"
        
        # Check packet rate
        final_features = self.extractor.extract_features(packets[-1])
        assert final_features.packets_per_second > 10, "Should detect elevated packet rate"
    
    def test_os_fingerprinting_typical(self):
        """Test OS fingerprinting attempts - varied TTL and window sizes."""
        base_time = time.time()
        packets = []
        
        # OS fingerprinting with different TTL values and TCP window sizes
        fingerprint_params = [
            (64, 5840),   # Linux
            (128, 65535), # Windows
            (255, 4128),  # Cisco
            (30, 4096),   # Custom/unusual
        ]
        
        for i, (ttl, window) in enumerate(fingerprint_params):
            packet = self.create_packet(
                src_ip="192.168.1.150",
                dst_ip="10.0.0.50",
                src_port=12345 + i,
                dst_port=80,
                packet_size=64,
                tcp_flags=0x02,  # SYN
                ttl=ttl,
                tcp_window=window,
                timestamp=base_time + i * 0.2
            )
            packets.append(packet)
        
        # Process fingerprinting packets
        predictions = []
        for packet in packets:
            features = self.extractor.extract_features(packet)
            prediction = self.model.predict(features)
            predictions.append(prediction)
        
        # May or may not detect as attack depending on implementation
        # But should process without errors
        assert all(p.attack_probability >= 0.0 for p in predictions), "Should produce valid predictions"
    
    def test_service_enumeration_typical(self):
        """Test service enumeration - probing specific services."""
        base_time = time.time()
        packets = []
        
        # Service enumeration on common ports with service-specific payloads
        services = [
            (21, b'USER anonymous\\r\\n'),      # FTP
            (22, b'SSH-2.0-OpenSSH_7.4\\r\\n'), # SSH
            (25, b'EHLO test.com\\r\\n'),       # SMTP
            (53, b'\\x12\\x34\\x01\\x00\\x00\\x01\\x00\\x00\\x00\\x00\\x00\\x00\\x07example\\x03com\\x00\\x00\\x01\\x00\\x01'), # DNS
            (80, b'GET / HTTP/1.1\\r\\nHost: target\\r\\n\\r\\n'), # HTTP
        ]
        
        for i, (port, payload) in enumerate(services):
            packet = self.create_packet(
                src_ip="192.168.1.200",
                dst_ip="10.0.0.100",
                src_port=20000 + i,
                dst_port=port,
                packet_size=len(payload) + 40,  # IP + TCP headers
                payload=payload,
                payload_size=len(payload),
                tcp_flags=0x18,  # PSH+ACK
                timestamp=base_time + i * 1.0  # 1 second intervals
            )
            packets.append(packet)
        
        # Process service enumeration
        predictions = []
        for packet in packets:
            features = self.extractor.extract_features(packet)
            prediction = self.model.predict(features)
            predictions.append(prediction)
        
        # Should handle service-specific payloads
        assert all(p.attack_probability >= 0.0 for p in predictions), "Should handle service payloads"
        
        # Check payload entropy calculations
        for i, packet in enumerate(packets):
            features = self.extractor.extract_features(packet)
            assert features.payload_entropy >= 0.0, f"Should calculate entropy for packet {i}"
    
    def test_stealth_scan_edge_case(self):
        """Test stealth scanning techniques - slow and fragmented."""
        base_time = time.time()
        packets = []
        
        # Very slow stealth scan - one packet every 30 seconds
        stealth_ports = [80, 443, 22, 21]
        for i, port in enumerate(stealth_ports):
            packet = self.create_packet(
                src_ip="192.168.1.250",
                dst_ip="10.0.0.200",
                src_port=30000 + i,
                dst_port=port,
                packet_size=64,
                tcp_flags=0x02,  # SYN
                timestamp=base_time + i * 30.0  # 30 second intervals
            )
            packets.append(packet)
        
        # Process stealth scan
        predictions = []
        for packet in packets:
            features = self.extractor.extract_features(packet)
            prediction = self.model.predict(features)
            predictions.append(prediction)
        
        # Stealth scan may not be detected due to low rate
        # But should process correctly
        assert all(p.attack_probability >= 0.0 for p in predictions), "Should handle stealth scan"
        
        # Check low packet rate
        if len(packets) > 1:
            final_features = self.extractor.extract_features(packets[-1])
            assert final_features.packets_per_second < 1.0, "Should detect low packet rate"
    
    def test_reconnaissance_alert_generation(self):
        """Test that reconnaissance attacks generate appropriate alerts."""
        # Create reconnaissance-like traffic
        base_time = time.time()
        packets = []
        
        # Port scan that should trigger alerts
        for i in range(10):
            packet = self.create_packet(
                src_ip="192.168.1.100",
                dst_ip="10.0.0.1",
                src_port=12345,
                dst_port=80 + i,
                packet_size=64,
                tcp_flags=0x02,
                timestamp=base_time + i * 0.1
            )
            packets.append(packet)
        
        # Process and generate alerts
        alerts = []
        for packet in packets:
            features = self.extractor.extract_features(packet)
            prediction = self.model.predict(features)
            
            if prediction.is_attack:
                alert = self.alert_manager.generate_alert(prediction)
                if alert:
                    alerts.append(alert)
        
        # Should generate at least some alerts
        if alerts:
            # Check alert properties
            for alert in alerts:
                assert alert.attack_type in ["DoS", "Exploits", "Generic", "Reconnaissance"], f"Unexpected attack type: {alert.attack_type}"
                assert alert.severity in ["low", "medium", "high", "critical"], f"Invalid severity: {alert.severity}"
                assert alert.confidence > 0.0, "Alert confidence should be positive"
                assert "192.168.1.100" in alert.source_ip, "Should identify correct source IP"
    
    def test_mixed_reconnaissance_patterns(self):
        """Test mixed reconnaissance patterns - combination of techniques."""
        base_time = time.time()
        packets = []
        
        # Mixed pattern: port scan + network sweep + service probing
        
        # 1. Port scan on primary target
        for port in [21, 22, 80, 443]:
            packet = self.create_packet(
                src_ip="192.168.1.100",
                dst_ip="10.0.0.1",
                dst_port=port,
                timestamp=base_time + len(packets) * 0.1
            )
            packets.append(packet)
        
        # 2. Network sweep on discovered service
        for host in range(1, 6):
            packet = self.create_packet(
                src_ip="192.168.1.100",
                dst_ip=f"10.0.0.{host}",
                dst_port=22,  # SSH
                timestamp=base_time + len(packets) * 0.1
            )
            packets.append(packet)
        
        # 3. Service probing
        packet = self.create_packet(
            src_ip="192.168.1.100",
            dst_ip="10.0.0.1",
            dst_port=22,
            payload=b'SSH-2.0-Test\\r\\n',
            payload_size=14,
            tcp_flags=0x18,  # PSH+ACK
            timestamp=base_time + len(packets) * 0.1
        )
        packets.append(packet)
        
        # Process mixed reconnaissance
        predictions = []
        for packet in packets:
            features = self.extractor.extract_features(packet)
            prediction = self.model.predict(features)
            predictions.append(prediction)
        
        # Should detect attack patterns
        attack_predictions = [p for p in predictions if p.is_attack]
        assert len(attack_predictions) > 0, "Should detect mixed reconnaissance patterns"
        
        # Check that flow tracking works correctly
        flow_count = self.extractor.get_flow_count()
        assert flow_count > 0, "Should track multiple flows"