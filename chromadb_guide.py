"""
ChromaDB 사용 가이드 - 카카오톡 알림톡 정책 벡터 데이터베이스

이 가이드는 ChromaDB를 사용하여 정책 문서를 벡터 데이터베이스에 저장하고
검색하는 방법을 보여줍니다.
"""

# 1. 기본 설정
import chromadb
from typing import List, Dict

def setup_chromadb():
    """ChromaDB 클라이언트 초기화"""
    # 로컬 파일에 저장하는 영구 클라이언트
    client = chromadb.PersistentClient(path="./chroma_db")

    # 메모리에만 저장하는 임시 클라이언트 (테스트용)
    # client = chromadb.EphemeralClient()

    return client

def create_policy_collection():
    """정책 문서 컬렉션 생성"""
    client = setup_chromadb()

    # 컬렉션 생성 또는 기존 컬렉션 가져오기
    collection = client.get_or_create_collection(
        name="kakao_policies",
        metadata={
            "description": "카카오톡 알림톡 정책 문서",
            "version": "1.0"
        }
    )

    return collection

# 2. 정책 문서 추가
def add_policy_documents():
    """정책 문서를 벡터 데이터베이스에 추가"""
    collection = create_policy_collection()

    # 정책 문서 데이터
    policy_documents = [
        "카카오톡 알림톡 메시지는 1,000자를 초과할 수 없습니다. 이는 사용자 경험과 메시지 전달 효율성을 위한 제한사항입니다.",
        "변수는 #{변수명} 형식으로 사용해야 합니다. 예: #{고객명}, #{주문번호}, #{예약일시}",
        "광고성 메시지와 정보성 메시지는 명확히 구분하여 작성해야 합니다. 정보성 메시지에는 과도한 광고 요소를 포함할 수 없습니다.",
        "발신자 정보는 수신자가 명확히 식별할 수 있도록 표시되어야 합니다. 브랜드명 또는 서비스명을 포함하세요.",
        "개인정보 수집 및 이용에 관한 동의를 받은 고객에게만 알림톡을 발송할 수 있습니다.",
        "스팸성 키워드나 과장된 표현은 사용하지 마세요. '무료', '할인', '이벤트' 등의 단어 사용 시 주의가 필요합니다.",
        "음식점의 경우 메뉴명과 가격 정보를 정확히 표시해야 하며, 알레르기 유발 가능 식재료 정보를 포함하는 것을 권장합니다.",
        "예약 확인 메시지에는 예약 일시, 장소, 연락처, 취소 방법을 모두 포함해야 합니다."
    ]

    # 메타데이터 (문서별 분류 정보)
    metadatas = [
        {"category": "character_limit", "importance": "high", "policy_type": "technical"},
        {"category": "variable_format", "importance": "high", "policy_type": "technical"},
        {"category": "message_classification", "importance": "medium", "policy_type": "content"},
        {"category": "sender_identification", "importance": "high", "policy_type": "compliance"},
        {"category": "privacy_compliance", "importance": "critical", "policy_type": "legal"},
        {"category": "content_restrictions", "importance": "medium", "policy_type": "content"},
        {"category": "business_specific", "importance": "medium", "policy_type": "industry", "business_type": "restaurant"},
        {"category": "business_specific", "importance": "high", "policy_type": "industry", "business_type": "reservation"}
    ]

    # 문서 ID 생성
    document_ids = [f"policy_{i:03d}" for i in range(len(policy_documents))]

    # ChromaDB에 문서 추가
    collection.add(
        documents=policy_documents,
        metadatas=metadatas,
        ids=document_ids
    )

    print(f"✅ {len(policy_documents)}개의 정책 문서가 추가되었습니다.")
    return collection

# 3. 정책 검색
def search_policies(query: str, n_results: int = 3) -> Dict:
    """정책 문서 검색"""
    collection = create_policy_collection()

    # 유사도 검색 실행
    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        include=['documents', 'metadatas', 'distances']
    )

    return results

