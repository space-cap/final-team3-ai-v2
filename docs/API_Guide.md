# API 가이드

카카오 알림톡 템플릿 AI 생성 시스템의 API 사용법을 상세히 설명합니다.

## 기본 정보

- **Base URL**: `http://localhost:8000`
- **API 버전**: v1
- **Content-Type**: `application/json`
- **문서**: 
  - Swagger UI: `http://localhost:8000/docs`
  - ReDoc: `http://localhost:8000/redoc`

## 인증

현재 버전에서는 별도의 인증이 필요하지 않습니다. 향후 버전에서 API 키 또는 토큰 기반 인증이 추가될 예정입니다.

## 공통 응답 형식

모든 API 응답은 다음과 같은 기본 구조를 따릅니다:

```json
{
  "success": true,
  "message": "요청이 성공적으로 처리되었습니다.",
  "timestamp": "2024-01-01T12:00:00Z",
  // 추가 데이터...
}
```

### 오류 응답

```json
{
  "success": false,
  "message": "오류 메시지",
  "error_code": "ERROR_CODE",
  "error_details": "상세 오류 정보",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## API 엔드포인트

### 1. 세션 관리

#### 1.1 세션 생성

새로운 사용자 세션을 생성합니다.

**요청**
```http
POST /api/v1/sessions
Content-Type: application/json

