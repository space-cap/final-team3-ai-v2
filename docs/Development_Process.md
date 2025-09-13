# 개발 과정 문서

이 문서는 Claude AI가 카카오 알림톡 템플릿 AI 생성 시스템을 어떻게 설계하고 구현했는지에 대한 상세한 과정을 기록합니다.

## 📋 프로젝트 진행 개요

### 초기 상황
- 사용자가 이미 `data/policies` 디렉토리에 정책 문서들을 정리해놓은 상태
- 문서들이 GitBook 형식에서 일반 마크다운으로 정제 완료 (`data/cleaned_policies`)
- 사용자 요구사항: Python 3.13, OpenAI API, LangChain, 에이전트, 도구, RAG, LangGraph, Chroma, FastAPI, MySQL 8.4 사용

## 🔄 단계별 개발 과정

### 1단계: 프로젝트 구조 설계 및 폴더 생성

**작업 내용:**
```
final-team3-ai-v2/
├── app/                     # 메인 애플리케이션
│   ├── agents/             # AI 에이전트
│   ├── api/                # API 엔드포인트
│   ├── models/             # 데이터베이스 모델
│   ├── services/           # 비즈니스 로직
│   └── tools/              # AI 도구
├── config/                 # 설정 파일
├── scripts/                # 유틸리티 스크립트
└── docs/                   # 문서
```

**설계 원칙:**
- 관심사 분리 (Separation of Concerns)
- 계층형 아키텍처 (Layered Architecture)
- 모듈화와 재사용성

### 2단계: 환경 설정 파일 생성

**작업한 파일들:**
1. **`.env.example`** - 환경변수 템플릿
```env
# OpenAI 설정
OPENAI_API_KEY=your_openai_api_key_here

# 데이터베이스 설정 (로컬 개발)
LOCAL_DB_HOST=localhost
LOCAL_DB_USER=steve
LOCAL_DB_PASSWORD=doolman
LOCAL_DB_NAME=alimtalk_ai_v2

# 애플리케이션 설정
APP_HOST=0.0.0.0
APP_PORT=8000
APP_DEBUG=True
```

2. **`requirements.txt`** - Python 의존성 패키지
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
mysql-connector-python==8.2.0
python-dotenv==1.0.0
pydantic==2.5.0
langchain==0.0.348
langchain-openai==0.0.2
langchain-community==0.0.10
openai==1.3.8
chromadb==0.4.18
numpy==1.24.4
```

**고려사항:**
- 최신 안정 버전 선택
- 윈도우 환경 호환성 확인
- 의존성 충돌 방지

### 3단계: MySQL 데이터베이스 스키마 설계

**설계 접근법:**
1. **도메인 모델링**: 세션, 질의, 템플릿, 프롬프트 엔티티 식별
2. **관계 설정**: 외래키와 인덱스 설계
3. **SQLAlchemy ORM 적용**: 코드 우선 접근법

**구현한 모델들:**
- **Session**: 사용자 세션 관리
- **Query**: 사용자 질의 추적
- **Template**: 생성된 템플릿 저장
- **Prompt**: 시스템 프롬프트 관리

**핵심 설계 결정:**
```python
# UUID를 사용한 세션 ID (보안 강화)
session_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

# Enum을 사용한 상태 관리 (타입 안정성)
status = Column(Enum(QueryStatus), default=QueryStatus.PENDING)

# 성능을 위한 인덱스 설계
Index('idx_user_sessions', 'user_id', 'is_active')
```

### 4단계: Chroma 벡터 데이터베이스 설정

**구현 전략:**
1. **문서 처리 파이프라인** 설계
2. **청킹 전략** 결정 (1000자 단위, 200자 오버랩)
3. **임베딩 모델** 선택 (OpenAI text-embedding-ada-002)

**핵심 구현:**
```python
class VectorStoreService:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        
    def initialize_from_documents(self, documents_path: str):
        # 1. 문서 로드 및 정제
        # 2. 청킹 처리
        # 3. 임베딩 생성
        # 4. 벡터 저장소에 저장
