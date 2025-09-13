"""
벡터 데이터베이스 초기화 스크립트
정제된 정책 문서들을 Chroma DB에 임베딩
"""
import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.vector_store import vector_store_service

def init_vector_database():
    """
    벡터 데이터베이스 초기화 함수
    """
    print("=== 벡터 데이터베이스 초기화 시작 ===")
    
    try:
        # 벡터 스토어 서비스 상태 확인
        print("1. 벡터 스토어 서비스 상태 확인...")
        info = vector_store_service.get_collection_info()
        if info:
            print(f"   - 컬렉션: {info.get('name', 'unknown')}")
            print(f"   - 기존 문서 수: {info.get('count', 0)}")
        
        # 정책 문서 임베딩
        print("2. 정책 문서 임베딩 시작...")
        success = vector_store_service.load_and_embed_policies("./data/cleaned_policies")
        
        if success:
            print("3. 임베딩 완료 - 상태 확인...")
            info = vector_store_service.get_collection_info()
            print(f"   - 최종 문서 수: {info.get('count', 0)}")
            
            # 테스트 검색 수행
            print("4. 테스트 검색 수행...")
            test_query = "알림톡 템플릿 승인 기준"
            results = vector_store_service.similarity_search(test_query, k=3)
            
            print(f"   - 검색 쿼리: '{test_query}'")
            print(f"   - 검색 결과 수: {len(results)}")
            
            for i, doc in enumerate(results[:2]):  # 처음 2개 결과만 출력
                print(f"   - 결과 {i+1}: {doc.metadata.get('source', 'unknown')} "
                      f"(길이: {len(doc.page_content)}자)")
            
            print("=== 벡터 데이터베이스 초기화 완료 ===")
        else:
            print("!!! 벡터 데이터베이스 초기화 실패 !!!")
            
    except Exception as e:
        print(f"벡터 데이터베이스 초기화 중 오류 발생: {e}")
        raise

def test_vector_search():
    """
    벡터 검색 기능 테스트
    """
    print("\n=== 벡터 검색 테스트 ===")
    
    test_queries = [
        "회원가입 알림톡 템플릿",
        "주문 완료 메시지",
        "배송 상태 안내",
        "포인트 적립 알림",
        "예약 확인 메시지"
    ]
    
    for query in test_queries:
        print(f"\n검색 쿼리: '{query}'")
        results = vector_store_service.get_relevant_policies(query, k=2)
        
        print(f"검색 결과: {results['total_results']}개")
        for i, policy in enumerate(results['policies']):
            print(f"  {i+1}. {policy['source']} (점수: {policy['relevance_score']:.3f})")
            print(f"     내용: {policy['content'][:100]}...")

if __name__ == "__main__":
    init_vector_database()
    test_vector_search()