{
  "user_id": "user123",
  "session_name": "전자상거래 템플릿 생성",
  "session_description": "주문 확인 알림톡 템플릿 생성",
  "client_info": {
    "browser": "Chrome",
    "version": "120.0",
    "os": "Windows"
  }
}
```

**응답**
```json
{
  "success": true,
  "message": "세션이 성공적으로 생성되었습니다.",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user123",
  "session_name": "전자상거래 템플릿 생성",
  "is_active": true,
  "created_at": "2024-01-01T12:00:00Z",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 2. 템플릿 생성

#### 2.1 AI 템플릿 생성

AI를 통해 카카오 알림톡 템플릿을 생성합니다.

**요청**
```http
POST /api/v1/templates/generate
Content-Type: application/json

{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user123",
  "query_text": "온라인 쇼핑몰 주문 확인 알림톡 템플릿을 만들어주세요",
  "business_type": "전자상거래",
  "template_type": "주문확인",
  "additional_context": {
    "target_audience": "일반 고객",
    "tone": "친근함"
  }
}
```

**응답**
```json
{
  "success": true,
  "message": "템플릿이 성공적으로 생성되었습니다.",
  "query_id": 12345,
  "template_id": 67890,
  "template_content": "안녕하세요, #{customer_name}님!\n\n주문이 정상적으로 접수되었습니다.\n\n▶ 주문번호: #{order_number}\n▶ 주문일시: #{order_date}\n▶ 상품명: #{product_name}\n▶ 결제금액: #{payment_amount}원\n\n배송 준비가 완료되면 다시 안내드리겠습니다.\n\n감사합니다.",
  "template_analysis": {
    "template_type": "거래성",
    "message_type": "정보성",
    "character_count": 156,
    "variable_count": 5,
    "variables": ["customer_name", "order_number", "order_date", "product_name", "payment_amount"],
    "quality_score": 0.95,
    "compliance_score": 0.98,
    "suggestions": []
  },
  "processing_time": 2.34,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### 2.2 템플릿 목록 조회

사용자의 템플릿 목록을 조회합니다.

**요청**
```http
GET /api/v1/templates?user_id=user123&limit=20&offset=0&session_id=550e8400-e29b-41d4-a716-446655440000&business_category=전자상거래&template_type=주문확인&is_favorite=true
```

**응답**
```json
{
  "success": true,
  "message": "템플릿 목록을 성공적으로 조회했습니다.",
  "templates": [
    {
      "template_id": 67890,
      "template_name": "주문 확인 템플릿",
      "template_content": "안녕하세요, #{customer_name}님!...",
      "template_type": "거래성",
      "business_category": "전자상거래",
      "quality_score": 0.95,
      "is_favorite": true,
      "created_at": "2024-01-01T12:00:00Z"
    }
  ],
  "total_count": 1,
  "has_more": false,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### 2.3 템플릿 피드백 제출

생성된 템플릿에 대한 사용자 피드백을 제출합니다.

**요청**
```http
POST /api/v1/templates/feedback
Content-Type: application/json

{
  "template_id": 67890,
  "user_id": "user123",
  "rating": 5,
  "feedback": "매우 만족스러운 템플릿입니다. 실제로 사용해보니 승인도 빠르게 받았어요.",
  "is_favorite": true
}
```

**응답**
```json
{
  "success": true,
  "message": "피드백이 성공적으로 등록되었습니다.",
  "template_id": 67890,
  "updated": true,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 3. 정책 관련

#### 3.1 정책 질의응답

카카오 알림톡 정책에 대한 질의응답을 수행합니다.

**요청**
```http
POST /api/v1/query
Content-Type: application/json

{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user123",
  "query_text": "알림톡에서 할인 이벤트 관련 내용을 포함할 수 있나요?",
  "context": {
    "business_type": "전자상거래",
    "specific_concern": "광고성 내용"
  }
}
```

**응답**
```json
{
  "success": true,
  "message": "질의에 대한 응답이 생성되었습니다.",
  "query_id": 12346,
  "answer": "카카오 알림톡에서는 직접적인 광고성 내용은 제한됩니다. '할인', '이벤트' 등의 키워드는 사용을 피하시고, 대신 '안내', '혜택' 등의 표현을 사용하는 것이 좋습니다. 알림톡은 정보성 메시지에 중점을 두어야 합니다.",
  "source_documents": [
    {
      "source": "카카오 알림톡 가이드 v3.2",
      "content": "광고성 표현 제한 관련 내용...",
      "relevance": 0.89
    }
  ],
  "confidence_score": 0.92,
  "processing_time": 1.56,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### 3.2 정책 문서 검색

특정 키워드로 정책 문서를 검색합니다.

**요청**
```http
POST /api/v1/policies/search
Content-Type: application/json

{
  "query": "변수 사용 규칙",
  "limit": 5
}
```

**응답**
```json
{
  "success": true,
  "message": "정책 문서 검색이 완료되었습니다.",
  "query": "변수 사용 규칙",
  "documents": [
    {
      "source": "카카오 알림톡 변수 가이드",
      "content": "변수는 #{변수명} 형식으로 사용하며, 최대 40개까지 설정 가능합니다...",
      "relevance_score": 0.95,
      "metadata": {
        "section": "변수 규칙",
        "last_updated": "2024-01-01"
      }
    }
  ],
  "total_results": 5,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 4. 시스템

#### 4.1 헬스체크

시스템 상태를 확인합니다.

**요청**
```http
GET /api/v1/health
```

**응답**
```json
{
  "success": true,
  "message": "시스템이 정상적으로 동작하고 있습니다.",
  "status": {
    "database_connected": true,
    "vectordb_loaded": true,
    "vectordb_document_count": 1250,
    "ai_model_available": true,
    "uptime": 86400.5
  },
  "version": "1.0.0",
  "environment": "development",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## 오류 코드

| 코드 | 설명 |
|------|------|
| `HTTP_400` | 잘못된 요청 |
| `HTTP_404` | 리소스를 찾을 수 없음 |
| `HTTP_422` | 유효성 검증 실패 |
| `HTTP_500` | 서버 내부 오류 |
| `INTERNAL_SERVER_ERROR` | 시스템 오류 |
| `VALIDATION_ERROR` | 입력 데이터 검증 오류 |
| `DATABASE_ERROR` | 데이터베이스 오류 |
| `AI_SERVICE_ERROR` | AI 서비스 오류 |

## 사용 예시

### Python을 사용한 기본 워크플로우

```python
import requests
import json

# API 기본 URL
BASE_URL = "http://localhost:8000/api/v1"

# 1. 세션 생성
def create_session(user_id, session_name):
    response = requests.post(f"{BASE_URL}/sessions", json={
        "user_id": user_id,
        "session_name": session_name,
        "session_description": "API 테스트 세션"
    })
    return response.json()

# 2. 템플릿 생성
def generate_template(session_id, user_id, query_text, business_type):
    response = requests.post(f"{BASE_URL}/templates/generate", json={
        "session_id": session_id,
        "user_id": user_id,
        "query_text": query_text,
        "business_type": business_type,
        "template_type": "정보성"
    })
    return response.json()

# 3. 정책 질의
def query_policy(session_id, user_id, question):
    response = requests.post(f"{BASE_URL}/query", json={
        "session_id": session_id,
        "user_id": user_id,
        "query_text": question
    })
    return response.json()

# 실행 예시
if __name__ == "__main__":
    user_id = "test_user"
    
    # 세션 생성
    session_result = create_session(user_id, "테스트 세션")
    session_id = session_result["session_id"]
    print(f"세션 생성: {session_id}")
    
    # 템플릿 생성
    template_result = generate_template(
        session_id, 
        user_id, 
        "회원가입 완료 안내 메시지를 만들어주세요",
        "IT서비스"
    )
    print(f"템플릿 생성: {template_result['template_content']}")
    
    # 정책 질의
    policy_result = query_policy(
        session_id,
        user_id,
        "회원가입 축하 메시지에서 주의할 점이 있나요?"
    )
    print(f"정책 답변: {policy_result['answer']}")
```

### JavaScript/Node.js를 사용한 예시

```javascript
const axios = require('axios');

const BASE_URL = 'http://localhost:8000/api/v1';

class AlimtalkAPI {
  async createSession(userId, sessionName) {
    try {
      const response = await axios.post(`${BASE_URL}/sessions`, {
        user_id: userId,
        session_name: sessionName,
        session_description: 'JavaScript API 테스트'
      });
      return response.data;
    } catch (error) {
      console.error('세션 생성 실패:', error.response.data);
      throw error;
    }
  }

  async generateTemplate(sessionId, userId, queryText, businessType) {
    try {
      const response = await axios.post(`${BASE_URL}/templates/generate`, {
        session_id: sessionId,
        user_id: userId,
        query_text: queryText,
        business_type: businessType,
        template_type: '정보성'
      });
      return response.data;
    } catch (error) {
      console.error('템플릿 생성 실패:', error.response.data);
      throw error;
    }
  }

  async getTemplates(userId, limit = 20, offset = 0) {
    try {
      const response = await axios.get(`${BASE_URL}/templates`, {
        params: {
          user_id: userId,
          limit: limit,
          offset: offset
        }
      });
      return response.data;
    } catch (error) {
      console.error('템플릿 조회 실패:', error.response.data);
      throw error;
    }
  }
}

// 사용 예시
async function main() {
  const api = new AlimtalkAPI();
  const userId = 'js_test_user';
  
  try {
    // 세션 생성
    const session = await api.createSession(userId, 'JavaScript 테스트');
    console.log('세션 ID:', session.session_id);
    
    // 템플릿 생성
    const template = await api.generateTemplate(
      session.session_id,
      userId,
      '예약 확인 메시지를 만들어주세요',
      '서비스업'
    );
    console.log('생성된 템플릿:', template.template_content);
    
    // 템플릿 목록 조회
    const templates = await api.getTemplates(userId);
    console.log('총 템플릿 수:', templates.total_count);
    
  } catch (error) {
    console.error('API 호출 실패:', error.message);
  }
}

main();
```

## 모범 사례

### 1. 세션 관리
- 사용자별로 고유한 세션을 생성하세요
- 세션 ID는 안전하게 저장하고 재사용하세요
- 장기간 사용하지 않는 세션은 정리하세요

### 2. 에러 처리
- 항상 API 응답의 `success` 필드를 확인하세요
- 오류 발생 시 `error_code`와 `message`를 활용하세요
- 네트워크 오류에 대비해 재시도 로직을 구현하세요

### 3. 성능 최적화
- 불필요한 API 호출을 줄이세요
- 적절한 `limit`과 `offset`을 사용해 페이징을 구현하세요
- 자주 사용하는 데이터는 클라이언트에서 캐싱하세요

### 4. 보안
- API 키가 도입되면 안전하게 관리하세요
- HTTPS를 사용하세요 (운영 환경)
- 민감한 정보는 로그에 기록하지 마세요

## 문제 해결

### 일반적인 문제들

1. **연결 오류**
   - 서버가 실행 중인지 확인
   - 포트 번호가 올바른지 확인 (기본값: 8000)
   - 방화벽 설정 확인

2. **응답 지연**
   - AI 모델 처리 시간은 2-5초 정도 소요될 수 있음
   - 타임아웃 설정을 충분히 길게 설정
   - 벡터 데이터베이스 상태 확인

3. **빈 응답**
   - 요청 데이터 형식 확인
   - 필수 필드가 모두 포함되었는지 확인
   - 헬스체크 API로 시스템 상태 확인

### 디버깅 팁

- `Content-Type: application/json` 헤더 포함 확인
- 요청 본문이 유효한 JSON 형식인지 확인
- API 문서(`/docs`)를 참조하여 스키마 확인
- 개발자 도구나 로그를 통해 상세 오류 메시지 확인

---

더 자세한 정보나 지원이 필요하시면 GitHub Issues를 통해 문의해주세요.