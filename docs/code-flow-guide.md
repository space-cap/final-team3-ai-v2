# 카카오 알림톡 템플릿 AI 생성 시스템 - 코드 흐름 가이드

## 📋 개요

이 문서는 신입 개발자가 카카오 알림톡 템플릿 AI 생성 시스템의 코드 구조와 데이터 흐름을 쉽게 이해할 수 있도록 작성되었습니다.

### 시스템 목적
- 카카오 알림톡 정책을 준수하는 템플릿 자동 생성
- RAG(Retrieval-Augmented Generation) 기반 정책 문서 검색 및 활용
- 사용자별 세션 관리 및 대화 히스토리 보존

### 핵심 기술 스택
- **Backend**: FastAPI, SQLAlchemy, MySQL 8.4
- **AI**: OpenAI GPT-4, LangChain, RAG
- **Vector DB**: FAISS (Chroma DB 대체)
- **Language**: Python 3.13

---

## 🏗️ 프로젝트 구조

```
final-team3-ai-v2/
├── main.py                    # FastAPI 메인 애플리케이션
├── app/
│   ├── api/                   # API 관련
│   │   ├── endpoints.py       # API 엔드포인트 정의
│   │   └── schemas.py         # Pydantic 스키마 모델
│   ├── models/                # 데이터베이스 모델
│   │   ├── sessions.py        # 세션 테이블
│   │   ├── queries.py         # 질의 테이블
│   │   ├── templates.py       # 템플릿 테이블
│   │   └── token_usage.py     # 토큰 사용량 추적
│   ├── services/              # 비즈니스 로직
│   │   ├── rag_service.py     # RAG 기반 AI 응답 생성
│   │   ├── vector_store_simple.py # 벡터 저장소 (FAISS)
│   │   └── token_service.py   # 토큰 사용량 추적
│   ├── agents/                # AI 에이전트
│   │   └── template_agent.py  # 템플릿 생성 AI 에이전트
│   └── tools/                 # AI 도구
├── config/                    # 설정
│   └── database.py           # 데이터베이스 설정
├── data/                      # 데이터
│   └── policies/             # 카카오 알림톡 정책 문서 (Korean)
└── scripts/                   # 유틸리티 스크립트
    └── init_vectordb.py      # 벡터DB 초기화
```

---

## 🔄 템플릿 생성 코드 흐름

### 1. API 요청 진입점
**파일**: `app/api/endpoints.py:70-187`

```python
@router.post("/templates/generate", response_model=TemplateGenerationResponse)
async def generate_template(request: TemplateGenerationRequest, db: Session = Depends(get_db)):
```

**주요 동작**:
1. 익명 세션 자동 생성 (세션 검증 제거됨)
2. 사용자 질의를 DB에 저장 (`Query` 모델)
3. RAG 서비스 호출하여 템플릿 생성
4. 생성된 템플릿 분석 및 DB 저장
5. 토큰 사용량 추적

### 2. RAG 서비스 - 핵심 비즈니스 로직
**파일**: `app/services/rag_service.py:308-339`

```python
def generate_template(self, user_request: str, business_type: Optional[str] = None,
                     template_type: Optional[str] = None, session_id: Optional[str] = None):
```

**데이터 흐름**:
```
user_request → context 구성 → generate_response() 호출 → RAG 체인 실행
```

### 3. RAG 응답 생성 프로세스
**파일**: `app/services/rag_service.py:112-194`

```python
def generate_response(self, query: str, session_id: Optional[str] = None,
                     context: Optional[Dict[str, Any]] = None) -> RAGResponse:
```

**세부 단계**:

#### 3.1 쿼리 강화
```python
enhanced_query = self._enhance_query(query, context)
# 예: "주문 확인 템플릿 만들어줘" → "주문 확인 템플릿 만들어줘 (업종: 쇼핑몰) (템플릿 유형: 기본형)"
```

#### 3.2 RAG 체인 실행
```python
result = self.rag_chain({
    "question": enhanced_query,
    "chat_history": self.memory.chat_memory.messages
})
```

**내부 동작 순서**:
1. **벡터 검색**: 정책 문서에서 관련 내용 검색
2. **컨텍스트 압축**: LLM을 이용해 관련성 높은 부분만 추출
3. **프롬프트 생성**: 정책 문서 + 사용자 요청을 결합
4. **LLM 호출**: OpenAI GPT 모델로 템플릿 생성

### 4. 벡터 검색 시스템
**파일**: `app/services/vector_store_simple.py`

#### 4.1 정책 문서 임베딩
```python
def load_and_embed_policies(self, policies_dir: str = "./data/cleaned_policies"):
```

**처리 과정**:
```
정책 MD 파일 → 청크 분할 → 임베딩 생성 → FAISS 인덱스 저장
```

#### 4.2 유사도 검색
```python
def similarity_search_with_score(self, query: str, k: int = 5):
```

