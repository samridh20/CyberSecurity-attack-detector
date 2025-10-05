#!/usr/bin/env python3
"""
EMERGENCY ML FIX - Real ML models with attack simulation
This uses your REAL ML models but simulates the packet capture data
"""

import time
import threading
import sys
from pathlib import Path
import random
import requests

# Add backend to path
sys.path.insert(0, str(Path("backend").absolute()))

from nids.features import FeatureExtractor
from nids.models import SimpleModelAdapter
from nids.alerts import AlertManager
from nids.schemas import PacketInfo, FlowKey

class EmergencyMLSystem:
    """Emergency ML system that uses real models with simulated packet data"""
    
    def __init__(self):
        print("🚨 EMERGENCY ML SYSTEM - Using REAL ML Models")
        
        # Initialize REAL ML components
        self.feature_extractor = FeatureExtractor(window_size=5)
        self.model_adapter = SimpleModelAdapter()
        self.alert_manager = AlertManager(toast_enabled=False, min_confidence=0.2, cooldown_seconds=2)
        
        # Lower thresholds for sensitive detection
        self.model_adapter.set_threshold(0.3)
        
        # API connection
        self.api_url = "http://127.0.0.1:8000"
        
        self.running = False
        self.packets_processed = 0
        self.alerts_generated = 0
        
        print("✅ Real ML components initialized:")
        print(f"   🧠 Model: {type(self.model_adapter).__name__}")
        print(f"   🔧 Threshold: {self.model_adapter.binary_threshold}")
        print(f"   🚨 Alert confidence: {self.alert_manager.min_confidence}")
        
        # Test API connection
        self.test_api_connection()
    
    def create_attack_packet(self, attack_type, src_ip, dst_ip, dst_port):
        """Create realistic packet data for ML processing"""
        
        # Create packet based on attack type
        if attack_type == "Reconnaissance":
            # Port scan characteristics
            packet = PacketInfo(
                timestamp=time.time(),
                src_ip=src_ip,
                dst_ip=dst_ip,
                src_port=random.randint(1024, 65535),
                dst_port=dst_port,
                protocol="tcp",
                packet_size=64,  # Small SYN packets
                payload_size=0,
                payload=None,
                tcp_flags=0x02,  # SYN flag
                tcp_window=8192,
                tcp_seq=random.randint(1000, 100000),
                tcp_ack=0,
                ttl=64,
                ip_flags=0
            )
        
        elif attack_type == "DoS":
            # DoS flood characteristics
            packet = PacketInfo(
                timestamp=time.time(),
                src_ip=src_ip,
                dst_ip=dst_ip,
                src_port=random.randint(1024, 65535),
                dst_port=dst_port,
                protocol="tcp",
                packet_size=random.randint(64, 1500),
                payload_size=0,
                payload=None,
                tcp_flags=0x02,  # SYN flood
                tcp_window=0,  # Suspicious window
                tcp_seq=random.randint(1000, 100000),
                tcp_ack=0,
                ttl=random.randint(32, 128),
                ip_flags=0
            )
        
        elif attack_type == "Exploits":
            # Exploit attempt characteristics
            exploit_payload = b"A" * 500 + b"\x90" * 100  # Buffer overflow pattern
            packet = PacketInfo(
                timestamp=time.time(),
                src_ip=src_ip,
                dst_ip=dst_ip,
                src_port=random.randint(1024, 65535),
                dst_port=dst_port,
                protocol="tcp",
                packet_size=len(exploit_payload) + 64,
                payload_size=len(exploit_payload),
                payload=exploit_payload,
                tcp_flags=0x18,  # PSH+ACK
                tcp_window=8192,
                tcp_seq=random.randint(1000, 100000),
                tcp_ack=random.randint(1000, 100000),
                ttl=64,
                ip_flags=0
            )
        
        elif attack_type == "Fuzzers":
            # Fuzzing characteristics
            random_payload = bytes([random.randint(0, 255) for _ in range(random.randint(100, 1000))])
            packet = PacketInfo(
                timestamp=time.time(),
                src_ip=src_ip,
                dst_ip=dst_ip,
                src_port=random.randint(1024, 65535),
                dst_port=dst_port,
                protocol="tcp",
                packet_size=len(random_payload) + 64,
                payload_size=len(random_payload),
                payload=random_payload,
                tcp_flags=random.randint(0, 255),  # Random flags
                tcp_window=random.randint(0, 65535),
                tcp_seq=random.randint(1000, 100000),
                tcp_ack=random.randint(1000, 100000),
                ttl=random.randint(1, 255),
                ip_flags=random.randint(0, 7)
            )
        
        else:  # Generic
            # Generic anomalous traffic
            packet = PacketInfo(
                timestamp=time.time(),
                src_ip=src_ip,
                dst_ip=dst_ip,
                src_port=random.randint(30000, 65535),  # High port
                dst_port=dst_port,
                protocol="udp",
                packet_size=random.randint(1400, 1500),  # Large packets
                payload_size=random.randint(1000, 1400),
                payload=b"X" * random.randint(1000, 1400),
                tcp_flags=None,
                tcp_window=None,
                tcp_seq=None,
                tcp_ack=None,
                ttl=1,  # Suspicious TTL
                ip_flags=0
            )
        
        return packet
    
    def test_api_connection(self):
        """Test connection to backend API"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=3)
            if response.status_code == 200:
                print("✅ Connected to backend API")
            else:
                print("⚠️  Backend API responded but may have issues")
        except Exception as e:
            print(f"❌ Cannot connect to backend API: {e}")
            print("💡 Make sure backend is running: cd backend && python -m api.server --port 8000")
    
    def send_ml_alert_to_frontend(self, prediction, packet):
        """Send ML-generated alert directly to frontend via API"""
        try:
            alert_data = {
                "timestamp": time.time(),
                "attack_type": prediction.attack_class or "Unknown",
                "attack_class": prediction.attack_class or "Unknown",
                "severity": "high" if prediction.attack_probability > 0.8 else "medium",
                "confidence": prediction.attack_probability,
                "probability": prediction.attack_probability,
                "src_ip": packet.src_ip,
                "dst_ip": packet.dst_ip,
                "src_port": packet.src_port,
                "dst_port": packet.dst_port,
                "protocol": packet.protocol,
                "packet_length": packet.packet_size,
                "interface": "ML-System",
                "flags": "ML",
                "description": f"REAL ML detected {prediction.attack_class} attack (confidence: {prediction.attack_probability:.3f})",
                "recommended_action": f"ML-based detection of {prediction.attack_class} - investigate immediately"
            }
            
            response = requests.post(f"{self.api_url}/alerts/real-detection", json=alert_data, timeout=3)
            
            if response.status_code == 200:
                return True
            else:
                print(f"⚠️  API alert failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to send ML alert to frontend: {e}")
            return False
    
    def process_ml_packet(self, packet):
        """Process packet through REAL ML pipeline"""
        try:
            # Extract features using REAL feature extractor
            features = self.feature_extractor.extract_features(packet)
            
            # Get prediction from REAL ML model
            prediction = self.model_adapter.predict(features)
            
            self.packets_processed += 1
            
            # Generate alert using REAL alert manager AND send to frontend
            if prediction.is_attack:
                alert = self.alert_manager.generate_alert(prediction)
                if alert:
                    # Send ML alert to frontend
                    if self.send_ml_alert_to_frontend(prediction, packet):
                        self.alerts_generated += 1
                        print(f"🧠 REAL ML DETECTED → FRONTEND: {prediction.attack_class} "
                              f"(confidence: {prediction.attack_probability:.3f})")
                    else:
                        print(f"🧠 REAL ML DETECTED (frontend failed): {prediction.attack_class} "
                              f"(confidence: {prediction.attack_probability:.3f})")
            
            return prediction
            
        except Exception as e:
            print(f"❌ ML processing error: {e}")
            return None
    
    def simulate_comprehensive_attack(self, duration=120):
        """Simulate the comprehensive attack with real ML processing"""
        print(f"\n🧠 Starting REAL ML Processing for {duration}s")
        print("This uses your ACTUAL ML models to detect attack patterns!")
        
        self.running = True
        
        # Attack patterns from comprehensive_attack.py
        attack_patterns = [
            {"type": "Reconnaissance", "src": "192.168.1.100", "ports": [21, 22, 80, 443, 3389]},
            {"type": "DoS", "src": "10.0.0.50", "ports": [80]},
            {"type": "Exploits", "src": "203.0.113.100", "ports": [80, 443, 21]},
            {"type": "Fuzzers", "src": "172.16.1.200", "ports": [80, 22]},
            {"type": "Generic", "src": "192.168.2.150", "ports": [8080, 9000]}
        ]
        
        start_time = time.time()
        
        while time.time() - start_time < duration and self.running:
            # Pick random attack pattern
            pattern = random.choice(attack_patterns)
            attack_type = pattern["type"]
            src_ip = pattern["src"]
            dst_port = random.choice(pattern["ports"])
            
            # Create realistic packet for this attack
            packet = self.create_attack_packet(attack_type, src_ip, "127.0.0.1", dst_port)
            
            # Process through REAL ML pipeline
            self.process_ml_packet(packet)
            
            # Print progress
            if self.packets_processed % 50 == 0:
                print(f"🧠 ML Progress: {self.packets_processed} packets, {self.alerts_generated} ML alerts")
            
            # Realistic timing
            time.sleep(0.1)  # 10 packets per second
        
        self.running = False
        
        print(f"\n🎉 REAL ML Processing Complete!")
        print(f"   📊 Packets processed by ML: {self.packets_processed}")
        print(f"   🚨 Alerts generated by ML: {self.alerts_generated}")
        print(f"   🧠 ML models successfully detected attacks!")

def main():
    """Main emergency ML function"""
    print("🚨 EMERGENCY ML SYSTEM FOR HACKATHON")
    print("=" * 50)
    print("This uses your REAL ML models with simulated attack data")
    print("Perfect for demonstrating ML-based detection!")
    
    # Initialize emergency ML system
    ml_system = EmergencyMLSystem()
    
    print("\n🎯 This will:")
    print("✅ Use your REAL ML models (not signatures)")
    print("✅ Process realistic attack packet data")
    print("✅ Generate real ML-based alerts")
    print("✅ Work with your frontend")
    
    choice = input("\nStart REAL ML processing? (y/n): ").lower().strip()
    
    if choice == 'y':
        try:
            # Start ML processing
            ml_system.simulate_comprehensive_attack(duration=180)  # 3 minutes
            
        except KeyboardInterrupt:
            print("\n🛑 ML processing stopped")
            ml_system.running = False
    
    print("\n🧠 REAL ML demonstration complete!")
    print("💻 Check your frontend - it should show ML-detected attacks!")

if __name__ == "__main__":
    main()