#!/usr/bin/env python3
"""
Test Frontend Update - Inject new ML alerts to test frontend
"""

import requests
import time
import random

def inject_new_ml_alert():
    """Inject a new ML alert with current timestamp"""
    
    attack_types = ["DoS", "Exploits", "Reconnaissance", "Fuzzers", "Generic"]
    
    alert_data = {
        "timestamp": time.time(),  # Current timestamp
        "attack_type": random.choice(attack_types),
        "attack_class": random.choice(attack_types),
        "severity": "high",
        "confidence": random.uniform(0.7, 0.95),
        "probability": random.uniform(0.7, 0.95),
        "src_ip": f"192.168.1.{random.randint(100, 200)}",
        "dst_ip": "127.0.0.1",
        "src_port": random.randint(1024, 65535),
        "dst_port": random.choice([80, 443, 22, 21]),
        "protocol": "tcp",
        "packet_length": random.randint(64, 1500),
        "interface": "Wi-Fi",
        "flags": "SYN",
        "description": f"REAL ML {random.choice(attack_types)} detected",
        "recommended_action": "Investigate immediately"
    }
    
    try:
        response = requests.post("http://127.0.0.1:8000/alerts/real-detection", json=alert_data, timeout=5)
        
        if response.status_code == 200:
            print(f"✅ Injected ML alert: {alert_data['attack_type']} at {alert_data['timestamp']}")
            return True
        else:
            print(f"❌ Failed to inject: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_frontend_updates():
    """Test if frontend updates with new alerts"""
    print("🧪 Testing Frontend Updates with New ML Alerts")
    print("=" * 50)
    print("This will inject new ML alerts every 5 seconds")
    print("Watch your frontend to see if it updates!")
    print()
    
    for i in range(10):  # Inject 10 new alerts
        print(f"Injecting alert {i+1}/10...")
        
        if inject_new_ml_alert():
            print("   ✅ Alert injected - check frontend!")
        else:
            print("   ❌ Injection failed")
        
        print(f"   Waiting 5 seconds...")
        time.sleep(5)
    
    print("\n🎉 Test complete!")
    print("💻 Check your frontend - you should see 10 new alerts!")

if __name__ == "__main__":
    test_frontend_updates()