#!/usr/bin/env python3
"""
Simple API Test Script
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_basic_functionality():
    """Test basic functionality"""
    print("=== Basic API Tests ===\n")
    
    # 1. Root endpoint test
    print("1. Testing root endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/")
        data = response.json()
        print(f"   SUCCESS: {data['message']}")
        print(f"   Status: {data['status']}")
    except Exception as e:
        print(f"   FAILED: {str(e)}")
        return False
    
    # 2. Health check test
    print("\n2. Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        data = response.json()
        print(f"   SUCCESS: {data['status']}")
        print(f"   Environment: {data['environment']}")
        print(f"   OpenAI Key: {'Present' if data['openai_key_present'] else 'Missing'}")
        print(f"   Database Config: {'Present' if data['database_configured'] else 'Missing'}")
    except Exception as e:
        print(f"   FAILED: {str(e)}")
        return False
    
    # 3. Response time test
    print("\n3. Testing response time...")
    try:
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/health")
        response_time = (time.time() - start_time) * 1000
        print(f"   SUCCESS: Response time {response_time:.2f}ms")
    except Exception as e:
        print(f"   FAILED: {str(e)}")
        return False
    
    return True

def test_environment_setup():
    """Test environment setup"""
    print("\n=== Environment Check ===\n")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        import os
        
        # Check environment variables
        required_vars = [
            "OPENAI_API_KEY",
            "LOCAL_DB_NAME", 
            "LOCAL_DB_USER",
            "LOCAL_DB_PASSWORD",
            "APP_PORT"
        ]
        
        print("Environment Variables:")
        for var in required_vars:
            value = os.getenv(var)
            if value:
                if "API_KEY" in var or "PASSWORD" in var:
                    display_value = f"{value[:10]}..." if len(value) > 10 else "***"
                else:
                    display_value = value
                print(f"   OK {var}: {display_value}")
            else:
                print(f"   MISSING {var}")
        
        return True
    except Exception as e:
        print(f"   FAILED: {str(e)}")
        return False

def main():
    """Main test function"""
    print("Kakao AlimTalk Template AI System Test\n")
    
    # Basic functionality test
    basic_test = test_basic_functionality()
    
    # Environment setup test
    env_test = test_environment_setup()
    
    # Summary
    print("\n=== Test Results ===")
    print(f"Basic API Tests: {'PASS' if basic_test else 'FAIL'}")
    print(f"Environment Check: {'PASS' if env_test else 'FAIL'}")
    
    if basic_test and env_test:
        print("\nSUCCESS: All basic tests passed!")
        print("API Docs: http://localhost:8000/docs")
        print("NOTE: Full system testing requires additional packages.")
        return True
    else:
        print("\nWARNING: Some tests failed. Check your configuration.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)