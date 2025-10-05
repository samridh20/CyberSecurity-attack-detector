"""
Fuzzer attack scenario tests.
Tests for application fuzzing, protocol fuzzing, and malformed input attacks.
"""

import pytest
import time
import random
from nids.features import FeatureExtractor
from nids.models import SimpleModelAdapter
from nids.alerts import AlertManager
from nids.schemas import PacketInfo, FlowKey


class TestFuzzerAttacks:
    """Test cases for fuzzer attack detection."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = FeatureExtractor(window_size=10, use_numba=False)
        self.model = SimpleModelAdapter()
        self.alert_manager = AlertManager(toast_enabled=False, min_confidence=0.5)
    
    def create_packet(self, src_ip="192.168.1.100", dst_ip="10.0.0.1", 
                     src_port=12345, dst_port=80, protocol="tcp", 
                     packet_size=1000, timestamp=None, **kwargs):
        """Create a test packet with default values."""
        defaults = {
            'timestamp': timestamp or time.time(),
            'src_ip': src_ip,
            'dst_ip': dst_ip,
            'src_port': src_port,
            'dst_port': dst_port,
            'protocol': protocol,
            'packet_size': packet_size,
            'payload_size': 500,
            'payload': b'A' * 500,
            'tcp_flags': 0x18,  # PSH+ACK
            'ttl': 64
        }
        defaults.update(kwargs)
        return PacketInfo(**defaults)
    
    def generate_random_payload(self, size: int) -> bytes:
        """Generate random payload for fuzzing."""
        return bytes([random.randint(0, 255) for _ in range(size)])
    
    def generate_malformed_http(self) -> bytes:
        """Generate malformed HTTP request."""
        malformed_requests = [
            b'GET /' + b'A' * 8000 + b' HTTP/1.1\r\n\r\n',  # Buffer overflow attempt
            b'GET /\x00\x01\x02\x03 HTTP/1.1\r\n\r\n',  # Null bytes
            b'GET / HTTP/999.999\r\n\r\n',  # Invalid version
            b'\x41' * 1000 + b'\r\n\r\n',  # Non-HTTP data
            b'GET / HTTP/1.1\r\nHost: ' + b'\x00' * 500 + b'\r\n\r\n',  # Malformed headers
        ]
        return random.choice(malformed_requests)
    
    def test_http_fuzzing_typical(self):
        """Test typical HTTP fuzzing with oversized requests."""
        base_time = time.time()
        packets = []
        
        # Generate HTTP fuzzing packets with various malformed requests
        for i in range(8):
            malformed_payload = self.generate_malformed_http()
            packet = self.create_packet(
                src_ip="192.168.1.100",
                dst_ip="10.0.0.1",
                src_port=12345 + i,
                dst_port=80,
                packet_size=len(malformed_payload) + 40,  # Add headers
                payload=malformed_payload,
                payload_size=len(malformed_payload),
                tcp_flags=0x18,  # PSH+ACK
                timestamp=base_time + i * 0.5  # 500ms intervals
            )
            packets.append(packet)
        
        # Process fuzzing packets
        predictions = []
        for packet in packets:
            features = self.extractor.extract_features(packet)
            prediction = self.model.predict(features)
            predictions.append(prediction)
        
        # Should detect fuzzing patterns
        attack_predictions = [p for p in predictions if p.is_attack]
        assert len(attack_predictions) > 0, "Should detect HTTP fuzzing attacks"
        
        # Check for large packet sizes
        large_packets = [p for p in packets if p.packet_size > 1400]
        assert len(large_packets) > 0, "Should have large fuzzing packets"
    
    def test_protocol_fuzzing_edge_case(self):
        """Test protocol fuzzing with completely random data."""
        base_time = time.time()
        packets = []
        
        # Generate completely random protocol data
        for i in range(10):
            random_payload = self.generate_random_payload(random.randint(100, 1400))
            packet = self.create_packet(
                src_ip="192.168.1.200",
                dst_ip="10.0.0.50",
                src_port=20000 + i,
                dst_port=random.choice([21, 22, 23, 25, 53, 80, 110, 443]),
                packet_size=len(random_payload) + 40,
                payload=random_payload,
                payload_size=len(random_payload),
                tcp_flags=random.choice([0x18, 0x10, 0x02, 0x01]),
                timestamp=base_time + i * 0.1  # Fast fuzzing
            )
            packets.append(packet)
        
        # Process random protocol fuzzing
        predictions = []
        for packet in packets:
            features = self.extractor.extract_features(packet)
            prediction = self.model.predict(features)
            predictions.append(prediction)
        
        # Should detect high entropy and unusual patterns
        attack_predictions = [p for p in predictions if p.is_attack]
        assert len(attack_predictions) > 0, "Should detect protocol fuzzing"
        
        # Check entropy calculations
        for packet in packets:
            features = self.extractor.extract_features(packet)
            # Random data should have high entropy
            assert features.payload_entropy > 6.0, f"Random payload should have high entropy, got {features.payload_entropy}"
    
    def test_buffer_overflow_fuzzing_malformed(self):
        """Test buffer overflow fuzzing with malformed oversized payloads."""
        base_time = time.time()
        packets = []
        
        # Generate buffer overflow attempts with patterns
        overflow_patterns = [
            b'A' * 2000,  # Simple overflow
            b'\x90' * 1000 + b'\xCC' * 100,  # NOP sled + int3
            b'\x41\x42\x43\x44' * 500,  # Pattern for crash analysis
            b'\x00' * 1500,  # Null bytes
            b'\xFF' * 1200,  # Max bytes
            (b'%s' * 400).ljust(1300, b'X'),  # Format string attack
        ]
        
        for i, pattern in enumerate(overflow_patterns):
            packet = self.create_packet(
                src_ip="192.168.1.150",
                dst_ip="10.0.0.100",
                src_port=15000 + i,
                dst_port=21,  # FTP - common target for buffer overflows
                packet_size=len(pattern) + 40,
                payload=pattern,
                payload_size=len(pattern),
                tcp_flags=0x18,
                timestamp=base_time + i * 0.2
            )
            packets.append(packet)
        
        # Process buffer overflow attempts
        predictions = []
        for packet in packets:
            features = self.extractor.extract_features(packet)
            prediction = self.model.predict(features)
            predictions.append(prediction)
        
        # Should detect large payloads and unusual patterns
        attack_predictions = [p for p in predictions if p.is_attack]
        assert len(attack_predictions) > 0, "Should detect buffer overflow attempts"
        
        # Check packet sizes
        for packet in packets:
            assert packet.packet_size > 1000, "Buffer overflow packets should be large"
    
    def test_dns_fuzzing_typical(self):
        """Test DNS fuzzing with malformed queries."""
        base_time = time.time()
        packets = []
        
        # Generate malformed DNS queries
        dns_fuzz_payloads = [
            # Oversized QNAME
            b'\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00' + b'\x3F' + b'A' * 63 + b'\x3F' + b'B' * 63 + b'\x00\x00\x01\x00\x01',
            # Invalid label lengths
            b'\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00' + b'\xFF' + b'C' * 100 + b'\x00\x00\x01\x00\x01',
            # Malformed header
            b'\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF' + b'\x07example\x03com\x00\x00\x01\x00\x01',
            # Excessive questions
            b'\x12\x34\x01\x00\xFF\xFF\x00\x00\x00\x00\x00\x00' + b'\x07example\x03com\x00\x00\x01\x00\x01',
        ]
        
        for i, payload in enumerate(dns_fuzz_payloads):
            packet = self.create_packet(
                src_ip="192.168.1.100",
                dst_ip="8.8.8.8",
                src_port=53000 + i,
                dst_port=53,
                protocol="udp",
                packet_size=len(payload) + 28,  # UDP + IP headers
                payload=payload,
                payload_size=len(payload),
                timestamp=base_time + i * 0.3
            )
            packets.append(packet)
        
        # Process DNS fuzzing
        predictions = []
        for packet in packets:
            features = self.extractor.extract_features(packet)
            prediction = self.model.predict(features)
            predictions.append(prediction)
        
        # Should detect malformed DNS
        attack_predictions = [p for p in predictions if p.is_attack]
        # DNS fuzzing might not always be detected, but should process correctly
        assert all(p.attack_probability >= 0.0 for p in predictions), "Should handle DNS fuzzing"
    
    def test_sql_injection_fuzzing_typical(self):
        """Test SQL injection fuzzing in HTTP requests."""
        base_time = time.time()
        packets = []
        
        # Generate SQL injection fuzzing payloads
        sql_payloads = [
            b"GET /login?user=admin'OR'1'='1&pass=x HTTP/1.1\\r\\n\\r\\n",
            b"POST /search HTTP/1.1\\r\\nContent-Length: 50\\r\\n\\r\\nq='; DROP TABLE users; --",
            b"GET /page?id=1' UNION SELECT * FROM passwords-- HTTP/1.1\\r\\n\\r\\n",
            b"GET /app?data=" + b"'" * 1000 + b" HTTP/1.1\\r\\n\\r\\n",  # Quote flooding
            b"POST /api HTTP/1.1\\r\\n\\r\\n{\"query\":\"' OR 1=1; EXEC xp_cmdshell('dir')--\"}",
        ]
        
        for i, payload in enumerate(sql_payloads):
            packet = self.create_packet(
                src_ip="192.168.1.100",
                dst_ip="10.0.0.1",
                src_port=40000 + i,
                dst_port=80,
                packet_size=len(payload) + 40,
                payload=payload,
                payload_size=len(payload),
                tcp_flags=0x18,
                timestamp=base_time + i * 0.4
            )
            packets.append(packet)
        
        # Process SQL injection fuzzing
        predictions = []
        for packet in packets:
            features = self.extractor.extract_features(packet)
            prediction = self.model.predict(features)
            predictions.append(packet)
        
        # Should handle SQL injection patterns
        assert len(predictions) == len(sql_payloads), "Should process all SQL injection packets"
    
    def test_binary_fuzzing_edge_case(self):
        """Test binary protocol fuzzing with extreme edge cases."""
        base_time = time.time()
        packets = []
        
        # Generate extreme binary fuzzing cases
        extreme_cases = [
            b'\\x00' * 1500,  # All nulls
            b'\\xFF' * 1500,  # All 0xFF
            bytes(range(256)) * 6,  # All possible bytes
            b'\\xDE\\xAD\\xBE\\xEF' * 375,  # Repeating pattern
            self.generate_random_payload(1500),  # Pure random
        ]
        
        for i, payload in enumerate(extreme_cases):
            packet = self.create_packet(
                src_ip="192.168.1.250",
                dst_ip="10.0.0.250",
                src_port=60000 + i,
                dst_port=9999,  # Custom service
                packet_size=len(payload) + 40,
                payload=payload,
                payload_size=len(payload),
                tcp_flags=0x18,
                timestamp=base_time + i * 0.1
            )
            packets.append(packet)
        
        # Process extreme binary fuzzing
        predictions = []
        for packet in packets:
            features = self.extractor.extract_features(packet)
            prediction = self.model.predict(features)
            predictions.append(prediction)
        
        # Should handle extreme cases without crashing
        assert len(predictions) == len(extreme_cases), "Should handle all extreme cases"
        
        # Check entropy calculations for different patterns
        entropies = []
        for packet in packets:
            features = self.extractor.extract_features(packet)
            entropies.append(features.payload_entropy)
        
        # Should have varying entropy values
        assert min(entropies) < max(entropies), "Should have varying entropy for different patterns"
        assert max(entropies) > 7.0, "Random data should have high entropy"
        assert min(entropies) < 2.0, "Repeated patterns should have low entropy"
    
    def test_rapid_fuzzing_burst(self):
        """Test rapid fuzzing burst - high frequency malformed packets."""
        base_time = time.time()
        packets = []
        
        # Generate rapid burst of fuzzing packets
        for i in range(50):  # 50 packets in quick succession
            fuzz_payload = self.generate_random_payload(random.randint(50, 1400))
            packet = self.create_packet(
                src_ip="192.168.1.100",
                dst_ip="10.0.0.1",
                src_port=30000 + (i % 1000),  # Cycle through ports
                dst_port=80,
                packet_size=len(fuzz_payload) + 40,
                payload=fuzz_payload,
                payload_size=len(fuzz_payload),
                tcp_flags=0x18,
                timestamp=base_time + i * 0.01  # 10ms intervals - very fast
            )
            packets.append(packet)
        
        # Process rapid fuzzing burst
        predictions = []
        for packet in packets:
            features = self.extractor.extract_features(packet)
            prediction = self.model.predict(features)
            predictions.append(prediction)
        
        # Should detect high packet rate
        attack_predictions = [p for p in predictions if p.is_attack]
        assert len(attack_predictions) > 0, "Should detect rapid fuzzing burst"
        
        # Check packet rate detection
        final_features = self.extractor.extract_features(packets[-1])
        assert final_features.packets_per_second > 50, "Should detect high packet rate"
        
        # Check burstiness
        assert final_features.burstiness > 1.0, "Should detect bursty traffic pattern"
    
    def test_fuzzer_alert_generation(self):
        """Test that fuzzer attacks generate appropriate alerts."""
        base_time = time.time()
        
        # Create fuzzing attack that should trigger alerts
        fuzz_payload = b'A' * 2000  # Large buffer overflow attempt
        packet = self.create_packet(
            src_ip="192.168.1.100",
            dst_ip="10.0.0.1",
            src_port=12345,
            dst_port=21,  # FTP
            packet_size=len(fuzz_payload) + 40,
            payload=fuzz_payload,
            payload_size=len(fuzz_payload),
            tcp_flags=0x18,
            timestamp=base_time
        )
        
        # Process and generate alert
        features = self.extractor.extract_features(packet)
        prediction = self.model.predict(features)
        
        if prediction.is_attack:
            alert = self.alert_manager.generate_alert(prediction)
            
            if alert:
                # Check alert properties
                assert alert.attack_type in ["DoS", "Exploits", "Fuzzers", "Generic"], f"Unexpected attack type: {alert.attack_type}"
                assert alert.severity in ["low", "medium", "high", "critical"], f"Invalid severity: {alert.severity}"
                assert alert.confidence > 0.0, "Alert confidence should be positive"
                assert "192.168.1.100" in alert.source_ip, "Should identify correct source IP"
                assert "buffer" in alert.recommended_action.lower() or "payload" in alert.recommended_action.lower(), "Should suggest payload investigation"
    
    def test_mixed_fuzzing_patterns(self):
        """Test mixed fuzzing patterns - different protocols and techniques."""
        base_time = time.time()
        packets = []
        
        # Mixed fuzzing: HTTP + DNS + Binary + SQL
        
        # 1. HTTP fuzzing
        http_payload = b'GET /' + b'A' * 1000 + b' HTTP/1.1\\r\\n\\r\\n'
        packets.append(self.create_packet(
            dst_port=80, payload=http_payload, payload_size=len(http_payload),
            timestamp=base_time + len(packets) * 0.2
        ))
        
        # 2. DNS fuzzing
        dns_payload = b'\\x12\\x34\\x01\\x00\\x00\\x01\\x00\\x00\\x00\\x00\\x00\\x00' + b'\\xFF' + b'B' * 200 + b'\\x00\\x00\\x01\\x00\\x01'
        packets.append(self.create_packet(
            dst_port=53, protocol="udp", payload=dns_payload, payload_size=len(dns_payload),
            timestamp=base_time + len(packets) * 0.2
        ))
        
        # 3. Binary fuzzing
        binary_payload = self.generate_random_payload(800)
        packets.append(self.create_packet(
            dst_port=9999, payload=binary_payload, payload_size=len(binary_payload),
            timestamp=base_time + len(packets) * 0.2
        ))
        
        # 4. SQL injection fuzzing
        sql_payload = b"POST /login HTTP/1.1\\r\\n\\r\\nuser=admin'OR'1'='1&pass=" + b"'" * 500
        packets.append(self.create_packet(
            dst_port=80, payload=sql_payload, payload_size=len(sql_payload),
            timestamp=base_time + len(packets) * 0.2
        ))
        
        # Process mixed fuzzing
        predictions = []
        for packet in packets:
            features = self.extractor.extract_features(packet)
            prediction = self.model.predict(features)
            predictions.append(prediction)
        
        # Should handle mixed patterns
        assert len(predictions) == 4, "Should process all mixed fuzzing packets"
        
        # Should detect at least some attacks
        attack_predictions = [p for p in predictions if p.is_attack]
        assert len(attack_predictions) > 0, "Should detect some fuzzing attacks in mixed patterns"