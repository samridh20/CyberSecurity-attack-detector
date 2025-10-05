#!/usr/bin/env python3
"""
Safe attack simulation for testing NIDS detection capabilities.
This generates network traffic patterns that mimic attacks without causing harm.
"""

import time
import socket
import threading
import argparse
from concurrent.futures import ThreadPoolExecutor
import requests
import subprocess
import sys

def simulate_dos_flood(target_host="127.0.0.1", target_port=80, duration=10, threads=50):
    """
    Simulate a DoS attack by creating many rapid connections.
    Uses localhost to avoid affecting external systems.
    """
    print(f"Starting DoS simulation: {threads} threads for {duration} seconds")
    
    def flood_worker():
        end_time = time.time() + duration
        connections = 0
        
        while time.time() < end_time:
            try:
                # Create rapid TCP connections
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.1)
                sock.connect((target_host, target_port))
                sock.close()
                connections += 1
                time.sleep(0.01)  # Small delay to avoid overwhelming
            except:
                pass  # Expected to fail, just generating traffic patterns
        
        print(f"Thread completed: {connections} connection attempts")
    
    # Start multiple threads
    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = [executor.submit(flood_worker) for _ in range(threads)]
        
        # Wait for completion
        for future in futures:
            future.result()
    
    print("DoS simulation completed")

def simulate_port_scan(target_host="127.0.0.1", start_port=1, end_port=1000, delay=0.01):
    """
    Simulate port scanning activity.
    """
    print(f"Starting port scan simulation: ports {start_port}-{end_port}")
    
    open_ports = []
    
    for port in range(start_port, min(end_port + 1, 1001)):  # Limit to avoid too much traffic
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.1)
            result = sock.connect_ex((target_host, port))
            
            if result == 0:
                open_ports.append(port)
                print(f"Port {port}: Open")
            
            sock.close()
            time.sleep(delay)
            
        except:
            pass
    
    print(f"Port scan completed. Found {len(open_ports)} open ports: {open_ports}")

def simulate_http_flood(target_url="http://httpbin.org/get", requests_count=100, threads=10):
    """
    Simulate HTTP flood attack.
    Uses httpbin.org which is designed for testing.
    """
    print(f"Starting HTTP flood simulation: {requests_count} requests with {threads} threads")
    
    def http_worker(requests_per_thread):
        for i in range(requests_per_thread):
            try:
                response = requests.get(target_url, timeout=1)
                if i % 10 == 0:
                    print(f"HTTP request {i}: {response.status_code}")
            except:
                pass  # Expected timeouts/failures
    
    requests_per_thread = requests_count // threads
    
    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = [executor.submit(http_worker, requests_per_thread) for _ in range(threads)]
        
        for future in futures:
            future.result()
    
    print("HTTP flood simulation completed")

def simulate_suspicious_payload():
    """
    Generate network traffic with suspicious payload patterns.
    """
    print("Starting suspicious payload simulation")
    
    # Create suspicious payloads that might trigger detection
    suspicious_payloads = [
        b"\\x90" * 100 + b"\\x31\\xc0\\x50\\x68",  # NOP sled + shellcode pattern
        b"SELECT * FROM users WHERE id=1; DROP TABLE users;--",  # SQL injection
        b"<script>alert('xss')</script>",  # XSS attempt
        b"../../../../etc/passwd",  # Directory traversal
        b"cmd.exe /c dir",  # Command injection
    ]
    
    for i, payload in enumerate(suspicious_payloads):
        try:
            # Send via HTTP POST to httpbin
            response = requests.post(
                "http://httpbin.org/post", 
                data=payload,
                timeout=2
            )
            print(f"Suspicious payload {i+1} sent: {response.status_code}")
            time.sleep(1)
        except:
            pass
    
    print("Suspicious payload simulation completed")

def main():
    parser = argparse.ArgumentParser(description="Safe attack simulation for NIDS testing")
    parser.add_argument("--attack-type", choices=["dos", "scan", "http", "payload", "all"], 
                       default="all", help="Type of attack to simulate")
    parser.add_argument("--duration", type=int, default=10, help="Duration for DoS simulation")
    parser.add_argument("--threads", type=int, default=20, help="Number of threads for DoS")
    parser.add_argument("--target", default="127.0.0.1", help="Target host (default: localhost)")
    
    args = parser.parse_args()
    
    print("=== NIDS Attack Simulation ===")
    print("This script generates network traffic patterns that mimic attacks")
    print("for testing intrusion detection systems safely.")
    print()
    
    if args.attack_type in ["dos", "all"]:
        print("1. DoS Flood Simulation")
        simulate_dos_flood(target_host=args.target, duration=args.duration, threads=args.threads)
        time.sleep(2)
    
    if args.attack_type in ["scan", "all"]:
        print("\\n2. Port Scan Simulation")
        simulate_port_scan(target_host=args.target, start_port=20, end_port=100)
        time.sleep(2)
    
    if args.attack_type in ["http", "all"]:
        print("\\n3. HTTP Flood Simulation")
        simulate_http_flood(requests_count=50, threads=5)
        time.sleep(2)
    
    if args.attack_type in ["payload", "all"]:
        print("\\n4. Suspicious Payload Simulation")
        simulate_suspicious_payload()
    
    print("\\n=== Simulation Complete ===")
    print("Check your NIDS logs and alerts for detected attacks!")

if __name__ == "__main__":
    main()