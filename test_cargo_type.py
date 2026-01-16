"""
Test script for Cargo Type API
"""
import requests
import json
from typing import Optional

# API Configuration
BASE_URL = "http://localhost:8000"
LOGIN_ENDPOINT = f"{BASE_URL}/api/login"
CARGO_TYPE_ENDPOINT = f"{BASE_URL}/api/cargoType"


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


def test_get_cargo_types(token: str, **filters):
    """Test GET /api/cargoType with filters"""
    print("\n" + "=" * 60)
    filter_desc = ", ".join([f"{k}={v}" for k, v in filters.items()]) if filters else "No filters"
    print(f"Testing GET /api/cargoType ({filter_desc})")
    print("=" * 60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(
            CARGO_TYPE_ENDPOINT,
            headers=headers,
            params=filters
        )
        
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Success!")
            print(f"   Code: {data['code']}")
            print(f"   Message: {data['message']}")
            print(f"   Total Cargo Types: {len(data['data'])}")
            
            if data['data']:
                print(f"\n📋 Cargo Types (showing all):")
                for i, cargo_type in enumerate(data['data'], 1):
                    print(f"\n   {i}. Cargo Type ID: {cargo_type['cargoTypeId']}")
                    print(f"      Name: {cargo_type['cargoTypeName']}")
                    print(f"      Created: {cargo_type['createdDate']}")
                    print(f"      Modified: {cargo_type['modifiedDate']}")
            
            return data
        else:
            print(f"❌ Failed!")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None


def test_get_cargo_type_by_id(token: str, cargo_type_id: str):
    """Test GET /api/cargoType/{cargo_type_id}"""
    print("\n" + "=" * 60)
    print(f"Testing GET /api/cargoType/{cargo_type_id}")
    print("=" * 60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(
            f"{CARGO_TYPE_ENDPOINT}/{cargo_type_id}",
            headers=headers
        )
        
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Cargo Type Found!")
            print(f"   Code: {data['code']}")
            print(f"   Message: {data['message']}")
            
            if data['data']:
                cargo_type = data['data']
                print(f"\n📋 Cargo Type Details:")
                print(f"   ID: {cargo_type['cargoTypeId']}")
                print(f"   Name: {cargo_type['cargoTypeName']}")
                print(f"   Created: {cargo_type['createdDate']}")
                print(f"   Modified: {cargo_type['modifiedDate']}")
            
            return data
        elif response.status_code == 404:
            print(f"❌ Cargo type not found!")
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
        CARGO_TYPE_ENDPOINT,
        headers=headers,
        params={"page": 1, "limit": 3}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ Got {len(data['data'])} records")
        if data['data']:
            print(f"   First type: {data['data'][0]['cargoTypeName']}")
    
    # Test page 2
    print("\n📄 Page 2 (limit=3):")
    response = requests.get(
        CARGO_TYPE_ENDPOINT,
        headers=headers,
        params={"page": 2, "limit": 3}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ Got {len(data['data'])} records")
        if data['data']:
            print(f"   First type: {data['data'][0]['cargoTypeName']}")


def test_without_auth():
    """Test endpoint without authentication"""
    print("\n" + "=" * 60)
    print("Testing without authentication (should fail)")
    print("=" * 60)
    
    try:
        response = requests.get(CARGO_TYPE_ENDPOINT)
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 401:
            print(f"✅ Correctly rejected! (401 Unauthorized)")
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    print("🚀 TOS Cargo Type API - Test Suite")
    print(f"Server: {BASE_URL}")
    print()
    
    # Test 1: Login
    token = login()
    
    if not token:
        print("\n❌ Cannot proceed without token")
        exit(1)
    
    # Test 2: Get all cargo types (default pagination)
    test_get_cargo_types(token)
    
    # Test 3: Get cargo types with custom pagination
    test_get_cargo_types(token, page=1, limit=5)
    
    # Test 4: Test pagination
    test_pagination(token)
    
    # Test 5: Get specific cargo type by ID
    print("\n" + "=" * 60)
    print("Getting cargo type ID for detail test...")
    print("=" * 60)
    
    response = requests.get(
        CARGO_TYPE_ENDPOINT,
        headers={"Authorization": f"Bearer {token}"},
        params={"limit": 1}
    )
    
    if response.status_code == 200:
        data = response.json()
        if data['data']:
            cargo_type_id = data['data'][0]['cargoTypeId']
            print(f"Using cargo type ID: {cargo_type_id}")
            test_get_cargo_type_by_id(token, cargo_type_id)
        else:
            print("No cargo types found to test detail endpoint")
    
    # Test 6: Test invalid cargo type ID
    test_get_cargo_type_by_id(token, "INVALID999")
    
    # Test 7: Test without authentication
    test_without_auth()
    
    print("\n" + "=" * 60)
    print("✨ Test Suite Completed!")
    print("=" * 60)
