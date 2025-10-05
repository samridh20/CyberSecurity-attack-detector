#!/usr/bin/env python3
"""
REALISTIC Packet Detector - Only detects actual attacks, not normal traffic
"""

import time
import threading
import requests
from scapy.all import *
import sys
from pathlib import Path

class RealisticPacketDetector:
    """Realistic detector that only flags actual suspicious activity"""
    
    def __init__(self):
        self.api_url = "http://127.0.0.1:8000"
        self.packets_seen = 0
        self.attacks_detected = 0
        
        # More sophisticated tracking
        self.flow_stats = {}
        self.port_scan_tracking = {}
        self.syn_flood_tracking = {}
        
    def is_suspicious_activity(self, src_ip, dst_ip, dst_port, protocol, tcp_flags=None):
        """Determine if activity is actually suspicious"""
        current_time = time.time()
        
        # Skip local/internal traffic (not suspicious)
        if (src_ip.startswith("192.168.") or src_ip.startswith("10.") or 
            src_ip.startswith("172.16.") or src_ip.startswith("127.")):
            
            # Only flag if it's clearly attack-like patterns
            if protocol == "tcp" and tcp_flags:
                # Real SYN flood: Many SYNs in short time to same target
                flood_key = f"{src_ip}->{dst_ip}:{dst_port}"
                
                if flood_key not in self.syn_flood_tracking:
                    self.syn_flood_tracking[flood_key] = {'syns': [], 'first_syn': current_time}
                
                # Track SYN packets
                if tcp_flags & 0x02:  # SYN flag
                    self.syn_flood_tracking[flood_key]['syns'].append(current_time)
                    
                    # Remove old SYNs (older than 10 seconds)
                    recent_syns = [t for t in self.syn_flood_tracking[flood_key]['syns'] 
                                  if current_time - t < 10]
                    self.syn_flood_tracking[flood_key]['syns'] = recent_syns
                    
                    # Real SYN flood: 10+ SYNs in 10 seconds to same target
                    if len(recent_syns) >= 10:
                        return True, "DoS"
                
                # Real port scan: Many different ports in short time
                scan_key = src_ip
                
                if scan_key not in self.port_scan_tracking:
                    self.port_scan_tracking[scan_key] = {'ports': {}, 'first_scan': current_time}
                
                # Track port access
                if dst_port not in self.port_scan_tracking[scan_key]['ports']:
                    self.port_scan_tracking[scan_key]['ports'][dst_port] = current_time
                
                # Remove old port accesses (older than 30 seconds)
                recent_ports = {port: timestamp for port, timestamp in 
                               self.port_scan_tracking[scan_key]['ports'].items()
                               if current_time - timestamp < 30}
                self.port_scan_tracking[scan_key]['ports'] = recent_ports
                
                # Real port scan: 10+ different ports in 30 seconds
                if len(recent_ports) >= 10:
                    return True, "Reconnaissance"
        
        # External traffic patterns
        else:
            # External SYN flood is more suspicious
            if protocol == "tcp" and tcp_flags and (tcp_flags & 0x02):
                flood_key = f"{src_ip}->{dst_ip}:{dst_port}"
                
                if flood_key not in self.syn_flood_tracking:
                    self.syn_flood_tracking[flood_key] = {'syns': [], 'first_syn': current_time}
                
                self.syn_flood_tracking[flood_key]['syns'].append(current_time)
                
                # Remove old SYNs
                recent_syns = [t for t in self.syn_flood_tracking[flood_key]['syns'] 
                              if current_time - t < 5]
                self.syn_flood_tracking[flood_key]['syns'] = recent_syns
                
                # External SYN flood: 5+ SYNs in 5 seconds
                if len(recent_syns) >= 5:
                    return True, "DoS"
            
            # External port scanning
            if protocol == "tcp":
                scan_key = src_ip
                
                if scan_key not in self.port_scan_tracking:
                    self.port_scan_tracking[scan_key] = {'ports': {}, 'first_scan': current_time}
                
                if dst_port not in self.port_scan_tracking[scan_key]['ports']:
                    self.port_scan_tracking[scan_key]['ports'][dst_port] = current_time
                
                # Remove old ports
                recent_ports = {port: timestamp for port, timestamp in 
                               self.port_scan_tracking[scan_key]['ports'].items()
                               if current_time - timestamp < 20}
                self.port_scan_tracking[scan_key]['ports'] = recent_ports
                
                # External port scan: 5+ different ports in 20 seconds
                if len(recent_ports) >= 5:
                    return True, "Reconnaissance"
        
        return False, None
    
    def packet_handler(self, packet):
        """Handle captured packets with realistic detection"""
        try:
            self.packets_seen += 1
            
            if not packet.haslayer(IP):
                return
            
            src_ip = packet[IP].src
            dst_ip = packet[IP].dst
            
            # Skip broadcast and multicast
            if dst_ip.startswith("224.") or dst_ip.startswith("255."):
                return
            
            dst_port = 0
            protocol = "unknown"
            tcp_flags = None
            
            # Analyze packet
            if packet.haslayer(TCP):
                tcp_layer = packet[TCP]
                dst_port = tcp_layer.dport
                protocol = "tcp"
                tcp_flags = tcp_layer.flags
            elif packet.haslayer(UDP):
                udp_layer = packet[UDP]
                dst_port = udp_layer.dport
                protocol = "udp"
            elif packet.haslayer(ICMP):
                protocol = "icmp"
                # ICMP floods are suspicious if many in short time
                # For now, we'll be conservative and not flag ICMP
            
            # Check if this is suspicious
            is_attack, attack_type = self.is_suspicious_activity(
                src_ip, dst_ip, dst_port, protocol, tcp_flags
            )
            
            if is_attack:
                self.generate_real_alert(src_ip, dst_ip, dst_port, attack_type)
            
            # Print progress every 50 packets (less spam)
            if self.packets_seen % 50 == 0:
                print(f"📊 Packets: {self.packets_seen}, Attacks: {self.attacks_detected}")
        
        except Exception as e:
            pass  # Ignore packet processing errors to avoid spam
    
    def generate_real_alert(self, src_ip, dst_ip, dst_port, attack_type):
        """Generate real alert from packet analysis"""
        try:
            alert_data = {
                "timestamp": time.time(),
                "attack_type": attack_type,
                "attack_class": attack_type,
                "severity": "high",
                "confidence": 0.85,
                "probability": 0.85,
                "src_ip": src_ip,
                "dst_ip": dst_ip,
                "src_port": 0,
                "dst_port": dst_port,
                "protocol": "tcp",
                "packet_length": 1024,
                "interface": "realistic-capture",
                "flags": "SYN",
                "description": f"REAL {attack_type} detected from network analysis",
                "recommended_action": f"Investigate {src_ip} for malicious activity"
            }
            
            response = requests.post(f"{self.api_url}/alerts/real-detection", json=alert_data, timeout=2)
            
            if response.status_code == 200:
                self.attacks_detected += 1
                print(f"🚨 REAL ATTACK #{self.attacks_detected}: {attack_type}")
                print(f"   {src_ip} -> {dst_ip}:{dst_port}")
            
        except Exception as e:
            pass  # Don't spam errors
    
    def start_monitoring(self, duration=120):
        """Start realistic packet monitoring"""
        print("🕷️  REALISTIC Packet Detector")
        print("=" * 40)
        print("This only detects ACTUAL suspicious activity, not normal traffic")
        
        # Check API
        try:
            response = requests.get(f"{self.api_url}/health", timeout=3)
            if response.status_code != 200:
                print("❌ Backend API not healthy")
                return
        except:
            print("❌ Backend API not reachable!")
            return
        
        print(f"✅ Backend API connected")
        print(f"🔍 Monitoring for {duration} seconds...")
        print("💡 Normal traffic will NOT be flagged as attacks")
        print("🎯 Only real attack patterns will generate alerts")
        print()
        
        try:
            # Start packet capture
            sniff(
                prn=self.packet_handler,
                filter="tcp or udp",  # Skip ICMP for now
                timeout=duration,
                store=False
            )
        
        except Exception as e:
            print(f"❌ Capture failed: {e}")
        
        print(f"\n✅ Monitoring complete!")
        print(f"📊 Total packets analyzed: {self.packets_seen}")
        print(f"🚨 Real attacks detected: {self.attacks_detected}")
        
        if self.attacks_detected == 0:
            print("\n✅ No attacks detected - this is GOOD!")
            print("💡 Your network traffic appears normal")
            print("🧪 To test detection, run: python real_packet_attack.py 127.0.0.1")
        else:
            print(f"\n⚠️  {self.attacks_detected} real attacks detected!")
            print("🔍 Check your network for suspicious activity")

def main():
    """Main function"""
    detector = RealisticPacketDetector()
    
    print("This detector uses REALISTIC thresholds:")
    print("- SYN Flood: 10+ SYNs in 10 seconds (internal) or 5+ in 5 seconds (external)")
    print("- Port Scan: 10+ ports in 30 seconds (internal) or 5+ in 20 seconds (external)")
    print("- Normal web browsing will NOT be flagged")
    print()
    
    choice = input("Start realistic monitoring? (y/n): ").lower().strip()
    
    if choice == 'y':
        detector.start_monitoring(duration=120)  # 2 minutes
    else:
        print("Cancelled.")

if __name__ == "__main__":
    main()