# P05_API_설계

## API 개요

FastAPI 기반 RESTful API 서버로 카카오톡 알림톡 템플릿 생성 및 관리 서비스 제공

### 기술 스택
- **프레임워크**: FastAPI 0.104+
- **인증**: JWT Token 기반
- **문서화**: OpenAPI 3.0 (Swagger UI)
- **배포**: Uvicorn ASGI 서버
- **보안**: CORS, Rate Limiting, Input Validation

## API 기본 구조

### 1. 서버 설정
```python
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn

app = FastAPI(
    title="KakaoTalk Template Generator API",
    description="AI-powered KakaoTalk notification template generation service",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 인증 설정
security = HTTPBearer()
```

### 2. 응답 모델 정의
```python
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum

class ResponseStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"

class BaseResponse(BaseModel):
    status: ResponseStatus
    message: str
    timestamp: datetime
    data: Optional[Dict] = None

class ErrorResponse(BaseModel):
    status: ResponseStatus = ResponseStatus.ERROR
    message: str
    error_code: str
    details: Optional[Dict] = None
```

## 인증 및 사용자 관리

### 1. 사용자 등록/로그인
```python
class UserRegistration(BaseModel):
    user_id: str
    password: str
    business_name: str
    business_type: str
    business_number: Optional[str] = None
    contact_email: str
    contact_phone: Optional[str] = None

class UserLogin(BaseModel):
    user_id: str
    password: str

class UserResponse(BaseModel):
    user_id: str
    business_name: str
    business_type: str
    is_verified: bool
    subscription_tier: str
    created_at: datetime

@app.post("/auth/register", response_model=BaseResponse)
async def register_user(user_data: UserRegistration):
    """사용자 회원가입"""
    try:
        # 사용자 중복 확인
        existing_user = await user_service.get_user(user_data.user_id)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already exists"
            )

        # 사용자 생성
        new_user = await user_service.create_user(user_data)
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="User registered successfully",
            timestamp=datetime.now(),
            data={"user_id": new_user.user_id}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/auth/login", response_model=BaseResponse)
async def login_user(login_data: UserLogin):
    """사용자 로그인"""
    user = await user_service.authenticate_user(
        login_data.user_id, login_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    access_token = create_access_token(data={"sub": user.user_id})
    return BaseResponse(
        status=ResponseStatus.SUCCESS,
        message="Login successful",
        timestamp=datetime.now(),
        data={
            "access_token": access_token,
            "token_type": "bearer",
            "user": UserResponse.from_orm(user)
        }
    )
```

### 2. JWT 토큰 관리
```python
from jose import JWTError, jwt
from datetime import timedelta

SECRET_KEY = "your-secret-key"  # 환경변수로 관리
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await user_service.get_user(user_id)
    if user is None:
        raise credentials_exception
    return user
```

## 템플릿 생성 API

### 1. 템플릿 생성 요청
```python
class TemplateGenerationRequest(BaseModel):
    business_type: str
    message_purpose: str
    content_requirements: str
    target_audience: str
    special_requirements: Optional[str] = None
    include_variables: Optional[List[str]] = None
    template_name: Optional[str] = None

class TemplateResponse(BaseModel):
    template_id: int
    template_name: str
    content: str
    variables: List[Dict[str, str]]
    category: str
    template_type: str
    confidence_score: float
    policy_compliance: Dict[str, any]

@app.post("/templates/generate", response_model=BaseResponse)
async def generate_template(
    request: TemplateGenerationRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """AI 템플릿 생성"""
    try:
        # 입력 검증
        if not request.business_type or not request.message_purpose:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Business type and message purpose are required"
            )

        # AI 템플릿 생성 호출
        generation_result = await template_service.generate_template(
            user_id=current_user.user_id,
            request_data=request
        )

        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="Template generated successfully",
            timestamp=datetime.now(),
            data={
                "template": TemplateResponse(**generation_result),
                "generation_time": generation_result.get("processing_time"),
                "improvement_suggestions": generation_result.get("suggestions", [])
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Template generation failed: {str(e)}"
        )
```

