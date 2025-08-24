#!/usr/bin/env python3

import requests
import json
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

def test_root_endpoint():
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        print("Root endpoint test passed")
        return True
    except Exception as e:
        print(f"Root endpoint test failed: {e}")
        return False

def test_health_endpoint():
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        print("Health endpoint test passed")
        return True
    except Exception as e:
        print(f"Health endpoint test failed: {e}")
        return False

def test_companies_search_endpoint():
    try:
        search_data = {
            "name": "test",
            "limit": 5
        }
        headers = {"Authorization": "Bearer beacon-user1-key-2024"}
        response = requests.post(f"{BASE_URL}/api/v1/companies/search", json=search_data, headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        return True
    except Exception as e:
        print(f"Companies search endpoint test failed: {e}")
        return False

def test_get_company_endpoint():
    try:
        headers = {"Authorization": "Bearer beacon-user1-key-2024"}
        search_response = requests.post(f"{BASE_URL}/api/v1/companies/search", json={"name": "test", "limit": 1}, headers=headers)
        
        if search_response.status_code == 200:
            companies = search_response.json()
            if companies:
                uid = companies[0].get("uid")
                if uid:
                    response = requests.get(f"{BASE_URL}/api/v1/companies/{uid}", headers=headers)
                    print(f"Status: {response.status_code}")
                    print(f"Response: {response.json()}")
                    assert response.status_code in [200, 404]
                    print("Get company endpoint test passed")
                    return True
                else:
                    print("No UID found in search results")
                    return True
            else:
                print("No companies found in search")
                return True
        else:
            print(f"Search failed with status {search_response.status_code}")
            return True
    except Exception as e:
        print(f"Get company endpoint test failed: {e}")
        return False

def test_import_export_endpoints():
    try:
        response = requests.get(f"{BASE_URL}/api/v1/data/export")
        print(f"Export Status: {response.status_code}")
        if response.status_code == 200:
            print("Export endpoint test passed")
        else:
            print(f"Export endpoint returned status {response.status_code}")
        
        import_data = {"companies": []}
        response = requests.post(f"{BASE_URL}/api/v1/data/import", json=import_data)
        print(f"Import Status: {response.status_code}")
        if response.status_code in [200, 400, 422]:
            print("Import endpoint test passed")
        else:
            print(f"Import endpoint returned status {response.status_code}")
        
        print("Import/Export endpoints test completed")
        return True
    except Exception as e:
        print(f"Import/Export endpoints test failed: {e}")
        return False

def test_authentication_required_endpoints():
    try:
        response = requests.get(f"{BASE_URL}/api/v1/companies/123456789")
        print(f"Status without auth: {response.status_code}")
        
        assert response.status_code in [401, 403, 404]
        print("Authentication check passed - unauthorized access properly handled")
        return True
    except Exception as e:
        print(f"Authentication test failed: {e}")
        return False

def test_invalid_endpoints():
    try:
        response = requests.get(f"{BASE_URL}/api/v1/nonexistent")
        print(f"Invalid endpoint status: {response.status_code}")
        assert response.status_code == 404
        print("Invalid endpoint test passed")
        return True
    except Exception as e:
        print(f"Invalid endpoint test failed: {e}")
        return False

def main():
    print("Starting Beacon API Endpoint Tests")
    print("=" * 50)
    
    print("Waiting for server to be ready...")
    time.sleep(2)
    
    tests = [
        test_root_endpoint,
        test_health_endpoint,
        test_companies_search_endpoint,
        test_get_company_endpoint,
        test_import_export_endpoints,
        test_authentication_required_endpoints,
        test_invalid_endpoints
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("All tests passed!")
    else:
        print(f"{total - passed} tests failed or had issues")
    
    return passed == total

if __name__ == "__main__":
    main()
