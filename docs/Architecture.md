# 시스템 아키텍처

카카오 알림톡 템플릿 AI 생성 시스템의 전체적인 아키텍처와 각 구성 요소에 대해 설명합니다.

## 전체 시스템 개요

본 시스템은 다음과 같은 마이크로서비스 아키텍처를 채택하고 있습니다:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │───▶│   FastAPI        │───▶│   AI Services   │
│   (예정)        │    │   Web Server     │    │   (OpenAI)      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                               │                         │
                               ▼                         ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │   MySQL          │    │   Chroma        │
                       │   Database       │    │   Vector DB     │
                       └──────────────────┘    └─────────────────┘
```

## 아키텍처 레이어

### 1. Presentation Layer (표현 계층)

#### FastAPI Web Framework
- **역할**: REST API 엔드포인트 제공
- **기술**: FastAPI, Pydantic, Uvicorn
- **주요 기능**:
  - HTTP 요청/응답 처리
  - 입력 데이터 검증
  - API 문서 자동 생성
  - CORS, 미들웨어 관리

```python
# 주요 컴포넌트
├── main.py                    # FastAPI 앱 진입점
├── app/api/
│   ├── endpoints.py          # REST API 엔드포인트
│   └── schemas.py            # 요청/응답 스키마
```

### 2. Business Logic Layer (비즈니스 로직 계층)

#### AI Agents (AI 에이전트)
- **TemplateGenerationAgent**: 템플릿 생성 전문 에이전트
- **PolicyComplianceAgent**: 정책 준수 검증 에이전트

```python
# 에이전트 아키텍처
┌─────────────────────────────┐
│  Agent Controller           │
├─────────────────────────────┤
│  • LLM Integration         │
│  • Tool Management         │
│  • Context Management      │
│  • Error Handling          │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  Specialized Tools          │
├─────────────────────────────┤
│  • TemplateValidatorTool   │
│  • PolicyCheckerTool       │
│  • ViolationDetectorTool   │
│  • ImprovementSuggestor    │
└─────────────────────────────┘
```

#### RAG System (검색 증강 생성)
- **벡터 검색**: 정책 문서에서 관련 정보 검색
- **컨텍스트 압축**: 검색된 문서의 핵심 내용 추출
- **응답 생성**: LLM과 검색 결과를 결합한 답변 생성

```python
# RAG 처리 플로우
User Query → Vector Search → Context Compression → LLM Generation → Response
     ↓              ↓                 ↓                ↓            ↓
   임베딩          유사도 검색        핵심 추출         프롬프트      최종 응답
```

### 3. Data Layer (데이터 계층)

#### MySQL Database
- **역할**: 구조화된 데이터 저장
- **주요 테이블**:
  - `sessions`: 사용자 세션 정보
  - `queries`: 질의 기록
  - `templates`: 생성된 템플릿
  - `prompts`: 시스템 프롬프트

#### Chroma Vector Database
- **역할**: 문서 임베딩 벡터 저장 및 검색
- **기능**:
  - 정책 문서 벡터화
  - 유사도 기반 검색
  - 메타데이터 관리

## 주요 구성 요소 상세

### AI 에이전트 아키텍처

#### 1. TemplateGenerationAgent

```python
class TemplateGenerationAgent:
    """
    템플릿 생성 전문 에이전트
    
    구성 요소:
    - LLM (GPT-4)
    - Specialized Tools
    - Template Validator
    - Business Type Analyzer
    """
    
    def generate_template(self, user_request, business_type, template_type):
        # 1. 사용자 요청 분석
        # 2. 관련 정책 검색 (RAG)
        # 3. 초안 템플릿 생성
        # 4. 정책 준수 검증
        # 5. 품질 개선
        # 6. 최종 템플릿 반환
```

**처리 플로우:**
```
User Request → Request Analysis → Policy Search → Draft Generation → Validation → Improvement → Final Template
```

#### 2. PolicyComplianceAgent

```python
class PolicyComplianceAgent:
    """
    정책 준수 검증 전문 에이전트
    
    구성 요소:
    - Compliance Checker Tools
    - Violation Detector
    - Improvement Suggestor
    - Policy Rule Manager
    """
    
    def analyze_compliance(self, template_content, business_type):
        # 1. 기본 정책 검증 (길이, 변수 등)
        # 2. 콘텐츠 위반 탐지
        # 3. 비즈니스 특화 규칙 적용
        # 4. 위반 사항 분류 및 우선순위 설정
        # 5. 개선 방안 제시
        # 6. 최종 분석 결과 반환
