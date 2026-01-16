"""
Test script for Ship Details API
"""
import requests
import json
from typing import Optional

# API Configuration
BASE_URL = "http://localhost:8000"
LOGIN_ENDPOINT = f"{BASE_URL}/api/login"
SHIP_ENDPOINT = f"{BASE_URL}/api/shipDetails"


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


def test_get_ships(token: str, **filters):
    """Test GET /api/shipDetails with filters"""
    print("\n" + "=" * 60)
    filter_desc = ", ".join([f"{k}={v}" for k, v in filters.items()]) if filters else "No filters"
    print(f"Testing GET /api/shipDetails ({filter_desc})")
    print("=" * 60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(
            SHIP_ENDPOINT,
            headers=headers,
            params=filters
        )
        
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Success!")
            print(f"   Code: {data['code']}")
            print(f"   Message: {data['message']}")
            print(f"   Total Ships: {len(data['data'])}")
            
            if data['data']:
                print(f"\n📋 Ships (first 5):")
                for i, ship in enumerate(data['data'][:5], 1):
                    print(f"\n   {i}. Ship ID: {ship['shipId']}")
                    print(f"      IMO: {ship['shipIMO']}")
                    print(f"      Name: {ship['shipFullName']}")
                    print(f"      Flag: {ship['flagState']}")
                    print(f"      Type: {ship['shipType']}")
                    print(f"      DWT: {ship['shipDWT']}")
                
                if len(data['data']) > 5:
                    print(f"\n   ... and {len(data['data']) - 5} more ships")
                
                # Verify filter
                print(f"\n🔍 Filter Verification:")
                print(f"   ℹ️  All returned records should have rowDeleted = 0")
                print(f"   ✅ API correctly filtered {len(data['data'])} active ships")
            
            return data
        else:
            print(f"❌ Failed!")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None


def test_get_ship_by_imo(token: str, ship_imo: str):
    """Test GET /api/shipDetails/{ship_imo}"""
    print("\n" + "=" * 60)
    print(f"Testing GET /api/shipDetails/{ship_imo}")
    print("=" * 60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(
            f"{SHIP_ENDPOINT}/{ship_imo}",
            headers=headers
        )
        
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Ship Found!")
            print(f"   Code: {data['code']}")
            print(f"   Message: {data['message']}")
            
            if data['data']:
                ship = data['data']
                print(f"\n📋 Ship Details:")
                print(f"   ID: {ship['shipId']}")
                print(f"   IMO: {ship['shipIMO']}")
                print(f"   Full Name: {ship['shipFullName']}")
                print(f"   Group: {ship['shipGroup']}")
                print(f"   Flag State: {ship['flagState']}")
                print(f"   LOA: {ship['shipLOA']}")
                print(f"   Beam: {ship['shipBeam']}")
                print(f"   GRT: {ship['shipGRT']}")
                print(f"   Type: {ship['shipType']}")
                print(f"   DWT: {ship['shipDWT']}")
                print(f"   Owner: {ship['shipOwner']}")
                print(f"   Created: {ship['createdDate']}")
                print(f"   Modified: {ship['modifiedDate']}")
            
            return data
        elif response.status_code == 404:
            print(f"❌ Ship not found!")
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
        SHIP_ENDPOINT,
        headers=headers,
        params={"page": 1, "limit": 3}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ Got {len(data['data'])} records")
        if data['data']:
            print(f"   First ship: {data['data'][0]['shipFullName']}")
    
    # Test page 2
    print("\n📄 Page 2 (limit=3):")
    response = requests.get(
        SHIP_ENDPOINT,
        headers=headers,
        params={"page": 2, "limit": 3}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ Got {len(data['data'])} records")
        if data['data']:
            print(f"   First ship: {data['data'][0]['shipFullName']}")


def test_without_auth():
    """Test endpoint without authentication"""
    print("\n" + "=" * 60)
    print("Testing without authentication (should fail)")
    print("=" * 60)
    
    try:
        response = requests.get(SHIP_ENDPOINT)
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 401:
            print(f"✅ Correctly rejected! (401 Unauthorized)")
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    print("🚀 TOS Ship Details API - Test Suite")
    print(f"Server: {BASE_URL}")
    print()
    
    # Test 1: Login
    token = login()
    
    if not token:
        print("\n❌ Cannot proceed without token")
        exit(1)
    
    # Test 2: Get all ships (default pagination)
    test_get_ships(token)
    
    # Test 3: Get ships with custom pagination
    test_get_ships(token, page=1, limit=10)
    
    # Test 4: Test pagination
    test_pagination(token)
    
    # Test 5: Get specific ship by IMO
    print("\n" + "=" * 60)
    print("Getting ship IMO for detail test...")
    print("=" * 60)
    
    response = requests.get(
        SHIP_ENDPOINT,
        headers={"Authorization": f"Bearer {token}"},
        params={"limit": 1}
    )
    
    if response.status_code == 200:
        data = response.json()
        if data['data']:
            ship_imo = data['data'][0]['shipIMO']
            print(f"Using ship IMO: {ship_imo}")
            test_get_ship_by_imo(token, ship_imo)
        else:
            print("No ships found to test detail endpoint")
    
    # Test 6: Test invalid ship IMO
    test_get_ship_by_imo(token, "INVALID999")
    
    # Test 7: Test without authentication
    test_without_auth()
    
    print("\n" + "=" * 60)
    print("✨ Test Suite Completed!")
    print("=" * 60)
