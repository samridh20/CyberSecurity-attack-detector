"""
DDoS attack scenario tests.
Tests for Distributed Denial of Service attacks including volumetric, protocol, and application layer attacks.
"""

import pytest
import time
import random
from nids.features import FeatureExtractor
from nids.models import SimpleModelAdapter
from nids.alerts import AlertManager
from nids.schemas import PacketInfo, FlowKey


class TestDDoSAttacks:
    """Test cases for DDoS attack detection."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = FeatureExtractor(window_size=20, use_numba=False)  # Larger window for DDoS
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
            'payload_size': 100,
            'payload': b'DDoS attack payload',
            'tcp_flags': 0x02,  # SYN for most DDoS
            'ttl': 64
        }
        defaults.update(kwargs)
        return PacketInfo(**defaults)
    
    def generate_botnet_ips(self, count: int) -> list:
        """Generate list of botnet IP addresses."""
        ips = []
        for i in range(count):
            # Generate diverse IP ranges
            if i % 4 == 0:
                ip = f"192.168.{random.randint(1, 254)}.{random.randint(1, 254)}"
            elif i % 4 == 1:
                ip = f"10.{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}"
            elif i % 4 == 2:
                ip = f"172.{random.randint(16, 31)}.{random.randint(1, 254)}.{random.randint(1, 254)}"
            else:
                ip = f"{random.randint(1, 223)}.{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}"
            ips.append(ip)
        return ips
    
    def test_syn_flood_typical(self):
        """Test typical SYN flood attack from multiple sources."""
        base_time = time.time()
        packets = []
        
        # Generate SYN flood from multiple sources
        botnet_ips = self.generate_botnet_ips(50)
        
        for i, src_ip in enumerate(botnet_ips):
            packet = self.create_packet(
                src_ip=src_ip,
                dst_ip="10.0.0.1",
                src_port=random.randint(1024, 65535),
                dst_port=80,
                packet_size=64,  # Small SYN packets
                tcp_flags=0x02,  # SYN only
                timestamp=base_time + i * 0.01,  # 10ms intervals - very fast
                payload=b'',
                payload_size=0
            )
            packets.append(packet)
        
        # Process SYN flood
        predictions = []
        for packet in packets:
            features = self.extractor.extract_features(packet)
            prediction = self.model.predict(features)
            predictions.append(prediction)
        
        # Should detect high packet rate
        attack_predictions = [p for p in predictions if p.is_attack]
        assert len(attack_predictions) > 0, "Should detect SYN flood attack"
        
        # Check packet rate detection
        if len(packets) > 10:
            final_features = self.extractor.extract_features(packets[-1])
            assert final_features.packets_per_second > 100, f"Should detect high packet rate, got {final_features.packets_per_second}"
    
    def test_udp_flood_typical(self):
        """Test typical UDP flood attack."""
        base_time = time.time()
        packets = []
        
        # Generate UDP flood
        botnet_ips = self.generate_botnet_ips(30)
        
        for i, src_ip in enumerate(botnet_ips):
            # Random UDP payload
            payload_size = random.randint(100, 1400)
            payload = bytes([random.randint(0, 255) for _ in range(payload_size)])
            
            packet = self.create_packet(
                src_ip=src_ip,
                dst_ip="10.0.0.1",
                src_port=random.randint(1024, 65535),
                dst_port=random.choice([53, 123, 161, 1900]),  # Common UDP targets
                protocol="udp",
                packet_size=payload_size + 28,  # UDP + IP headers
                payload=payload,
                payload_size=payload_size,
                timestamp=base_time + i * 0.02  # 20ms intervals
            )
            packets.append(packet)
        
        # Process UDP flood
        predictions = []
        for packet in packets:
            features = self.extractor.extract_features(packet)
            prediction = self.model.predict(features)
            predictions.append(prediction)
        
        # Should detect UDP flood
        attack_predictions = [p for p in predictions if p.is_attack]
        assert len(attack_predictions) > 0, "Should detect UDP flood attack"
    
    def test_icmp_flood_edge_case(self):
        """Test ICMP flood with various packet sizes."""
        base_time = time.time()
        packets = []
        
        # Generate ICMP flood with varying sizes
        botnet_ips = self.generate_botnet_ips(25)
        
        for i, src_ip in enumerate(botnet_ips):
            # Vary ICMP packet sizes
            if i % 3 == 0:
                packet_size = 64   # Small ping
            elif i % 3 == 1:
                packet_size = 1500  # Large ping
            else:
                packet_size = random.randint(100, 1400)
            
            packet = self.create_packet(
                src_ip=src_ip,
                dst_ip="10.0.0.1",
                src_port=0,  # ICMP doesn't use ports
                dst_port=0,
                protocol="icmp",
                packet_size=packet_size,
                payload=b'\\x08\\x00' + b'\\x00' * (packet_size - 10),  # ICMP echo request
                payload_size=packet_size - 8,  # Minus ICMP header
                timestamp=base_time + i * 0.05  # 50ms intervals
            )
            packets.append(packet)
        
        # Process ICMP flood
        predictions = []
        for packet in packets:
            features = self.extractor.extract_features(packet)
            prediction = self.model.predict(features)
            predictions.append(prediction)
        
        # Should detect ICMP flood
        attack_predictions = [p for p in predictions if p.is_attack]
        assert len(attack_predictions) > 0, "Should detect ICMP flood attack"
    
    def test_amplification_attack_typical(self):
        """Test DNS/NTP amplification attack."""
        base_time = time.time()
        packets = []
        
        # Simulate amplification attack - small requests, large responses
        amplification_targets = [
            ("8.8.8.8", 53, b'\\x12\\x34\\x01\\x00\\x00\\x01\\x00\\x00\\x00\\x00\\x00\\x00\\x07version\\x04bind\\x00\\x00\\x10\\x00\\x03'),  # DNS
            ("pool.ntp.org", 123, b'\\x17\\x00\\x03\\x2a' + b'\\x00' * 44),  # NTP monlist
        ]
        
        # Generate amplification requests (spoofed source)
        for i in range(20):
            target_ip, target_port, request_payload = random.choice(amplification_targets)
            
            packet = self.create_packet(
                src_ip="10.0.0.1",  # Spoofed victim IP
                dst_ip=target_ip,
                src_port=random.randint(1024, 65535),
                dst_port=target_port,
                protocol="udp",
                packet_size=len(request_payload) + 28,
                payload=request_payload,
                payload_size=len(request_payload),
                timestamp=base_time + i * 0.1
            )
            packets.append(packet)
        
        # Generate amplified responses (large)
        for i in range(20):
            # Large response payload
            response_payload = b'\\x12\\x34\\x81\\x80' + b'A' * 1400  # Large DNS/NTP response
            
            packet = self.create_packet(
                src_ip=random.choice(["8.8.8.8", "pool.ntp.org"]),
                dst_ip="10.0.0.1",  # Victim
                src_port=random.choice([53, 123]),
                dst_port=random.randint(1024, 65535),
                protocol="udp",
                packet_size=len(response_payload) + 28,
                payload=response_payload,
                payload_size=len(response_payload),
                timestamp=base_time + 10.0 + i * 0.05  # Responses come later
            )
            packets.append(packet)
        
        # Process amplification attack
        predictions = []
        for packet in packets:
            features = self.extractor.extract_features(packet)
            prediction = self.model.predict(features)
            predictions.append(prediction)
        
        # Should detect amplification patterns
        attack_predictions = [p for p in predictions if p.is_attack]
        assert len(attack_predictions) > 0, "Should detect amplification attack"
    
    def test_slowloris_attack_edge_case(self):
        """Test Slowloris-style application layer DDoS."""
        base_time = time.time()
        packets = []
        
        # Slowloris: many partial HTTP requests
        botnet_ips = self.generate_botnet_ips(100)
        
        for i, src_ip in enumerate(botnet_ips):
            # Partial HTTP request
            partial_request = b"GET / HTTP/1.1\\r\\nHost: target.com\\r\\nUser-Agent: Mozilla/5.0\\r\\nAccept: */*\\r\\n"
            # Note: Missing final \\r\\n to keep connection open
            
            packet = self.create_packet(
                src_ip=src_ip,
                dst_ip="10.0.0.1",
                src_port=random.randint(1024, 65535),
                dst_port=80,
                packet_size=len(partial_request) + 40,
                payload=partial_request,
                payload_size=len(partial_request),
                tcp_flags=0x18,  # PSH+ACK
                timestamp=base_time + i * 1.0  # Slow - 1 second intervals
            )
            packets.append(packet)
        
        # Process Slowloris attack
        predictions = []
        for packet in packets:
            features = self.extractor.extract_features(packet)
            prediction = self.model.predict(features)
            predictions.append(prediction)
        
        # Slowloris might not be detected due to low rate, but should process
        assert len(predictions) == len(packets), "Should process all Slowloris packets"
        
        # Check for multiple flows (many connections)
        flow_count = self.extractor.get_flow_count()
        assert flow_count > 50, f"Should track many flows for Slowloris, got {flow_count}"
    
    def test_http_flood_malformed(self):
        """Test HTTP flood with malformed requests."""
        base_time = time.time()
        packets = []
        
        # Generate malformed HTTP flood
        malformed_requests = [
            b"GET / HTTP/1.1\\r\\n\\r\\n",
            b"POST / HTTP/1.1\\r\\nContent-Length: -1\\r\\n\\r\\n",
            b"GET /" + b"A" * 8000 + b" HTTP/1.1\\r\\n\\r\\n",
            b"\\x00\\x01\\x02\\x03 / HTTP/1.1\\r\\n\\r\\n",
            b"GET / HTTP/999.999\\r\\n\\r\\n",
        ]
        
        botnet_ips = self.generate_botnet_ips(50)
        
        for i, src_ip in enumerate(botnet_ips):
            malformed_request = random.choice(malformed_requests)
            
            packet = self.create_packet(
                src_ip=src_ip,
                dst_ip="10.0.0.1",
                src_port=random.randint(1024, 65535),
                dst_port=80,
                packet_size=len(malformed_request) + 40,
                payload=malformed_request,
                payload_size=len(malformed_request),
                tcp_flags=0x18,
                timestamp=base_time + i * 0.02  # 20ms intervals
            )
            packets.append(packet)
        
        # Process malformed HTTP flood
        predictions = []
        for packet in packets:
            features = self.extractor.extract_features(packet)
            prediction = self.model.predict(features)
            predictions.append(prediction)
        
        # Should detect HTTP flood
        attack_predictions = [p for p in predictions if p.is_attack]
        assert len(attack_predictions) > 0, "Should detect malformed HTTP flood"
    
    def test_mixed_protocol_ddos_typical(self):
        """Test mixed protocol DDoS attack."""
        base_time = time.time()
        packets = []
        
        # Mixed protocol attack: TCP + UDP + ICMP
        botnet_ips = self.generate_botnet_ips(60)
        
        for i, src_ip in enumerate(botnet_ips):
            if i % 3 == 0:
                # TCP SYN flood
                packet = self.create_packet(
                    src_ip=src_ip,
                    dst_ip="10.0.0.1",
                    dst_port=80,
                    protocol="tcp",
                    packet_size=64,
                    tcp_flags=0x02,
                    payload=b'',
                    payload_size=0,
                    timestamp=base_time + i * 0.01
                )
            elif i % 3 == 1:
                # UDP flood
                udp_payload = bytes([random.randint(0, 255) for _ in range(500)])
                packet = self.create_packet(
                    src_ip=src_ip,
                    dst_ip="10.0.0.1",
                    dst_port=53,
                    protocol="udp",
                    packet_size=len(udp_payload) + 28,
                    payload=udp_payload,
                    payload_size=len(udp_payload),
                    timestamp=base_time + i * 0.01
                )
            else:
                # ICMP flood
                packet = self.create_packet(
                    src_ip=src_ip,
                    dst_ip="10.0.0.1",
                    src_port=0,
                    dst_port=0,
                    protocol="icmp",
                    packet_size=1000,
                    payload=b'\\x08\\x00' + b'\\x00' * 990,
                    payload_size=992,
                    timestamp=base_time + i * 0.01
                )
            
            packets.append(packet)
        
        # Process mixed protocol DDoS
        predictions = []
        for packet in packets:
            features = self.extractor.extract_features(packet)
            prediction = self.model.predict(features)
            predictions.append(prediction)
        
        # Should detect mixed protocol attack
        attack_predictions = [p for p in predictions if p.is_attack]
        assert len(attack_predictions) > 0, "Should detect mixed protocol DDoS"
        
        # Check high packet rate
        if len(packets) > 20:
            final_features = self.extractor.extract_features(packets[-1])
            assert final_features.packets_per_second > 50, "Should detect high packet rate in mixed attack"
    
    def test_reflection_attack_typical(self):
        """Test reflection attack using legitimate services."""
        base_time = time.time()
        packets = []
        
        # Reflection attack: requests to legitimate servers with spoofed source
        reflection_services = [
            ("8.8.8.8", 53, b'\\x12\\x34\\x01\\x00\\x00\\x01\\x00\\x00\\x00\\x00\\x00\\x00\\x03www\\x06google\\x03com\\x00\\x00\\x01\\x00\\x01'),
            ("1.1.1.1", 53, b'\\x56\\x78\\x01\\x00\\x00\\x01\\x00\\x00\\x00\\x00\\x00\\x00\\x07example\\x03com\\x00\\x00\\x01\\x00\\x01'),
            ("time.nist.gov", 123, b'\\x1b\\x00\\x00\\x00' + b'\\x00' * 44),
        ]
        
        # Generate reflection requests
        for i in range(30):
            server_ip, server_port, request_payload = random.choice(reflection_services)
            
            packet = self.create_packet(
                src_ip="10.0.0.1",  # Spoofed victim IP
                dst_ip=server_ip,
                src_port=random.randint(1024, 65535),
                dst_port=server_port,
                protocol="udp",
                packet_size=len(request_payload) + 28,
                payload=request_payload,
                payload_size=len(request_payload),
                timestamp=base_time + i * 0.05
            )
            packets.append(packet)
        
        # Process reflection attack
        predictions = []
        for packet in packets:
            features = self.extractor.extract_features(packet)
            prediction = self.model.predict(features)
            predictions.append(prediction)
        
        # Reflection attack might not be detected from requester side
        # But should process without errors
        assert len(predictions) == len(packets), "Should process all reflection packets"
    
    def test_volumetric_attack_edge_case(self):
        """Test extreme volumetric attack with massive packet rates."""
        base_time = time.time()
        packets = []
        
        # Extreme volumetric attack
        botnet_ips = self.generate_botnet_ips(200)  # Large botnet
        
        for i, src_ip in enumerate(botnet_ips):
            # Very small packets for maximum PPS
            packet = self.create_packet(
                src_ip=src_ip,
                dst_ip="10.0.0.1",
                src_port=random.randint(1024, 65535),
                dst_port=80,
                packet_size=40,  # Minimum size
                payload=b'',
                payload_size=0,
                tcp_flags=0x02,
                timestamp=base_time + i * 0.001  # 1ms intervals - extremely fast
            )
            packets.append(packet)
        
        # Process volumetric attack
        predictions = []
        for packet in packets:
            features = self.extractor.extract_features(packet)
            prediction = self.model.predict(features)
            predictions.append(prediction)
        
        # Should detect extreme volumetric attack
        attack_predictions = [p for p in predictions if p.is_attack]
        assert len(attack_predictions) > 0, "Should detect extreme volumetric attack"
        
        # Check extreme packet rate
        if len(packets) > 50:
            final_features = self.extractor.extract_features(packets[-1])
            assert final_features.packets_per_second > 500, f"Should detect extreme packet rate, got {final_features.packets_per_second}"
    
    def test_ddos_alert_generation(self):
        """Test that DDoS attacks generate appropriate alerts."""
        base_time = time.time()
        packets = []
        
        # Generate clear DDoS pattern
        botnet_ips = self.generate_botnet_ips(20)
        
        for i, src_ip in enumerate(botnet_ips):
            packet = self.create_packet(
                src_ip=src_ip,
                dst_ip="10.0.0.1",
                src_port=random.randint(1024, 65535),
                dst_port=80,
                packet_size=64,
                tcp_flags=0x02,
                payload=b'',
                payload_size=0,
                timestamp=base_time + i * 0.01
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
        
        # Should generate DDoS alerts
        if alerts:
            for alert in alerts:
                assert alert.attack_type in ["DoS", "Generic"], f"Unexpected attack type: {alert.attack_type}"
                assert alert.severity in ["low", "medium", "high", "critical"], f"Invalid severity: {alert.severity}"
                assert alert.confidence > 0.0, "Alert confidence should be positive"
                
                # DDoS alerts should suggest rate limiting
                assert any(word in alert.recommended_action.lower() for word in ["rate", "limiting", "block"]), "Should suggest rate limiting"
    
    def test_distributed_coordination_patterns(self):
        """Test detection of coordinated distributed attack patterns."""
        base_time = time.time()
        packets = []
        
        # Coordinated attack: multiple attack vectors simultaneously
        
        # Vector 1: SYN flood
        syn_ips = self.generate_botnet_ips(20)
        for i, src_ip in enumerate(syn_ips):
            packet = self.create_packet(
                src_ip=src_ip,
                dst_ip="10.0.0.1",
                dst_port=80,
                tcp_flags=0x02,
                packet_size=64,
                timestamp=base_time + i * 0.01
            )
            packets.append(packet)
        
        # Vector 2: UDP flood (simultaneous)
        udp_ips = self.generate_botnet_ips(15)
        for i, src_ip in enumerate(udp_ips):
            packet = self.create_packet(
                src_ip=src_ip,
                dst_ip="10.0.0.1",
                dst_port=53,
                protocol="udp",
                packet_size=512,
                timestamp=base_time + i * 0.01
            )
            packets.append(packet)
        
        # Vector 3: HTTP flood (simultaneous)
        http_ips = self.generate_botnet_ips(10)
        for i, src_ip in enumerate(http_ips):
            packet = self.create_packet(
                src_ip=src_ip,
                dst_ip="10.0.0.1",
                dst_port=80,
                payload=b"GET / HTTP/1.1\\r\\nHost: target\\r\\n\\r\\n",
                payload_size=35,
                tcp_flags=0x18,
                timestamp=base_time + i * 0.01
            )
            packets.append(packet)
        
        # Sort packets by timestamp to simulate real attack
        packets.sort(key=lambda p: p.timestamp)
        
        # Process coordinated attack
        predictions = []
        for packet in packets:
            features = self.extractor.extract_features(packet)
            prediction = self.model.predict(features)
            predictions.append(prediction)
        
        # Should detect coordinated attack
        attack_predictions = [p for p in predictions if p.is_attack]
        assert len(attack_predictions) > 0, "Should detect coordinated DDoS attack"
        
        # Check that multiple flows are tracked
        flow_count = self.extractor.get_flow_count()
        assert flow_count > 20, f"Should track many flows in coordinated attack, got {flow_count}"