### 2. 템플릿 검증 API
```python
class TemplateValidationRequest(BaseModel):
    content: str
    business_type: str
    template_type: Optional[str] = "info"

class ValidationResult(BaseModel):
    overall_score: float
    is_compliant: bool
    violations: List[Dict[str, any]]
    suggestions: List[str]
    character_count: int
    estimated_approval_rate: float

@app.post("/templates/validate", response_model=BaseResponse)
async def validate_template(
    request: TemplateValidationRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """템플릿 정책 준수 검증"""
    try:
        validation_result = await validation_service.validate_template(
            content=request.content,
            business_type=request.business_type,
            template_type=request.template_type
        )

        return BaseResponse(
            status=ResponseStatus.SUCCESS if validation_result.is_compliant else ResponseStatus.WARNING,
            message="Template validation completed",
            timestamp=datetime.now(),
            data={"validation": ValidationResult(**validation_result)}
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Template validation failed: {str(e)}"
        )
```

## 템플릿 관리 API

### 1. 템플릿 CRUD
```python
class TemplateUpdateRequest(BaseModel):
    template_name: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None

@app.get("/templates", response_model=BaseResponse)
async def get_user_templates(
    page: int = 1,
    size: int = 10,
    status_filter: Optional[str] = None,
    category_filter: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """사용자 템플릿 목록 조회"""
    templates = await template_service.get_user_templates(
        user_id=current_user.user_id,
        page=page,
        size=size,
        status_filter=status_filter,
        category_filter=category_filter
    )

    return BaseResponse(
        status=ResponseStatus.SUCCESS,
        message="Templates retrieved successfully",
        timestamp=datetime.now(),
        data={
            "templates": templates["items"],
            "pagination": {
                "page": page,
                "size": size,
                "total": templates["total"],
                "pages": templates["pages"]
            }
        }
    )

@app.get("/templates/{template_id}", response_model=BaseResponse)
async def get_template(
    template_id: int,
    current_user: UserResponse = Depends(get_current_user)
):
    """특정 템플릿 상세 조회"""
    template = await template_service.get_template(
        template_id=template_id,
        user_id=current_user.user_id
    )

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )

    return BaseResponse(
        status=ResponseStatus.SUCCESS,
        message="Template retrieved successfully",
        timestamp=datetime.now(),
        data={"template": TemplateResponse(**template)}
    )

@app.put("/templates/{template_id}", response_model=BaseResponse)
async def update_template(
    template_id: int,
    request: TemplateUpdateRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """템플릿 수정"""
    updated_template = await template_service.update_template(
        template_id=template_id,
        user_id=current_user.user_id,
        update_data=request
    )

    return BaseResponse(
        status=ResponseStatus.SUCCESS,
        message="Template updated successfully",
        timestamp=datetime.now(),
        data={"template": TemplateResponse(**updated_template)}
    )

@app.delete("/templates/{template_id}", response_model=BaseResponse)
async def delete_template(
    template_id: int,
    current_user: UserResponse = Depends(get_current_user)
):
    """템플릿 삭제"""
    await template_service.delete_template(
        template_id=template_id,
        user_id=current_user.user_id
    )

    return BaseResponse(
        status=ResponseStatus.SUCCESS,
        message="Template deleted successfully",
        timestamp=datetime.now()
    )
```

### 2. 템플릿 내보내기/가져오기
```python
@app.get("/templates/{template_id}/export", response_model=BaseResponse)
async def export_template(
    template_id: int,
    format_type: str = "json",  # json, csv, txt
    current_user: UserResponse = Depends(get_current_user)
):
    """템플릿 내보내기"""
    export_data = await template_service.export_template(
        template_id=template_id,
        user_id=current_user.user_id,
        format_type=format_type
    )

    return BaseResponse(
        status=ResponseStatus.SUCCESS,
        message="Template exported successfully",
        timestamp=datetime.now(),
        data={"export_data": export_data}
    )

@app.post("/templates/import", response_model=BaseResponse)
async def import_template(
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user)
):
    """템플릿 가져오기"""
    import_result = await template_service.import_template(
        file=file,
        user_id=current_user.user_id
    )

    return BaseResponse(
        status=ResponseStatus.SUCCESS,
        message="Template imported successfully",
        timestamp=datetime.now(),
        data={"import_result": import_result}
    )
```

## 정책 관리 API

### 1. 정책 정보 조회
```python
@app.get("/policies", response_model=BaseResponse)
async def get_policies(
    category: Optional[str] = None,
    business_type: Optional[str] = None
):
    """정책 가이드라인 조회"""
    policies = await policy_service.get_policies(
        category=category,
        business_type=business_type
    )

    return BaseResponse(
        status=ResponseStatus.SUCCESS,
        message="Policies retrieved successfully",
        timestamp=datetime.now(),
        data={"policies": policies}
    )

@app.get("/policies/business-types", response_model=BaseResponse)
async def get_business_types():
    """지원 업종 목록 조회"""
    business_types = await policy_service.get_business_types()

    return BaseResponse(
        status=ResponseStatus.SUCCESS,
        message="Business types retrieved successfully",
        timestamp=datetime.now(),
        data={"business_types": business_types}
    )
```

