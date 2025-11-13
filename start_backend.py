#!/usr/bin/env python3
"""
Startup script for Phishing Detector Extension Backend
This script helps ensure the backend starts properly and is accessible.
"""

import subprocess
import sys
import time
import requests
import os
from pathlib import Path

def check_backend_health():
    """Check if backend is already running."""
    try:
        response = requests.get("http://localhost:5000/health", timeout=3)
        if response.status_code == 200:
            print("✅ Backend is already running!")
            return True
    except:
        pass
    return False

def start_backend():
    """Start the backend server."""
    print("🚀 Starting Phishing Detector Backend...")
    
    # Check if backend is already running
    if check_backend_health():
        return True
    
    # Change to backend directory
    backend_dir = Path(__file__).parent / "backend"
    if not backend_dir.exists():
        print("❌ Backend directory not found!")
        return False
    
    os.chdir(backend_dir)
    
    # Check if requirements are installed
    try:
        import flask
        import pandas
        import sklearn
        import requests
        from bs4 import BeautifulSoup  # beautifulsoup4 package imports as bs4
        print("✅ All required packages are installed")
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("📦 Installing requirements...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
            print("✅ Requirements installed successfully")
        except subprocess.CalledProcessError:
            print("❌ Failed to install requirements")
            return False
    
    # Start the backend
    try:
        print("🔄 Starting Flask server...")
        process = subprocess.Popen([
            sys.executable, "app.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Wait a moment for server to start
        time.sleep(3)
        
        # Check if server started successfully
        if check_backend_health():
            print("✅ Backend started successfully!")
            print("🌐 Server running at: http://localhost:5000")
            print("📊 Health check: http://localhost:5000/health")
            print("\n💡 You can now use the Phishing Detector Extension!")
            print("🔄 To stop the server, press Ctrl+C")
            
            try:
                # Keep the process running
                process.wait()
            except KeyboardInterrupt:
                print("\n⏹️ Stopping backend server...")
                process.terminate()
                print("✅ Backend stopped")
            
            return True
        else:
            print("❌ Backend failed to start properly")
            process.terminate()
            return False
            
    except Exception as e:
        print(f"❌ Error starting backend: {e}")
        return False

def main():
    """Main function."""
    print("🛡️ Phishing Detector Extension - Backend Startup")
    print("=" * 50)
    
    try:
        if start_backend():
            print("\n🎉 Backend is ready!")
        else:
            print("\n❌ Failed to start backend")
            print("\n🔧 Troubleshooting:")
            print("1. Make sure Python is installed")
            print("2. Check if port 5000 is available")
            print("3. Install requirements: pip install -r backend/requirements.txt")
            print("4. Try running manually: cd backend && python app.py")
            
    except KeyboardInterrupt:
        print("\n⏹️ Startup interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