```

**최적화 기법:**
- 배치 처리로 임베딩 생성 효율화
- 메타데이터를 활용한 필터링 기능
- 컬렉션별 문서 관리

### 5단계: LangChain 기반 RAG 시스템 구현

**RAG 아키텍처 설계:**
```
Query → Vector Search → Context Compression → LLM Generation → Response
```

**핵심 구성 요소:**
1. **검색기 (Retriever)**: 관련 문서 검색
2. **압축기 (Compressor)**: 컨텍스트 최적화
3. **생성기 (Generator)**: 최종 응답 생성

**구현한 서비스들:**
- **RAGService**: 기본 RAG 기능
- **TemplateRAGService**: 템플릿 생성 특화
- **PolicyRAGService**: 정책 질의 특화

**프롬프트 엔지니어링:**
```python
TEMPLATE_GENERATION_PROMPT = """
당신은 카카오 알림톡 템플릿 생성 전문가입니다.

다음 정책 정보를 참고하여 템플릿을 생성하세요:
{context}

사용자 요청: {user_request}
비즈니스 유형: {business_type}

템플릿 생성 시 반드시 지켜야 할 규칙:
1. 1,000자 이하로 작성
2. 변수는 40개 이하, #{변수명} 형식 사용
3. 광고성 표현 금지
4. 정보성 내용으로 작성

템플릿:
"""
```

### 6단계: FastAPI 서버 및 엔드포인트 구현

**API 설계 원칙:**
- RESTful 설계 패턴
- Pydantic을 통한 엄격한 데이터 검증
- 일관된 응답 형식

**구현한 엔드포인트:**
1. **세션 관리**: `POST /api/v1/sessions`
2. **템플릿 생성**: `POST /api/v1/templates/generate`
3. **정책 질의**: `POST /api/v1/query`
4. **템플릿 목록**: `GET /api/v1/templates`
5. **시스템 헬스**: `GET /api/v1/health`

**미들웨어 및 예외 처리:**
```python
# 요청 로깅 미들웨어
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    logger.info(f"📨 {request.method} {request.url.path}")
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"📤 {response.status_code} ({process_time:.3f}s)")
    return response

# 전역 예외 처리
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"❌ Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(status_code=500, content={...})
```

### 7단계: TemplateGenerationAgent 구현

**에이전트 설계 철학:**
- 전문성: 템플릿 생성에 특화
- 자율성: 최소한의 감독으로 동작
- 적응성: 다양한 비즈니스 유형 대응

**핵심 구현:**
```python
class TemplateGenerationAgent:
    def __init__(self, llm=None):
        self.llm = llm or ChatOpenAI(model="gpt-4", temperature=0.2)
        self.tools = self._initialize_tools()
        self.agent = create_openai_functions_agent(...)
        
    def generate_template(self, user_request, business_type, template_type):
        # 1. 사용자 요청 분석
        # 2. 관련 정책 검색 (RAG)
        # 3. 초안 템플릿 생성
        # 4. 정책 준수 검증
        # 5. 품질 개선
        # 6. 최종 템플릿 반환
```

**도구 통합:**
- TemplateValidatorTool
- PolicyCheckerTool  
- VariableExtractorTool
- BusinessTypeSuggestorTool

### 8단계: PolicyComplianceAgent 구현

**검증 전략:**
- 계층적 검증: 기본 → 고급 → 비즈니스 특화
- 심각도 분류: Critical, Major, Minor
- 개선 방안 제시: 구체적이고 실행 가능한 제안

**구현 아키텍처:**
```python
class PolicyComplianceAgent:
    def analyze_compliance(self, template_content, business_type):
        # 1. 기본 분석 (길이, 변수 개수)
        # 2. 에이전트 기반 상세 분석
        # 3. 위반 사항 구조화
        # 4. 개선 제안 생성
        # 5. 최종 점수 산출
