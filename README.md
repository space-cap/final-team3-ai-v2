# 카카오 알림톡 템플릿 AI 생성 시스템

카카오 알림톡 정책을 완전히 준수하는 고품질 템플릿을 자동으로 생성하는 AI 시스템입니다.

## 📋 프로젝트 개요

### 프로젝트 주제
카카오 알림톡 템플릿 자동 생성 AI 서비스 개발

### 제작 배경
소상공인들이 카카오 알림톡을 활용한 고객 관리를 시도할 때 가장 큰 어려움 중 하나는 까다로운 템플릿 승인 정책입니다. 수십 페이지에 달하는 가이드라인을 일일이 숙지하고 준수하기 어렵기 때문에, 많은 소상공인이 메시지 작성 단계에서부터 포기하거나 정책 위반으로 반려되는 경험을 합니다. 이는 소상공인의 효과적인 마케팅 활동을 방해하는 주요 진입 장벽이 됩니다.

본 프로젝트는 이 문제를 해결하기 위해, 사용자가 원하는 메시지 내용을 입력하면 AI가 카카오 알림톡 정책에 완벽하게 부합하는 템플릿을 자동으로 생성해주는 서비스를 개발하고자 합니다. 이를 통해 소상공인은 복잡한 정책을 고민할 필요 없이, 쉽고 빠르게 템플릿을 만들어 승인받고 마케팅에 활용할 수 있게 됩니다.

## 🚀 주요 기능

### 핵심 기능
- **AI 기반 템플릿 생성**: GPT-4를 활용한 고품질 알림톡 템플릿 자동 생성
- **정책 준수 검증**: 카카오 알림톡 정책을 실시간으로 검증하고 준수 여부 확인
- **RAG 시스템**: 벡터 데이터베이스 기반 정책 문서 검색 및 활용
- **세션 기반 대화**: 사용자별 세션 관리 및 대화 히스토리 보존
- **템플릿 분석**: 생성된 템플릿의 품질 분석 및 개선 제안
- **피드백 시스템**: 사용자 피드백을 통한 지속적인 품질 개선

### AI 에이전트 & 도구
- **TemplateGenerationAgent**: 템플릿 생성 전문 에이전트
- **PolicyComplianceAgent**: 정책 준수 검증 전문 에이전트
- **전문 도구들**: 템플릿 검증, 정책 확인, 변수 추출, 위반 탐지 등

## 🛠 기술 스택

### AI & 머신러닝
- **Python 3.13**: 최신 Python 버전
- **OpenAI GPT-4**: 고성능 언어 모델
- **LangChain**: AI 애플리케이션 프레임워크
- **LangGraph**: 복잡한 AI 워크플로우 관리
- **Chroma**: 벡터 데이터베이스

### 웹 프레임워크
- **FastAPI**: 고성능 웹 API 프레임워크
- **SQLAlchemy**: ORM 및 데이터베이스 관리
- **Pydantic**: 데이터 검증 및 직렬화

### 데이터베이스
- **MySQL 8.4**: 메인 데이터베이스
- **Chroma**: 벡터 임베딩 저장소

## 📁 프로젝트 구조

