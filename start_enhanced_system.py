#!/usr/bin/env python3
"""
Start Enhanced NIDS System with Spoken Alerts
Starts backend with ElevenLabs integration and frontend
"""

import subprocess
import time
import sys
import threading
import requests
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking Dependencies...")
    
    # Check Python packages
    try:
        import aiohttp
        print("   ✅ aiohttp installed")
    except ImportError:
        print("   ❌ aiohttp missing - run: pip install aiohttp")
        return False
    
    try:
        import fastapi
        print("   ✅ FastAPI installed")
    except ImportError:
        print("   ❌ FastAPI missing - run: pip install fastapi")
        return False
    
    # Check Node.js
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True, check=True)
        print(f"   ✅ Node.js: {result.stdout.strip()}")
    except:
        print("   ❌ Node.js not found - install from https://nodejs.org/")
        return False
    
    return True

def start_backend():
    """Start backend API server with ElevenLabs support"""
    print("🚀 Starting Enhanced Backend...")
    
    backend_dir = Path("backend")
    if not backend_dir.exists():
        print("❌ Backend directory not found!")
        return None
    
    try:
        process = subprocess.Popen(
            [sys.executable, "-m", "api.server", "--port", "8000"],
            cwd=backend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for backend to start
        for i in range(20):
            try:
                response = requests.get("http://127.0.0.1:8000/health", timeout=3)
                if response.status_code == 200:
                    print("✅ Enhanced backend started with ElevenLabs support!")
                    return process
            except:
                pass
            
            time.sleep(1)
            print(f"   Waiting for backend... ({i+1}/20)")
        
        print("❌ Backend failed to start within 20 seconds")
        return None
        
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        return None

def start_frontend():
    """Start frontend development server"""
    print("🎨 Starting Frontend...")
    
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("❌ Frontend directory not found!")
        return None
    
    try:
        process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=frontend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait a bit for frontend to start
        time.sleep(5)
        print("✅ Frontend started!")
        return process
        
    except Exception as e:
        print(f"❌ Failed to start frontend: {e}")
        return None

def test_speech_system():
    """Test the speech generation system"""
    print("\n🔊 Testing Speech System...")
    
    try:
        # Test basic speech endpoint
        response = requests.post(
            "http://127.0.0.1:8000/speech/generate",
            json={
                "text": "Enhanced alerting system is ready.",
                "voice": "urgent"
            },
            timeout=15
        )
        
        if response.status_code == 200:
            print("✅ Speech generation working!")
            print(f"   Generated {len(response.content)} bytes of audio")
            return True
        else:
            print(f"⚠️  Speech generation returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Speech test failed: {e}")
        return False

def main():
    """Main startup function"""
    print("🕷️  V.E.N.O.M SYSTEM STARTUP")
    print("=" * 50)
    print("Versatile Event & Network Observation Module")
    print("Features: Spoken Alerts + Automated Response")
    print()
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Missing dependencies - please install them first")
        return False
    
    processes = []
    
    try:
        # Start backend
        backend_process = start_backend()
        if backend_process:
            processes.append(backend_process)
        else:
            print("❌ Cannot start backend")
            return False
        
        # Test speech system
        if not test_speech_system():
            print("⚠️  Speech system may have issues")
        
        # Start frontend
        frontend_process = start_frontend()
        if frontend_process:
            processes.append(frontend_process)
        else:
            print("❌ Cannot start frontend")
            return False
        
        print("\n🎉 V.E.N.O.M SYSTEM READY!")
        print("=" * 50)
        print("🌐 Frontend: http://localhost:5173")
        print("🔧 Backend API: http://127.0.0.1:8000")
        print()
        print("🚨 ENHANCED FEATURES ACTIVE:")
        print("   ✅ Automatic spoken alerts via ElevenLabs")
        print("   ✅ Automated PowerShell command execution")
        print("   ✅ Real-time progress tracking")
        print("   ✅ Fixed UI popup positioning")
        print()
        print("🧪 TEST THE SYSTEM:")
        print("   1. Run: python test_enhanced_alerting.py")
        print("   2. Or: python reconnaissance_attack.py")
        print("   3. Watch for automatic spoken alerts!")
        print()
        print("🛑 Press Ctrl+C to stop all services")
        
        # Keep running
        while True:
            time.sleep(5)
            
            # Check if processes are still running
            for process in processes[:]:
                if process.poll() is not None:
                    print(f"⚠️  Process {process.pid} stopped unexpectedly")
                    processes.remove(process)
            
            if not processes:
                print("❌ All processes stopped")
                break
    
    except KeyboardInterrupt:
        print("\n🛑 Shutting down enhanced system...")
        
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
        
        print("✅ Enhanced system stopped")
    
    print("\n🎯 Enhanced alerting session complete!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)