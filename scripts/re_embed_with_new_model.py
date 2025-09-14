"""
새로운 임베딩 모델로 전체 재임베딩 스크립트
"""
import os
import sys
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app.services.vector_store import vector_store_service

def main():
    print("=== 임베딩 모델 변경 후 재임베딩 프로세스 시작 ===")

    # 1. 현재 벡터 스토어 정보 확인
    print("\n1. 현재 벡터 스토어 상태 확인...")
    info = vector_store_service.get_collection_info()
    print(f"컬렉션: {info.get('name', 'N/A')}")
    print(f"문서 수: {info.get('count', 0)}")

    # 2. 재임베딩 실행
    print("\n2. 정책 문서 재임베딩 시작...")
    success = vector_store_service.load_and_embed_policies()

    if success:
        # 3. 재임베딩 결과 확인
        print("\n3. 재임베딩 결과 확인...")
        new_info = vector_store_service.get_collection_info()
        print(f"새 컬렉션: {new_info.get('name', 'N/A')}")
        print(f"새 문서 수: {new_info.get('count', 0)}")

        # 4. 검색 테스트
        print("\n4. 검색 기능 테스트...")
        test_query = "카카오톡 알림톡 변수 사용 방법"
        results = vector_store_service.get_relevant_policies(test_query, k=2)

        print(f"테스트 쿼리: '{test_query}'")
        print(f"검색 결과: {results['total_results']}건")

        for i, policy in enumerate(results['policies'], 1):
            print(f"  {i}. {policy['source']} (점수: {policy['relevance_score']:.4f})")

        print("\n=== 재임베딩 프로세스 완료 ===")
    else:
        print("\n❌ 재임베딩 실패!")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())