"""
Test script for Handling Method List API
"""
import requests
import json
from typing import Optional

# API Configuration
BASE_URL = "http://localhost:8000"
LOGIN_ENDPOINT = f"{BASE_URL}/api/login"
HANDLING_METHOD_ENDPOINT = f"{BASE_URL}/api/handlingMethodList"


def login() -> Optional[str]:
    """Login and get access token"""
    print("=" * 60)
    print("Logging in...")
    print("=" * 60)
    
    response = requests.post(
        LOGIN_ENDPOINT,
        json={
            "Username": "abc",
            "Password": "6504E4EF9274BDE48162B6F2BE0FDF0"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        token = data["AccessToken"]
        print(f"✅ Login successful!")
        print(f"   Token: {token[:30]}...")
        return token
    else:
        print(f"❌ Login failed: {response.status_code}")
        return None


def test_get_handling_methods(token: str, **filters):
    """Test GET /api/handlingMethodList with filters"""
    print("\n" + "=" * 60)
    filter_desc = ", ".join([f"{k}={v}" for k, v in filters.items()]) if filters else "No filters"
    print(f"Testing GET /api/handlingMethodList ({filter_desc})")
    print("=" * 60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(
            HANDLING_METHOD_ENDPOINT,
            headers=headers,
            params=filters
        )
        
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Success!")
            print(f"   Code: {data['code']}")
            print(f"   Message: {data['message']}")
            print(f"   Total Handling Methods: {len(data['data'])}")
            
            if data['data']:
                print(f"\n📋 Handling Methods (first 5):")
                for i, method in enumerate(data['data'][:5], 1):
                    print(f"\n   {i}. Method ID: {method['handlingMethodId']}")
                    print(f"      Name: {method['handlingMethodName']}")
                    print(f"      Created: {method['createdDate']}")
                    print(f"      Modified: {method['modifiedDate']}")
                
                if len(data['data']) > 5:
                    print(f"\n   ... and {len(data['data']) - 5} more methods")
            
            return data
        else:
            print(f"❌ Failed!")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None


def test_get_handling_method_by_id(token: str, method_id: str):
    """Test GET /api/handlingMethodList/{method_id}"""
    print("\n" + "=" * 60)
    print(f"Testing GET /api/handlingMethodList/{method_id}")
    print("=" * 60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(
            f"{HANDLING_METHOD_ENDPOINT}/{method_id}",
            headers=headers
        )
        
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Handling Method Found!")
            print(f"   Code: {data['code']}")
            print(f"   Message: {data['message']}")
            
            if data['data']:
                method = data['data']
                print(f"\n📋 Method Details:")
                print(f"   ID: {method['handlingMethodId']}")
                print(f"   Name: {method['handlingMethodName']}")
                print(f"   Created: {method['createdDate']}")
                print(f"   Modified: {method['modifiedDate']}")
            
            return data
        elif response.status_code == 404:
            print(f"❌ Handling method not found!")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Failed!")
            print(f"   Response: {response.text}")
            
        return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None


def test_pagination(token: str):
    """Test pagination"""
    print("\n" + "=" * 60)
    print("Testing Pagination")
    print("=" * 60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test page 1
    print("\n📄 Page 1 (limit=3):")
    response = requests.get(
        HANDLING_METHOD_ENDPOINT,
        headers=headers,
        params={"page": 1, "limit": 3}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ Got {len(data['data'])} records")
        if data['data']:
            print(f"   First method: {data['data'][0]['handlingMethodName']}")
    
    # Test page 2
    print("\n📄 Page 2 (limit=3):")
    response = requests.get(
        HANDLING_METHOD_ENDPOINT,
        headers=headers,
        params={"page": 2, "limit": 3}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ Got {len(data['data'])} records")
        if data['data']:
            print(f"   First method: {data['data'][0]['handlingMethodName']}")


def test_without_auth():
    """Test endpoint without authentication"""
    print("\n" + "=" * 60)
    print("Testing without authentication (should fail)")
    print("=" * 60)
    
    try:
        response = requests.get(HANDLING_METHOD_ENDPOINT)
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 401:
            print(f"✅ Correctly rejected! (401 Unauthorized)")
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    print("🚀 TOS Handling Method List API - Test Suite")
    print(f"Server: {BASE_URL}")
    print()
    
    # Test 1: Login
    token = login()
    
    if not token:
        print("\n❌ Cannot proceed without token")
        exit(1)
    
    # Test 2: Get all handling methods (default pagination)
    test_get_handling_methods(token)
    
    # Test 3: Get handling methods with custom pagination
    test_get_handling_methods(token, page=1, limit=10)
    
    # Test 4: Test pagination
    test_pagination(token)
    
    # Test 5: Get specific handling method by ID
    print("\n" + "=" * 60)
    print("Getting handling method ID for detail test...")
    print("=" * 60)
    
    response = requests.get(
        HANDLING_METHOD_ENDPOINT,
        headers={"Authorization": f"Bearer {token}"},
        params={"limit": 1}
    )
    
    if response.status_code == 200:
        data = response.json()
        if data['data']:
            method_id = data['data'][0]['handlingMethodId']
            print(f"Using handling method ID: {method_id}")
            test_get_handling_method_by_id(token, method_id)
        else:
            print("No handling methods found to test detail endpoint")
    
    # Test 6: Test invalid handling method ID
    test_get_handling_method_by_id(token, "INVALID999")
    
    # Test 7: Test without authentication
    test_without_auth()
    
    print("\n" + "=" * 60)
    print("✨ Test Suite Completed!")
    print("=" * 60)