```

**검증 플로우:**
```
Template Input → Basic Validation → Content Analysis → Business Rules → Violation Detection → Improvement Suggestions → Compliance Report
```

### RAG 시스템 아키텍처

#### 1. 문서 처리 파이프라인

```python
# 문서 임베딩 과정
Raw Policy Documents → Text Cleaning → Chunking → Embedding → Vector Storage
         ↓                  ↓           ↓          ↓           ↓
    원본 정책 문서        텍스트 정제     청크 분할    벡터 변환    Chroma 저장
```

#### 2. 검색 시스템

```python
class VectorStoreService:
    """
    벡터 저장소 서비스
    
    주요 기능:
    - 문서 임베딩 및 저장
    - 유사도 기반 검색
    - 메타데이터 필터링
    - 결과 순위 조정
    """
    
    def get_relevant_policies(self, user_query, k=5):
        # 1. 질의 임베딩 생성
        # 2. 벡터 유사도 검색
        # 3. 메타데이터 필터링
        # 4. 결과 순위 조정
        # 5. 상위 k개 결과 반환
```

#### 3. 컨텍스트 압축

```python
class ContextualCompressionRetriever:
    """
    검색 결과 압축 및 최적화
    
    기능:
    - 중복 내용 제거
    - 핵심 정보 추출
    - 컨텍스트 길이 최적화
    """
```

## 데이터베이스 설계

### MySQL 스키마

#### 1. 세션 관리
```sql
-- sessions 테이블
CREATE TABLE sessions (
    session_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    session_name VARCHAR(200),
    session_description TEXT,
    client_info TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_is_active (is_active)
);
```

#### 2. 질의 관리
```sql
-- queries 테이블
CREATE TABLE queries (
    query_id INT PRIMARY KEY AUTO_INCREMENT,
    session_id VARCHAR(36),
    user_id VARCHAR(100) NOT NULL,
    query_text TEXT NOT NULL,
    business_type VARCHAR(100),
    template_type VARCHAR(100),
    status ENUM('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED') DEFAULT 'PENDING',
    processing_started_at TIMESTAMP NULL,
    processing_completed_at TIMESTAMP NULL,
    processing_duration INT,
    error_message TEXT,
    additional_context TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id),
    INDEX idx_user_id (user_id),
    INDEX idx_status (status)
);
```

#### 3. 템플릿 관리
```sql
-- templates 테이블
CREATE TABLE templates (
    template_id INT PRIMARY KEY AUTO_INCREMENT,
    query_id INT,
    session_id VARCHAR(36),
    user_id VARCHAR(100) NOT NULL,
    template_name VARCHAR(200),
    template_content TEXT NOT NULL,
    template_type VARCHAR(100),
    message_type VARCHAR(100),
    business_category VARCHAR(100),
    quality_score DECIMAL(3,2),
    compliance_score DECIMAL(3,2),
    has_variables BOOLEAN DEFAULT FALSE,
    variable_count INT DEFAULT 0,
    character_count INT,
    is_favorite BOOLEAN DEFAULT FALSE,
    user_rating INT,
    user_feedback TEXT,
    ai_model_used VARCHAR(100),
    generation_context TEXT,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (query_id) REFERENCES queries(query_id),
    FOREIGN KEY (session_id) REFERENCES sessions(session_id),
    INDEX idx_user_id (user_id),
    INDEX idx_business_category (business_category),
    INDEX idx_template_type (template_type),
    INDEX idx_is_favorite (is_favorite)
);
```

### Chroma Vector Database 구조

```python
# 컬렉션 구조
{
    "collection_name": "policy_documents",
    "documents": [
        {
            "id": "doc_001",
            "content": "정책 문서 내용...",
            "metadata": {
                "source": "카카오 알림톡 가이드 v3.2",
                "section": "변수 사용 규칙",
                "category": "template_rules",
                "last_updated": "2024-01-01",
                "language": "ko"
            },
            "embedding": [0.1, 0.2, 0.3, ...]  # 1536차원 벡터
        }
    ]
}
```

## 보안 아키텍처

### 1. 데이터 보호
- **암호화**: 민감한 설정 정보 환경변수 저장
- **접근 제어**: 데이터베이스 사용자 권한 분리
- **입력 검증**: Pydantic을 통한 엄격한 데이터 검증

### 2. API 보안
- **CORS 정책**: 운영환경에서 도메인 제한
- **Rate Limiting**: API 호출 빈도 제한 (향후 추가 예정)
- **인증/인가**: JWT 토큰 기반 인증 (향후 추가 예정)

### 3. AI 모델 보안
- **API 키 관리**: OpenAI API 키 안전한 저장
- **컨텍스트 제한**: 민감한 정보 LLM 전송 방지
- **로깅**: AI 요청/응답 적절한 수준에서 로깅

## 성능 최적화

### 1. 데이터베이스 최적화
```python
# 커넥션 풀 설정
DATABASE_CONFIG = {
    "pool_size": 10,
    "max_overflow": 20,
    "pool_timeout": 30,
    "pool_recycle": 3600,
    "echo": False  # 운영환경에서는 False
}
```

### 2. 캐싱 전략
- **벡터 검색 결과 캐싱**: 자주 검색되는 정책 정보
- **템플릿 메타데이터 캐싱**: 빠른 목록 조회
- **세션 정보 캐싱**: 사용자 컨텍스트 유지

### 3. 비동기 처리
```python
# FastAPI 비동기 처리
@router.post("/templates/generate")
async def generate_template(request: TemplateGenerationRequest):
    # 비동기로 처리하여 동시성 향상
    result = await rag_service.generate_template_async(...)
    return result
