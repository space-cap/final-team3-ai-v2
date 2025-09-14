"""
RAG (Retrieval-Augmented Generation) 서비스
LangChain 기반으로 정책 문서 검색과 AI 응답 생성을 결합
"""
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from langchain.memory import ConversationBufferWindowMemory
from langchain.chains import ConversationalRetrievalChain
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor

try:
    from app.services.vector_store_simple import simple_vector_store_service as vector_store_service
except ImportError:
    from app.services.vector_store import vector_store_service
from app.services.token_service import token_service, TokenMetrics
from dotenv import load_dotenv

load_dotenv()

@dataclass
class RAGResponse:
    """RAG 응답 데이터 클래스"""
    answer: str
    source_documents: List[Dict[str, Any]]
    confidence_score: float
    processing_time: float
    metadata: Dict[str, Any]
    token_metrics: Optional[TokenMetrics] = None

class RAGService:
    """
    RAG 서비스 클래스
    벡터 검색과 LLM을 결합하여 정책 기반 응답 생성
    """
    
    def __init__(self):
        """초기화"""
        # OpenAI LLM 설정
        self.llm = ChatOpenAI(
            api_key=os.getenv('OPENAI_API_KEY'),
            model_name=os.getenv('AGENT_MODEL', 'gpt-4o-mini'),
            temperature=float(os.getenv('AGENT_TEMPERATURE', 0.1)),
            max_tokens=int(os.getenv('AGENT_MAX_TOKENS', 2000))
        )
        
        # 메모리 설정 (대화 히스토리)
        self.memory = ConversationBufferWindowMemory(
            k=5,  # 최근 5개 대화만 기억
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"
        )
        
        # 컨텍스트 압축 리트리버 설정
        self.retriever = self._setup_retriever()
        
        # 대화형 RAG 체인 설정
        self.rag_chain = self._setup_rag_chain()
    
    def _setup_retriever(self):
        """리트리버 설정"""
        try:
            # 기본 벡터 스토어 리트리버
            base_retriever = vector_store_service.vector_store.as_retriever(
                search_type="similarity_score_threshold",
                search_kwargs={
                    "k": 10,  # 더 많은 문서를 가져온 후 압축
                    "score_threshold": 0.3  # 유사도 임계값
                }
            )
            
            # LLM 기반 컨텍스트 압축기
            compressor = LLMChainExtractor.from_llm(self.llm)
            
            # 압축 리트리버 생성
            compression_retriever = ContextualCompressionRetriever(
                base_compressor=compressor,
                base_retriever=base_retriever
            )
            
            return compression_retriever
            
        except Exception as e:
            print(f"리트리버 설정 중 오류: {e}")
            # 기본 리트리버로 폴백
            return vector_store_service.vector_store.as_retriever(search_kwargs={"k": 5})
    
    def _setup_rag_chain(self):
        """RAG 체인 설정"""
        try:
            # 대화형 RAG 체인 생성
            rag_chain = ConversationalRetrievalChain.from_llm(
                llm=self.llm,
                retriever=self.retriever,
                memory=self.memory,
                return_source_documents=True,
                verbose=os.getenv('APP_DEBUG', 'False').lower() == 'true'
            )
            
            return rag_chain
            
        except Exception as e:
            print(f"RAG 체인 설정 중 오류: {e}")
            raise
    
    def generate_response(
        self, 
        query: str, 
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> RAGResponse:
        """
        사용자 쿼리에 대한 RAG 기반 응답 생성
        
        Args:
            query: 사용자 질의
            session_id: 세션 ID (대화 컨텍스트용)
            context: 추가 컨텍스트 정보
            
        Returns:
            RAGResponse: 생성된 응답
        """
        import time
        start_time = time.time()
        
        try:
            # 컨텍스트 정보 추가
            enhanced_query = self._enhance_query(query, context)
            
            # RAG 체인 실행
            result = self.rag_chain({
                "question": enhanced_query,
                "chat_history": self.memory.chat_memory.messages
            })

            # 처리 시간 계산 (토큰 추적 전)
            processing_time = time.time() - start_time

            # 토큰 사용량 추적
            token_metrics_obj = None
            try:
                metrics, usage_record = token_service.track_llm_call(
                    llm_response=result,
                    model_name=self.llm.model_name,
                    provider="openai",
                    session_id=session_id,
                    request_type="rag_query",
                    user_query=query,
                    processing_time=processing_time
                )
                token_metrics_obj = metrics
            except Exception as e:
                print(f"토큰 추적 중 오류: {e}")

            # 소스 문서 정보 처리
            source_docs = self._process_source_documents(result.get("source_documents", []))

            # 신뢰도 점수 계산
            confidence_score = self._calculate_confidence_score(result, source_docs)
            
            # 응답 생성
            response = RAGResponse(
                answer=result["answer"],
                source_documents=source_docs,
                confidence_score=confidence_score,
                processing_time=processing_time,
                metadata={
                    "query": query,
                    "enhanced_query": enhanced_query,
                    "session_id": session_id,
                    "model_used": self.llm.model_name,
                    "retrieval_count": len(source_docs)
                },
                token_metrics=token_metrics_obj
            )
            
            return response
            
        except Exception as e:
            print(f"RAG 응답 생성 중 오류: {e}")
            # 오류 시 기본 응답 반환
            return RAGResponse(
                answer=f"죄송합니다. 응답 생성 중 오류가 발생했습니다: {str(e)}",
                source_documents=[],
                confidence_score=0.0,
                processing_time=time.time() - start_time,
                metadata={"error": str(e), "query": query}
            )
    
    def _enhance_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """쿼리에 컨텍스트 정보 추가"""
        enhanced_query = query
        
        if context:
            # 비즈니스 유형 추가
            if "business_type" in context:
                enhanced_query += f" (업종: {context['business_type']})"
            
            # 템플릿 유형 추가
            if "template_type" in context:
                enhanced_query += f" (템플릿 유형: {context['template_type']})"
            
            # 추가 요구사항
            if "requirements" in context:
                enhanced_query += f" (요구사항: {context['requirements']})"
        
        return enhanced_query
    
    def _process_source_documents(self, source_docs: List[Any]) -> List[Dict[str, Any]]:
        """소스 문서 정보 처리"""
        processed_docs = []
        
        for doc in source_docs:
            doc_info = {
                "content": doc.page_content,
                "source": doc.metadata.get("source", "unknown"),
                "chunk_id": doc.metadata.get("chunk_id", 0),
                "document_type": doc.metadata.get("document_type", "policy"),
                "relevance_score": getattr(doc, 'relevance_score', None)
            }
            processed_docs.append(doc_info)
        
        return processed_docs
    
    def _calculate_confidence_score(self, result: Dict[str, Any], source_docs: List[Dict[str, Any]]) -> float:
        """신뢰도 점수 계산"""
        try:
            # 기본 점수
            base_score = 0.5
            
            # 소스 문서 수에 따른 가중치
            doc_count_weight = min(len(source_docs) * 0.1, 0.3)
            
            # 답변 길이에 따른 가중치
            answer_length = len(result.get("answer", ""))
            length_weight = min(answer_length / 1000, 0.2)
            
            # 최종 신뢰도 점수
            confidence = base_score + doc_count_weight + length_weight
            
            return min(confidence, 1.0)  # 최대 1.0으로 제한
            
        except Exception as e:
            print(f"신뢰도 점수 계산 중 오류: {e}")
            return 0.5
    
    def clear_memory(self):
        """대화 메모리 초기화"""
        self.memory.clear()
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """현재 메모리 상태 조회"""
        return {
            "message_count": len(self.memory.chat_memory.messages),
            "memory_key": self.memory.memory_key,
            "messages": [
                {
                    "type": type(msg).__name__,
                    "content": msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                }
                for msg in self.memory.chat_memory.messages
            ]
        }

class TemplateRAGService(RAGService):
    """
    템플릿 생성 특화 RAG 서비스
    알림톡 템플릿 생성에 최적화된 RAG 시스템
    """
    
    def __init__(self):
        super().__init__()
        # 템플릿 생성용 특별 프롬프트 설정
        self.template_prompt = self._setup_template_prompt()
    
    def _setup_template_prompt(self):
        """템플릿 생성용 프롬프트 설정"""
        template = """당신은 카카오 알림톡 템플릿 생성 전문가입니다.

다음 정책 문서를 참고하여 사용자 요청에 맞는 알림톡 템플릿을 생성해주세요:

{context}

사용자 요청: {question}

템플릿 생성 시 다음 사항을 준수해주세요:
1. 카카오 알림톡 정책 완전 준수
2. 정보성 메시지 기준에 맞는 내용
3. 1,000자 이내 작성
4. 변수는 #{변수명} 형식 사용
5. 명확하고 간결한 정보 전달

중요: 반드시 순수한 알림톡 템플릿 내용만 응답해주세요. 
마크다운, 코드블록, 추가 설명, 제목 등은 포함하지 마세요.
오직 실제 고객에게 전송될 메시지 내용만 작성해주세요.

이전 대화: {chat_history}
"""
        
        return ChatPromptTemplate.from_template(template)
    
    def generate_template(
        self,
        user_request: str,
        business_type: Optional[str] = None,
        template_type: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> RAGResponse:
        """
        알림톡 템플릿 생성
        
        Args:
            user_request: 사용자 요청
            business_type: 업종
            template_type: 템플릿 유형
            session_id: 세션 ID
            
        Returns:
            RAGResponse: 생성된 템플릿 응답
        """
        # 컨텍스트 정보 구성
        context = {
            "business_type": business_type,
            "template_type": template_type,
            "purpose": "template_generation"
        }
        
        # RAG 기반 템플릿 생성
        return self.generate_response(
            query=user_request,
            session_id=session_id,
            context=context
        )

# 전역 RAG 서비스 인스턴스
rag_service = TemplateRAGService()