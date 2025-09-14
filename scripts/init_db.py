"""
데이터베이스 초기화 스크립트
"""
import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import create_database_if_not_exists, create_tables, check_connection
from app.models import Session, Query, Template, Prompt, TokenUsage, TokenPricing
from app.services.token_service import initialize_default_pricing

def init_database():
    """
    데이터베이스 초기화 함수
    """
    print("=== 데이터베이스 초기화 시작 ===")
    
    try:
        # 1. 데이터베이스 생성
        print("1. 데이터베이스 생성 중...")
        create_database_if_not_exists()
        
        # 2. 연결 확인
        print("2. 데이터베이스 연결 확인 중...")
        if not check_connection():
            raise Exception("데이터베이스 연결 실패")
        print("   - 연결 성공!")
        
        # 3. 테이블 생성
        print("3. 테이블 생성 중...")
        create_tables()
        
        # 4. 기본 프롬프트 데이터 삽입
        print("4. 기본 데이터 삽입 중...")
        insert_default_prompts()

        # 5. 기본 토큰 가격 정보 삽입
        print("5. 기본 토큰 가격 정보 삽입 중...")
        initialize_default_pricing()

        print("=== 데이터베이스 초기화 완료 ===")
        
    except Exception as e:
        print(f"데이터베이스 초기화 중 오류 발생: {e}")
        raise

def insert_default_prompts():
    """
    기본 프롬프트 데이터 삽입
    """
    from config.database import SessionLocal
    from app.models.prompts import Prompt, PromptType, PromptStatus
    
    db = SessionLocal()
    
    try:
        # 기본 시스템 프롬프트
        system_prompt = Prompt(
            prompt_name="기본 시스템 프롬프트",
            prompt_type=PromptType.SYSTEM,
            prompt_content="""당신은 카카오 알림톡 템플릿 생성 전문가입니다.

역할과 목표:
- 카카오 알림톡 정책을 완벽하게 준수하는 템플릿을 생성
- 사용자의 비즈니스 요구사항을 정확히 파악하고 반영
- 정보성 메시지 기준에 맞는 고품질 템플릿 제작

핵심 원칙:
1. 정보통신망법 준수 (영리목적 광고성 정보의 예외 기준)
2. 카카오 알림톡 심사 가이드 준수
3. 사용자 친화적이고 명확한 메시지 작성
4. 변수 사용 규칙 준수 (#{변수명} 형식)

항상 정책 문서를 참조하여 정확하고 승인 가능성이 높은 템플릿을 생성하세요.""",
            prompt_description="AI 시스템의 기본 역할과 지침을 정의하는 프롬프트",
            version="1.0",
            status=PromptStatus.ACTIVE,
            is_default=True,
            created_by="system"
        )
        
        # 템플릿 생성 프롬프트
        template_generation_prompt = Prompt(
            prompt_name="알림톡 템플릿 생성 프롬프트",
            prompt_type=PromptType.TEMPLATE_GENERATION,
            prompt_content="""사용자 요청: {user_request}

관련 정책 정보:
{policy_context}

위 정보를 바탕으로 다음 요구사항을 만족하는 알림톡 템플릿을 생성해주세요:

1. 템플릿 내용 생성
   - 1,000자 이내로 작성
   - 명확하고 간결한 정보 전달
   - 변수는 #{변수명} 형식으로 표기
   - 정보성 메시지 기준 준수

2. 템플릿 분석 제공
   - 템플릿 유형 분류 (기본형/부가정보형/채널추가형 등)
   - 정책 준수 여부 확인
   - 개선 제안사항

3. 응답 형식:
```json
{{
  "template_content": "생성된 템플릿 내용",
  "template_type": "템플릿 유형",
  "message_type": "정보성",
  "variables": ["변수1", "변수2"],
  "character_count": 글자수,
  "compliance_check": {{
    "is_compliant": true/false,
    "compliance_score": 0.0-1.0,
    "issues": ["문제점1", "문제점2"]
  }},
  "suggestions": ["개선사항1", "개선사항2"]
}}
```""",
            prompt_description="사용자 요청에 따른 알림톡 템플릿 생성",
            version="1.0",
            status=PromptStatus.ACTIVE,
            is_default=True,
            created_by="system"
        )
        
        # 정책 검증 프롬프트
        policy_check_prompt = Prompt(
            prompt_name="정책 준수 검증 프롬프트",
            prompt_type=PromptType.POLICY_CHECK,
            prompt_content="""템플릿 내용: {template_content}

관련 정책:
{policy_context}

위 템플릿이 카카오 알림톡 정책을 준수하는지 검증해주세요:

검증 항목:
1. 정보성 메시지 기준 준수 여부
2. 금지된 표현이나 내용 포함 여부
3. 변수 사용 규칙 준수 여부
4. 글자 수 제한 준수 여부
5. 템플릿 구성 요소 적절성

응답 형식:
```json
{{
  "is_compliant": true/false,
  "compliance_score": 0.0-1.0,
  "approval_probability": 0.0-1.0,
  "violations": [
    {{
      "type": "위반 유형",
      "description": "위반 내용",
      "severity": "high/medium/low"
    }}
  ],
  "recommendations": ["수정 권장사항1", "수정 권장사항2"]
}}
```""",
            prompt_description="생성된 템플릿의 정책 준수 여부 검증",
            version="1.0",
            status=PromptStatus.ACTIVE,
            is_default=True,
            created_by="system"
        )
        
        # 프롬프트들을 데이터베이스에 추가
        db.add_all([system_prompt, template_generation_prompt, policy_check_prompt])
        db.commit()
        
        print("   - 기본 프롬프트 데이터 삽입 완료")
        
    except Exception as e:
        db.rollback()
        print(f"   - 기본 데이터 삽입 중 오류: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    init_database()