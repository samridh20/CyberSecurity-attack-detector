#!/usr/bin/env python3
"""
Direct test of NIDS detection using the synthetic demo approach.
This bypasses network capture and directly feeds packets to the NIDS.
"""

import sys
import time
import random
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from nids import RealTimeNIDS
from nids.schemas import PacketInfo
from loguru import logger

def create_attack_packet(attack_type="dos"):
    """Create a packet that should trigger alerts."""
    base_time = time.time()
    
    if attack_type == "dos":
        # High rate, small packets - should trigger DoS detection
        return PacketInfo(
            timestamp=base_time,
            src_ip="192.168.1.200",
            dst_ip="10.0.0.100",
            src_port=random.randint(1024, 65535),
            dst_port=80,
            protocol="tcp",
            packet_size=64,  # Small packets
            payload_size=0,
            payload=b"",
            tcp_flags=0x02,  # SYN flood
            tcp_window=1024,
            ttl=64
        )
    
    elif attack_type == "large_payload":
        # Large payload - should trigger size-based detection
        large_payload = b"A" * 1500  # Large payload
        return PacketInfo(
            timestamp=base_time,
            src_ip="192.168.1.150",
            dst_ip="10.0.0.100",
            src_port=random.randint(1024, 65535),
            dst_port=443,
            protocol="tcp",
            packet_size=len(large_payload) + 40,
            payload_size=len(large_payload),
            payload=large_payload,
            tcp_flags=0x18,  # PSH+ACK
            tcp_window=32768,
            ttl=64
        )
    
    elif attack_type == "high_entropy":
        # High entropy payload - should trigger entropy-based detection
        entropy_payload = bytes([random.randint(0, 255) for _ in range(800)])
        return PacketInfo(
            timestamp=base_time,
            src_ip="192.168.1.100",
            dst_ip="10.0.0.100",
            src_port=random.randint(1024, 65535),
            dst_port=443,
            protocol="tcp",
            packet_size=len(entropy_payload) + 40,
            payload_size=len(entropy_payload),
            payload=entropy_payload,
            tcp_flags=0x18,
            tcp_window=32768,
            ttl=64
        )
    
    elif attack_type == "port_scan":
        # Port scanning pattern
        return PacketInfo(
            timestamp=base_time,
            src_ip="192.168.1.180",
            dst_ip="10.0.0.100",
            src_port=random.randint(1024, 65535),
            dst_port=random.randint(1, 1024),  # Scanning low ports
            protocol="tcp",
            packet_size=64,
            payload_size=0,
            payload=b"",
            tcp_flags=0x02,  # SYN
            tcp_window=1024,
            ttl=64
        )

def test_attack_detection():
    """Test attack detection by directly feeding packets to NIDS."""
    print("=== Direct NIDS Attack Detection Test ===")
    
    # Initialize NIDS
    nids = RealTimeNIDS("config.yaml")
    
    attack_types = ["dos", "large_payload", "high_entropy", "port_scan"]
    alerts_generated = 0
    
    print("Feeding attack packets directly to NIDS...")
    
    for attack_type in attack_types:
        print(f"\\nTesting {attack_type} attack...")
        
        # Generate multiple packets of this attack type
        for i in range(50):  # 50 packets per attack type
            packet = create_attack_packet(attack_type)
            
            # Process through NIDS pipeline
            try:
                features = nids.feature_extractor.extract_features(packet)
                prediction = nids.model_adapter.predict(features)
                
                # Check for alerts
                if prediction.is_attack:
                    alerts_generated += 1
                    print(f"  🚨 ATTACK DETECTED!")
                    print(f"     Confidence: {prediction.attack_probability:.3f}")
                    print(f"     Attack Type: {prediction.attack_class}")
                    print(f"     Source: {packet.src_ip}:{packet.src_port}")
                    
                    # Try to generate alert
                    alert = nids.alert_manager.generate_alert(prediction)
                    if alert:
                        print(f"     Alert: {alert.description}")
                    else:
                        print(f"     (Alert generation failed or filtered)")
                
                # Add some timing variation
                time.sleep(0.01)  # 10ms between packets = 100 pps
                
            except Exception as e:
                print(f"  Error processing packet: {e}")
    
    print(f"\\n=== Test Complete ===")
    print(f"Total alerts generated: {alerts_generated}")
    
    # Get final status
    status = nids.get_status()
    print(f"Active flows: {status['active_flows']}")

if __name__ == "__main__":
    test_attack_detection()