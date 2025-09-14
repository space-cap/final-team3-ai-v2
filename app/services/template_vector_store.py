"""
Template Vector Store Implementation
카카오 알림톡 승인받은 템플릿과 패턴을 위한 벡터 데이터베이스
"""

import os
import json
from typing import List, Dict, Any, Optional
from pathlib import Path

try:
    import faiss
    from langchain_community.vectorstores import FAISS
    from langchain_openai import OpenAIEmbeddings
    from langchain.docstore.document import Document
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

    # Fallback dummy classes
    class Document:
        def __init__(self, page_content: str, metadata: Dict[str, Any] = None):
            self.page_content = page_content
            self.metadata = metadata or {}

from dotenv import load_dotenv

load_dotenv()


class TemplateVectorStoreService:
    """
    카카오 알림톡 템플릿 전용 벡터 스토어 서비스
    승인받은 템플릿, 패턴, 성공 지표 관리
    """

    def __init__(self):
        """Initialize template vector store"""
        self.persist_directory = os.getenv(
            "TEMPLATE_PERSIST_DIRECTORY", "./data/vectordb_templates"
        )

        # 컬렉션별 디렉토리 설정
        self.templates_dir = f"{self.persist_directory}/templates"
        self.patterns_dir = f"{self.persist_directory}/patterns"

        # Create persist directories
        Path(self.templates_dir).mkdir(parents=True, exist_ok=True)
        Path(self.patterns_dir).mkdir(parents=True, exist_ok=True)

        if not FAISS_AVAILABLE:
            print("WARNING: FAISS not available. Template vector search will be disabled.")
            self.templates_store = None
            self.patterns_store = None
            self.embeddings = None
            return

        # OpenAI embeddings
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            model="text-embedding-3-small",
        )

        # Vector stores
        self.templates_store = None
        self.patterns_store = None

        # Initialize vector stores
        self._initialize_vector_stores()

    def _initialize_vector_stores(self):
        """Initialize both template and pattern vector stores"""
        if not FAISS_AVAILABLE:
            return

        try:
            # Initialize templates vector store
            templates_index_path = Path(self.templates_dir) / "index.faiss"
            if templates_index_path.exists():
                self.templates_store = FAISS.load_local(
                    self.templates_dir,
                    self.embeddings,
                    allow_dangerous_deserialization=True,
                )
                print(f"Templates vector store loaded from {self.templates_dir}")

            # Initialize patterns vector store
            patterns_index_path = Path(self.patterns_dir) / "index.faiss"
            if patterns_index_path.exists():
                self.patterns_store = FAISS.load_local(
                    self.patterns_dir,
                    self.embeddings,
                    allow_dangerous_deserialization=True,
                )
                print(f"Patterns vector store loaded from {self.patterns_dir}")

        except Exception as e:
            print(f"Template vector stores initialization error: {e}")

    def load_template_data(self, json_data_path: str = "./data/kakao_template_vectordb_data.json") -> bool:
        """
        JSON 데이터에서 템플릿과 패턴 정보를 로드하여 벡터 데이터베이스에 저장
        """
        if not FAISS_AVAILABLE:
            print("FAISS not available - skipping template data loading")
            return False

        try:
            # JSON 데이터 로드
            json_path = Path(json_data_path)
            if not json_path.exists():
                print(f"Template JSON data file not found: {json_data_path}")
                return False

            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 템플릿 데이터 처리
            templates_data = data.get('templates', [])
            if templates_data:
                template_documents = self._create_template_documents(templates_data)
                if template_documents:
                    if self.templates_store is None:
                        self.templates_store = FAISS.from_documents(template_documents, self.embeddings)
                    else:
                        self.templates_store.add_documents(template_documents)

                    # 저장
                    self.templates_store.save_local(self.templates_dir)
                    print(f"템플릿 문서 {len(template_documents)}개 임베딩 완료")

            # 패턴 데이터 처리
            patterns_data = data.get('patterns', [])
            if patterns_data:
                pattern_documents = self._create_pattern_documents(patterns_data)
                if pattern_documents:
                    if self.patterns_store is None:
                        self.patterns_store = FAISS.from_documents(pattern_documents, self.embeddings)
                    else:
                        self.patterns_store.add_documents(pattern_documents)

                    # 저장
                    self.patterns_store.save_local(self.patterns_dir)
                    print(f"패턴 문서 {len(pattern_documents)}개 임베딩 완료")

            print("템플릿 벡터 데이터베이스 로딩 완료!")
            return True

        except Exception as e:
            print(f"Template data loading error: {e}")
            return False

    def _create_template_documents(self, templates_data: List[Dict]) -> List[Document]:
        """승인받은 템플릿을 Document 객체로 변환"""
        documents = []

        for template in templates_data:
            # 템플릿 텍스트와 메타데이터로 검색 가능한 텍스트 생성
            text_content = template.get('text', '')
            metadata = template.get('metadata', {})

            # 검색 최적화를 위한 컨텐츠 보강
            enhanced_content = f"""
템플릿 내용: {text_content}

분류: {metadata.get('category_1', '')} - {metadata.get('category_2', '')}
업무분류: {metadata.get('business_type', '')}
서비스분류: {metadata.get('service_type', '')}
사용변수: {', '.join(metadata.get('variables', []))}
버튼: {metadata.get('button', '')}
길이: {metadata.get('length', 0)}자
특징: {'인사말 포함' if metadata.get('has_greeting') else '인사말 없음'}, {'버튼 언급' if metadata.get('has_button_mention') else '버튼 언급 없음'}
            """.strip()

            doc = Document(
                page_content=enhanced_content,
                metadata={
                    **metadata,
                    'document_type': 'approved_template',
                    'template_id': template.get('id'),
                    'original_text': text_content,
                }
            )
            documents.append(doc)

        return documents

    def _create_pattern_documents(self, patterns_data: List[Dict]) -> List[Document]:
        """분류별 패턴을 Document 객체로 변환"""
        documents = []

        for pattern in patterns_data:
            category = pattern.get('category', '')
            metadata = pattern.get('metadata', {})

            # 패턴 정보를 텍스트로 구성
            pattern_content = f"""
카테고리: {category}
템플릿 수: {metadata.get('template_count', 0)}개

주요 변수:
{self._format_dict_as_text(metadata.get('common_variables', {}))}

특징적 단어:
{self._format_dict_as_text(metadata.get('characteristic_words', {}))}

일반적 버튼:
{self._format_dict_as_text(metadata.get('common_buttons', {}))}

평균 길이: {metadata.get('avg_length', 0)}자
길이 범위: {metadata.get('length_range', {}).get('min', 0)}-{metadata.get('length_range', {}).get('max', 0)}자

성공 지표:
- 인사말 사용률: {metadata.get('success_indicators', {}).get('greeting_usage', 0):.1%}
- 변수 사용률: {metadata.get('success_indicators', {}).get('variable_usage', 0):.1f}
- 버튼 사용률: {metadata.get('success_indicators', {}).get('button_usage', 0):.1%}
            """.strip()

            doc = Document(
                page_content=pattern_content,
                metadata={
                    **metadata,
                    'document_type': 'category_pattern',
                    'pattern_id': pattern.get('id'),
                    'category': category,
                }
            )
            documents.append(doc)

        return documents

    def _format_dict_as_text(self, data_dict: Dict) -> str:
        """딕셔너리를 읽기 쉬운 텍스트로 변환"""
        if not data_dict:
            return "없음"

        items = []
        for key, value in data_dict.items():
            items.append(f"- {key}: {value}")

        return '\n'.join(items)

    def find_similar_templates(
        self,
        query: str,
        category_filter: Optional[str] = None,
        business_type_filter: Optional[str] = None,
        k: int = 5
    ) -> List[Document]:
        """유사한 승인받은 템플릿 검색"""
        if not FAISS_AVAILABLE or not self.templates_store:
            print("Templates vector search not available")
            return []

        try:
            # 기본 검색
            results = self.templates_store.similarity_search(query, k=k*2)  # 여유있게 더 가져와서 필터링

            # 필터 적용
            filtered_results = []
            for doc in results:
                metadata = doc.metadata

                # 카테고리 필터
                if category_filter and metadata.get('category_1') != category_filter:
                    continue

                # 업무분류 필터
                if business_type_filter and metadata.get('business_type') != business_type_filter:
                    continue

                filtered_results.append(doc)

                if len(filtered_results) >= k:
                    break

            return filtered_results

        except Exception as e:
            print(f"Similar templates search error: {e}")
            return []

    def find_category_patterns(
        self,
        category: str,
        k: int = 3
    ) -> List[Document]:
        """특정 카테고리의 패턴 정보 검색"""
        if not FAISS_AVAILABLE or not self.patterns_store:
            print("Patterns vector search not available")
            return []

        try:
            # 카테고리 기반 검색
            query = f"카테고리 {category} 패턴 특징 변수 버튼"
            results = self.patterns_store.similarity_search(query, k=k)

            return results

        except Exception as e:
            print(f"Category patterns search error: {e}")
            return []

    def get_template_recommendations(
        self,
        user_input: str,
        category_1: Optional[str] = None,
        category_2: Optional[str] = None,
        business_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """사용자 입력 기반 템플릿 추천"""
        try:
            recommendations = {
                'query': user_input,
                'similar_templates': [],
                'category_patterns': [],
                'suggestions': []
            }

            # 1. 유사한 승인 템플릿 검색
            similar_templates = self.find_similar_templates(
                user_input,
                category_filter=category_1,
                business_type_filter=business_type,
                k=5
            )

            for doc in similar_templates:
                template_info = {
                    'text': doc.metadata.get('original_text', ''),
                    'category_1': doc.metadata.get('category_1'),
                    'category_2': doc.metadata.get('category_2'),
                    'business_type': doc.metadata.get('business_type'),
                    'variables': doc.metadata.get('variables', []),
                    'button': doc.metadata.get('button'),
                    'length': doc.metadata.get('length'),
                    'template_id': doc.metadata.get('template_id')
                }
                recommendations['similar_templates'].append(template_info)

            # 2. 카테고리 패턴 정보
            if category_1:
                patterns = self.find_category_patterns(category_1)
                for doc in patterns:
                    pattern_info = {
                        'category': doc.metadata.get('category'),
                        'template_count': doc.metadata.get('template_count'),
                        'common_variables': doc.metadata.get('common_variables', {}),
                        'characteristic_words': doc.metadata.get('characteristic_words', {}),
                        'common_buttons': doc.metadata.get('common_buttons', {}),
                        'avg_length': doc.metadata.get('avg_length'),
                        'success_indicators': doc.metadata.get('success_indicators', {})
                    }
                    recommendations['category_patterns'].append(pattern_info)

            # 3. 개선 제안 생성
            recommendations['suggestions'] = self._generate_suggestions(
                similar_templates, category_1, category_2
            )

            return recommendations

        except Exception as e:
            print(f"Template recommendations error: {e}")
            return {
                'query': user_input,
                'similar_templates': [],
                'category_patterns': [],
                'suggestions': []
            }

    def _generate_suggestions(
        self,
        similar_templates: List[Document],
        category_1: Optional[str],
        category_2: Optional[str]
    ) -> List[str]:
        """템플릿 생성을 위한 제안사항 생성"""
        suggestions = []

        if similar_templates:
            # 공통 패턴 분석
            common_variables = set()
            common_buttons = set()
            lengths = []

            for doc in similar_templates:
                metadata = doc.metadata
                common_variables.update(metadata.get('variables', []))
                button = metadata.get('button', '')
                if button and button != 'X':
                    common_buttons.add(button)
                lengths.append(metadata.get('length', 0))

            # 제안사항 생성
            if common_variables:
                top_variables = list(common_variables)[:3]
                suggestions.append(f"권장 변수: {', '.join(f'#{{{var}}}' for var in top_variables)}")

            if common_buttons:
                suggestions.append(f"추천 버튼: {', '.join(common_buttons)}")

            if lengths:
                avg_length = sum(lengths) / len(lengths)
                suggestions.append(f"권장 길이: {avg_length:.0f}자 내외")

            # 카테고리별 조언
            if category_1 == '서비스이용':
                suggestions.append("서비스 이용 템플릿은 '안녕하세요 #{고객성명}님'으로 시작하는 것이 효과적입니다")
                suggestions.append("서비스 완료/진행 상황을 명확히 안내하세요")
            elif category_1 == '상품':
                suggestions.append("상품 관련 템플릿은 #{상품명}, #{주문번호} 변수를 포함하세요")
                suggestions.append("픽업이나 배송 관련 안내를 포함하세요")
            elif category_1 == '예약':
                suggestions.append("예약 템플릿은 #{날짜}, #{시간} 정보를 포함하세요")
                suggestions.append("변경이나 취소 방법을 안내하세요")

        return suggestions

    def get_store_info(self) -> Dict[str, Any]:
        """벡터 스토어 정보 조회"""
        if not FAISS_AVAILABLE:
            return {
                'templates_count': 0,
                'patterns_count': 0,
                'status': 'not_available'
            }

        try:
            templates_count = 0
            patterns_count = 0

            if self.templates_store and hasattr(self.templates_store, 'index'):
                templates_count = self.templates_store.index.ntotal

            if self.patterns_store and hasattr(self.patterns_store, 'index'):
                patterns_count = self.patterns_store.index.ntotal

            return {
                'templates_count': templates_count,
                'patterns_count': patterns_count,
                'status': 'available',
                'persist_directory': self.persist_directory
            }

        except Exception as e:
            print(f"Store info error: {e}")
            return {
                'templates_count': 0,
                'patterns_count': 0,
                'status': 'error'
            }


# Global instance
template_vector_store_service = TemplateVectorStoreService()