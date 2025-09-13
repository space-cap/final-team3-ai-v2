#!/usr/bin/env python3
"""
빠른 API 테스트 스크립트
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_basic_functionality():
    """기본 기능 테스트"""
    print("=== 카카오 알림톡 AI 시스템 기본 테스트 ===\n")
    
    # 1. 루트 엔드포인트 테스트
    print("1. 루트 엔드포인트 테스트...")
    try:
        response = requests.get(f"{BASE_URL}/")
        data = response.json()
        print(f"   ✅ 성공: {data['message']}")
        print(f"   상태: {data['status']}")
    except Exception as e:
        print(f"   ❌ 실패: {str(e)}")
        return False
    
    # 2. 헬스체크 테스트
    print("\n2. 헬스체크 테스트...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        data = response.json()
        print(f"   ✅ 성공: {data['status']}")
        print(f"   환경: {data['environment']}")
        print(f"   OpenAI 키 설정: {'있음' if data['openai_key_present'] else '없음'}")
        print(f"   데이터베이스 설정: {'있음' if data['database_configured'] else '없음'}")
    except Exception as e:
        print(f"   ❌ 실패: {str(e)}")
        return False
    
    # 3. 응답 시간 테스트
    print("\n3. 응답 시간 테스트...")
    try:
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/health")
        response_time = (time.time() - start_time) * 1000
        print(f"   ✅ 응답 시간: {response_time:.2f}ms")
    except Exception as e:
        print(f"   ❌ 실패: {str(e)}")
        return False
    
    return True

def test_environment_setup():
    """환경 설정 테스트"""
    print("\n=== 환경 설정 확인 ===\n")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        import os
        
        # 환경 변수 확인
        required_vars = [
            "OPENAI_API_KEY",
            "LOCAL_DB_NAME", 
            "LOCAL_DB_USER",
            "LOCAL_DB_PASSWORD",
            "APP_PORT"
        ]
        
        print("환경 변수 확인:")
        for var in required_vars:
            value = os.getenv(var)
            if value:
                if "API_KEY" in var or "PASSWORD" in var:
                    display_value = f"{value[:10]}..." if len(value) > 10 else "***"
                else:
                    display_value = value
                print(f"   ✅ {var}: {display_value}")
            else:
                print(f"   ❌ {var}: 설정되지 않음")
        
        return True
    except Exception as e:
        print(f"   ❌ 환경 설정 확인 실패: {str(e)}")
        return False

def main():
    """메인 테스트 함수"""
    print("카카오 알림톡 템플릿 AI 생성 시스템 테스트 시작\n")
    
    # 기본 기능 테스트
    basic_test = test_basic_functionality()
    
    # 환경 설정 테스트
    env_test = test_environment_setup()
    
    # 결과 요약
    print("\n=== 테스트 결과 요약 ===")
    print(f"기본 기능 테스트: {'✅ 통과' if basic_test else '❌ 실패'}")
    print(f"환경 설정 테스트: {'✅ 통과' if env_test else '❌ 실패'}")
    
    if basic_test and env_test:
        print("\n🎉 모든 기본 테스트가 성공했습니다!")
        print("📚 API 문서: http://localhost:8000/docs")
        print("💡 전체 시스템 테스트를 위해서는 추가 패키지 설치가 필요합니다.")
        return True
    else:
        print("\n⚠️ 일부 테스트가 실패했습니다. 설정을 확인해주세요.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)