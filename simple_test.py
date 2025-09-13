#!/usr/bin/env python3
"""
간단한 FastAPI 테스트 서버
"""
from fastapi import FastAPI
from dotenv import load_dotenv
import os

# 환경 변수 로드
load_dotenv()

app = FastAPI(title="카카오 알림톡 AI 시스템 테스트")

@app.get("/")
async def root():
    return {
        "message": "카카오 알림톡 템플릿 AI 생성 시스템",
        "status": "running",
        "test": "success"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "environment": os.getenv("APP_ENVIRONMENT", "development"),
        "openai_key_present": bool(os.getenv("OPENAI_API_KEY")),
        "database_configured": bool(os.getenv("LOCAL_DB_NAME"))
    }

if __name__ == "__main__":
    import uvicorn
    print("Starting simple test server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)