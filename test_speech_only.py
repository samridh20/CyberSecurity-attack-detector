#!/usr/bin/env python3
"""
Test ElevenLabs Speech Generation Only
Simple test to verify speech is working
"""

import requests
import time
import sys

def test_backend_speech():
    """Test backend speech generation"""
    print("🔊 Testing ElevenLabs Speech Generation...")
    
    try:
        # Test basic speech
        print("1. Testing basic speech...")
        response = requests.post(
            "http://127.0.0.1:8000/speech/generate",
            json={
                "text": "This is a test of the speech system. Can you hear this message?",
                "voice": "urgent"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            print(f"✅ Basic speech: {len(response.content)} bytes")
            
            # Save to file for testing
            with open("test_basic_speech.mp3", "wb") as f:
                f.write(response.content)
            print("   Saved as: test_basic_speech.mp3")
        else:
            print(f"❌ Basic speech failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
        
        # Test alert speech
        print("2. Testing alert speech...")
        response = requests.post(
            "http://127.0.0.1:8000/speech/alert",
            json={
                "attack_type": "DDoS",
                "source_ip": "192.168.1.100",
                "confidence": 0.85
            },
            timeout=30
        )
        
        if response.status_code == 200:
            print(f"✅ Alert speech: {len(response.content)} bytes")
            
            # Save to file for testing
            with open("test_alert_speech.mp3", "wb") as f:
                f.write(response.content)
            print("   Saved as: test_alert_speech.mp3")
            
            print("\n🎵 MANUAL TEST:")
            print("   Play these files to verify speech:")
            print("   - test_basic_speech.mp3")
            print("   - test_alert_speech.mp3")
            print("   On macOS: open test_alert_speech.mp3")
            
            return True
        else:
            print(f"❌ Alert speech failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Speech test failed: {e}")
        return False

def test_frontend_speech():
    """Test frontend speech by triggering an alert"""
    print("\n🚨 Testing Frontend Speech Integration...")
    
    try:
        # Create a test alert that should trigger speech
        alert_data = {
            "timestamp": time.time(),
            "attack_type": "DDoS",
            "attack_class": "DDoS",
            "severity": "critical",
            "confidence": 0.85,
            "probability": 0.85,
            "src_ip": "203.0.113.100",
            "dst_ip": "10.0.0.1",
            "src_port": 12345,
            "dst_port": 80,
            "protocol": "tcp",
            "description": "Test DDoS attack for speech verification"
        }
        
        response = requests.post(
            "http://127.0.0.1:8000/alerts/real-detection",
            json=alert_data,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Test alert created - check frontend for speech!")
            print("   Open: http://localhost:5173")
            print("   The popup should appear with spoken alert")
            return True
        else:
            print(f"❌ Failed to create test alert: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Frontend speech test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🔊 SPEECH GENERATION TEST")
    print("=" * 40)
    
    # Check backend connection
    try:
        response = requests.get("http://127.0.0.1:8000/health", timeout=5)
        if response.status_code != 200:
            print("❌ Backend not running - start with: cd backend && python -m api.server")
            return False
        print("✅ Backend connected")
    except:
        print("❌ Backend not reachable - start with: cd backend && python -m api.server")
        return False
    
    # Test backend speech
    backend_ok = test_backend_speech()
    
    # Test frontend integration
    frontend_ok = test_frontend_speech()
    
    print("\n" + "=" * 40)
    print("📋 SPEECH TEST RESULTS")
    print("=" * 40)
    print(f"Backend Speech:  {'✅ PASS' if backend_ok else '❌ FAIL'}")
    print(f"Frontend Integration: {'✅ PASS' if frontend_ok else '❌ FAIL'}")
    
    if backend_ok and frontend_ok:
        print("\n🎉 Speech system working!")
        print("\n🚀 NEXT STEPS:")
        print("   1. Open frontend: http://localhost:5173")
        print("   2. Run attack: python reconnaissance_attack.py")
        print("   3. Listen for spoken alerts!")
    else:
        print("\n⚠️  Speech system has issues")
        print("\n🔧 TROUBLESHOOTING:")
        print("   1. Check ElevenLabs API key")
        print("   2. Verify internet connection")
        print("   3. Check browser audio permissions")
        print("   4. Look at browser console for errors")
    
    return backend_ok and frontend_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)