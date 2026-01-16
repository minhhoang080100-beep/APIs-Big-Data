"""
Test script for Cargo Category API
"""
import requests
import json
from typing import Optional

# API Configuration
BASE_URL = "http://localhost:8000"
LOGIN_ENDPOINT = f"{BASE_URL}/api/login"
CARGO_ENDPOINT = f"{BASE_URL}/api/cargoCategory"


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


def test_get_cargo_categories(token: str, **filters):
    """Test GET /api/cargoCategory with filters"""
    print("\n" + "=" * 60)
    filter_desc = ", ".join([f"{k}={v}" for k, v in filters.items()]) if filters else "No filters"
    print(f"Testing GET /api/cargoCategory ({filter_desc})")
    print("=" * 60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(
            CARGO_ENDPOINT,
            headers=headers,
            params=filters
        )
        
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Success!")
            print(f"   Code: {data['code']}")
            print(f"   Message: {data['message']}")
            print(f"   Total Cargo Categories: {len(data['data'])}")
            
            if data['data']:
                print(f"\n📋 Sample Cargo (first 3):")
                for i, cargo in enumerate(data['data'][:3], 1):
                    print(f"\n   {i}. Cargo ID: {cargo['cargoId']}")
                    print(f"      Name: {cargo['cargoName']}")
                    print(f"      Type ID: {cargo['cargoTypeId']}")
                    print(f"      Parent ID: {cargo['cargoParentId']}")
                    print(f"      Created: {cargo['createdDate']}")
                    print(f"      Modified: {cargo['modifiedDate']}")
                
                if len(data['data']) > 3:
                    print(f"\n   ... and {len(data['data']) - 3} more cargos")
            
            return data
        else:
            print(f"❌ Failed!")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None


def test_get_cargo_by_id(token: str, cargo_id: int):
    """Test GET /api/cargoCategory/{cargo_id}"""
    print("\n" + "=" * 60)
    print(f"Testing GET /api/cargoCategory/{cargo_id}")
    print("=" * 60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(
            f"{CARGO_ENDPOINT}/{cargo_id}",
            headers=headers
        )
        
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Cargo Found!")
            print(f"   Code: {data['code']}")
            print(f"   Message: {data['message']}")
            
            if data['data']:
                cargo = data['data']
                print(f"\n📋 Cargo Details:")
                print(f"   ID: {cargo['cargoId']}")
                print(f"   Name: {cargo['cargoName']}")
                print(f"   Type ID: {cargo['cargoTypeId']}")
                print(f"   Parent ID: {cargo['cargoParentId']}")
                print(f"   Created: {cargo['createdDate']}")
                print(f"   Modified: {cargo['modifiedDate']}")
            
            return data
        elif response.status_code == 404:
            print(f"❌ Cargo not found!")
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
    print("\n📄 Page 1 (limit=5):")
    response = requests.get(
        CARGO_ENDPOINT,
        headers=headers,
        params={"page": 1, "limit": 5}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ Got {len(data['data'])} records")
        if data['data']:
            print(f"   First cargo: {data['data'][0]['cargoName']}")
    
    # Test page 2
    print("\n📄 Page 2 (limit=5):")
    response = requests.get(
        CARGO_ENDPOINT,
        headers=headers,
        params={"page": 2, "limit": 5}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ Got {len(data['data'])} records")
        if data['data']:
            print(f"   First cargo: {data['data'][0]['cargoName']}")


def test_without_auth():
    """Test endpoint without authentication"""
    print("\n" + "=" * 60)
    print("Testing without authentication (should fail)")
    print("=" * 60)
    
    try:
        response = requests.get(CARGO_ENDPOINT)
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 401:
            print(f"✅ Correctly rejected! (401 Unauthorized)")
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    print("🚀 TOS Cargo Category API - Test Suite")
    print(f"Server: {BASE_URL}")
    print()
    
    # Test 1: Login
    token = login()
    
    if not token:
        print("\n❌ Cannot proceed without token")
        exit(1)
    
    # Test 2: Get all cargo categories (no filter, default pagination)
    test_get_cargo_categories(token)
    
    # Test 3: Get cargo categories with pagination
    test_get_cargo_categories(token, page=1, limit=10)
    
    # Test 4: Get cargo categories with cargoTypeId filter
    # Note: Need to know actual cargoTypeId values from database
    # test_get_cargo_categories(token, cargoTypeId=1234)
    
    # Test 5: Test pagination
    test_pagination(token)
    
    # Test 6: Get specific cargo by ID
    print("\n" + "=" * 60)
    print("Getting cargo ID for detail test...")
    print("=" * 60)
    
    response = requests.get(
        CARGO_ENDPOINT,
        headers={"Authorization": f"Bearer {token}"},
        params={"limit": 1}
    )
    
    if response.status_code == 200:
        data = response.json()
        if data['data']:
            cargo_id = data['data'][0]['cargoId']
            print(f"Using cargo ID: {cargo_id}")
            test_get_cargo_by_id(token, cargo_id)
        else:
            print("No cargos found to test detail endpoint")
    
    # Test 7: Test invalid cargo ID
    test_get_cargo_by_id(token, 999999)
    
    # Test 8: Test without authentication
    test_without_auth()
    
    print("\n" + "=" * 60)
    print("✨ Test Suite Completed!")
    print("=" * 60)
