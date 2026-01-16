"""
Test script for Customer API
"""
import requests
import json
from typing import Optional

# API Configuration
BASE_URL = "http://localhost:8000"
LOGIN_ENDPOINT = f"{BASE_URL}/api/login"
CUSTOMERS_ENDPOINT = f"{BASE_URL}/api/customers"


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
        print(f"   Expires: {data['ExpireIn']}")
        return token
    else:
        print(f"❌ Login failed: {response.status_code}")
        return None


def test_get_customers(token: str, **filters):
    """Test GET /api/customers with filters"""
    print("\n" + "=" * 60)
    filter_desc = ", ".join([f"{k}={v}" for k, v in filters.items()]) if filters else "No filters"
    print(f"Testing GET /api/customers ({filter_desc})")
    print("=" * 60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(
            CUSTOMERS_ENDPOINT,
            headers=headers,
            params=filters
        )
        
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Success!")
            print(f"   Code: {data['code']}")
            print(f"   Message: {data['message']}")
            print(f"   Total Customers: {len(data['data'])}")
            
            if data['data']:
                print(f"\n📋 Sample Customer (first):")
                customer = data['data'][0]
                print(f"   Code: {customer['customerCode']}")
                print(f"   Name (VN): {customer['customerNameVN']}")
                print(f"   Name (EN): {customer['customerNameEN']}")
                print(f"   Tax Code: {customer['customerTaxCode']}")
                print(f"   Email: {customer['customerEmail']}")
                print(f"   Phone: {customer['customerPhoneNum']}")
                print(f"   Address: {customer['customerAddress']}")
                
                # Show more if there are more
                if len(data['data']) > 1:
                    print(f"\n   ... and {len(data['data']) - 1} more customers")
            
            return data
        else:
            print(f"❌ Failed!")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None


def test_get_customer_by_id(token: str, customer_id: str):
    """Test GET /api/customers/{customer_id}"""
    print("\n" + "=" * 60)
    print(f"Testing GET /api/customers/{customer_id}")
    print("=" * 60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(
            f"{CUSTOMERS_ENDPOINT}/{customer_id}",
            headers=headers
        )
        
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Customer Found!")
            print(f"   Code: {data['code']}")
            print(f"   Message: {data['message']}")
            
            if data['data']:
                customer = data['data']
                print(f"\n📋 Customer Details:")
                print(f"   Code: {customer['customerCode']}")
                print(f"   Name (VN): {customer['customerNameVN']}")
                print(f"   Name (EN): {customer['customerNameEN']}")
                print(f"   Tax Code: {customer['customerTaxCode']}")
                print(f"   Email: {customer['customerEmail']}")
                print(f"   Phone: {customer['customerPhoneNum']}")
                print(f"   Address: {customer['customerAddress']}")
                print(f"   Is Carrier: {customer['isCarrier']}")
                print(f"   Is Agent: {customer['isAgent']}")
            
            return data
        elif response.status_code == 404:
            print(f"❌ Customer not found!")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Failed!")
            print(f"   Response: {response.text}")
            
        return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None


def test_without_auth():
    """Test endpoint without authentication"""
    print("\n" + "=" * 60)
    print("Testing without authentication (should fail)")
    print("=" * 60)
    
    try:
        response = requests.get(CUSTOMERS_ENDPOINT)
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 401:
            print(f"✅ Correctly rejected! (401 Unauthorized)")
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    print("🚀 TOS Customer API - Test Suite")
    print(f"Server: {BASE_URL}")
    print()
    
    # Test 1: Login
    token = login()
    
    if not token:
        print("\n❌ Cannot proceed without token")
        exit(1)
    
    # Test 2: Get all customers (no filter)
    test_get_customers(token)
    
    # Test 3: Get customers with date filter
    test_get_customers(
        token,
        startDate="2024-01-01",
        endDate="2024-12-31"
    )
    
    # Test 4: Get specific customer by ID
    # First get a customer ID from the list
    print("\n" + "=" * 60)
    print("Getting customer ID for detail test...")
    print("=" * 60)
    
    response = requests.get(
        CUSTOMERS_ENDPOINT,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        if data['data']:
            customer_id = str(data['data'][0]['customerCode'])
            print(f"Using customer ID: {customer_id}")
            test_get_customer_by_id(token, customer_id)
        else:
            print("No customers found to test detail endpoint")
    
    # Test 5: Test invalid customer ID
    test_get_customer_by_id(token, "999999")
    
    # Test 6: Test without authentication
    test_without_auth()
    
    print("\n" + "=" * 60)
    print("✨ Test Suite Completed!")
    print("=" * 60)
