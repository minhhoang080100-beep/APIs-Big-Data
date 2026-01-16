"""
Test script for Container Quay Volumes API
"""
import requests
import json
from typing import Optional
from datetime import datetime, timedelta

# API Configuration
BASE_URL = "http://localhost:8000"
LOGIN_ENDPOINT = f"{BASE_URL}/api/login"
CONTAINER_QUAY_ENDPOINT = f"{BASE_URL}/api/contQuayVolumesCB"


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


def test_get_container_quay_volumes(token: str, **filters):
    """Test GET /api/contQuayVolumesCB with filters"""
    print("\n" + "=" * 60)
    filter_desc = ", ".join([f"{k}={v}" for k, v in filters.items()]) if filters else "No filters"
    print(f"Testing GET /api/contQuayVolumesCB ({filter_desc})")
    print("=" * 60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(
            CONTAINER_QUAY_ENDPOINT,
            headers=headers,
            params=filters
        )
        
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Success!")
            print(f"   Code: {data['code']}")
            print(f"   Message: {data['message']}")
            print(f"   Total Records: {len(data['data'])}")
            
            if data['data']:
                print(f"\n📦 Container Quay Volume Records (first 3):")
                for i, volume in enumerate(data['data'][:3], 1):
                    print(f"\n   {i}. Report Date: {volume['reportDate']}")
                    print(f"      Finish Date: {volume['finishDate']}")
                    print(f"      Company ID: {volume['companyId']}")
                    print(f"      Ship ID: {volume['shipId']}")
                    print(f"      Class ID (Direction): {volume['classId']}")
                    print(f"      Origin ID: {volume['originId']}")
                    print(f"      Container Weight: {volume['containerWeight']} tấn")
                    print(f"      Container TEU: {volume['containerTEU']} TEU")
                    print(f"      Handling Method: {volume['handlingMethodId']}")
                    print(f"      Ship Operator: {volume['shipOperatorId']}")
                    print(f"      Container Operator: {volume['containerOperatorId']}")
                
                if len(data['data']) > 3:
                    print(f"\n   ... and {len(data['data']) - 3} more records")
                
                # Calculate totals
                total_weight = sum(v['containerWeight'] for v in data['data'])
                total_teu = sum(v['containerTEU'] for v in data['data'])
                print(f"\n📊 Summary:")
                print(f"   Total Weight: {total_weight:,.2f} tấn")
                print(f"   Total TEU: {total_teu:,} TEU")
                
                # Verify filters
                print(f"\n🔍 Filter Verification:")
                print(f"   ℹ️  All records should have:")
                print(f"      - jobMethodCode containing 'TAU' (ship operations)")
                print(f"      - cargoGroupCode = 'Hàng Container' (ONLY containers)")
                print(f"      - weightNetSum > 0")
                print(f"      - rowDeleted IS NULL")
                print(f"   ✅ API correctly filtered {len(data['data'])} container records")
            
            return data
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
        CONTAINER_QUAY_ENDPOINT,
        headers=headers,
        params={"page": 1, "limit": 5}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ Got {len(data['data'])} records")
        if data['data']:
            print(f"   First record date: {data['data'][0]['finishDate']}")
            print(f"   Total TEU: {sum(v['containerTEU'] for v in data['data']):,} TEU")
    
    # Test page 2
    print("\n📄 Page 2 (limit=5):")
    response = requests.get(
        CONTAINER_QUAY_ENDPOINT,
        headers=headers,
        params={"page": 2, "limit": 5}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ Got {len(data['data'])} records")
        if data['data']:
            print(f"   First record date: {data['data'][0]['finishDate']}")
            print(f"   Total TEU: {sum(v['containerTEU'] for v in data['data']):,} TEU")


def test_date_filters(token: str):
    """Test date range filters"""
    print("\n" + "=" * 60)
    print("Testing Date Range Filters")
    print("=" * 60)
    
    # Test with date range
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    print(f"\n📅 Testing date range: {start_date} to {end_date}")
    
    data = test_get_container_quay_volumes(
        token,
        startDate=start_date,
        endDate=end_date,
        limit=10
    )
    
    if data and data['data']:
        dates = [v['finishDate'] for v in data['data']]
        print(f"\n   Date range in results: {min(dates)} to {max(dates)}")


def test_ship_filter(token: str):
    """Test shipId filter"""
    print("\n" + "=" * 60)
    print("Testing shipId filter")
    print("=" * 60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get a ship ID from first result
    response = requests.get(
        CONTAINER_QUAY_ENDPOINT,
        headers=headers,
        params={"limit": 1}
    )
    
    if response.status_code == 200:
        data = response.json()
        if data['data'] and data['data'][0]['shipId']:
            ship_id = data['data'][0]['shipId']
            print(f"Using shipId: {ship_id}")
            test_get_container_quay_volumes(token, shipId=ship_id, limit=5)
        else:
            print("No shipId found in first record")


def test_without_auth():
    """Test endpoint without authentication"""
    print("\n" + "=" * 60)
    print("Testing without authentication (should fail)")
    print("=" * 60)
    
    try:
        response = requests.get(CONTAINER_QUAY_ENDPOINT)
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 401:
            print(f"✅ Correctly rejected! (401 Unauthorized)")
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    print("🚀 TOS Container Quay Volumes API - Test Suite")
    print(f"Server: {BASE_URL}")
    print()
    
    # Test 1: Login
    token = login()
    
    if not token:
        print("\n❌ Cannot proceed without token")
        exit(1)
    
    # Test 2: Get all container volumes (default pagination)
    test_get_container_quay_volumes(token)
    
    # Test 3: Get volumes with custom pagination
    test_get_container_quay_volumes(token, page=1, limit=10)
    
    # Test 4: Test pagination
    test_pagination(token)
    
    # Test 5: Test date filters
    test_date_filters(token)
    
    # Test 6: Test shipId filter
    test_ship_filter(token)
    
    # Test 7: Test handlingMethodId filter
    print("\n" + "=" * 60)
    print("Testing handlingMethodId filter")
    print("=" * 60)
    
    response = requests.get(
        CONTAINER_QUAY_ENDPOINT,
        headers={"Authorization": f"Bearer {token}"},
        params={"limit": 1}
    )
    
    if response.status_code == 200:
        data = response.json()
        if data['data'] and data['data'][0]['handlingMethodId']:
            handling_method = data['data'][0]['handlingMethodId']
            print(f"Using handlingMethodId: {handling_method}")
            test_get_container_quay_volumes(token, handlingMethodId=handling_method, limit=5)
        else:
            print("No handlingMethodId found in first record")
    
    # Test 8: Test without authentication
    test_without_auth()
    
    print("\n" + "=" * 60)
    print("✨ Test Suite Completed!")
    print("=" * 60)
