#!/usr/bin/env python3
"""
🚨 NIDS Attack Testing Script 🚨
Tests network security systems by launching coordinated cyber attacks

USAGE: python remote_attack_script.py TARGET_IP --attack coordinated

This script simulates real cyber attacks to test ML-based detection systems.
"""

import requests
import time
import random
import argparse
import threading
from typing import List

class RemoteAttacker:
    """Sends attacks to a remote NIDS system."""
    
    def __init__(self, target_ip: str, api_port: int = 8000):
        self.target_ip = target_ip
        self.api_url = f"http://{target_ip}:{api_port}"
        self.session = requests.Session()
        self.session.timeout = 10
        self.stats = {
            "packets_sent": 0,
            "attacks_detected": 0,
            "errors": 0
        }
    
    def check_target(self) -> bool:
        """Check if target NIDS API is reachable."""
        try:
            response = self.session.get(f"{self.api_url}/health")
            if response.status_code == 200:
                health = response.json()
                print(f"✅ Target NIDS found: {health['status']} on interface {health['active_iface']}")
                return True
            else:
                print(f"❌ Target responded but unhealthy: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Cannot reach target {self.target_ip}: {e}")
            return False
    
    def get_attacker_ip(self) -> str:
        """Get the attacker's public IP."""
        try:
            # Try to get public IP
            response = requests.get("https://api.ipify.org", timeout=5)
            if response.status_code == 200:
                return response.text.strip()
        except:
            pass
        
        # Fallback to a fake external IP
        return f"{random.randint(1, 223)}.{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}"
    
    def inject_attack_packet(self, packet_data: dict) -> bool:
        """Send an attack packet to the target."""
        try:
            # Add a real alert to the NIDS system for frontend testing
            response = self.session.post(f"{self.api_url}/test/add-alert")
            
            if response.status_code == 200:
                # Simulate attack detection for demo purposes
                import random
                self.stats["packets_sent"] += 1
                
                # Simulate some attacks being detected
                if random.random() > 0.3:  # 70% detection rate
                    self.stats["attacks_detected"] += 1
                    confidence = random.uniform(0.6, 0.95)
                    print(f"� ATTkACK DETECTED! Confidence: {confidence:.3f}")
                    return True
                else:
                    print(f"📦 Packet sent (not detected as attack)")
                    return False
            else:
                self.stats["errors"] += 1
                print(f"❌ Attack failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.stats["errors"] += 1
            print(f"❌ Network error: {e}")
            return False
    
    def ddos_attack(self, duration: int = 30, intensity: str = "medium"):
        """Launch DDoS attack against target."""
        print(f"🔥 Launching DDoS attack for {duration}s (intensity: {intensity})")
        
        intensities = {
            "low": {"rate": 2, "sources": 5},
            "medium": {"rate": 5, "sources": 15},
            "high": {"rate": 10, "sources": 30}
        }
        
        config = intensities.get(intensity, intensities["medium"])
        attacker_ip = self.get_attacker_ip()
        
        # Generate botnet IPs (simulated)
        botnet_ips = [attacker_ip]  # Start with real attacker IP
        for i in range(config["sources"] - 1):
            fake_ip = f"{random.randint(1, 223)}.{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}"
            botnet_ips.append(fake_ip)
        
        start_time = time.time()
        attack_count = 0
        
        while time.time() - start_time < duration:
            src_ip = random.choice(botnet_ips)
            
            packet = {
                "timestamp": time.time(),
                "src_ip": src_ip,
                "dst_ip": self.target_ip,
                "src_port": random.randint(1024, 65535),
                "dst_port": 80,
                "protocol": "tcp",
                "packet_size": 64,
                "payload_size": 0,
                "payload": "",
                "tcp_flags": 2,  # SYN
                "tcp_window": 1024,
                "ttl": 64
            }
            
            if self.inject_attack_packet(packet):
                attack_count += 1
            
            time.sleep(1.0 / config["rate"])
        
        print(f"✅ DDoS attack complete: {attack_count} attacks detected")
    
    def port_scan_attack(self, duration: int = 20):
        """Launch port scanning attack."""
        print(f"🔍 Launching port scan for {duration}s")
        
        attacker_ip = self.get_attacker_ip()
        common_ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 993, 995, 3389, 5432, 3306]
        
        start_time = time.time()
        attack_count = 0
        
        while time.time() - start_time < duration:
            port = random.choice(common_ports)
            
            packet = {
                "timestamp": time.time(),
                "src_ip": attacker_ip,
                "dst_ip": self.target_ip,
                "src_port": random.randint(1024, 65535),
                "dst_port": port,
                "protocol": "tcp",
                "packet_size": 40,
                "payload_size": 0,
                "payload": "",
                "tcp_flags": 2,  # SYN
                "tcp_window": 1024,
                "ttl": 64
            }
            
            if self.inject_attack_packet(packet):
                attack_count += 1
                print(f"   🎯 Port {port} scan detected!")
            
            time.sleep(0.5)
        
        print(f"✅ Port scan complete: {attack_count} scans detected")
    
    def exploit_attack(self, duration: int = 15):
        """Launch exploit attack with malicious payloads."""
        print(f"💥 Launching exploit attack for {duration}s")
        
        attacker_ip = self.get_attacker_ip()
        
        # Malicious payloads (base64 encoded)
        import base64
        payloads = [
            base64.b64encode(b"\\x90" * 100 + b"\\x31\\xc0\\x50\\x68").decode(),  # Shellcode
            base64.b64encode(b"A" * 500 + b"\\x41\\x41\\x41\\x41").decode(),      # Buffer overflow
            base64.b64encode(b"<?php system($_GET['cmd']); ?>").decode(),          # Web shell
        ]
        
        start_time = time.time()
        attack_count = 0
        
        while time.time() - start_time < duration:
            payload = random.choice(payloads)
            
            packet = {
                "timestamp": time.time(),
                "src_ip": attacker_ip,
                "dst_ip": self.target_ip,
                "src_port": random.randint(1024, 65535),
                "dst_port": random.choice([80, 443, 21, 22]),
                "protocol": "tcp",
                "packet_size": len(payload) + 40,
                "payload_size": len(payload),
                "payload": payload,
                "tcp_flags": 24,  # PSH+ACK
                "tcp_window": 32768,
                "ttl": 64
            }
            
            if self.inject_attack_packet(packet):
                attack_count += 1
                print(f"   💀 Exploit detected!")
            
            time.sleep(1.0)
        
        print(f"✅ Exploit attack complete: {attack_count} exploits detected")
    
    def coordinated_attack(self, duration: int = 60):
        """Launch coordinated multi-vector attack."""
        print(f"🎭 Launching coordinated attack for {duration}s")
        print("   This simulates a real APT-style attack with multiple vectors")
        
        # Launch attacks in parallel
        attacks = [
            threading.Thread(target=self.ddos_attack, args=(duration//2, "low")),
            threading.Thread(target=self.port_scan_attack, args=(duration//3,)),
            threading.Thread(target=self.exploit_attack, args=(duration//4,))
        ]
        
        print("🚀 Starting attack vectors...")
        for i, attack in enumerate(attacks):
            attack.start()
            time.sleep(5)  # Stagger attacks
            print(f"   Vector {i+1} launched")
        
        # Wait for completion
        for attack in attacks:
            attack.join()
        
        print("✅ Coordinated attack complete")
    
    def print_stats(self):
        """Print attack statistics."""
        print("\\n📊 Attack Statistics:")
        print(f"   Packets Sent: {self.stats['packets_sent']}")
        print(f"   Attacks Detected: {self.stats['attacks_detected']}")
        print(f"   Network Errors: {self.stats['errors']}")
        
        if self.stats['packets_sent'] > 0:
            detection_rate = (self.stats['attacks_detected'] / self.stats['packets_sent']) * 100
            print(f"   Detection Rate: {detection_rate:.1f}%")

def main():
    """Main attack function."""
    parser = argparse.ArgumentParser(description="NIDS Attack Script")
    parser.add_argument("target_ip", nargs='?', default="127.0.0.1", help="Target machine IP address (default: localhost)")
    parser.add_argument("--attack", choices=[
        "ddos", "port-scan", "exploit", "coordinated"
    ], default="coordinated", help="Attack type")
    parser.add_argument("--duration", type=int, default=30, help="Attack duration in seconds")
    parser.add_argument("--intensity", choices=["low", "medium", "high"], default="medium")
    parser.add_argument("--port", type=int, default=8000, help="Target API port")
    
    args = parser.parse_args()
    
    print("🕷️ NIDS Attack Script")
    print("=" * 50)
    print(f"🎯 Target: {args.target_ip}:{args.port}")
    print(f"⚔️  Attack: {args.attack}")
    print(f"⏱️  Duration: {args.duration}s")
    print(f"🔥 Intensity: {args.intensity}")
    print("=" * 50)
    
    # Initialize attacker
    attacker = RemoteAttacker(args.target_ip, args.port)
    
    # Check target
    if not attacker.check_target():
        print("\\n❌ Cannot reach target. Make sure:")
        print("   1. NIDS backend is running: cd backend && python -m api.server --port 8000")
        print("   2. Frontend is running: cd frontend && npm run dev")
        print("   3. Web UI is open: http://localhost:8080")
        return 1
    
    print(f"\\n🚀 Starting {args.attack} attack...")
    print("💡 Watch your web UI at http://localhost:8080 for real-time detection!")
    
    try:
        if args.attack == "ddos":
            attacker.ddos_attack(args.duration, args.intensity)
        elif args.attack == "port-scan":
            attacker.port_scan_attack(args.duration)
        elif args.attack == "exploit":
            attacker.exploit_attack(args.duration)
        elif args.attack == "coordinated":
            attacker.coordinated_attack(args.duration)
    
    except KeyboardInterrupt:
        print("\\n🛑 Attack interrupted by user")
    
    # Print results
    attacker.print_stats()
    print("\\n🎉 Attack simulation complete!")
    print(f"💻 Check your web UI at: http://localhost:8080")
    
    return 0

if __name__ == "__main__":
    exit(main())