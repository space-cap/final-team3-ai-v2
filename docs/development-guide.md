# 개발 가이드 - 카카오 알림톡 템플릿 생성 시스템

## 🏗️ 프로젝트 구조

```
final-team3-ai-v2/
├── app/
│   ├── api/
│   │   ├── endpoints.py          # API 엔드포인트 (기존 + 신규 4개)
│   │   └── schemas.py            # Pydantic 스키마 모델
│   ├── models/                   # SQLAlchemy 모델
│   ├── services/
│   │   ├── rag_service.py        # 기존 RAG 서비스
│   │   ├── template_generation_service.py  # 신규: AI 생성 서비스
│   │   ├── template_vector_store.py        # 신규: 템플릿 벡터 스토어
│   │   ├── token_service.py      # 토큰 사용량 추적
│   │   └── vector_store_simple.py         # 정책 벡터 스토어
│   └── ...
├── data/
│   ├── JJ템플릿.xlsx             # 원본 분석 데이터
│   ├── policies/                 # 카카오 정책 문서
│   ├── approved_templates.json   # 승인 템플릿 데이터
│   ├── template_patterns.json    # 패턴 데이터
│   ├── success_indicators.json   # 성공 지표
│   ├── kakao_template_vectordb_data.json  # 통합 벡터DB 데이터
│   ├── vectordb/                 # 정책 벡터DB
│   └── vectordb_templates/       # 템플릿 벡터DB
│       ├── templates/            # 템플릿 FAISS 인덱스
│       └── patterns/             # 패턴 FAISS 인덱스
├── docs/                         # 문서
├── 분석 스크립트들/               # 데이터 분석 및 전처리
└── 테스트 파일들/                 # API 테스트
```

## 🔧 핵심 컴포넌트

### 1. TemplateGenerationService

**파일**: `app/services/template_generation_service.py`

**주요 기능**:
- 승인받은 템플릿 패턴 기반 AI 생성
- 다차원 템플릿 검증
- 정책 준수도 평가
- 개선 제안 생성

**핵심 메서드**:
```python
class TemplateGenerationService:
    def generate_template(self, user_request, business_type, category_1, ...):
        """스마트 템플릿 생성"""

    def optimize_template(self, template, target_improvements):
        """기존 템플릿 최적화"""

    def _validate_template(self, template):
        """템플릿 검증 (길이, 변수, 정책준수 등)"""

    def _generate_suggestions(self, template, validation, similar_templates):
        """개선 제안 생성"""
```

### 2. TemplateVectorStoreService

**파일**: `app/services/template_vector_store.py`

**주요 기능**:
- 승인받은 템플릿 벡터 검색
- 카테고리별 패턴 분석
- 템플릿 추천 시스템

**핵심 메서드**:
```python
class TemplateVectorStoreService:
    def load_template_data(self, json_data_path):
        """JSON 데이터를 벡터DB에 로드"""

    def find_similar_templates(self, query, category_filter, k=5):
        """유사한 승인받은 템플릿 검색"""

    def find_category_patterns(self, category, k=3):
        """카테고리별 패턴 정보 검색"""

    def get_template_recommendations(self, user_input, category_1, business_type):
        """템플릿 추천 및 제안"""
```

## 🚀 설치 및 실행

### 1. 환경 설정

```bash
# 가상환경 활성화
source .venv/Scripts/activate  # Windows
# 또는 source .venv/bin/activate  # Linux/Mac

# 필요한 패키지 설치
pip install pandas openpyxl faiss-cpu requests

# 환경 변수 설정 (.env 파일)
OPENAI_API_KEY=your_openai_api_key
MYSQL_HOST=localhost
MYSQL_USER=your_username
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=your_database
```

### 2. 데이터 준비

```bash
# 1. Excel 데이터 JSON으로 변환
python create_template_json.py

# 2. 템플릿 벡터 데이터베이스 구축
python load_template_vectordb_simple.py
```

