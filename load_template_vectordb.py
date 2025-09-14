"""
템플릿 벡터 데이터베이스 로딩 스크립트
JSON 데이터를 벡터 데이터베이스에 임베딩
"""

import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python 패스에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.template_vector_store import template_vector_store_service

def main():
    """템플릿 벡터 데이터베이스 로딩"""
    print("=== 카카오 알림톡 템플릿 벡터 데이터베이스 로딩 ===\n")

    # JSON 데이터 파일 경로
    json_data_path = "./data/kakao_template_vectordb_data.json"

    if not Path(json_data_path).exists():
        print(f"❌ JSON 데이터 파일을 찾을 수 없습니다: {json_data_path}")
        print("먼저 create_template_json.py를 실행해주세요.")
        return False

    # 벡터 데이터베이스에 데이터 로드
    print("📥 JSON 데이터를 벡터 데이터베이스에 로딩 중...")
    success = template_vector_store_service.load_template_data(json_data_path)

    if success:
        print("✅ 템플릿 벡터 데이터베이스 로딩 완료!")

        # 스토어 정보 출력
        store_info = template_vector_store_service.get_store_info()
        print(f"📊 로딩 결과:")
        print(f"   - 템플릿 문서 수: {store_info['templates_count']}")
        print(f"   - 패턴 문서 수: {store_info['patterns_count']}")
        print(f"   - 상태: {store_info['status']}")

        # 테스트 검색 수행
        print("\n🔍 테스트 검색 수행 중...")
        test_search()

    else:
        print("❌ 템플릿 벡터 데이터베이스 로딩 실패!")
        return False

    return True

def test_search():
    """벡터 데이터베이스 테스트 검색"""
    try:
        # 1. 유사한 템플릿 검색 테스트
        print("\n1. 유사 템플릿 검색 테스트:")
        similar_templates = template_vector_store_service.find_similar_templates(
            "주문 완료 안내", k=3
        )

        for i, doc in enumerate(similar_templates, 1):
            original_text = doc.metadata.get('original_text', '')
            category = doc.metadata.get('category_1', '')
            length = doc.metadata.get('length', 0)
            print(f"   {i}. [{category}] {original_text[:50]}... ({length}자)")

        # 2. 카테고리 패턴 검색 테스트
        print("\n2. 카테고리 패턴 검색 테스트:")
        patterns = template_vector_store_service.find_category_patterns("서비스이용", k=2)

        for i, doc in enumerate(patterns, 1):
            category = doc.metadata.get('category', '')
            template_count = doc.metadata.get('template_count', 0)
            print(f"   {i}. [{category}] {template_count}개 템플릿 패턴")

        # 3. 템플릿 추천 테스트
        print("\n3. 템플릿 추천 테스트:")
        recommendations = template_vector_store_service.get_template_recommendations(
            "예약 확인 메시지를 보내고 싶습니다",
            category_1="예약"
        )

        print(f"   - 유사 템플릿: {len(recommendations['similar_templates'])}개")
        print(f"   - 패턴 정보: {len(recommendations['category_patterns'])}개")
        print(f"   - 제안사항: {len(recommendations['suggestions'])}개")

        if recommendations['suggestions']:
            print("   제안사항:")
            for suggestion in recommendations['suggestions']:
                print(f"     • {suggestion}")

        print("\n✅ 테스트 검색 완료!")

    except Exception as e:
        print(f"❌ 테스트 검색 실패: {e}")

if __name__ == "__main__":
    main()