#!/usr/bin/env python3
"""
Script to trigger NIDS alerts by generating traffic patterns that match the SimpleModelAdapter heuristics.
"""

import socket
import time
import threading
import requests
from concurrent.futures import ThreadPoolExecutor

def high_rate_connections(duration=20):
    """Generate high packet rate to trigger DoS detection."""
    print("Generating high-rate connections to trigger DoS detection...")
    
    def worker():
        end_time = time.time() + duration
        count = 0
        while time.time() < end_time:
            try:
                # Rapid connection attempts
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.1)
                sock.connect(('127.0.0.1', 8080))
                sock.send(b'GET / HTTP/1.1\\r\\nHost: localhost\\r\\n\\r\\n')
                sock.close()
                count += 1
                time.sleep(0.005)  # Very short delay = high rate
            except:
                pass
        print(f"Worker generated {count} connections")
    
    # Use multiple threads to increase packet rate
    threads = []
    for i in range(20):  # 20 threads
        t = threading.Thread(target=worker)
        t.start()
        threads.append(t)
    
    for t in threads:
        t.join()
    
    print("High-rate connection test completed")

def unusual_ports_scan():
    """Scan unusual ports to trigger reconnaissance detection."""
    print("Scanning unusual ports to trigger reconnaissance detection...")
    
    unusual_ports = [1337, 31337, 4444, 5555, 6666, 7777, 8888, 9999, 12345, 54321]
    
    for port in unusual_ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.1)
            sock.connect(('127.0.0.1', port))
            sock.close()
        except:
            pass  # Expected to fail
        time.sleep(0.1)
    
    print("Unusual ports scan completed")

def large_payloads():
    """Send large payloads to trigger size-based detection."""
    print("Sending large payloads to trigger size-based detection...")
    
    # Create large payload (>1400 bytes)
    large_payload = b'A' * 2000
    
    try:
        response = requests.post('http://httpbin.org/post', data=large_payload, timeout=5)
        print(f"Large payload sent: {len(large_payload)} bytes, response: {response.status_code}")
    except Exception as e:
        print(f"Large payload request failed: {e}")

def suspicious_patterns():
    """Generate traffic with suspicious patterns."""
    print("Generating suspicious traffic patterns...")
    
    # High entropy data (encrypted/compressed-like)
    import random
    high_entropy_data = bytes([random.randint(0, 255) for _ in range(1000)])
    
    try:
        response = requests.post('http://httpbin.org/post', data=high_entropy_data, timeout=5)
        print(f"High entropy payload sent, response: {response.status_code}")
    except Exception as e:
        print(f"High entropy request failed: {e}")

def main():
    print("=== NIDS Alert Trigger Test ===")
    print("This will generate traffic patterns designed to trigger the SimpleModelAdapter alerts")
    print()
    
    # Test 1: High packet rate (should trigger DoS detection)
    print("Test 1: High packet rate")
    high_rate_connections(duration=10)
    time.sleep(2)
    
    # Test 2: Unusual port scanning
    print("\\nTest 2: Unusual port scanning")
    unusual_ports_scan()
    time.sleep(2)
    
    # Test 3: Large payloads
    print("\\nTest 3: Large payloads")
    large_payloads()
    time.sleep(2)
    
    # Test 4: Suspicious patterns
    print("\\nTest 4: Suspicious patterns")
    suspicious_patterns()
    
    print("\\n=== Alert trigger test completed ===")
    print("Check the NIDS output for alerts!")

if __name__ == "__main__":
    main()