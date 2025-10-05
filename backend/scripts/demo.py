#!/usr/bin/env python3
"""
Demo script for the Real-Time Network Intrusion Detection System.
Generates synthetic traffic and demonstrates the complete pipeline.
"""

import time
import random
import argparse
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from nids import RealTimeNIDS
from nids.schemas import PacketInfo
from loguru import logger


def generate_synthetic_packet(attack_type: str = "normal") -> PacketInfo:
    """Generate synthetic network packet for demonstration."""
    
    base_time = time.time()
    
    if attack_type == "normal":
        # Normal web traffic
        return PacketInfo(
            timestamp=base_time,
            src_ip=f"192.168.1.{random.randint(10, 50)}",
            dst_ip="10.0.0.100",
            src_port=random.randint(1024, 65535),
            dst_port=random.choice([80, 443]),
            protocol="tcp",
            packet_size=random.randint(64, 1500),
            payload_size=random.randint(0, 1400),
            payload=b"GET / HTTP/1.1\\r\\nHost: example.com\\r\\n\\r\\n",
            tcp_flags=0x18,  # PSH+ACK
            tcp_window=65535,
            ttl=64
        )
    
    elif attack_type == "dos":
        # DoS attack - high packet rate, small packets
        return PacketInfo(
            timestamp=base_time,
            src_ip=f"192.168.1.{random.randint(200, 254)}",
            dst_ip="10.0.0.100",
            src_port=random.randint(1024, 65535),
            dst_port=80,
            protocol="tcp",
            packet_size=64,  # Small packets
            payload_size=0,
            payload=b"",
            tcp_flags=0x02,  # SYN
            tcp_window=1024,
            ttl=64
        )
    
    elif attack_type == "exploit":
        # Exploit attempt - suspicious payload
        suspicious_payload = b"\\x90" * 100 + b"\\x31\\xc0\\x50\\x68"  # NOP sled + shellcode
        return PacketInfo(
            timestamp=base_time,
            src_ip=f"192.168.1.{random.randint(100, 150)}",
            dst_ip="10.0.0.100",
            src_port=random.randint(1024, 65535),
            dst_port=443,
            protocol="tcp",
            packet_size=len(suspicious_payload) + 40,  # +headers
            payload_size=len(suspicious_payload),
            payload=suspicious_payload,
            tcp_flags=0x18,  # PSH+ACK
            tcp_window=32768,
            ttl=64
        )
    
    elif attack_type == "recon":
        # Reconnaissance - port scanning
        return PacketInfo(
            timestamp=base_time,
            src_ip=f"192.168.1.{random.randint(150, 200)}",
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
    
    else:
        # Default to normal
        return generate_synthetic_packet("normal")


def run_synthetic_demo(nids: RealTimeNIDS, duration: int = 60, packets_per_second: int = 100):
    """
    Run synthetic traffic demo.
    
    Args:
        nids: NIDS instance
        duration: Demo duration in seconds
        packets_per_second: Packet generation rate
    """
    logger.info(f"Starting synthetic demo: {duration}s duration, {packets_per_second} pps")
    
    start_time = time.time()
    packet_count = 0
    
    # Traffic mix: 80% normal, 10% DoS, 5% exploits, 5% recon
    traffic_types = (
        ["normal"] * 80 + 
        ["dos"] * 10 + 
        ["exploit"] * 5 + 
        ["recon"] * 5
    )
    
    try:
        while time.time() - start_time < duration:
            # Generate packet
            attack_type = random.choice(traffic_types)
            packet = generate_synthetic_packet(attack_type)
            
            # Process through NIDS pipeline
            features = nids.feature_extractor.extract_features(packet)
            prediction = nids.model_adapter.predict(features)
            
            # Generate alert if needed
            if prediction.is_attack:
                alert = nids.alert_manager.generate_alert(prediction)
                if alert:
                    logger.warning(f"ALERT: {alert.description}")
            
            packet_count += 1
            
            # Log progress
            if packet_count % 1000 == 0:
                elapsed = time.time() - start_time
                current_pps = packet_count / elapsed
                logger.info(f"Processed {packet_count} packets ({current_pps:.1f} pps)")
            
            # Rate limiting
            time.sleep(1.0 / packets_per_second)
    
    except KeyboardInterrupt:
        logger.info("Demo interrupted by user")
    
    # Final statistics
    elapsed = time.time() - start_time
    final_pps = packet_count / elapsed
    
    logger.info(f"Demo complete: {packet_count} packets in {elapsed:.1f}s ({final_pps:.1f} pps)")
    
    # Get system status
    status = nids.get_status()
    logger.info(f"Final status: {status}")


def main():
    """Main demo function."""
    parser = argparse.ArgumentParser(description="NIDS Demo Script")
    parser.add_argument("--config", default="config.yaml", help="Configuration file path")
    parser.add_argument("--duration", type=int, default=60, help="Demo duration in seconds")
    parser.add_argument("--pps", type=int, default=100, help="Packets per second")
    parser.add_argument("--mode", choices=["synthetic", "live"], default="synthetic", 
                       help="Demo mode: synthetic traffic or live capture")
    
    args = parser.parse_args()
    
    # Initialize NIDS
    logger.info("Initializing NIDS...")
    nids = RealTimeNIDS(args.config)
    
    try:
        if args.mode == "synthetic":
            # Run synthetic traffic demo
            run_synthetic_demo(nids, args.duration, args.pps)
        
        elif args.mode == "live":
            # Run live capture demo
            logger.info("Starting live capture demo...")
            nids.start_detection()
            
            # Run for specified duration
            time.sleep(args.duration)
            
            nids.stop_detection()
            
            # Show final statistics
            status = nids.get_status()
            logger.info(f"Live demo complete: {status}")
    
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        return 1
    
    logger.info("Demo completed successfully!")
    return 0


if __name__ == "__main__":
    exit(main())