### 3. 서버 실행

```bash
# 개발 서버 실행
uvicorn main:app --reload --port 8000

# 또는 백그라운드 실행
nohup uvicorn main:app --host 0.0.0.0 --port 8000 &
```

### 4. 테스트

```bash
# API 테스트 실행
python simple_api_test.py

# 수동 테스트
curl http://localhost:8000/api/v1/health
```

## 🔍 개발 워크플로우

### 새로운 기능 추가

1. **스키마 정의** (`app/api/schemas.py`)
```python
class NewFeatureRequest(BaseModel):
    parameter1: str
    parameter2: Optional[int] = None

class NewFeatureResponse(BaseResponse):
    result: str
    metadata: Dict[str, Any]
```

2. **서비스 로직 구현** (`app/services/`)
```python
class NewFeatureService:
    def __init__(self):
        # 초기화 로직

    def process_feature(self, request_data):
        # 비즈니스 로직 구현
        return result
```

3. **API 엔드포인트 추가** (`app/api/endpoints.py`)
```python
@router.post("/new-feature", response_model=NewFeatureResponse)
async def new_feature_endpoint(request: NewFeatureRequest):
    try:
        result = new_feature_service.process_feature(request)
        return NewFeatureResponse(success=True, result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

4. **테스트 작성**
```python
def test_new_feature():
    data = {"parameter1": "test", "parameter2": 123}
    response = requests.post(f"{BASE_URL}/new-feature", json=data)
    assert response.status_code == 200
```

### 벡터 데이터베이스 업데이트

**새로운 템플릿 데이터 추가 시**:

1. 데이터 전처리
```python
# create_template_json.py 수정
# 새로운 데이터 소스 추가
new_templates = load_new_data("new_templates.xlsx")
existing_data = load_existing_data()
merged_data = merge_template_data(existing_data, new_templates)
save_json_data(merged_data)
```

2. 벡터DB 재구축
```python
# load_template_vectordb_simple.py 실행
python load_template_vectordb_simple.py
```

3. 서버 재시작으로 새로운 데이터 반영

## 🐛 디버깅 가이드

### 자주 발생하는 문제들

#### 1. 벡터DB 로드 실패
**증상**: `Templates vector store loaded` 메시지가 보이지 않음

**해결책**:
```bash
# 벡터DB 파일 확인
ls -la data/vectordb_templates/

# 재생성
python load_template_vectordb_simple.py

# 서버 재시작
```

#### 2. API 404 오류
**증상**: 새로운 엔드포인트가 404 Not Found 반환

**해결책**:
```python
# app/api/endpoints.py에서 라우터 등록 확인
from app.services.template_generation_service import template_generation_service

# main.py에서 서비스 import 확인
```

#### 3. OpenAI API 오류
**증상**: `openai.error.RateLimitError` 또는 `AuthenticationError`

**해결책**:
```bash
# API 키 확인
echo $OPENAI_API_KEY

# .env 파일 확인
cat .env | grep OPENAI

# 사용량 제한 확인 (OpenAI 대시보드)
```

#### 4. 인코딩 오류 (Windows)
**증상**: `UnicodeEncodeError: 'cp949' codec`

**해결책**:
```python
# 출력 시 이모지나 특수문자 제거
print("Success")  # ✅ 대신
print("ERROR")    # ❌ 대신
```

### 로그 분석

**주요 로그 위치**:
```bash
# 서버 콘솔 로그
uvicorn main:app --log-level debug

# SQLAlchemy 쿼리 로그
# config/database.py에서 echo=True 설정

# 커스텀 로그
# logging.getLogger(__name__) 사용
```

**유용한 로그 패턴**:
```python
import logging
logger = logging.getLogger(__name__)

# 서비스 호출 로그
logger.info(f"템플릿 생성 요청: {user_request}")

# 에러 로그
logger.error(f"템플릿 생성 실패: {str(e)}", exc_info=True)

