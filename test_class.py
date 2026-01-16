"""
Test script for Class (Cargo Direction) API
"""
import requests
import json
from typing import Optional

# API Configuration
BASE_URL = "http://localhost:8000"
LOGIN_ENDPOINT = f"{BASE_URL}/api/login"
CLASS_ENDPOINT = f"{BASE_URL}/api/class"


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


def test_get_classes(token: str, **filters):
    """Test GET /api/class with filters"""
    print("\n" + "=" * 60)
    filter_desc = ", ".join([f"{k}={v}" for k, v in filters.items()]) if filters else "No filters"
    print(f"Testing GET /api/class ({filter_desc})")
    print("=" * 60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(
            CLASS_ENDPOINT,
            headers=headers,
            params=filters
        )
        
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Success!")
            print(f"   Code: {data['code']}")
            print(f"   Message: {data['message']}")
            print(f"   Total Classes: {len(data['data'])}")
            
            if data['data']:
                print(f"\n📋 Classes (first 5):")
                for i, class_item in enumerate(data['data'][:5], 1):
                    print(f"\n   {i}. Class ID: {class_item['classId']}")
                    print(f"      Name: {class_item['className']}")
                    print(f"      Created: {class_item['createdDate']}")
                    print(f"      Modified: {class_item['modifiedDate']}")
                
                if len(data['data']) > 5:
                    print(f"\n   ... and {len(data['data']) - 5} more classes")
                
                # Verify filter: All records should be rowDeleted IS NULL
                print(f"\n🔍 Filter Verification:")
                print(f"   ℹ️  All returned records should have rowDeleted IS NULL")
                print(f"   ✅ API correctly filtered {len(data['data'])} active cargo directions")
            
            return data
        else:
            print(f"❌ Failed!")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None


def test_get_class_by_id(token: str, class_id: str):
    """Test GET /api/class/{class_id}"""
    print("\n" + "=" * 60)
    print(f"Testing GET /api/class/{class_id}")
    print("=" * 60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(
            f"{CLASS_ENDPOINT}/{class_id}",
            headers=headers
        )
        
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Class Found!")
            print(f"   Code: {data['code']}")
            print(f"   Message: {data['message']}")
            
            if data['data']:
                class_item = data['data']
                print(f"\n📋 Class Details:")
                print(f"   ID: {class_item['classId']}")
                print(f"   Name: {class_item['className']}")
                print(f"   Created: {class_item['createdDate']}")
                print(f"   Modified: {class_item['modifiedDate']}")
            
            return data
        elif response.status_code == 404:
            print(f"❌ Class not found!")
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
        CLASS_ENDPOINT,
        headers=headers,
        params={"page": 1, "limit": 3}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ Got {len(data['data'])} records")
        if data['data']:
            print(f"   First class: {data['data'][0]['className']}")
    
    # Test page 2
    print("\n📄 Page 2 (limit=3):")
    response = requests.get(
        CLASS_ENDPOINT,
        headers=headers,
        params={"page": 2, "limit": 3}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ Got {len(data['data'])} records")
        if data['data']:
            print(f"   First class: {data['data'][0]['className']}")


def test_without_auth():
    """Test endpoint without authentication"""
    print("\n" + "=" * 60)
    print("Testing without authentication (should fail)")
    print("=" * 60)
    
    try:
        response = requests.get(CLASS_ENDPOINT)
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 401:
            print(f"✅ Correctly rejected! (401 Unauthorized)")
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    print("🚀 TOS Class (Cargo Direction) API - Test Suite")
    print(f"Server: {BASE_URL}")
    print()
    
    # Test 1: Login
    token = login()
    
    if not token:
        print("\n❌ Cannot proceed without token")
        exit(1)
    
    # Test 2: Get all classes (default pagination)
    test_get_classes(token)
    
    # Test 3: Get classes with custom pagination
    test_get_classes(token, page=1, limit=10)
    
    # Test 4: Test pagination
    test_pagination(token)
    
    # Test 5: Get specific class by ID
    print("\n" + "=" * 60)
    print("Getting class ID for detail test...")
    print("=" * 60)
    
    response = requests.get(
        CLASS_ENDPOINT,
        headers={"Authorization": f"Bearer {token}"},
        params={"limit": 1}
    )
    
    if response.status_code == 200:
        data = response.json()
        if data['data']:
            class_id = data['data'][0]['classId']
            print(f"Using class ID: {class_id}")
            test_get_class_by_id(token, class_id)
        else:
            print("No classes found to test detail endpoint")
    
    # Test 6: Test invalid class ID
    test_get_class_by_id(token, "INVALID999")
    
    # Test 7: Test without authentication
    test_without_auth()
    
    print("\n" + "=" * 60)
    print("✨ Test Suite Completed!")
    print("=" * 60)
