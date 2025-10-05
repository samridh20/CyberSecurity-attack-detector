#!/usr/bin/env python3
"""
Start REAL ML-Based NIDS System
This runs the actual machine learning pipeline, not signature matching
"""

import subprocess
import time
import sys
import threading
import requests
from pathlib import Path

def check_backend():
    """Check if backend API is running"""
    try:
        response = requests.get("http://127.0.0.1:8000/health", timeout=3)
        return response.status_code == 200
    except:
        return False

def start_backend_with_ml():
    """Start backend API server with real ML NIDS"""
    print("🧠 Starting Backend with REAL ML NIDS...")
    
    backend_dir = Path("backend")
    if not backend_dir.exists():
        print("❌ Backend directory not found!")
        return None
    
    try:
        # Start backend API with real NIDS
        process = subprocess.Popen(
            [sys.executable, "-m", "api.server", "--port", "8000"],
            cwd=backend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for backend to start
        for i in range(20):
            if check_backend():
                print("✅ Backend with ML NIDS started!")
                return process
            time.sleep(1)
            print(f"   Waiting for ML backend... ({i+1}/20)")
        
        print("❌ Backend failed to start within 20 seconds")
        return None
        
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        return None

def test_ml_detection():
    """Test that ML detection is working"""
    print("\n🧪 Testing ML Detection...")
    
    try:
        # Check health
        response = requests.get("http://127.0.0.1:8000/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            print(f"✅ ML NIDS Status: {health['status']}")
        
        # Check stats
        response = requests.get("http://127.0.0.1:8000/stats", timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print(f"📊 ML Stats: {stats['packets_processed']} packets, {stats['alerts_generated']} ML alerts")
        
        # Check alerts
        response = requests.get("http://127.0.0.1:8000/alerts/recent", timeout=5)
        if response.status_code == 200:
            alerts = response.json()
            print(f"🧠 ML Alerts Available: {len(alerts)}")
            
            if alerts:
                print("   Recent ML detections:")
                for alert in alerts[:3]:
                    print(f"   - {alert.get('attack_type', 'Unknown')}: {alert.get('confidence', 0):.2f} confidence")
        
        return True
        
    except Exception as e:
        print(f"❌ ML detection test failed: {e}")
        return False

def main():
    """Main startup function"""
    print("🕷️  REAL ML-Based NIDS Startup")
    print("=" * 50)
    print("This starts your ACTUAL machine learning NIDS system")
    print("NO signature matching - pure ML detection!")
    print()
    
    processes = []
    
    try:
        # Check if backend is already running
        if check_backend():
            print("✅ Backend already running")
        else:
            # Start backend with real ML NIDS
            backend_process = start_backend_with_ml()
            if backend_process:
                processes.append(backend_process)
            else:
                print("❌ Cannot start ML backend")
                return
        
        # Test ML detection
        if test_ml_detection():
            print("\n🎉 REAL ML NIDS SYSTEM IS READY!")
        else:
            print("\n⚠️  ML system may have issues")
        
        print("\n🎯 INSTRUCTIONS FOR ML TESTING:")
        print("=" * 50)
        print("1. The REAL ML-based NIDS is now running")
        print("2. Run attacks: python comprehensive_attack.py 127.0.0.1")
        print("3. ML models will analyze packets and detect attacks")
        print("4. Start frontend: cd frontend && npm run dev")
        print("5. View ML detections at: http://localhost:5173")
        print()
        print("🧠 Machine Learning Pipeline Active:")
        print("   Packets → Feature Extraction → ML Models → Real Alerts")
        print()
        print("🛑 Press Ctrl+C to stop ML NIDS system")
        
        # Keep running
        while True:
            time.sleep(5)
            
            # Check ML stats periodically
            try:
                response = requests.get("http://127.0.0.1:8000/stats", timeout=2)
                if response.status_code == 200:
                    stats = response.json()
                    if stats['packets_processed'] > 0:
                        print(f"🧠 ML Processing: {stats['packets_processed']} packets, {stats['alerts_generated']} ML alerts")
            except:
                pass
    
    except KeyboardInterrupt:
        print("\n🛑 Shutting down ML NIDS system...")
        
        # Kill all processes
        for process in processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                try:
                    process.kill()
                except:
                    pass
        
        print("✅ ML NIDS system stopped")
    
    print("\n🧠 Machine Learning NIDS session complete!")

if __name__ == "__main__":
    main()