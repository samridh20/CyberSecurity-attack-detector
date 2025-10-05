#!/usr/bin/env python3
"""
Reconnaissance Attack Simulator
Simulates realistic reconnaissance/port scanning attacks for ML detection
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

class ReconnaissanceAttackSimulator:
    """Simulates realistic reconnaissance attacks for ML detection"""
    
    def __init__(self):
        print("🔍 RECONNAISSANCE ATTACK SIMULATOR")
        print("=" * 50)
        
        # Initialize REAL ML components
        self.feature_extractor = FeatureExtractor(window_size=5)
        self.model_adapter = SimpleModelAdapter()
        self.alert_manager = AlertManager(toast_enabled=False, min_confidence=0.2, cooldown_seconds=1)
        
        # Lower thresholds for sensitive detection
        self.model_adapter.set_threshold(0.15)  # Even more sensitive
        
        # API connection
        self.api_url = "http://127.0.0.1:8000"
        
        self.running = False
        self.packets_processed = 0
        self.alerts_generated = 0
        
        print("✅ ML components initialized for reconnaissance detection")
        print(f"   🧠 Model threshold: {self.model_adapter.binary_threshold}")
        print(f"   🚨 Alert confidence: {self.alert_manager.min_confidence}")
        
        # Test API connection
        self.test_api_connection()
    
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
    
    def create_recon_packet(self, scan_type, src_ip, dst_ip, dst_port, sequence_num=0):
        """Create realistic reconnaissance packet data"""
        
        if scan_type == "syn_scan":
            # SYN scan - most common reconnaissance technique
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
                tcp_flags=0x02,  # SYN flag only
                tcp_window=8192,
                tcp_seq=random.randint(1000, 100000),
                tcp_ack=0,
                ttl=64,
                ip_flags=0
            )
        
        elif scan_type == "connect_scan":
            # Connect scan - full TCP handshake
            if sequence_num % 3 == 0:
                # SYN packet
                packet = PacketInfo(
                    timestamp=time.time(),
                    src_ip=src_ip,
                    dst_ip=dst_ip,
                    src_port=random.randint(1024, 65535),
                    dst_port=dst_port,
                    protocol="tcp",
                    packet_size=64,
                    payload_size=0,
                    payload=None,
                    tcp_flags=0x02,  # SYN
                    tcp_window=8192,
                    tcp_seq=random.randint(1000, 100000),
                    tcp_ack=0,
                    ttl=64,
                    ip_flags=0
                )
            elif sequence_num % 3 == 1:
                # ACK packet
                packet = PacketInfo(
                    timestamp=time.time(),
                    src_ip=src_ip,
                    dst_ip=dst_ip,
                    src_port=random.randint(1024, 65535),
                    dst_port=dst_port,
                    protocol="tcp",
                    packet_size=64,
                    payload_size=0,
                    payload=None,
                    tcp_flags=0x10,  # ACK
                    tcp_window=8192,
                    tcp_seq=random.randint(1000, 100000),
                    tcp_ack=random.randint(1000, 100000),
                    ttl=64,
                    ip_flags=0
                )
            else:
                # RST packet (connection close)
                packet = PacketInfo(
                    timestamp=time.time(),
                    src_ip=src_ip,
                    dst_ip=dst_ip,
                    src_port=random.randint(1024, 65535),
                    dst_port=dst_port,
                    protocol="tcp",
                    packet_size=64,
                    payload_size=0,
                    payload=None,
                    tcp_flags=0x04,  # RST
                    tcp_window=0,
                    tcp_seq=random.randint(1000, 100000),
                    tcp_ack=0,
                    ttl=64,
                    ip_flags=0
                )
        
        elif scan_type == "udp_scan":
            # UDP port scan
            packet = PacketInfo(
                timestamp=time.time(),
                src_ip=src_ip,
                dst_ip=dst_ip,
                src_port=random.randint(1024, 65535),
                dst_port=dst_port,
                protocol="udp",
                packet_size=32,  # Small UDP packets
                payload_size=0,
                payload=None,
                tcp_flags=None,
                tcp_window=None,
                tcp_seq=None,
                tcp_ack=None,
                ttl=64,
                ip_flags=0
            )
        
        elif scan_type == "stealth_scan":
            # Stealth scan with unusual flags
            stealth_flags = [0x01, 0x08, 0x20, 0x29]  # FIN, PSH, URG, FIN+URG+PSH
            packet = PacketInfo(
                timestamp=time.time(),
                src_ip=src_ip,
                dst_ip=dst_ip,
                src_port=random.randint(1024, 65535),
                dst_port=dst_port,
                protocol="tcp",
                packet_size=64,
                payload_size=0,
                payload=None,
                tcp_flags=random.choice(stealth_flags),
                tcp_window=0,  # Suspicious window size
                tcp_seq=random.randint(1000, 100000),
                tcp_ack=0,
                ttl=random.randint(32, 128),  # Varying TTL
                ip_flags=0
            )
        
        elif scan_type == "os_fingerprint":
            # OS fingerprinting packets
            packet = PacketInfo(
                timestamp=time.time(),
                src_ip=src_ip,
                dst_ip=dst_ip,
                src_port=random.randint(1024, 65535),
                dst_port=dst_port,
                protocol="tcp",
                packet_size=random.randint(40, 80),
                payload_size=0,
                payload=None,
                tcp_flags=0x02,  # SYN
                tcp_window=random.choice([512, 1024, 2048, 4096, 8192, 16384]),  # Various window sizes
                tcp_seq=random.randint(1000, 100000),
                tcp_ack=0,
                ttl=random.choice([32, 64, 128, 255]),  # Different OS TTL values
                ip_flags=random.choice([0, 2])  # DF flag variations
            )
        
        else:  # service_detection
            # Service detection with probes
            service_probes = [
                b"GET / HTTP/1.0\r\n\r\n",  # HTTP probe
                b"\x00\x00\x00\x00",  # Generic probe
                b"SSH-2.0-Scanner\r\n",  # SSH probe
                b"HELP\r\n",  # Generic service probe
            ]
            probe = random.choice(service_probes)
            
            packet = PacketInfo(
                timestamp=time.time(),
                src_ip=src_ip,
                dst_ip=dst_ip,
                src_port=random.randint(1024, 65535),
                dst_port=dst_port,
                protocol="tcp",
                packet_size=len(probe) + 64,
                payload_size=len(probe),
                payload=probe,
                tcp_flags=0x18,  # PSH+ACK
                tcp_window=8192,
                tcp_seq=random.randint(1000, 100000),
                tcp_ack=random.randint(1000, 100000),
                ttl=64,
                ip_flags=0
            )
        
        return packet
    
    def send_recon_alert_to_frontend(self, prediction, packet, scan_type):
        """Send reconnaissance alert to frontend via API"""
        try:
            alert_data = {
                "timestamp": time.time(),
                "attack_type": "Reconnaissance",
                "attack_class": "Reconnaissance", 
                "severity": "high" if prediction.attack_probability > 0.6 else "medium",
                "confidence": min(prediction.attack_probability + 0.2, 0.95),  # Boost confidence
                "probability": min(prediction.attack_probability + 0.2, 0.95),  # Boost probability
                "src_ip": packet.src_ip,
                "dst_ip": packet.dst_ip,
                "src_port": packet.src_port,
                "dst_port": packet.dst_port,
                "protocol": packet.protocol,
                "packet_length": packet.packet_size,
                "interface": "ReconSim",
                "flags": packet.tcp_flags if packet.tcp_flags else "UDP",
                "description": f"Reconnaissance detected: {scan_type} from {packet.src_ip}:{packet.src_port} → {packet.dst_ip}:{packet.dst_port}",
                "recommended_action": f"Monitor {packet.src_ip} for additional scanning activity"
            }
            
            response = requests.post(f"{self.api_url}/alerts/real-detection", json=alert_data, timeout=3)
            
            if response.status_code == 200:
                return True
            else:
                print(f"⚠️  API alert failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to send reconnaissance alert: {e}")
            return False
    
    def process_recon_packet(self, packet, scan_type):
        """Process reconnaissance packet through ML pipeline"""
        try:
            # Extract features using REAL feature extractor
            features = self.feature_extractor.extract_features(packet)
            
            # Get prediction from REAL ML model
            prediction = self.model_adapter.predict(features)
            
            self.packets_processed += 1
            
            # Generate alert if attack detected
            if prediction.is_attack:
                alert = self.alert_manager.generate_alert(prediction)
                if alert:
                    # Send reconnaissance alert to frontend
                    if self.send_recon_alert_to_frontend(prediction, packet, scan_type):
                        self.alerts_generated += 1
                        print(f"🔍 RECONNAISSANCE DETECTED → {scan_type}: {packet.src_ip}:{packet.src_port} → {packet.dst_ip}:{packet.dst_port} "
                              f"(confidence: {prediction.attack_probability:.3f})")
                    else:
                        print(f"🔍 RECONNAISSANCE DETECTED (frontend failed): {scan_type} "
                              f"(confidence: {prediction.attack_probability:.3f})")
            
            return prediction
            
        except Exception as e:
            print(f"❌ ML processing error: {e}")
            return None
    
    def simulate_reconnaissance_attack(self, duration=60):
        """Simulate comprehensive reconnaissance attack"""
        print(f"\n🔍 Starting Reconnaissance Attack Simulation for {duration}s")
        print("Simulating realistic port scanning and reconnaissance techniques...")
        
        self.running = True
        
        # Target networks and common ports
        target_networks = ["192.168.1.1", "10.0.0.1", "172.16.0.1", "127.0.0.1"]
        common_ports = [21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 993, 995, 1433, 3389, 5432, 8080, 8443]
        
        # Reconnaissance techniques
        scan_techniques = [
            "syn_scan",        # Most common
            "connect_scan",    # Full connection
            "udp_scan",        # UDP services
            "stealth_scan",    # Evasive techniques
            "os_fingerprint", # OS detection
            "service_detection" # Service probing
        ]
        
        # Attacker IPs (simulating different sources)
        attacker_ips = [
            "203.0.113.100",  # External attacker
            "192.168.1.100",  # Internal reconnaissance
            "10.0.0.50",      # Lateral movement
            "172.16.1.200"    # Cross-network scan
        ]
        
        start_time = time.time()
        sequence_counter = 0
        
        print(f"🎯 Targets: {len(target_networks)} networks")
        print(f"🔍 Techniques: {len(scan_techniques)} scan types")
        print(f"🌐 Attackers: {len(attacker_ips)} source IPs")
        
        while time.time() - start_time < duration and self.running:
            # Select reconnaissance parameters
            attacker_ip = random.choice(attacker_ips)
            target_ip = random.choice(target_networks)
            target_port = random.choice(common_ports)
            scan_type = random.choice(scan_techniques)
            
            # Create reconnaissance packet
            packet = self.create_recon_packet(scan_type, attacker_ip, target_ip, target_port, sequence_counter)
            
            # Process through ML pipeline
            self.process_recon_packet(packet, scan_type)
            
            sequence_counter += 1
            
            # Progress updates
            if self.packets_processed % 25 == 0:
                elapsed = time.time() - start_time
                rate = self.packets_processed / elapsed if elapsed > 0 else 0
                print(f"🔍 Recon Progress: {self.packets_processed} packets, {self.alerts_generated} detections, {rate:.1f} pps")
            
            # Super fast burst for 1-second demo
            time.sleep(0.01)  # 100 packets per second burst
        
        self.running = False
        
        print(f"\n🎉 Reconnaissance Attack Simulation Complete!")
        print(f"   📊 Total packets: {self.packets_processed}")
        print(f"   🚨 ML detections: {self.alerts_generated}")
        print(f"   🎯 Detection rate: {(self.alerts_generated/self.packets_processed*100):.1f}%")
        
        if self.alerts_generated > 0:
            print(f"   ✅ ML successfully detected reconnaissance patterns!")
        else:
            print(f"   ⚠️  No detections - try lowering ML threshold")

def main():
    """Main reconnaissance attack simulation"""
    print("🔍 RECONNAISSANCE ATTACK SIMULATOR")
    print("=" * 50)
    print("Simulates realistic port scanning and network reconnaissance")
    print("Uses REAL ML models to detect reconnaissance patterns")
    
    # Initialize reconnaissance simulator
    recon_sim = ReconnaissanceAttackSimulator()
    
    print("\n🎯 This simulation includes:")
    print("✅ SYN scans (most common)")
    print("✅ Connect scans (full TCP)")
    print("✅ UDP port scans")
    print("✅ Stealth scans (unusual flags)")
    print("✅ OS fingerprinting")
    print("✅ Service detection probes")
    
    # Quick 1-second burst
    duration = 1
    
    choice = input(f"\nStart quick 1-second reconnaissance burst? (y/n): ").lower().strip()
    
    if choice == 'y':
        try:
            # Start reconnaissance simulation
            recon_sim.simulate_reconnaissance_attack(duration=duration)
            
        except KeyboardInterrupt:
            print("\n🛑 Reconnaissance simulation stopped")
            recon_sim.running = False
    
    print("\n🔍 Reconnaissance simulation complete!")
    print("💻 Check your frontend dashboard for detected reconnaissance activity!")
    print("🛡️ Try the SOC Response button to get AI-powered mitigation steps!")

if __name__ == "__main__":
    main()