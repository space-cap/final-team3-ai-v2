# API 문서 - 카카오 알림톡 템플릿 생성 시스템

## 📋 개요

카카오 알림톡 템플릿 AI 생성 시스템의 API 엔드포인트 문서입니다.
기존 정책 RAG 시스템에 새롭게 추가된 4개의 스마트 템플릿 생성 API를 포함합니다.

**Base URL**: `http://localhost:8000/api/v1`

## 🆕 신규 추가된 API 엔드포인트

### 1. 스마트 템플릿 생성

**Endpoint**: `POST /templates/smart-generate`

승인받은 템플릿 패턴을 학습하여 정책을 준수하는 고품질 템플릿을 자동 생성합니다.

#### 요청 (Request)
```json
{
  "user_request": "예약 확인 메시지를 만들어주세요",
  "business_type": "서비스업",
  "category_1": "예약",
  "category_2": "예약확인",
  "target_length": 120,
  "include_variables": ["고객성명", "예약날짜", "예약시간"],
  "context": {}
}
```

#### 응답 (Response)
```json
{
  "success": true,
  "message": "스마트 템플릿이 성공적으로 생성되었습니다.",
  "timestamp": "2025-09-14T18:30:00.000Z",
  "generated_template": "안녕하세요 #{고객성명}님,\n예약해주신 #{서비스명}에 대해 안내드립니다.\n\n예약일시: #{예약날짜} #{예약시간}\n장소: #{장소}\n\n예약 변경이나 취소를 원하시면 아래 버튼을 눌러주세요.\n감사합니다!",
  "validation": {
    "length": 118,
    "length_appropriate": true,
    "has_greeting": true,
    "variables": ["고객성명", "서비스명", "예약날짜", "예약시간", "장소"],
    "variable_count": 5,
    "has_politeness": true,
    "potential_ad_content": false,
    "has_contact_info": false,
    "sentence_count": 4,
    "compliance_score": 85.7
  },
  "suggestions": [
    "템플릿이 적절한 길이입니다.",
    "#{연락처} 변수를 추가하면 더 유용할 수 있습니다.",
    "정책 준수도가 우수합니다!"
  ],
  "reference_data": {
    "similar_templates": 3,
    "category_patterns": 2,
    "policy_references": 5
  },
  "metadata": {
    "generated_at": "2025-09-14T18:30:00.000Z",
    "business_type": "서비스업",
    "category_1": "예약",
    "category_2": "예약확인",
    "user_request": "예약 확인 메시지를 만들어주세요"
  }
}
```

#### 파라미터 설명
- `user_request` (required): 생성하고 싶은 템플릿에 대한 요청사항
- `business_type` (optional): 업무 유형 (서비스, 상품, 예약 등)
- `category_1` (optional): 1차 분류 (서비스이용, 상품, 예약, 결제 등)
- `category_2` (optional): 2차 분류 (이용안내/정보, 방문안내, 결제완료 등)
- `target_length` (optional): 목표 길이 (50-300자)
- `include_variables` (optional): 포함할 변수 목록
- `context` (optional): 추가 컨텍스트 정보

---

### 2. 템플릿 최적화

**Endpoint**: `POST /templates/optimize`

기존 템플릿을 정책 준수도와 품질을 향상시키도록 최적화합니다.

#### 요청 (Request)
```json
{
  "template": "고객님 주문하신 상품 준비되었습니다.",
  "target_improvements": ["길이 증가", "변수 추가", "정중한 표현"]
}
```

#### 응답 (Response)
```json
{
  "success": true,
  "message": "템플릿이 성공적으로 최적화되었습니다.",
  "timestamp": "2025-09-14T18:30:00.000Z",
  "original_template": "고객님 주문하신 상품 준비되었습니다.",
  "optimized_template": "안녕하세요 #{고객성명}님,\n주문해주신 #{상품명}이 준비완료되어 안내드립니다.\n\n주문번호: #{주문번호}\n픽업 또는 배송이 가능합니다.\n\n감사합니다!",
  "original_validation": {
    "length": 21,
    "compliance_score": 45.0,
    "has_greeting": false,
    "variable_count": 0
  },
  "optimized_validation": {
    "length": 89,
    "compliance_score": 85.7,
    "has_greeting": true,
    "variable_count": 3
  },
  "improvement": {
    "compliance_score_change": 40.7,
    "length_change": 68,
    "variable_count_change": 3
  }
}
```

#### 파라미터 설명
- `template` (required): 최적화할 원본 템플릿
- `target_improvements` (optional): 개선 목표 사항 리스트

---

### 3. 유사 템플릿 검색

**Endpoint**: `POST /templates/similar-search`

승인받은 템플릿 중에서 사용자 요청과 유사한 템플릿을 검색합니다.

#### 요청 (Request)
```json
{
  "query": "주문 완료 안내 메시지",
  "category_filter": "서비스이용",
  "business_type_filter": "상품",
  "limit": 5
}
```