```

## 확장성 고려사항

### 1. 수평 확장
- **API 서버**: 로드 밸런서를 통한 다중 인스턴스
- **데이터베이스**: 읽기 복제본을 통한 부하 분산
- **벡터 데이터베이스**: 샤딩을 통한 검색 성능 향상

### 2. 모니터링 및 관찰성
```python
# 구조화된 로깅
import structlog

logger = structlog.get_logger()
logger.info(
    "template_generated",
    user_id=user_id,
    template_id=template_id,
    processing_time=processing_time,
    business_type=business_type
)
```

### 3. 메트릭스 수집
- **API 성능**: 응답 시간, 처리량
- **AI 성능**: 생성 품질, 정책 준수율
- **사용자 행동**: 세션 길이, 피드백 점수

## 배포 아키텍처

### 개발 환경
```
Developer Machine
├── Python 3.13 Virtual Environment
├── Local MySQL Instance
├── Local Chroma Storage
└── Environment Variables (.env)
```

### 운영 환경 (예상)
```
Load Balancer
    │
    ├── FastAPI Instance 1
    ├── FastAPI Instance 2
    └── FastAPI Instance N
            │
            ├── MySQL Cluster (Master/Slave)
            ├── Chroma Cluster
            └── Redis Cache (향후 추가)
```

## API 설계 원칙

### RESTful API 설계
- **리소스 기반 URL**: `/api/v1/templates`, `/api/v1/sessions`
- **HTTP 메서드 활용**: GET, POST, PUT, DELETE
- **상태 코드**: 적절한 HTTP 상태 코드 사용
- **버전 관리**: URL 기반 버전 관리 (`/v1/`)

### 응답 일관성
```python
# 모든 응답의 기본 구조
{
    "success": boolean,
    "message": string,
    "timestamp": datetime,
    # 추가 데이터...
}
```

## 에러 처리 전략

### 1. 계층적 에러 처리
```
Presentation Layer → Business Logic Layer → Data Layer
      ↓                       ↓                ↓
  HTTP Errors          Business Errors    Database Errors
      ↓                       ↓                ↓
  Status Codes          Custom Exceptions   Connection Errors
```

### 2. 복구 전략
- **재시도 메커니즘**: 일시적 네트워크 오류
- **Circuit Breaker**: 외부 서비스 오류 시 차단
- **Graceful Degradation**: 부분적 기능 제한으로 서비스 유지

## 향후 발전 방향

### 1. 단기 개선사항
- **인증 시스템 도입**: JWT 기반 사용자 인증
- **캐싱 시스템**: Redis를 통한 성능 향상
- **배치 처리**: 대량 템플릿 생성 지원

### 2. 장기 로드맵
- **마이크로서비스 분리**: AI 서비스 별도 분리
- **실시간 처리**: WebSocket 기반 실시간 알림
- **A/B 테스팅**: 템플릿 품질 개선을 위한 실험
- **자동 스케일링**: Kubernetes 기반 컨테이너 오케스트레이션

---

이 아키텍처는 확장성, 유지보수성, 성능을 고려하여 설계되었으며, 비즈니스 요구사항의 변화에 따라 지속적으로 발전시켜 나갈 계획입니다.