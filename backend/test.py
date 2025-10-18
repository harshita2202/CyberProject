import requests
import json

def test():
    # Test URLs - mix of safe and potentially suspicious
    test_urls = [
        "https://www.google.com",
        "https://github.com",
        "http://testsafebrowsing.appspot.com",  # This should be forced as phishing
        "https://bit.ly/test",  # Short URL
        "http://example.com"
    ]
    
    for url in test_urls:
        print(f"\n🔍 Testing URL: {url}")
        try:
            response = requests.post(
                "http://localhost:5000/check",
                json={"url": url},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Status: {result['status']}")
                print(f"   Confidence: {result['confidence']}%")
                print(f"   Risk Score: {result['riskScore']}")
                print(f"   Is Safe: {result['isSafe']}")
                print(f"   Is Phishing: {result['isPhishing']}")
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to backend. Make sure Flask app is running!")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    print("🚀 Starting backend test...")
    test()