```
final-team3-ai-v2/
├── app/                          # 메인 애플리케이션
│   ├── agents/                   # AI 에이전트
│   │   ├── template_agent.py     # 템플릿 생성 에이전트
│   │   └── policy_agent.py       # 정책 준수 에이전트
│   ├── api/                      # API 엔드포인트
│   │   ├── endpoints.py          # REST API 엔드포인트
│   │   └── schemas.py            # 요청/응답 스키마
│   ├── models/                   # 데이터베이스 모델
│   │   ├── sessions.py           # 세션 모델
│   │   ├── queries.py            # 질의 모델
│   │   ├── templates.py          # 템플릿 모델
│   │   └── prompts.py            # 프롬프트 모델
│   ├── services/                 # 비즈니스 로직
│   │   ├── rag_service.py        # RAG 시스템
│   │   └── vector_store.py       # 벡터 저장소 관리
│   └── tools/                    # AI 도구
│       ├── template_tools.py     # 템플릿 관련 도구
│       └── policy_tools.py       # 정책 관련 도구
├── config/                       # 설정 파일
│   └── database.py               # 데이터베이스 설정
├── data/                         # 데이터 파일
│   └── cleaned_policies/         # 정제된 정책 문서
├── scripts/                      # 유틸리티 스크립트
│   ├── init_db.py               # 데이터베이스 초기화
│   └── init_vectordb.py         # 벡터 DB 초기화
├── docs/                         # 문서
├── main.py                       # FastAPI 애플리케이션 진입점
├── requirements.txt              # Python 의존성
├── .env.example                  # 환경변수 예시
└── README.md                     # 프로젝트 문서
```

## 🔧 설치 및 설정

### 1. 환경 요구사항
- Python 3.13+
- MySQL 8.4+
- OpenAI API 키

### 2. 프로젝트 복제 및 가상환경 설정
```bash
git clone <repository-url>
cd final-team3-ai-v2

# 가상환경 생성 및 활성화 (Windows)
python -m venv venv
venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 3. 환경 변수 설정
```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집 (필요한 값들 설정)
```

주요 환경 변수:
```env
# OpenAI 설정
OPENAI_API_KEY=your_openai_api_key

# 데이터베이스 설정
LOCAL_DB_HOST=localhost
LOCAL_DB_USER=steve
LOCAL_DB_PASSWORD=doolman
LOCAL_DB_NAME=alimtalk_ai_v2

# 애플리케이션 설정
APP_HOST=0.0.0.0
APP_PORT=8000
APP_DEBUG=True
```

### 4. 데이터베이스 설정
```bash
# MySQL 데이터베이스 생성
mysql -u root -p
CREATE DATABASE alimtalk_ai_v2;

# 데이터베이스 스키마 초기화
python scripts/init_db.py

# 벡터 데이터베이스 초기화
python scripts/init_vectordb.py
```

### 5. 애플리케이션 실행
```bash
# 개발 서버 실행
python main.py

# 또는
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 📚 API 문서

애플리케이션 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🔗 주요 API 엔드포인트

### 세션 관리
- `POST /api/v1/sessions` - 새 세션 생성
- `GET /api/v1/sessions/{session_id}` - 세션 정보 조회

### 템플릿 생성
- `POST /api/v1/templates/generate` - AI 템플릿 생성
- `GET /api/v1/templates` - 템플릿 목록 조회
- `POST /api/v1/templates/feedback` - 템플릿 피드백 제출

### 정책 관련
- `POST /api/v1/query` - 정책 관련 질의응답
- `POST /api/v1/policies/search` - 정책 문서 검색

### 시스템
- `GET /api/v1/health` - 시스템 상태 확인

## 💡 사용 예시

### 1. 세션 생성
```python
import requests

# 세션 생성
response = requests.post("http://localhost:8000/api/v1/sessions", json={
    "user_id": "user123",
    "session_name": "전자상거래 템플릿 생성",
    "session_description": "주문 확인 알림톡 템플릿 생성"
})

session_data = response.json()
session_id = session_data["session_id"]
```

### 2. 템플릿 생성
```python
# 템플릿 생성 요청
response = requests.post("http://localhost:8000/api/v1/templates/generate", json={
    "session_id": session_id,
    "user_id": "user123",
    "query_text": "온라인 쇼핑몰 주문 확인 알림톡 템플릿을 만들어주세요",
    "business_type": "전자상거래",
    "template_type": "주문확인"
})

template_data = response.json()
print(template_data["template_content"])
```

## 🔍 AI 에이전트 활용

### TemplateGenerationAgent
카카오 알림톡 정책을 준수하는 고품질 템플릿을 자동으로 생성합니다.

