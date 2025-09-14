"""
토큰 추적 기능 테스트
"""
import os
import sys
import json

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.token_service import token_service
from app.services.rag_service import rag_service

def test_token_service():
    """토큰 서비스 기본 기능 테스트"""
    print("=== 토큰 서비스 기본 기능 테스트 ===")

    # 1. 가격 정보 조회 테스트
    print("1. 가격 정보 조회 테스트")
    pricing = token_service.get_pricing("openai", "gpt-4o-mini")
    if pricing:
        print(f"   - 모델: {pricing.model_name}")
        print(f"   - 입력 토큰 가격: ${pricing.prompt_price_per_1k}/1K")
        print(f"   - 출력 토큰 가격: ${pricing.completion_price_per_1k}/1K")
    else:
        print("   - 가격 정보를 찾을 수 없음")

    # 2. 비용 계산 테스트
    print("\n2. 비용 계산 테스트")
    prompt_tokens = 100
    completion_tokens = 50
    model_name = "gpt-4o-mini"

    prompt_cost, completion_cost, total_cost = token_service.calculate_cost(
        prompt_tokens, completion_tokens, model_name
    )

    print(f"   - 입력 토큰: {prompt_tokens}개")
    print(f"   - 출력 토큰: {completion_tokens}개")
    print(f"   - 입력 비용: ${prompt_cost:.6f}")
    print(f"   - 출력 비용: ${completion_cost:.6f}")
    print(f"   - 총 비용: ${total_cost:.6f}")

    # 3. 토큰 메트릭 생성 테스트
    print("\n3. 토큰 메트릭 생성 테스트")
    metrics = token_service.create_token_metrics(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        model_name=model_name,
        processing_time=1.23
    )

    print(f"   - 총 토큰: {metrics.total_tokens}개")
    print(f"   - 총 비용: ${metrics.total_cost:.6f}")
    print(f"   - 처리 시간: {metrics.processing_time}초")

    # 4. 데이터베이스 저장 테스트
    print("\n4. 데이터베이스 저장 테스트")
    try:
        usage_record = token_service.save_token_usage(
            metrics=metrics,
            session_id="test_session_001",
            request_type="test",
            user_query="테스트 쿼리입니다",
            response_length=200,
            success=True
        )
        print(f"   - 저장 성공: ID {usage_record.id}")
        print(f"   - 세션 ID: {usage_record.session_id}")
        print(f"   - 요청 유형: {usage_record.request_type}")
    except Exception as e:
        print(f"   - 저장 실패: {e}")

    # 5. 사용량 통계 조회 테스트
    print("\n5. 사용량 통계 조회 테스트")
    stats = token_service.get_usage_stats()
    print(f"   - 총 요청 수: {stats.get('total_requests', 0)}")
    print(f"   - 총 토큰 수: {stats.get('total_tokens', 0)}")
    print(f"   - 총 비용: ${stats.get('total_cost', 0):.6f}")
    print(f"   - 성공률: {stats.get('success_rate', 0)}%")

def test_rag_with_token_tracking():
    """RAG 서비스의 토큰 추적 기능 테스트"""
    print("\n=== RAG 서비스 토큰 추적 테스트 ===")

    try:
        # RAG 응답 생성 (토큰 추적 포함)
        response = rag_service.generate_response(
            query="카카오톡 알림톡 메시지에서 변수를 어떻게 사용하나요?",
            session_id="test_session_rag_001",
            context={"test": True}
        )

        print("1. RAG 응답 생성 완료")
        print(f"   - 응답 길이: {len(response.answer)}자")
        print(f"   - 신뢰도: {response.confidence_score:.2f}")
        print(f"   - 처리 시간: {response.processing_time:.2f}초")

        # 토큰 정보 확인
        if response.token_metrics:
            print("\n2. 토큰 사용량 정보")
            print(f"   - 입력 토큰: {response.token_metrics.prompt_tokens}개")
            print(f"   - 출력 토큰: {response.token_metrics.completion_tokens}개")
            print(f"   - 총 토큰: {response.token_metrics.total_tokens}개")
            print(f"   - 총 비용: ${response.token_metrics.total_cost:.6f}")
            print(f"   - 사용 모델: {response.token_metrics.model_name}")
        else:
            print("\n2. 토큰 정보가 없습니다.")

    except Exception as e:
        print(f"RAG 테스트 실패: {e}")

def test_api_response_format():
    """API 응답 형식 테스트"""
    print("\n=== API 응답 형식 테스트 ===")

    try:
        # RAG 응답 생성
        response = rag_service.generate_response(
            query="간단한 예약 확인 알림톡 템플릿을 만들어주세요",
            session_id="test_session_api_001"
        )

        # 응답을 API 형식으로 변환하는 시뮬레이션
        if response.token_metrics:
            from dataclasses import asdict
            from app.api.schemas import TokenMetrics as TokenMetricsSchema

            token_metrics_dict = asdict(response.token_metrics)
            token_metrics_schema = TokenMetricsSchema(**token_metrics_dict)

            api_response = {
                "success": True,
                "message": "응답이 성공적으로 생성되었습니다.",
                "answer": response.answer[:100] + "...",  # 일부만 표시
                "confidence_score": response.confidence_score,
                "processing_time": response.processing_time,
                "token_metrics": token_metrics_schema.dict()
            }

            print("API 응답 형식 (JSON):")
            print(json.dumps(api_response, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"API 응답 형식 테스트 실패: {e}")

if __name__ == "__main__":
    # 기본 토큰 서비스 테스트
    test_token_service()

    # RAG 서비스와 통합된 토큰 추적 테스트
    # 주의: OpenAI API 키가 필요합니다
    if os.getenv('OPENAI_API_KEY'):
        test_rag_with_token_tracking()
        test_api_response_format()
    else:
        print("\n주의: OPENAI_API_KEY가 설정되지 않아 RAG 테스트를 건너뜁니다.")

    print("\n=== 테스트 완료 ===")