# ChromaDB 사용 예제 - 카카오톡 알림톡 정책 벡터 데이터베이스
import chromadb
import os

def setup_chroma():
    """ChromaDB 클라이언트 설정"""
    # 로컬 파일시스템에 저장하는 클라이언트 생성
    client = chromadb.PersistentClient(path="./chroma_db")

    print("ChromaDB 클라이언트가 설정되었습니다.")
    print(f"저장 경로: {os.path.abspath('./chroma_db')}")

    return client

def create_policy_collection():
    """정책 문서를 위한 컬렉션 생성"""
    client = setup_chroma()

    # 컬렉션 생성 (이미 존재하면 가져오기)
    collection = client.get_or_create_collection(
        name="policy_documents",
        metadata={"description": "카카오톡 알림톡 정책 문서 저장소"}
    )

    return collection

def add_policy_documents():
    """정책 문서를 벡터 데이터베이스에 추가"""
    collection = create_policy_collection()

    # 예시 정책 문서들
    documents = [
        "카카오톡 알림톡 메시지는 1,000자를 초과할 수 없습니다.",
        "변수는 #{변수명} 형식으로 사용해야 합니다.",
        "광고성 메시지는 정보성 메시지와 구분하여 작성해야 합니다.",
        "수신자가 명확히 식별할 수 있는 발신자 정보를 포함해야 합니다.",
        "개인정보 수집 및 이용에 관한 동의를 받은 고객에게만 발송 가능합니다."
    ]

    # 메타데이터 추가
    metadatas = [
        {"category": "character_limit", "importance": "high"},
        {"category": "variable_format", "importance": "high"},
        {"category": "message_type", "importance": "medium"},
        {"category": "sender_info", "importance": "high"},
        {"category": "privacy", "importance": "critical"}
    ]

    # 각 문서에 고유 ID 부여
    ids = [f"policy_{i}" for i in range(len(documents))]

    # 문서를 컬렉션에 추가
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )

    print(f"Added {len(documents)} policy documents to the collection")

def search_policies(query):
    """정책 검색 함수"""
    collection = create_policy_collection()

    # 유사도 검색 (기본적으로 코사인 유사도 사용)
    results = collection.query(
        query_texts=[query],
        n_results=3  # 상위 3개 결과 반환
    )

    return results

def main():
    """메인 함수 - ChromaDB 사용 예제"""
    print("ChromaDB 설정 및 정책 문서 추가...")

    # 정책 문서 추가
    add_policy_documents()

    # 검색 예제들
    search_queries = [
        "메시지 길이 제한",
        "변수 사용법",
        "개인정보 처리"
    ]

    for query in search_queries:
        print(f"\n검색 쿼리: '{query}'")
        results = search_policies(query)

        print("검색 결과:")
        for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
            distance = results['distances'][0][i]
            print(f"  {i+1}. [{metadata['category']}] {doc}")
            print(f"     유사도 점수: {1-distance:.3f}")

if __name__ == "__main__":
    main()