```

**정책 규칙 데이터베이스:**
```python
policy_rules = {
    "length_limit": {"max_characters": 1000},
    "variable_limit": {"max_variables": 40, "format": "#{변수명}"},
    "forbidden_content": {
        "advertising": ["광고", "홍보", "할인", "무료"],
        "illegal": ["도박", "사행성", "불법"],
        "harmful": ["성인", "폭력", "혐오"]
    }
}
```

### 9단계: AI 도구(Tools) 구현

**도구 설계 원칙:**
- 단일 책임: 각 도구는 하나의 명확한 기능
- 조합 가능성: 에이전트가 필요에 따라 조합 사용
- 오류 처리: 견고한 예외 처리

**구현한 도구들:**

#### 템플릿 관련 도구 (template_tools.py)
1. **TemplateValidatorTool**: 기본 유효성 검증
2. **PolicyCheckerTool**: 정책 문서 검색
3. **VariableExtractorTool**: 변수 추출 및 분석
4. **BusinessTypeSuggestorTool**: 비즈니스 유형 추천

#### 정책 관련 도구 (policy_tools.py)
1. **PolicyRuleTool**: 정책 규칙 조회
2. **ComplianceCheckerTool**: 종합 준수 검사
3. **ViolationDetectorTool**: 위반 사항 탐지
4. **ImprovementSuggestorTool**: 개선 방안 제시

**도구 구현 예시:**
```python
class TemplateValidatorTool(BaseTool):
    name = "template_validator"
    description = "카카오 알림톡 템플릿의 기본적인 유효성을 검증합니다."
    
    def _run(self, template_content: str, business_type: Optional[str] = None):
        # 1. 길이 검증
        # 2. 변수 형식 검증
        # 3. 기본 구조 검사
        # 4. 비즈니스 특화 검증
        return json.dumps(validation_result, ensure_ascii=False)
```

### 10단계: 문서 작성

**문서화 전략:**
- 사용자 관점: README.md (설치, 사용법, 예시)
- 개발자 관점: API 가이드, 아키텍처 문서
- 운영 관점: 배포, 모니터링 가이드

**작성한 문서들:**
1. **README.md**: 프로젝트 전체 개요
2. **API_Guide.md**: 상세한 API 사용법
3. **Architecture.md**: 시스템 아키텍처 설명
4. **Development_Process.md**: 이 문서!

## 🎯 핵심 설계 결정사항

### 1. 기술 선택 이유

**LangChain 채택:**
- 에이전트와 도구 시스템의 표준화
- RAG 파이프라인의 쉬운 구축
- 다양한 LLM 모델 지원

**Chroma 선택:**
- 가벼운 벡터 데이터베이스
- Python 네이티브 지원
- 로컬 개발에 적합

**FastAPI 사용:**
- 자동 API 문서 생성
- 타입 힌팅 기반 검증
- 고성능 비동기 처리

### 2. 아키텍처 패턴

**에이전트 중심 설계:**
```
User Request → Agent Router → Specialized Agent → Tools → Response
```

**계층형 아키텍처:**
```
Presentation Layer (FastAPI)
    ↓
Business Logic Layer (Agents, Services)
    ↓
