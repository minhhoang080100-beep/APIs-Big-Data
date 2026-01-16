"""
Test script for Login API
"""
import requests
import json

# API Configuration
BASE_URL = "http://localhost:8000"
LOGIN_ENDPOINT = f"{BASE_URL}/api/login"

def test_login(username: str, password: str):
    """Test login endpoint"""
    print(f"\n{'='*60}")
    print(f"Testing login for user: {username}")
    print(f"{'='*60}")
    
    # Prepare request
    payload = {
        "Username": username,
        "Password": password
    }
    
    print(f"\n📤 Request:")
    print(f"  URL: {LOGIN_ENDPOINT}")
    print(f"  Payload: {json.dumps(payload, indent=2)}")
    
    try:
        # Make request
        response = requests.post(LOGIN_ENDPOINT, json=payload)
        
        print(f"\n📥 Response:")
        print(f"  Status Code: {response.status_code}")
        print(f"  Body: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print(f"\n✅ Login successful!")
            data = response.json()
            print(f"  Access Token: {data['AccessToken'][:50]}...")
            print(f"  Message: {data['Message']}")
            print(f"  Expires In: {data['ExpireIn']}")
            return data['AccessToken']
        else:
            print(f"\n❌ Login failed!")
            return None
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Error: Cannot connect to API server at {BASE_URL}")
        print(f"   Make sure the server is running: python main.py")
        return None
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return None


def test_protected_route(access_token: str):
    """Test protected route with access token"""
    print(f"\n{'='*60}")
    print(f"Testing protected route with token")
    print(f"{'='*60}")
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/api/protected", headers=headers)
        
        print(f"\n📥 Response:")
        print(f"  Status Code: {response.status_code}")
        print(f"  Body: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print(f"\n✅ Protected route access successful!")
        else:
            print(f"\n❌ Protected route access failed!")
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")


if __name__ == "__main__":
    print("🚀 TOS Big Data API - Login Test")
    print(f"Server: {BASE_URL}")
    
    # Test with user "abc" (from spec)
    token1 = test_login("abc", "6504E4EF9274BDE48162B6F2BE0FDF0")
    
    # Test with user "admin" (demo user)
    token2 = test_login("admin", "admin123")
    
    # Test with invalid credentials
    test_login("invalid_user", "wrong_password")
    
    # Test protected route if we have a token
    if token1:
        test_protected_route(token1)
    
    print("\n" + "="*60)
    print("✨ Test completed!")
    print("="*60)
