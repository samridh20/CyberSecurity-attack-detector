#!/usr/bin/env python3
"""
Debug script to see what features are being extracted from packets.
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

def create_test_packet():
    """Create a test packet."""
    return PacketInfo(
        timestamp=time.time(),
        src_ip="192.168.1.200",
        dst_ip="10.0.0.100",
        src_port=12345,
        dst_port=80,
        protocol="tcp",
        packet_size=1500,  # Large packet
        payload_size=1400,
        payload=b"A" * 1400,  # Large payload
        tcp_flags=0x02,  # SYN
        tcp_window=1024,
        ttl=64
    )

def debug_feature_extraction():
    """Debug what features are being extracted."""
    print("=== Feature Extraction Debug ===")
    
    # Initialize NIDS
    nids = RealTimeNIDS("config.yaml")
    
    # Create test packet
    packet = create_test_packet()
    print(f"Test packet: {packet.src_ip}:{packet.src_port} -> {packet.dst_ip}:{packet.dst_port}")
    print(f"Packet size: {packet.packet_size}, Payload size: {packet.payload_size}")
    
    # Extract features
    features = nids.feature_extractor.extract_features(packet)
    
    # Print all feature values
    print("\\nExtracted features:")
    for attr_name in dir(features):
        if not attr_name.startswith('_') and attr_name not in ['to_array', 'flow_key', 'timestamp']:
            value = getattr(features, attr_name)
            print(f"  {attr_name}: {value}")
    
    # Test prediction
    prediction = nids.model_adapter.predict(features)
    print(f"\\nPrediction:")
    print(f"  Is attack: {prediction.is_attack}")
    print(f"  Attack probability: {prediction.attack_probability:.3f}")
    print(f"  Attack class: {prediction.attack_class}")
    print(f"  Threshold used: {prediction.threshold_used}")

if __name__ == "__main__":
    debug_feature_extraction()