Data Layer (MySQL, Chroma)
```

### 3. 데이터 모델링

**정규화 vs 비정규화:**
- 핵심 엔티티는 정규화 (sessions, queries, templates)
- 분석 데이터는 비정규화 (template_analysis JSON)

**인덱싱 전략:**
- 자주 검색되는 필드에 인덱스 생성
- 복합 인덱스로 쿼리 성능 최적화

## 🔧 구현 중 해결한 문제들

### 1. 한글 처리 문제
**문제**: 벡터 임베딩에서 한글 토큰화 이슈
**해결**: OpenAI 임베딩 모델 사용으로 다국어 지원

### 2. 컨텍스트 길이 제한
**문제**: LLM 입력 토큰 제한
**해결**: ContextualCompressionRetriever로 핵심 정보만 추출

### 3. 동시성 처리
**문제**: 다중 요청 시 데이터베이스 연결 이슈
**해결**: SQLAlchemy 커넥션 풀링 적용

### 4. 오류 처리
**문제**: AI 서비스 호출 실패 시 복구
**해결**: 계층적 예외 처리 및 graceful degradation

## 📊 품질 보증 방법

### 1. 코드 품질
- **타입 힌팅**: 모든 함수에 타입 어노테이션
- **문서화**: 상세한 docstring 작성
- **에러 처리**: 포괄적인 예외 처리

### 2. 데이터 품질
- **Pydantic 검증**: 입력 데이터 엄격한 검증
- **데이터베이스 제약**: 외래키, 체크 제약 조건
- **로깅**: 구조화된 로깅으로 추적성 확보

### 3. AI 품질
- **프롬프트 엔지니어링**: 명확하고 구체적인 지시
- **검증 로직**: 생성 결과의 자동 검증
- **피드백 루프**: 사용자 피드백을 통한 개선

## 🚀 성능 최적화

### 1. 데이터베이스 최적화
```python
# 커넥션 풀 설정
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=3600
)
```

### 2. AI 서비스 최적화
```python
# 배치 임베딩 처리
embeddings = embedding_model.embed_documents(texts, batch_size=100)

# 컨텍스트 압축
compressed_docs = compression_retriever.get_relevant_documents(query)
```

### 3. API 최적화
```python
# 비동기 처리
@router.post("/templates/generate")
async def generate_template(request: TemplateGenerationRequest):
    result = await rag_service.generate_template_async(...)
    return result
```

## 📈 확장성 고려사항

### 1. 코드 확장성
- **플러그인 아키텍처**: 새로운 에이전트와 도구 쉽게 추가
- **설정 기반**: 환경변수로 다양한 배포 환경 지원
- **모듈화**: 독립적인 컴포넌트로 분리

### 2. 데이터 확장성
- **파티셔닝**: 대용량 데이터 처리 준비
- **인덱싱**: 성능 최적화된 검색
- **아카이빙**: 오래된 데이터 관리 전략

### 3. 서비스 확장성
- **수평 확장**: 로드 밸런서 지원 준비
- **마이크로서비스**: 서비스별 독립 배포 가능
- **캐싱**: Redis 도입 준비

## 🎉 개발 완료 후 결과

### 구현된 기능들
✅ **AI 기반 템플릿 자동 생성**
✅ **정책 준수 실시간 검증**
✅ **사용자 세션 관리**
✅ **RESTful API 제공**
✅ **벡터 기반 정책 검색**
✅ **에이전트 시스템**
✅ **전문 도구 8개**
✅ **포괄적인 문서화**

### 기술적 성과
- **마이크로서비스 아키텍처** 구현
- **LangChain 에이전트 시스템** 구축
- **RAG 파이프라인** 구현
- **타입 안전성** 확보
- **확장 가능한 설계** 완성

### 비즈니스 가치
- **소상공인 진입 장벽 해소**
- **템플릿 승인율 향상 기대**
- **정책 준수 자동화**
- **개발 생산성 향상**

## 🔮 향후 개선 방향

### 단기 개선사항
1. **인증 시스템** 도입
2. **캐싱 시스템** 추가
3. **실시간 알림** 기능
4. **A/B 테스팅** 플랫폼

### 장기 로드맵
1. **마이크로서비스 분리**
2. **컨테이너화 및 오케스트레이션**
3. **ML 파이프라인** 구축
4. **다국어 지원** 확장

---

이 개발 과정 문서는 Claude AI가 어떻게 체계적이고 전문적으로 복잡한 AI 시스템을 구축했는지를 보여주는 실제 사례입니다. 각 단계에서의 기술적 결정, 문제 해결 과정, 그리고 최종 결과물의 품질이 AI 기반 개발의 가능성을 잘 보여준다고 생각합니다.