def search_with_filter(query: str, category: str = None, business_type: str = None) -> Dict:
    """필터링된 정책 검색"""
    collection = create_policy_collection()

    # 필터 조건 구성
    where_condition = {}
    if category:
        where_condition["category"] = category
    if business_type:
        where_condition["business_type"] = business_type

    # 조건부 검색 실행
    if where_condition:
        results = collection.query(
            query_texts=[query],
            n_results=3,
            where=where_condition,
            include=['documents', 'metadatas', 'distances']
        )
    else:
        results = search_policies(query, 3)

    return results

# 4. 실제 사용 예제
def demo_chromadb_usage():
    """ChromaDB 사용 데모"""
    print("🚀 ChromaDB 정책 데이터베이스 데모")
    print("=" * 50)

    # 1. 정책 문서 추가
    print("1. 정책 문서 추가...")
    add_policy_documents()

    # 2. 기본 검색 테스트
    print("\n2. 기본 검색 테스트")
    search_queries = [
        "메시지 길이 제한",
        "변수 사용법",
        "개인정보 처리",
        "음식점 메뉴 정보"
    ]

    for query in search_queries:
        print(f"\n🔍 검색: '{query}'")
        results = search_policies(query)

        for i, (doc, metadata, distance) in enumerate(zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        )):
            similarity_score = 1 - distance  # 거리를 유사도로 변환
            print(f"  {i+1}. [{metadata['category']}] 유사도: {similarity_score:.3f}")
            print(f"     {doc[:80]}...")

    # 3. 필터 검색 테스트
    print(f"\n3. 카테고리별 검색 테스트")
    filtered_results = search_with_filter("메시지 작성", category="character_limit")
    print(f"📂 'character_limit' 카테고리에서 검색:")
    for doc in filtered_results['documents'][0]:
        print(f"   - {doc[:60]}...")

# 5. 고급 기능
def get_collection_info():
    """컬렉션 정보 조회"""
    collection = create_policy_collection()

    # 컬렉션 통계
    count = collection.count()
    print(f"📊 컬렉션 정보:")
    print(f"   - 문서 수: {count}")
    print(f"   - 컬렉션명: {collection.name}")

def update_policy_document(doc_id: str, new_content: str, new_metadata: Dict):
    """정책 문서 업데이트"""
    collection = create_policy_collection()

    collection.update(
        ids=[doc_id],
        documents=[new_content],
        metadatas=[new_metadata]
    )

    print(f"✏️ 문서 {doc_id}가 업데이트되었습니다.")

def delete_policy_document(doc_id: str):
    """정책 문서 삭제"""
    collection = create_policy_collection()

    collection.delete(ids=[doc_id])
    print(f"🗑️ 문서 {doc_id}가 삭제되었습니다.")

# 6. 정책 기반 템플릿 생성 지원 함수
def find_relevant_policies_for_template(business_type: str, message_purpose: str) -> List[str]:
    """템플릿 생성을 위한 관련 정책 검색"""
    query = f"{business_type} {message_purpose} 메시지 작성 규칙"

    # 일반 정책 검색
    general_results = search_policies(query, n_results=3)

    # 업종별 정책 검색
    business_results = search_with_filter(
        query=message_purpose,
        business_type=business_type
    )

    # 결과 조합
    relevant_policies = []
    for result_set in [general_results, business_results]:
        if result_set['documents'][0]:
            relevant_policies.extend(result_set['documents'][0])

    # 중복 제거
    unique_policies = list(set(relevant_policies))

    return unique_policies[:5]  # 상위 5개만 반환

if __name__ == "__main__":
    # 데모 실행
    demo_chromadb_usage()

    print("\n" + "=" * 50)
    print("🎯 실제 사용 시나리오:")

    # 실제 템플릿 생성 시 사용할 정책 검색
    relevant_policies = find_relevant_policies_for_template(
        business_type="restaurant",
        message_purpose="예약 확인"
    )

    print("🍽️ 음식점 예약 확인 메시지 관련 정책:")
    for i, policy in enumerate(relevant_policies, 1):
        print(f"   {i}. {policy[:70]}...")