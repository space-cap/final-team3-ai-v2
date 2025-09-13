"""
API 요청/응답 스키마 정의
Pydantic 모델을 사용한 데이터 검증
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

# 기본 응답 모델
class BaseResponse(BaseModel):
    """기본 응답 모델"""
    success: bool = Field(description="요청 성공 여부")
    message: str = Field(description="응답 메시지")
    timestamp: datetime = Field(default_factory=datetime.now, description="응답 시간")

class ErrorResponse(BaseResponse):
    """오류 응답 모델"""
    error_code: str = Field(description="오류 코드")
    error_details: Optional[Dict[str, Any]] = Field(default=None, description="오류 상세 정보")

# 세션 관련 스키마
class SessionCreate(BaseModel):
    """세션 생성 요청"""
    user_id: str = Field(..., min_length=1, max_length=100, description="사용자 식별자")
    session_name: Optional[str] = Field(None, max_length=200, description="세션명")
    session_description: Optional[str] = Field(None, description="세션 설명")
    client_info: Optional[Dict[str, Any]] = Field(default=None, description="클라이언트 정보")

class SessionResponse(BaseResponse):
    """세션 응답"""
    session_id: str = Field(description="세션 ID")
    user_id: str = Field(description="사용자 ID")
    session_name: Optional[str] = Field(description="세션명")
    is_active: bool = Field(description="활성 상태")
    created_at: datetime = Field(description="생성 시간")

# 템플릿 생성 관련 스키마
class TemplateGenerationRequest(BaseModel):
    """템플릿 생성 요청"""
    session_id: Optional[str] = Field(None, description="세션 ID (선택사항)")
    user_id: Optional[str] = Field(None, min_length=1, max_length=100, description="사용자 ID (선택사항)")
    query_text: str = Field(..., min_length=1, description="사용자 질의문")
    business_type: Optional[str] = Field(None, max_length=100, description="사업 유형")
    template_type: Optional[str] = Field(None, max_length=100, description="템플릿 유형")
    additional_context: Optional[Dict[str, Any]] = Field(default=None, description="추가 컨텍스트")

class TemplateGenerationResponse(BaseResponse):
    """템플릿 생성 응답"""
    query_id: int = Field(description="질의 ID")
    template_id: int = Field(description="생성된 템플릿 ID")
    template_content: str = Field(description="템플릿 내용")
    template_analysis: Dict[str, Any] = Field(description="템플릿 분석 결과")
    processing_time: float = Field(description="처리 시간(초)")

class TemplateAnalysis(BaseModel):
    """템플릿 분석 결과"""
    template_type: Optional[str] = Field(description="템플릿 유형")
    message_type: Optional[str] = Field(description="메시지 타입")
    character_count: int = Field(description="글자 수")
    variable_count: int = Field(description="변수 개수")
    variables: List[str] = Field(default=[], description="변수 목록")
    compliance_check: Dict[str, Any] = Field(description="정책 준수 확인")
    quality_score: float = Field(ge=0.0, le=1.0, description="품질 점수")
    suggestions: List[str] = Field(default=[], description="개선 제안")

# 쿼리 관련 스키마
class QueryRequest(BaseModel):
    """일반 질의 요청"""
    session_id: Optional[str] = Field(None, description="세션 ID (선택사항)")
    user_id: Optional[str] = Field(None, min_length=1, max_length=100, description="사용자 ID (선택사항)")
    query_text: str = Field(..., min_length=1, description="질의 내용")
    context: Optional[Dict[str, Any]] = Field(default=None, description="추가 컨텍스트")

class QueryResponse(BaseResponse):
    """일반 질의 응답"""
    query_id: int = Field(description="질의 ID")
    answer: str = Field(description="답변")
    source_documents: List[Dict[str, Any]] = Field(description="참조 문서")
    confidence_score: float = Field(ge=0.0, le=1.0, description="신뢰도 점수")
    processing_time: float = Field(description="처리 시간(초)")

# 템플릿 조회 관련 스키마
class TemplateListRequest(BaseModel):
    """템플릿 목록 조회 요청"""
    user_id: str = Field(..., description="사용자 ID")
    session_id: Optional[str] = Field(None, description="세션 ID (선택)")
    business_category: Optional[str] = Field(None, description="업종 분류")
    template_type: Optional[str] = Field(None, description="템플릿 유형")
    is_favorite: Optional[bool] = Field(None, description="즐겨찾기 여부")
    limit: int = Field(default=20, ge=1, le=100, description="조회 개수")
    offset: int = Field(default=0, ge=0, description="시작 위치")

class TemplateInfo(BaseModel):
    """템플릿 정보"""
    template_id: int = Field(description="템플릿 ID")
    template_name: Optional[str] = Field(description="템플릿명")
    template_content: str = Field(description="템플릿 내용")
    template_type: Optional[str] = Field(description="템플릿 유형")
    business_category: Optional[str] = Field(description="업종 분류")
    quality_score: Optional[float] = Field(description="품질 점수")
    is_favorite: bool = Field(description="즐겨찾기 여부")
    created_at: datetime = Field(description="생성 시간")

class TemplateListResponse(BaseResponse):
    """템플릿 목록 응답"""
    templates: List[TemplateInfo] = Field(description="템플릿 목록")
    total_count: int = Field(description="전체 개수")
    has_more: bool = Field(description="더 많은 데이터 존재 여부")

# 피드백 관련 스키마
class TemplateFeedback(BaseModel):
    """템플릿 피드백"""
    template_id: int = Field(..., description="템플릿 ID")
    user_id: str = Field(..., description="사용자 ID")
    rating: int = Field(..., ge=1, le=5, description="평점 (1-5)")
    feedback: Optional[str] = Field(None, description="피드백 내용")
    is_favorite: Optional[bool] = Field(None, description="즐겨찾기 설정")

class FeedbackResponse(BaseResponse):
    """피드백 응답"""
    template_id: int = Field(description="템플릿 ID")
    updated: bool = Field(description="업데이트 성공 여부")

# 정책 검색 관련 스키마
class PolicySearchRequest(BaseModel):
    """정책 검색 요청"""
    query: str = Field(..., min_length=1, description="검색 쿼리")
    limit: int = Field(default=5, ge=1, le=20, description="결과 개수")

class PolicyDocument(BaseModel):
    """정책 문서"""
    source: str = Field(description="문서 소스")
    content: str = Field(description="문서 내용")
    relevance_score: float = Field(description="관련성 점수")
    metadata: Dict[str, Any] = Field(description="메타데이터")

class PolicySearchResponse(BaseResponse):
    """정책 검색 응답"""
    query: str = Field(description="검색 쿼리")
    documents: List[PolicyDocument] = Field(description="검색 결과 문서")
    total_results: int = Field(description="전체 결과 수")

# 시스템 상태 관련 스키마
class SystemStatus(BaseModel):
    """시스템 상태"""
    database_connected: bool = Field(description="데이터베이스 연결 상태")
    vectordb_loaded: bool = Field(description="벡터DB 로드 상태")
    vectordb_document_count: int = Field(description="벡터DB 문서 수")
    ai_model_available: bool = Field(description="AI 모델 사용 가능 상태")
    uptime: float = Field(description="가동 시간(초)")

class HealthResponse(BaseResponse):
    """헬스체크 응답"""
    status: SystemStatus = Field(description="시스템 상태")
    version: str = Field(description="애플리케이션 버전")
    environment: str = Field(description="실행 환경")