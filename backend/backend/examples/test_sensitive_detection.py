#!/usr/bin/env python3
"""
Test NIDS with sensitive detection settings.
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

def create_attack_packet():
    """Create a packet that should trigger alerts."""
    return PacketInfo(
        timestamp=time.time(),
        src_ip="192.168.1.200",
        dst_ip="10.0.0.100",
        src_port=random.randint(1024, 65535),
        dst_port=80,
        protocol="tcp",
        packet_size=1500,  # Large packet
        payload_size=1400,
        payload=b"A" * 1400,  # Large payload
        tcp_flags=0x02,  # SYN
        tcp_window=1024,
        ttl=64
    )

def test_sensitive_detection():
    """Test with sensitive detection settings."""
    print("=== Sensitive NIDS Detection Test ===")
    
    # Initialize NIDS with sensitive config
    nids = RealTimeNIDS("config_sensitive.yaml")
    
    alerts_generated = 0
    total_attacks_detected = 0
    
    print("Testing with sensitive detection settings...")
    print("Watch for Windows toast notifications!")
    
    for i in range(10):  # Test with 10 attack packets
        packet = create_attack_packet()
        
        # Process through NIDS pipeline
        try:
            features = nids.feature_extractor.extract_features(packet)
            prediction = nids.model_adapter.predict(features)
            
            print(f"Packet {i+1}: Attack={prediction.is_attack}, Confidence={prediction.attack_probability:.3f}")
            
            # Check for alerts
            if prediction.is_attack:
                total_attacks_detected += 1
                alert = nids.alert_manager.generate_alert(prediction)
                if alert:
                    alerts_generated += 1
                    print(f"  🚨 ALERT GENERATED: {alert.description}")
                    print(f"     Severity: {alert.severity}")
                    print(f"     Timestamp: {alert.timestamp}")
                else:
                    print(f"  ⚠️  Attack detected but alert filtered")
            
            time.sleep(1)  # 1 second between packets
            
        except Exception as e:
            print(f"  Error processing packet: {e}")
    
    print(f"\\n=== Test Complete ===")
    print(f"Attacks detected: {total_attacks_detected}/10")
    print(f"Alerts generated: {alerts_generated}")
    print("Check for Windows toast notifications!")

if __name__ == "__main__":
    test_sensitive_detection()