# 성능 로그
start_time = time.time()
# ... 처리 ...
logger.info(f"처리 시간: {time.time() - start_time:.2f}초")
```

## 🧪 테스트 전략

### Unit Tests
```python
import pytest
from app.services.template_generation_service import TemplateGenerationService

class TestTemplateGeneration:
    def setup_method(self):
        self.service = TemplateGenerationService()

    def test_template_validation(self):
        template = "안녕하세요 #{고객성명}님, 주문이 완료되었습니다."
        validation = self.service._validate_template(template)

        assert validation['has_greeting'] == True
        assert validation['variable_count'] == 1
        assert validation['compliance_score'] > 70
```

### Integration Tests
```python
def test_api_integration():
    # 전체 API 플로우 테스트
    data = {"user_request": "테스트 메시지"}
    response = requests.post("/api/v1/templates/smart-generate", json=data)

    assert response.status_code == 200
    result = response.json()
    assert result['success'] == True
    assert len(result['generated_template']) > 0
```

### Performance Tests
```python
import time

def test_generation_performance():
    start_time = time.time()

    # 템플릿 생성 100회 실행
    for i in range(100):
        generate_template("테스트 요청 " + str(i))

    elapsed = time.time() - start_time
    assert elapsed < 30  # 30초 이내 완료
    print(f"평균 생성 시간: {elapsed/100:.2f}초")
```

## 📊 모니터링 및 메트릭

### 시스템 헬스체크
```python
# /api/v1/health 엔드포인트 활용
health_data = {
    "database_connected": True,
    "vectordb_loaded": True,
    "templates_count": 898,
    "ai_model_available": True,
    "uptime": 3600  # 초
}
```

### 비즈니스 메트릭
```python
# 템플릿 생성 성공률
success_rate = successful_generations / total_generations

# 평균 정책 준수도
avg_compliance = sum(compliance_scores) / len(compliance_scores)

# 사용자 만족도 (피드백 기반)
satisfaction_rate = positive_feedback / total_feedback
```

### 성능 메트릭
```python
# 응답 시간
response_times = []  # API 응답 시간 수집

# 토큰 사용량
total_tokens_used = sum(token_metrics)

# 벡터 검색 속도
vector_search_times = []  # 검색 시간 수집
```

## 🔒 보안 고려사항

### 입력 검증
```python
from pydantic import BaseModel, validator

class TemplateRequest(BaseModel):
    user_request: str

    @validator('user_request')
    def validate_request(cls, v):
        if len(v) > 1000:
            raise ValueError('요청이 너무 길습니다')
        return v.strip()
```

### API 보안
```python
# Rate Limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/templates/smart-generate")
@limiter.limit("10/minute")
async def generate_template(request: Request, ...):
    # API 구현
```

### 데이터 보안
- 개인정보 마스킹: `#{개인정보}` → `#{고객성명}`
- 로그에서 민감정보 제외
- 데이터베이스 암호화 (TDE)

## 📞 운영 가이드

### 배포 체크리스트
- [ ] 환경 변수 설정 확인
- [ ] 데이터베이스 마이그레이션
- [ ] 벡터DB 데이터 동기화
- [ ] API 엔드포인트 테스트
- [ ] 모니터링 대시보드 설정
- [ ] 백업 및 복구 테스트

### 장애 대응
1. **서비스 중단 시**: Health check로 상태 확인
2. **API 오류 증가 시**: 로그 분석 및 에러율 모니터링
3. **벡터DB 문제 시**: 재구축 또는 백업에서 복원
4. **OpenAI API 장애 시**: 캐시된 응답 또는 대체 모델 사용

---

### 📚 참고 자료

- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [LangChain 가이드](https://python.langchain.com/docs/get_started/introduction)
- [FAISS 벡터 검색](https://faiss.ai/)
- [OpenAI API 문서](https://platform.openai.com/docs)

**문서 버전**: v1.0
**마지막 업데이트**: 2025-09-14