**검색 과정**:
```
사용자 쿼리 → 임베딩 변환 → FAISS 유사도 검색 → 관련 정책 문서 반환
```

### 5. 템플릿 후처리
**파일**: `app/api/endpoints.py:515-603`

#### 5.1 템플릿 정제
```python
def _clean_template_content(content: str) -> str:
```

**정제 작업**:
- 마크다운 코드블록 제거
- 헤더, 볼드, 이탤릭 마크업 제거
- 변수 형식 정규화: `[변수]` → `#{변수}`
- 이모지 제거
- 공백 정리

#### 5.2 템플릿 분석
```python
def _analyze_template_content(content: str) -> Dict[str, Any]:
```

**분석 항목**:
- 변수 개수 및 목록 추출
- 글자 수 체크 (1,000자 제한)
- 품질 점수 계산
- 정책 준수 점수 계산
- 개선 제안 생성

---

## 📊 데이터베이스 흐름

### 1. 주요 테이블 관계
```
Sessions (1) ──→ (N) Queries ──→ (N) Templates
                     │
                     └──→ (N) TokenUsage
```

### 2. 템플릿 생성 시 데이터 저장 순서
1. **Session 생성**: 익명 세션 자동 생성
2. **Query 저장**: 사용자 요청 및 메타데이터
3. **Template 저장**: 생성된 템플릿 및 분석 결과
4. **TokenUsage 추적**: API 호출 비용 및 토큰 사용량

---

## 🤖 AI 에이전트 시스템

### Template Generation Agent
**파일**: `app/agents/template_agent.py`

현재 구현된 에이전트는 LangChain 기반이지만, 실제로는 RAG 서비스가 메인 로직을 담당합니다.

**에이전트 역할**:
- 사용자 요청 분석
- 정책 문서 검색
- 템플릿 생성 및 검증
- 품질 분석 및 개선 제안

---

## 🔧 주요 설정 및 환경

### 환경 변수
```env
OPENAI_API_KEY=your_openai_key
AGENT_MODEL=gpt-4o-mini
AGENT_TEMPERATURE=0.1
AGENT_MAX_TOKENS=2000
APP_DEBUG=True
```

### 데이터베이스 연결
**파일**: `config/database.py`
- MySQL 8.4 사용
- SQLAlchemy ORM
- 연결풀 관리

---

## 🚀 실행 흐름 요약

### 1. 시스템 시작
```
main.py → FastAPI 앱 생성 → 미들웨어 설정 → DB 연결 확인 → 벡터DB 로드 → API 라우터 등록
```

### 2. 템플릿 생성 요청 처리
```
POST /api/v1/templates/generate
    ↓
익명 세션 생성
    ↓
질의 DB 저장
    ↓
RAG 서비스 호출
    ↓
벡터 검색 (정책 문서)
    ↓
LLM 호출 (OpenAI GPT)
    ↓
템플릿 후처리 및 분석
    ↓
DB 저장 (템플릿, 토큰 사용량)
    ↓
응답 반환
```

### 3. 주요 응답 데이터
```json
{
  "success": true,
  "message": "템플릿이 성공적으로 생성되었습니다.",
  "template_content": "#{고객명}님의 주문이 확인되었습니다...",
  "template_analysis": {
    "template_type": "기본형",
    "character_count": 180,
    "variable_count": 3,
    "quality_score": 0.9,
    "compliance_score": 0.95
  },
  "token_metrics": {
    "total_tokens": 1250,
    "total_cost": 0.0032
  }
}
```

---

## 💡 개발 시 주의사항

### 1. 정책 준수
- 카카오 알림톡 정책 문서(`data/policies/`)를 반드시 참조
- 1,000자 제한, 변수 40개 제한 등 하드코딩된 제약사항 확인

### 2. 에러 처리
- 모든 서비스 레이어에서 예외 처리 구현
- DB 롤백 로직 포함
- 사용자 친화적 에러 메시지 제공

### 3. 토큰 비용 관리
- 모든 LLM 호출에 대해 토큰 사용량 추적
- `app/services/token_service.py`에서 비용 계산

### 4. 벡터DB 관리
- FAISS 인덱스 파일 관리 주의
- 정책 문서 업데이트 시 재임베딩 필요

---

## 🔍 디버깅 팁

### 1. 로그 확인
```python
# main.py에서 로깅 레벨 설정
logging.basicConfig(level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')))
```

### 2. API 문서 활용
- 개발 서버 실행 후 `http://localhost:8000/docs` 접속
- 실제 API 테스트 가능

### 3. 헬스체크 엔드포인트
```
GET /api/v1/health
```
- DB 연결, 벡터DB, AI 모델 상태 확인 가능

---

이 가이드를 통해 시스템의 전체적인 흐름을 파악하고, 각 컴포넌트의 역할과 상호작용을 이해할 수 있습니다. 추가 질문이나 특정 부분에 대한 자세한 설명이 필요하면 언제든 문의하세요.