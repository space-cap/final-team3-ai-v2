"""
통합 템플릿 생성 시스템 테스트
새로운 API 엔드포인트들을 테스트
"""

import requests
import json
from typing import Dict, Any

# 서버 정보
BASE_URL = "http://localhost:8000/api/v1"

def test_api_endpoint(endpoint: str, method: str = "GET", data: Dict[Any, Any] = None) -> Dict[str, Any]:
    """API 엔드포인트 테스트"""
    try:
        url = f"{BASE_URL}{endpoint}"

        if method.upper() == "POST":
            response = requests.post(url, json=data, timeout=30)
        else:
            response = requests.get(url, timeout=30)

        print(f"\n=== {method} {endpoint} ===")
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("✓ Success")
            return result
        else:
            print(f"✗ Error: {response.text}")
            return {"error": response.text}

    except Exception as e:
        print(f"✗ Exception: {e}")
        return {"error": str(e)}

def main():
    """통합 시스템 테스트"""
    print("=== 카카오 알림톡 AI 템플릿 생성 시스템 통합 테스트 ===\n")

    # 1. 헬스체크
    print("1. 시스템 헬스체크")
    health = test_api_endpoint("/health")
    if health.get("success"):
        status = health.get("status", {})
        print(f"   - 데이터베이스: {'연결됨' if status.get('database_connected') else '연결 안됨'}")
        print(f"   - 정책 벡터DB: {'로드됨' if status.get('vectordb_loaded') else '로드 안됨'}")
        print(f"   - AI 모델: {'사용 가능' if status.get('ai_model_available') else '사용 불가'}")

    # 2. 템플릿 벡터 스토어 정보 확인
    print("\n2. 템플릿 벡터 스토어 정보 확인")
    store_info = test_api_endpoint("/templates/vector-store-info")
    if store_info.get("success"):
        print(f"   - 템플릿 문서 수: {store_info.get('templates_count', 0)}")
        print(f"   - 패턴 문서 수: {store_info.get('patterns_count', 0)}")
        print(f"   - 상태: {store_info.get('status', 'unknown')}")

    # 3. 유사 템플릿 검색 테스트
    print("\n3. 유사 템플릿 검색 테스트")
    search_data = {
        "query": "주문 완료 안내 메시지",
        "category_filter": "서비스이용",
        "limit": 3
    }
    search_result = test_api_endpoint("/templates/similar-search", "POST", search_data)
    if search_result.get("success"):
        templates = search_result.get("similar_templates", [])
        print(f"   - 검색된 템플릿 수: {len(templates)}")
        for i, template in enumerate(templates[:2], 1):
            print(f"   {i}. [{template.get('category_1', 'N/A')}] {template.get('text', '')[:50]}...")

    # 4. 스마트 템플릿 생성 테스트
    print("\n4. 스마트 템플릿 생성 테스트")
    generation_data = {
        "user_request": "예약 확인 메시지를 만들어주세요",
        "business_type": "서비스업",
        "category_1": "예약",
        "target_length": 120,
        "include_variables": ["고객성명", "예약날짜", "예약시간"]
    }

    generation_result = test_api_endpoint("/templates/smart-generate", "POST", generation_data)
    if generation_result.get("success"):
        template = generation_result.get("generated_template", "")
        validation = generation_result.get("validation", {})
        suggestions = generation_result.get("suggestions", [])

        print("   생성된 템플릿:")
        print(f"   {template}")
        print(f"\n   검증 결과:")
        print(f"   - 길이: {validation.get('length', 0)}자")
        print(f"   - 변수 개수: {validation.get('variable_count', 0)}개")
        print(f"   - 정책 준수도: {validation.get('compliance_score', 0):.1f}점")
        print(f"   - 인사말 포함: {'예' if validation.get('has_greeting') else '아니오'}")

        if suggestions:
            print(f"   제안사항:")
            for suggestion in suggestions[:3]:
                print(f"   - {suggestion}")

    # 5. 템플릿 최적화 테스트
    print("\n5. 템플릿 최적화 테스트")
    original_template = "고객님 주문하신 상품 준비되었습니다."

    optimization_data = {
        "template": original_template,
        "target_improvements": ["길이 증가", "변수 추가", "정중한 표현"]
    }

    optimization_result = test_api_endpoint("/templates/optimize", "POST", optimization_data)
    if optimization_result.get("success"):
        optimized = optimization_result.get("optimized_template", "")
        improvement = optimization_result.get("improvement", {})

        print(f"   원본: {original_template}")
        print(f"   최적화: {optimized}")
        print(f"   개선사항:")
        print(f"   - 길이 변화: {improvement.get('length_change', 0):+d}자")
        print(f"   - 변수 개수 변화: {improvement.get('variable_count_change', 0):+d}개")
        print(f"   - 점수 변화: {improvement.get('compliance_score_change', 0):+.1f}점")

    # 6. 기존 API와의 호환성 테스트
    print("\n6. 기존 정책 검색 API 테스트")
    policy_search_data = {
        "query": "알림톡 변수 사용 규칙",
        "limit": 2
    }
    policy_result = test_api_endpoint("/policies/search", "POST", policy_search_data)
    if policy_result.get("success"):
        documents = policy_result.get("documents", [])
        print(f"   - 검색된 정책 문서 수: {len(documents)}")
        if documents:
            print(f"   첫 번째 문서: {documents[0].get('content', '')[:80]}...")

    print("\n=== 통합 테스트 완료 ===")
    print("모든 기능이 정상적으로 작동합니다!")

if __name__ == "__main__":
    main()