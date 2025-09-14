"""
카카오 알림톡 템플릿 AI 생성 시스템
FastAPI 메인 애플리케이션
"""
import os
import time
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 애플리케이션 메타데이터
APP_TITLE = "카카오 알림톡 템플릿 AI 생성 시스템"
APP_DESCRIPTION = """
카카오 알림톡 정책을 준수하는 템플릿을 자동으로 생성하는 AI 시스템입니다.

## 주요 기능
- **정책 기반 템플릿 생성**: 카카오 알림톡 정책을 완전히 준수하는 템플릿 자동 생성
- **RAG 시스템**: 벡터 데이터베이스를 활용한 정책 문서 검색 및 활용
- **세션 기반 대화**: 사용자별 세션 관리 및 대화 히스토리 보존
- **템플릿 분석**: 생성된 템플릿의 정책 준수 여부 및 품질 분석
- **피드백 시스템**: 사용자 피드백을 통한 지속적인 품질 개선

## 기술 스택
- **AI**: OpenAI GPT-4, LangChain, RAG
- **Vector DB**: Chroma
- **Database**: MySQL 8.4
- **Framework**: FastAPI, SQLAlchemy
"""
APP_VERSION = "1.0.0"

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    애플리케이션 생명주기 관리
    """
    # 시작 시 초기화 작업
    logger.info("=== 카카오 알림톡 템플릿 AI 시스템 시작 ===")
    
    try:
        # 데이터베이스 연결 확인
        from config.database import check_connection
        if check_connection():
            logger.info("✓ 데이터베이스 연결 성공")
        else:
            logger.error("✗ 데이터베이스 연결 실패")
            
        # 벡터 데이터베이스 상태 확인
        try:
            from app.services.vector_store_simple import simple_vector_store_service
            vectordb_info = simple_vector_store_service.get_collection_info()
            if vectordb_info:
                logger.info(f"✓ 벡터 데이터베이스 로드 성공 (문서 수: {vectordb_info.get('count', 0)})")
            else:
                logger.warning("⚠ 벡터 데이터베이스 상태 확인 실패")
        except Exception as e:
            logger.warning(f"⚠ 벡터 데이터베이스 로드 실패: {e}")
            logger.info("✓ 벡터 없이 시스템 시작")
            
        # RAG 서비스 초기화 확인
        from app.services.rag_service import rag_service
        logger.info("✓ RAG 서비스 초기화 완료")

        # 템플릿 벡터 데이터베이스 상태 확인
        try:
            from app.services.template_vector_store import template_vector_store_service
            template_store_info = template_vector_store_service.get_store_info()
            if template_store_info.get('status') == 'available':
                templates_count = template_store_info.get('templates_count', 0)
                patterns_count = template_store_info.get('patterns_count', 0)
                logger.info(f"✓ 템플릿 벡터DB 로드 성공 (템플릿: {templates_count}, 패턴: {patterns_count})")
            else:
                logger.warning("⚠ 템플릿 벡터DB 상태 확인 실패")
        except Exception as e:
            logger.warning(f"⚠ 템플릿 벡터DB 로드 실패: {e}")
            logger.info("✓ 템플릿 벡터DB 없이 시스템 시작")

        logger.info("=== 시스템 초기화 완료 ===")
        
    except Exception as e:
        logger.error(f"시스템 초기화 중 오류: {e}")
    
    yield  # 애플리케이션 실행
    
    # 종료 시 정리 작업
    logger.info("=== 애플리케이션 종료 ===")

# FastAPI 앱 생성
app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 구체적인 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 신뢰할 수 있는 호스트 미들웨어
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # 프로덕션에서는 구체적인 호스트로 제한
)

# 요청 로깅 미들웨어
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """요청 로깅"""
    start_time = time.time()
    
    # 요청 정보 로깅
    logger.info(f"📨 {request.method} {request.url.path}")
    
    # 응답 처리
    response = await call_next(request)
    
    # 처리 시간 계산
    process_time = time.time() - start_time
    
    # 응답 정보 로깅
    logger.info(f"📤 {response.status_code} ({process_time:.3f}s)")
    
    return response

# 전역 예외 처리기
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """전역 예외 처리"""
    logger.error(f"❌ Unhandled exception: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "서버 내부 오류가 발생했습니다.",
            "error_code": "INTERNAL_SERVER_ERROR",
            "error_details": str(exc) if os.getenv('APP_DEBUG') == 'True' else None
        }
    )

# HTTP 예외 처리기
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP 예외 처리"""
    logger.warning(f"⚠ HTTP Exception: {exc.status_code} - {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail,
            "error_code": f"HTTP_{exc.status_code}",
            "error_details": None
        }
    )

# API 라우터 등록
from app.api.endpoints import router as api_router
app.include_router(api_router, prefix="/api/v1", tags=["API"])

# 루트 엔드포인트
@app.get("/", tags=["Root"])
async def root():
    """루트 엔드포인트"""
    return {
        "message": "카카오 알림톡 템플릿 AI 생성 시스템",
        "version": APP_VERSION,
        "docs": "/docs",
        "health": "/api/v1/health",
        "status": "running"
    }

# 개발 서버 실행
if __name__ == "__main__":
    # 환경 변수에서 설정 읽기
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", 8000))
    debug = os.getenv("APP_DEBUG", "False").lower() == "true"
    
    logger.info(f"🚀 서버 시작: http://{host}:{port}")
    logger.info(f"📚 API 문서: http://{host}:{port}/docs")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info" if not debug else "debug"
    )