```python
from app.agents.template_agent import template_generation_agent

result = template_generation_agent.generate_template(
    user_request="배송 완료 알림 템플릿 생성",
    business_type="전자상거래",
    template_type="배송알림"
)
```

### PolicyComplianceAgent
템플릿의 정책 준수 여부를 상세히 분석하고 개선안을 제시합니다.

```python
from app.agents.policy_agent import policy_compliance_agent

analysis = policy_compliance_agent.analyze_compliance(
    template_content="생성된 템플릿 내용",
    business_type="전자상거래"
)
```

## 🛠 AI 도구 활용

시스템에는 다양한 전문 AI 도구들이 포함되어 있습니다:

### 템플릿 관련 도구
- **TemplateValidatorTool**: 템플릿 기본 유효성 검증
- **PolicyCheckerTool**: 정책 문서 검색 및 확인
- **VariableExtractorTool**: 변수 추출 및 분석
- **BusinessTypeSuggestorTool**: 비즈니스 유형 제안

### 정책 관련 도구
- **PolicyRuleTool**: 정책 규칙 조회
- **ComplianceCheckerTool**: 종합 준수 검사
- **ViolationDetectorTool**: 정책 위반 탐지
- **ImprovementSuggestorTool**: 개선 방안 제시

## 🗃 데이터베이스 스키마

### 주요 테이블
- **sessions**: 사용자 세션 정보
- **queries**: 사용자 질의 기록
- **templates**: 생성된 템플릿 정보
- **prompts**: 시스템 프롬프트 관리

자세한 스키마 정보는 `app/models/` 디렉토리의 파일들을 참조하세요.

## 📊 모니터링 및 로깅

시스템은 포괄적인 로깅과 모니터링 기능을 제공합니다:

- **요청/응답 로깅**: 모든 API 요청과 응답을 기록
- **처리 시간 측정**: 각 작업의 성능 지표 수집
- **오류 추적**: 상세한 오류 정보 및 스택 트레이스
- **헬스체크**: 시스템 구성요소 상태 모니터링

## 🔒 보안 고려사항

- **환경 변수**: 민감한 정보는 .env 파일로 관리
- **CORS 설정**: 운영환경에서는 적절한 도메인 제한 필요
- **API 키 보호**: OpenAI API 키 등 외부 서비스 키 보호
- **입력 검증**: Pydantic을 통한 엄격한 입력 검증

## 📈 성능 최적화

- **비동기 처리**: FastAPI의 async/await 활용
- **커넥션 풀링**: SQLAlchemy 커넥션 풀 관리
- **벡터 검색 최적화**: Chroma 인덱싱 및 검색 성능 최적화
- **캐싱**: 자주 사용되는 정책 정보 캐싱

## 🤝 기여 방법

1. 이 저장소를 포크합니다
2. 새로운 기능 브랜치를 생성합니다 (`git checkout -b feature/amazing-feature`)
3. 변경사항을 커밋합니다 (`git commit -m 'Add amazing feature'`)
4. 브랜치에 푸시합니다 (`git push origin feature/amazing-feature`)
5. Pull Request를 생성합니다

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 🆘 지원 및 문의

문제가 발생하거나 질문이 있으시면 다음을 통해 문의해주세요:

- **GitHub Issues**: 버그 리포트 및 기능 요청
- **Email**: 개발팀 연락처
- **Documentation**: `/docs` 디렉토리의 상세 문서

## 📋 버전 기록

### v1.0.0 (2024-01-01)
- 초기 릴리스
- AI 기반 템플릿 생성 기능
- 정책 준수 검증 시스템
- RAG 기반 정책 문서 검색
- 세션 기반 사용자 관리
- REST API 제공

---

**🤖 AI로 생성된 고품질 카카오 알림톡 템플릿으로 비즈니스 효율성을 높이세요!**
