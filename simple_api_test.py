# Simple API Test
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_health():
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            print("1. Health check: SUCCESS")
            return True
        else:
            print(f"1. Health check: FAILED ({response.status_code})")
            return False
    except Exception as e:
        print(f"1. Health check: ERROR - {e}")
        return False

def test_vector_store():
    try:
        response = requests.get(f"{BASE_URL}/templates/vector-store-info", timeout=10)
        if response.status_code == 200:
            data = response.json()
            templates = data.get('templates_count', 0)
            patterns = data.get('patterns_count', 0)
            print(f"2. Vector store: SUCCESS (templates: {templates}, patterns: {patterns})")
            return True
        else:
            print(f"2. Vector store: FAILED ({response.status_code})")
            return False
    except Exception as e:
        print(f"2. Vector store: ERROR - {e}")
        return False

def test_similar_search():
    try:
        data = {"query": "order completion", "limit": 3}
        response = requests.post(f"{BASE_URL}/templates/similar-search", json=data, timeout=15)
        if response.status_code == 200:
            result = response.json()
            count = len(result.get('similar_templates', []))
            print(f"3. Similar search: SUCCESS ({count} templates found)")
            return True
        else:
            print(f"3. Similar search: FAILED ({response.status_code})")
            print(f"   Error: {response.text[:100]}")
            return False
    except Exception as e:
        print(f"3. Similar search: ERROR - {e}")
        return False

def test_smart_generation():
    try:
        data = {
            "user_request": "reservation confirmation message",
            "business_type": "service",
            "category_1": "reservation",
            "target_length": 100,
            "include_variables": ["customer_name", "reservation_time"]
        }
        response = requests.post(f"{BASE_URL}/templates/smart-generate", json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            template = result.get('generated_template', '')
            validation = result.get('validation', {})
            length = validation.get('length', 0)
            score = validation.get('compliance_score', 0)
            print(f"4. Smart generation: SUCCESS")
            print(f"   Template: {template[:50]}...")
            print(f"   Length: {length} chars, Score: {score:.1f}")
            return True
        else:
            print(f"4. Smart generation: FAILED ({response.status_code})")
            print(f"   Error: {response.text[:100]}")
            return False
    except Exception as e:
        print(f"4. Smart generation: ERROR - {e}")
        return False

def main():
    print("=== Integrated Template Generation System Test ===")
    print()

    results = []
    results.append(test_health())
    results.append(test_vector_store())
    results.append(test_similar_search())
    results.append(test_smart_generation())

    print()
    print(f"=== Test Complete: {sum(results)}/{len(results)} SUCCESS ===")

    if sum(results) == len(results):
        print("All tests passed!")
    else:
        print("Some tests failed. Check the logs.")

if __name__ == "__main__":
    main()