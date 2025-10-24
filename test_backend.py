#!/usr/bin/env python3
"""
Quick test to verify the backend is working properly.
Run this script to test if the backend is accessible.
"""

import requests
import json
import sys

def test_backend():
    """Test if the backend is running and accessible."""
    print("🧪 Testing Phishing Detector Backend...")
    print("=" * 40)
    
    # Test health endpoint
    try:
        print("🔍 Testing health endpoint...")
        response = requests.get("http://localhost:5000/health", timeout=5)
        
        if response.status_code == 200:
            print("✅ Health check passed!")
            print(f"📊 Response: {response.json()}")
        else:
            print(f"❌ Health check failed: HTTP {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend server")
        print("💡 Make sure the backend is running:")
        print("   - Run: python start_backend.py")
        print("   - Or: cd backend && python app.py")
        return False
    except requests.exceptions.Timeout:
        print("❌ Backend server is not responding")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    # Test phishing detection endpoint
    try:
        print("\n🔍 Testing phishing detection...")
        test_url = "https://www.google.com"
        
        response = requests.post(
            "http://localhost:5000/check",
            json={"url": test_url},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Phishing detection working!")
            print(f"📊 URL: {test_url}")
            print(f"🛡️ Status: {data.get('status', 'Unknown')}")
            print(f"✅ Safe: {data.get('isSafe', False)}")
            print(f"📁 Category: {data.get('category', 'Unknown')}")
            print(f"🎯 Confidence: {data.get('confidence', 0):.1f}%")
            return True
        else:
            print(f"❌ Phishing detection failed: HTTP {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Phishing detection timed out")
        return False
    except Exception as e:
        print(f"❌ Phishing detection error: {e}")
        return False

def main():
    """Main function."""
    try:
        if test_backend():
            print("\n🎉 Backend is working perfectly!")
            print("✅ You can now use the Phishing Detector Extension")
        else:
            print("\n❌ Backend test failed")
            print("\n🔧 Troubleshooting steps:")
            print("1. Make sure the backend is running:")
            print("   - Run: python start_backend.py")
            print("   - Or: cd backend && python app.py")
            print("2. Check if port 5000 is available")
            print("3. Verify all requirements are installed")
            print("4. Check the backend console for errors")
            
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")

if __name__ == "__main__":
    main()