#### 응답 (Response)
```json
{
  "success": true,
  "message": "3개의 유사한 템플릿을 찾았습니다.",
  "timestamp": "2025-09-14T18:30:00.000Z",
  "query": "주문 완료 안내 메시지",
  "similar_templates": [
    {
      "template_id": "template_001",
      "text": "안녕하세요 #{고객성명}님, 주문하신 #{상품명}이 배송 준비 중입니다...",
      "category_1": "서비스이용",
      "category_2": "이용안내/정보",
      "business_type": "상품",
      "variables": ["고객성명", "상품명", "주문번호"],
      "button": "자세히 확인하기",
      "length": 95
    }
  ],
  "category_patterns": [
    {
      "category": "서비스이용",
      "template_count": 287,
      "common_variables": {
        "고객성명": 138,
        "업체명": 48,
        "날짜": 41
      },
      "characteristic_words": {
        "주문": 51,
        "배송": 27,
        "완료": 17
      },
      "common_buttons": {
        "자세히 확인하기": 200,
        "상세 확인": 31
      },
      "avg_length": 110,
      "success_indicators": {
        "greeting_usage": 0.84,
        "variable_usage": 2.1,
        "button_usage": 0.95
      }
    }
  ],
  "suggestions": [
    "권장 변수: #{고객성명}, #{주문번호}, #{상품명}",
    "추천 버튼: 자세히 확인하기",
    "권장 길이: 110자 내외"
  ]
}
```

#### 파라미터 설명
- `query` (required): 검색할 템플릿 내용
- `category_filter` (optional): 카테고리로 필터링
- `business_type_filter` (optional): 업무 유형으로 필터링
- `limit` (optional): 결과 개수 (1-20, 기본값: 5)

---

### 4. 벡터 스토어 정보 조회

**Endpoint**: `GET /templates/vector-store-info`

템플릿 벡터 데이터베이스의 상태와 정보를 조회합니다.

#### 요청 (Request)
```
GET /api/v1/templates/vector-store-info
```

#### 응답 (Response)
```json
{
  "success": true,
  "message": "템플릿 벡터 스토어 정보를 성공적으로 조회했습니다.",
  "timestamp": "2025-09-14T18:30:00.000Z",
  "templates_count": 898,
  "patterns_count": 9,
  "status": "available",
  "persist_directory": "./data/vectordb_templates"
}
```

## 🔍 기존 API 엔드포인트 (유지)

### 템플릿 생성 (기존)
**Endpoint**: `POST /templates/generate`
- 기본적인 RAG 기반 템플릿 생성
- 정책 문서 기반 검증

### 정책 검색
**Endpoint**: `POST /policies/search`
- 카카오 알림톡 정책 문서 검색

### 헬스체크
**Endpoint**: `GET /health`
- 시스템 전체 상태 확인

## 🚨 에러 응답

모든 API는 다음과 같은 형식의 에러 응답을 반환합니다:

```json
{
  "success": false,
  "message": "에러 메시지",
  "timestamp": "2025-09-14T18:30:00.000Z",
  "error_code": "ERROR_CODE",
  "error_details": "상세 에러 정보 (개발 환경에서만)"
}
```

### 주요 에러 코드
- `400`: 잘못된 요청 (Bad Request)
- `404`: 엔드포인트를 찾을 수 없음 (Not Found)
- `500`: 서버 내부 오류 (Internal Server Error)

## 🔐 인증 및 보안

현재는 개발 환경으로 인증이 비활성화되어 있습니다.
프로덕션 환경에서는 다음과 같은 보안 조치가 적용됩니다:

- API 키 인증
- 요청 속도 제한 (Rate Limiting)
- CORS 정책 강화
- 입력 데이터 검증 및 새니타이제이션

## 📈 사용 예시

### Python 클라이언트 예시

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# 스마트 템플릿 생성
def generate_smart_template():
    data = {
        "user_request": "배송 완료 알림",
        "business_type": "상품",
        "category_1": "배송",
        "target_length": 100,
        "include_variables": ["고객성명", "상품명"]
    }

    response = requests.post(
        f"{BASE_URL}/templates/smart-generate",
        json=data
    )

    if response.status_code == 200:
        result = response.json()
        print("생성된 템플릿:", result['generated_template'])
        print("점수:", result['validation']['compliance_score'])
    else:
        print("오류:", response.json()['message'])

# 유사 템플릿 검색
def search_similar_templates():
    data = {
        "query": "주문 확인",
        "limit": 3
    }

    response = requests.post(
        f"{BASE_URL}/templates/similar-search",
        json=data
    )

    if response.status_code == 200:
        result = response.json()
        for template in result['similar_templates']:
            print(f"템플릿: {template['text'][:50]}...")
```

## 📞 기술 지원

**API 문서 버전**: v1.0
**마지막 업데이트**: 2025-09-14
**개발자 문의**: 시스템 관리자

---

### 🔗 관련 문서

- [시스템 개발 보고서](./template-generation-system.md)
- [설치 및 설정 가이드](../CLAUDE.md)
- [템플릿 생성 가이드](../kakao_template_generation_guide.md)