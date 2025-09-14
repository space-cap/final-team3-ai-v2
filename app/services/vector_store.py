"""
Chroma 벡터 데이터베이스 관리 서비스
"""
import os
import json
from typing import List, Dict, Any, Optional
from pathlib import Path

import chromadb
from chromadb.config import Settings
from langchain_chroma import Chroma
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from dotenv import load_dotenv

load_dotenv()

class VectorStoreService:
    """
    Chroma 벡터 데이터베이스 관리 클래스
    정책 문서의 임베딩, 저장, 검색 기능 제공
    """
    
    def __init__(self):
        """초기화"""
        self.persist_directory = os.getenv('CHROMA_PERSIST_DIRECTORY', './data/vectordb')
        self.collection_name = os.getenv('CHROMA_COLLECTION_NAME', 'kakao_alimtalk_policies')
        
        # OpenAI 임베딩 모델 설정
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            model="text-embedding-ada-002"
        )
        
        # Chroma 클라이언트 설정
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # 벡터 스토어 초기화
        self.vector_store = None
        self._initialize_vector_store()
    
    def _initialize_vector_store(self):
        """벡터 스토어 초기화"""
        try:
            # 기존 컬렉션이 있는지 확인
            collections = self.client.list_collections()
            collection_exists = any(col.name == self.collection_name for col in collections)
            
            if collection_exists:
                # 기존 컬렉션 로드
                self.vector_store = Chroma(
                    client=self.client,
                    collection_name=self.collection_name,
                    embedding_function=self.embeddings
                )
                print(f"기존 벡터 스토어 '{self.collection_name}' 로드 완료")
            else:
                # 새 컬렉션 생성
                self.vector_store = Chroma(
                    client=self.client,
                    collection_name=self.collection_name,
                    embedding_function=self.embeddings
                )
                print(f"새 벡터 스토어 '{self.collection_name}' 생성 완료")
                
        except Exception as e:
            print(f"벡터 스토어 초기화 중 오류: {e}")
            raise
    
    def load_and_embed_policies(self, policies_dir: str = "./data/cleaned_policies") -> bool:
        """
        정제된 정책 문서들을 로드하고 벡터 데이터베이스에 임베딩
        
        Args:
            policies_dir: 정제된 정책 문서 디렉토리 경로
            
        Returns:
            bool: 성공 여부
        """
        try:
            policies_path = Path(policies_dir)
            if not policies_path.exists():
                print(f"정책 문서 디렉토리가 존재하지 않습니다: {policies_dir}")
                return False
            
            # 마크다운 파일들 찾기
            md_files = list(policies_path.glob("*.md"))
            if not md_files:
                print(f"정책 문서가 없습니다: {policies_dir}")
                return False
            
            print(f"{len(md_files)}개의 정책 문서를 로드합니다...")
            
            # 문서들을 로드하고 청킹
            documents = []
            for md_file in md_files:
                print(f"  - {md_file.name} 처리 중...")
                content = self._load_markdown_file(md_file)
                if content:
                    doc_chunks = self._split_document(content, md_file.stem)
                    documents.extend(doc_chunks)
            
            if not documents:
                print("임베딩할 문서가 없습니다.")
                return False
            
            print(f"총 {len(documents)}개의 문서 청크를 임베딩합니다...")
            
            # 기존 데이터 삭제 (선택적)
            self._clear_collection()
            
            # 벡터 스토어에 문서 추가
            self.vector_store.add_documents(documents)
            
            print("정책 문서 임베딩 완료!")
            return True
            
        except Exception as e:
            print(f"정책 문서 임베딩 중 오류: {e}")
            return False
    
    def _load_markdown_file(self, file_path: Path) -> Optional[str]:
        """마크다운 파일 로드"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"파일 로드 오류 ({file_path}): {e}")
            return None
    
    def _split_document(self, content: str, source: str) -> List[Document]:
        """
        문서를 적절한 크기로 분할
        
        Args:
            content: 문서 내용
            source: 문서 소스 (파일명)
            
        Returns:
            List[Document]: 분할된 문서 리스트
        """
        # 텍스트 스플리터 설정
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,           # 청크 크기
            chunk_overlap=200,         # 청크 간 중복
            length_function=len,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )
        
        # 텍스트 분할
        chunks = text_splitter.split_text(content)
        
        # Document 객체로 변환
        documents = []
        for i, chunk in enumerate(chunks):
            doc = Document(
                page_content=chunk,
                metadata={
                    "source": source,
                    "chunk_id": i,
                    "total_chunks": len(chunks),
                    "document_type": "policy",
                    "language": "korean"
                }
            )
            documents.append(doc)
        
        return documents
    
    def similarity_search(
        self, 
        query: str, 
        k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        유사도 기반 문서 검색
        
        Args:
            query: 검색 쿼리
            k: 반환할 문서 수
            filter_dict: 메타데이터 필터
            
        Returns:
            List[Document]: 검색 결과 문서 리스트
        """
        try:
            if not self.vector_store:
                raise Exception("벡터 스토어가 초기화되지 않았습니다.")
            
            # 검색 수행
            if filter_dict:
                results = self.vector_store.similarity_search(
                    query, 
                    k=k, 
                    filter=filter_dict
                )
            else:
                results = self.vector_store.similarity_search(query, k=k)
            
            return results
            
        except Exception as e:
            print(f"문서 검색 중 오류: {e}")
            return []
    
    def similarity_search_with_score(
        self, 
        query: str, 
        k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[tuple]:
        """
        유사도 점수와 함께 문서 검색
        
        Args:
            query: 검색 쿼리
            k: 반환할 문서 수
            filter_dict: 메타데이터 필터
            
        Returns:
            List[tuple]: (Document, score) 튜플 리스트
        """
        try:
            if not self.vector_store:
                raise Exception("벡터 스토어가 초기화되지 않았습니다.")
            
            # 점수와 함께 검색 수행
            if filter_dict:
                results = self.vector_store.similarity_search_with_score(
                    query, 
                    k=k, 
                    filter=filter_dict
                )
            else:
                results = self.vector_store.similarity_search_with_score(query, k=k)
            
            return results
            
        except Exception as e:
            print(f"점수와 함께 문서 검색 중 오류: {e}")
            return []
    
    def get_relevant_policies(
        self, 
        user_query: str, 
        template_type: Optional[str] = None,
        k: int = 5
    ) -> Dict[str, Any]:
        """
        사용자 쿼리에 관련된 정책 정보 검색
        
        Args:
            user_query: 사용자 질의
            template_type: 템플릿 유형 (선택사항)
            k: 반환할 문서 수
            
        Returns:
            Dict: 관련 정책 정보
        """
        try:
            # 필터 설정
            filter_dict = {"document_type": "policy"}
            
            # 검색 수행
            results = self.similarity_search_with_score(
                user_query, 
                k=k, 
                filter_dict=filter_dict
            )
            
            # 결과 정리
            policies = []
            for doc, score in results:
                policy_info = {
                    "content": doc.page_content,
                    "source": doc.metadata.get("source", "unknown"),
                    "relevance_score": score,
                    "metadata": doc.metadata
                }
                policies.append(policy_info)
            
            return {
                "query": user_query,
                "total_results": len(policies),
                "policies": policies
            }
            
        except Exception as e:
            print(f"관련 정책 검색 중 오류: {e}")
            return {
                "query": user_query,
                "total_results": 0,
                "policies": []
            }
    
    def _clear_collection(self):
        """컬렉션 데이터 삭제"""
        try:
            # 컬렉션 삭제 후 재생성
            self.client.delete_collection(self.collection_name)
            self.vector_store = Chroma(
                client=self.client,
                collection_name=self.collection_name,
                embedding_function=self.embeddings
            )
            print("기존 벡터 스토어 데이터 삭제 완료")
        except Exception as e:
            print(f"컬렉션 삭제 중 오류: {e}")
    
    def get_collection_info(self) -> Dict[str, Any]:
        """컬렉션 정보 조회"""
        try:
            collection = self.client.get_collection(self.collection_name)
            return {
                "name": collection.name,
                "count": collection.count(),
                "metadata": collection.metadata
            }
        except Exception as e:
            print(f"컬렉션 정보 조회 중 오류: {e}")
            return {}

# 전역 벡터 스토어 인스턴스
vector_store_service = VectorStoreService()