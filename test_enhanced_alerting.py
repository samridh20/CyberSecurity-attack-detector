#!/usr/bin/env python3
"""
Test Enhanced Alerting & Automated Response System
Tests the complete flow: Attack Detection → Spoken Alert → Automated Response
"""

import asyncio
import time
import requests
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path("backend").absolute()))

def test_backend_connection():
    """Test backend API connection"""
    try:
        response = requests.get("http://127.0.0.1:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend API connected")
            return True
        else:
            print(f"⚠️  Backend API responded with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend API not reachable: {e}")
        return False

def test_speech_generation():
    """Test ElevenLabs speech generation via backend"""
    try:
        print("\n🔊 Testing Speech Generation...")
        
        # Test basic speech
        response = requests.post(
            "http://127.0.0.1:8000/speech/generate",
            json={
                "text": "This is a test of the speech generation system.",
                "voice": "urgent",
                "stability": 0.5,
                "similarity_boost": 0.8
            },
            timeout=30
        )
        
        if response.status_code == 200:
            print("✅ Basic speech generation working")
            print(f"   Audio size: {len(response.content)} bytes")
        else:
            print(f"❌ Speech generation failed: {response.status_code}")
            return False
        
        # Test alert speech
        response = requests.post(
            "http://127.0.0.1:8000/speech/alert",
            json={
                "attack_type": "DDoS",
                "source_ip": "192.168.1.100",
                "confidence": 0.85,
                "target_ip": "10.0.0.1"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            print("✅ Alert speech generation working")
            print(f"   Alert audio size: {len(response.content)} bytes")
            return True
        else:
            print(f"❌ Alert speech generation failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Speech generation test failed: {e}")
        return False

def trigger_test_attack():
    """Trigger a test attack to verify the complete flow"""
    try:
        print("\n🚨 Triggering Test Attack...")
        
        # Create a high-confidence attack alert
        attack_data = {
            "timestamp": time.time(),
            "attack_type": "DDoS",
            "attack_class": "DDoS",
            "severity": "critical",
            "confidence": 0.92,
            "probability": 0.92,
            "src_ip": "203.0.113.100",
            "dst_ip": "10.0.0.1",
            "src_port": 12345,
            "dst_port": 80,
            "protocol": "tcp",
            "packet_length": 1024,
            "interface": "TestInterface",
            "flags": "SYN",
            "description": "High-confidence DDoS attack detected - automated test",
            "recommended_action": "Immediately block source IP and enable DDoS protection"
        }
        
        response = requests.post(
            "http://127.0.0.1:8000/alerts/real-detection",
            json=attack_data,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Test attack alert created successfully")
            print(f"   Attack: {attack_data['attack_type']} from {attack_data['src_ip']}")
            print(f"   Confidence: {attack_data['confidence']:.1%}")
            print("\n💡 Check your frontend dashboard - the enhanced alerting should trigger:")
            print("   1. 🔊 Spoken alert should play automatically")
            print("   2. 🤖 Automated response should execute steps")
            print("   3. 📊 Progress should be tracked in real-time")
            return True
        else:
            print(f"❌ Failed to create test attack: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test attack creation failed: {e}")
        return False

def check_recent_alerts():
    """Check if alerts are being stored correctly"""
    try:
        print("\n📊 Checking Recent Alerts...")
        
        response = requests.get("http://127.0.0.1:8000/alerts/recent?limit=5", timeout=10)
        
        if response.status_code == 200:
            alerts = response.json()
            print(f"✅ Found {len(alerts)} recent alerts")
            
            for i, alert in enumerate(alerts[:3]):
                print(f"   {i+1}. {alert.get('attack_type', 'Unknown')} - "
                      f"{alert.get('confidence', 0):.1%} confidence - "
                      f"from {alert.get('src_ip', 'unknown')}")
            
            return len(alerts) > 0
        else:
            print(f"❌ Failed to get alerts: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Alert check failed: {e}")
        return False

def main():
    """Main test function"""
    print("🕷️  V.E.N.O.M ALERTING SYSTEM TEST")
    print("=" * 50)
    print("Versatile Event & Network Observation Module")
    print("Testing: Spoken Alerts + Automated Response")
    print()
    
    # Test sequence
    tests = [
        ("Backend Connection", test_backend_connection),
        ("Speech Generation", test_speech_generation),
        ("Alert Storage", check_recent_alerts),
        ("Test Attack Trigger", trigger_test_attack),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        print("-" * 30)
        
        try:
            result = test_func()
            results.append((test_name, result))
            
            if result:
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
                
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name:<20} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("\n🚀 NEXT STEPS:")
        print("   1. Start frontend: cd frontend && npm run dev")
        print("   2. Open: http://localhost:5173")
        print("   3. Watch for automatic spoken alerts and response execution")
        print("   4. Test with: python reconnaissance_attack.py")
    else:
        print(f"\n⚠️  {total - passed} tests failed - check the errors above")
        print("\n🔧 TROUBLESHOOTING:")
        print("   1. Ensure backend is running: cd backend && python -m api.server")
        print("   2. Check ElevenLabs API key is valid")
        print("   3. Verify network connectivity")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)