## 분석 및 통계 API

### 1. 사용자 통계
```python
@app.get("/analytics/user-stats", response_model=BaseResponse)
async def get_user_statistics(
    current_user: UserResponse = Depends(get_current_user)
):
    """사용자 사용 통계"""
    stats = await analytics_service.get_user_statistics(
        user_id=current_user.user_id
    )

    return BaseResponse(
        status=ResponseStatus.SUCCESS,
        message="User statistics retrieved successfully",
        timestamp=datetime.now(),
        data={"statistics": stats}
    )

@app.get("/analytics/template-performance", response_model=BaseResponse)
async def get_template_performance(
    template_id: Optional[int] = None,
    period: str = "30d",  # 7d, 30d, 90d
    current_user: UserResponse = Depends(get_current_user)
):
    """템플릿 성과 분석"""
    performance = await analytics_service.get_template_performance(
        user_id=current_user.user_id,
        template_id=template_id,
        period=period
    )

    return BaseResponse(
        status=ResponseStatus.SUCCESS,
        message="Template performance retrieved successfully",
        timestamp=datetime.now(),
        data={"performance": performance}
    )
```

## 에러 처리 및 미들웨어

### 1. 전역 예외 처리
```python
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail,
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "message": "Validation error",
            "details": exc.errors(),
            "timestamp": datetime.now().isoformat()
        }
    )
```

### 2. 속도 제한 미들웨어
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/templates/generate")
@limiter.limit("10/minute")
async def generate_template_with_limit(
    request: Request,
    template_request: TemplateGenerationRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    # 템플릿 생성 로직
    pass
```

## 로깅 및 모니터링

### 1. 요청/응답 로깅
```python
import logging
from fastapi import Request
import time

logger = logging.getLogger("api")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    # 요청 로깅
    logger.info(f"Request: {request.method} {request.url}")

    response = await call_next(request)

    # 응답 로깅
    process_time = time.time() - start_time
    logger.info(f"Response: {response.status_code} - {process_time:.2f}s")

    return response
```

### 2. 헬스 체크
```python
@app.get("/health")
async def health_check():
    """서비스 상태 확인"""
    try:
        # 데이터베이스 연결 확인
        db_status = await check_database_connection()

        # AI 서비스 상태 확인
        ai_status = await check_ai_service_status()

        return {
            "status": "healthy",
            "timestamp": datetime.now(),
            "services": {
                "database": db_status,
                "ai_service": ai_status
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )
```

## 배포 설정

### 1. Docker 컨테이너
```python
# Dockerfile
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. 환경 설정
```python
from pydantic import BaseSettings

class Settings(BaseSettings):
    app_name: str = "KakaoTalk Template Generator"
    environment: str = "development"
    debug: bool = True

    # 데이터베이스
    mysql_host: str
    mysql_port: int = 3306
    mysql_database: str
    mysql_user: str
    mysql_password: str

    # AI 서비스
    openai_api_key: str
    chroma_persist_directory: str = "./chroma_db"

    # 보안
    secret_key: str
    access_token_expire_minutes: int = 30

    class Config:
        env_file = ".env"

settings = Settings()
```

## API 문서화

### 1. OpenAPI 태그 설정
```python
tags_metadata = [
    {
        "name": "auth",
        "description": "사용자 인증 및 권한 관리",
    },
    {
        "name": "templates",
        "description": "템플릿 생성 및 관리",
    },
    {
        "name": "policies",
        "description": "정책 가이드라인 조회",
    },
    {
        "name": "analytics",
        "description": "사용 통계 및 분석",
    },
]

app = FastAPI(
    title="KakaoTalk Template Generator API",
    description="AI 기반 카카오톡 알림톡 템플릿 자동 생성 서비스",
    version="1.0.0",
    openapi_tags=tags_metadata
)
```

### 2. API 버전 관리
```python
from fastapi import APIRouter

v1_router = APIRouter(prefix="/api/v1")
v2_router = APIRouter(prefix="/api/v2")

# V1 엔드포인트
v1_router.include_router(auth_router, tags=["auth"])
v1_router.include_router(template_router, tags=["templates"])

# V2 엔드포인트 (향후 확장)
v2_router.include_router(enhanced_template_router, tags=["templates"])

app.include_router(v1_router)
app.include_router(v2_router)
```