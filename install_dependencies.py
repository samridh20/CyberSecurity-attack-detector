#!/usr/bin/env python3
"""
Install all dependencies for NIDS system
Installs both backend Python packages and frontend Node.js packages
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd, cwd=None, description=""):
    """Run a command and handle errors"""
    print(f"📦 {description}")
    print(f"   Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True
        )
        print(f"   ✅ Success!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Failed!")
        print(f"   Error: {e.stderr}")
        return False

def install_backend_deps():
    """Install backend Python dependencies"""
    backend_dir = Path("backend")
    
    if not backend_dir.exists():
        print("❌ Backend directory not found!")
        return False
    
    requirements_file = backend_dir / "requirements.txt"
    if not requirements_file.exists():
        print("❌ Backend requirements.txt not found!")
        return False
    
    return run_command(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
        cwd=backend_dir,
        description="Installing backend Python dependencies"
    )

def install_frontend_deps():
    """Install frontend Node.js dependencies"""
    frontend_dir = Path("frontend")
    
    if not frontend_dir.exists():
        print("❌ Frontend directory not found!")
        return False
    
    package_json = frontend_dir / "package.json"
    if not package_json.exists():
        print("❌ Frontend package.json not found!")
        return False
    
    return run_command(
        ["npm", "install"],
        cwd=frontend_dir,
        description="Installing frontend Node.js dependencies"
    )

def check_prerequisites():
    """Check if required tools are installed"""
    print("🔍 Checking prerequisites...")
    
    # Check Python
    try:
        result = subprocess.run([sys.executable, "--version"], capture_output=True, text=True)
        print(f"   ✅ Python: {result.stdout.strip()}")
    except:
        print("   ❌ Python not found!")
        return False
    
    # Check pip
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], capture_output=True, check=True)
        print("   ✅ pip: Available")
    except:
        print("   ❌ pip not found!")
        return False
    
    # Check Node.js
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True, check=True)
        print(f"   ✅ Node.js: {result.stdout.strip()}")
    except:
        print("   ❌ Node.js not found! Please install Node.js 18+ from https://nodejs.org/")
        return False
    
    # Check npm
    try:
        result = subprocess.run(["npm", "--version"], capture_output=True, text=True, check=True)
        print(f"   ✅ npm: {result.stdout.strip()}")
    except:
        print("   ❌ npm not found!")
        return False
    
    return True

def main():
    """Main installation function"""
    print("🕷️  NIDS System Dependency Installation")
    print("=" * 45)
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Please install missing tools and try again.")
        return False
    
    print("\n🚀 Installing dependencies...")
    
    # Install backend dependencies
    backend_success = install_backend_deps()
    
    # Install frontend dependencies
    frontend_success = install_frontend_deps()
    
    # Summary
    print("\n📋 Installation Summary:")
    print(f"   Backend:  {'✅ Success' if backend_success else '❌ Failed'}")
    print(f"   Frontend: {'✅ Success' if frontend_success else '❌ Failed'}")
    
    if backend_success and frontend_success:
        print("\n🎉 All dependencies installed successfully!")
        print("\nNext steps:")
        print("   1. Run: python start_web_system.py")
        print("   2. Open: http://localhost:5173")
        return True
    else:
        print("\n❌ Some installations failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)