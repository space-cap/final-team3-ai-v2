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

# 토큰 사용량 관련 스키마 (먼저 정의)
class TokenMetrics(BaseModel):
    """토큰 메트릭"""
    prompt_tokens: int = Field(description="입력 토큰 수")
    completion_tokens: int = Field(description="출력 토큰 수")
    total_tokens: int = Field(description="총 토큰 수")
    prompt_cost: float = Field(description="입력 토큰 비용 (USD)")
    completion_cost: float = Field(description="출력 토큰 비용 (USD)")
    total_cost: float = Field(description="총 비용 (USD)")
    model_name: str = Field(description="사용된 모델명")
    provider: str = Field(description="AI 서비스 제공자")

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
    token_metrics: Optional[TokenMetrics] = Field(None, description="토큰 사용량 정보")

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
    token_metrics: Optional[TokenMetrics] = Field(None, description="토큰 사용량 정보")

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

class TokenUsageRequest(BaseModel):
    """토큰 사용량 조회 요청"""
    session_id: Optional[str] = Field(None, description="세션 ID (선택)")
    start_date: Optional[datetime] = Field(None, description="시작 날짜")
    end_date: Optional[datetime] = Field(None, description="종료 날짜")
    model_name: Optional[str] = Field(None, description="모델명 필터")

class TokenUsageStats(BaseModel):
    """토큰 사용량 통계"""
    total_requests: int = Field(description="총 요청 수")
    total_tokens: int = Field(description="총 토큰 수")
    total_cost: float = Field(description="총 비용 (USD)")
    avg_tokens_per_request: float = Field(description="요청당 평균 토큰 수")
    avg_cost_per_request: float = Field(description="요청당 평균 비용 (USD)")
    models_used: List[str] = Field(description="사용된 모델 목록")
    success_rate: float = Field(description="성공률 (%)")

class TokenUsageResponse(BaseResponse):
    """토큰 사용량 응답"""
    stats: TokenUsageStats = Field(description="토큰 사용량 통계")

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

# 새로운 템플릿 생성 관련 스키마
class SmartTemplateGenerationRequest(BaseModel):
    """스마트 템플릿 생성 요청"""
    user_request: str = Field(..., min_length=1, max_length=500, description="사용자 템플릿 생성 요청")
    business_type: Optional[str] = Field(None, description="업무 유형 (서비스, 상품, 예약 등)")
    category_1: Optional[str] = Field(None, description="1차 분류")
    category_2: Optional[str] = Field(None, description="2차 분류")
    target_length: Optional[int] = Field(None, ge=50, le=300, description="목표 길이")
    include_variables: Optional[List[str]] = Field(default=[], description="포함할 변수 목록")
    context: Optional[Dict[str, Any]] = Field(default={}, description="추가 컨텍스트")

class TemplateValidation(BaseModel):
    """템플릿 검증 결과"""
    length: int = Field(description="템플릿 길이")
    length_appropriate: bool = Field(description="길이 적절성")
    has_greeting: bool = Field(description="인사말 포함 여부")
    variables: List[str] = Field(description="사용된 변수 목록")
    variable_count: int = Field(description="변수 개수")
    has_politeness: bool = Field(description="정중한 표현 사용 여부")
    potential_ad_content: bool = Field(description="광고성 내용 포함 가능성")
    has_contact_info: bool = Field(description="연락처 정보 포함 여부")
    sentence_count: int = Field(description="문장 수")
    compliance_score: float = Field(description="정책 준수 점수 (0-100)")

class SmartTemplateGenerationResponse(BaseResponse):
    """스마트 템플릿 생성 응답"""
    generated_template: str = Field(description="생성된 템플릿")
    validation: TemplateValidation = Field(description="템플릿 검증 결과")
    suggestions: List[str] = Field(description="개선 제안사항")
    reference_data: Dict[str, Any] = Field(description="참조 데이터 정보")
    metadata: Dict[str, Any] = Field(description="생성 메타데이터")

class TemplateOptimizationRequest(BaseModel):
    """템플릿 최적화 요청"""
    template: str = Field(..., min_length=1, description="최적화할 템플릿")
    target_improvements: Optional[List[str]] = Field(default=[], description="개선 목표 사항")

class TemplateOptimizationResponse(BaseResponse):
    """템플릿 최적화 응답"""
    original_template: str = Field(description="원본 템플릿")
    optimized_template: str = Field(description="최적화된 템플릿")
    original_validation: TemplateValidation = Field(description="원본 검증 결과")
    optimized_validation: TemplateValidation = Field(description="최적화된 검증 결과")
    improvement: Dict[str, float] = Field(description="개선 사항")

class TemplateSimilarSearchRequest(BaseModel):
    """유사 템플릿 검색 요청"""
    query: str = Field(..., min_length=1, description="검색 쿼리")
    category_filter: Optional[str] = Field(None, description="카테고리 필터")
    business_type_filter: Optional[str] = Field(None, description="업무 유형 필터")
    limit: int = Field(default=5, ge=1, le=20, description="결과 개수")

class TemplateInfo(BaseModel):
    """템플릿 정보"""
    template_id: str = Field(description="템플릿 ID")
    text: str = Field(description="템플릿 텍스트")
    category_1: Optional[str] = Field(description="1차 분류")
    category_2: Optional[str] = Field(description="2차 분류")
    business_type: Optional[str] = Field(description="업무 유형")
    variables: List[str] = Field(description="사용된 변수")
    button: Optional[str] = Field(description="버튼")
    length: int = Field(description="길이")

class TemplateSimilarSearchResponse(BaseResponse):
    """유사 템플릿 검색 응답"""
    query: str = Field(description="검색 쿼리")
    similar_templates: List[TemplateInfo] = Field(description="유사한 템플릿 목록")
    category_patterns: List[Dict[str, Any]] = Field(description="카테고리 패턴 정보")
    suggestions: List[str] = Field(description="제안사항")

class TemplateVectorStoreInfoResponse(BaseResponse):
    """템플릿 벡터 스토어 정보 응답"""
    templates_count: int = Field(description="템플릿 문서 수")
    patterns_count: int = Field(description="패턴 문서 수")
    status: str = Field(description="상태")
    persist_directory: Optional[str] = Field(description="저장 디렉토리")