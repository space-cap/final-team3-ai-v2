"""
템플릿 생성 과정에서 LLM 호출 횟수 확인 테스트
"""
import os
import sys
import time

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.rag_service import rag_service
from app.services.token_service import token_service

def test_llm_call_count():
    """템플릿 생성 시 LLM 호출 횟수 테스트"""
    print("=== 템플릿 생성 시 LLM 호출 횟수 테스트 ===")

    # 테스트 전 기존 토큰 사용량 확인
    stats_before = token_service.get_usage_stats()
    requests_before = stats_before.get('total_requests', 0)

    print(f"테스트 전 총 요청 수: {requests_before}")

    # 템플릿 생성 테스트
    print("\n템플릿 생성 요청 시작...")

    start_time = time.time()
    response = rag_service.generate_template(
        user_request="간단한 예약 확인 알림톡을 만들어주세요",
        business_type="병원",
        template_type="예약확인",
        session_id="test_call_count_001"
    )
    end_time = time.time()

    print(f"템플릿 생성 완료 (소요시간: {end_time - start_time:.2f}초)")

    # 테스트 후 토큰 사용량 확인
    time.sleep(1)  # DB 저장 대기
    stats_after = token_service.get_usage_stats()
    requests_after = stats_after.get('total_requests', 0)

    llm_calls = requests_after - requests_before

    print(f"\n=== 결과 ===")
    print(f"테스트 후 총 요청 수: {requests_after}")
    print(f"이번 테스트에서 LLM 호출 횟수: {llm_calls}회")

    if response.token_metrics:
        print(f"토큰 사용량: {response.token_metrics.total_tokens}개")
        print(f"총 비용: ${response.token_metrics.total_cost:.6f}")

    print(f"\n생성된 템플릿 (일부):")
    print(response.answer[:200] + "..." if len(response.answer) > 200 else response.answer)

    return llm_calls

def test_simple_query():
    """간단한 쿼리로 LLM 호출 횟수 확인"""
    print("\n=== 일반 쿼리 시 LLM 호출 횟수 테스트 ===")

    # 테스트 전 기존 토큰 사용량 확인
    stats_before = token_service.get_usage_stats()
    requests_before = stats_before.get('total_requests', 0)

    print(f"테스트 전 총 요청 수: {requests_before}")

    # 간단한 쿼리 테스트
    print("\n일반 쿼리 요청 시작...")

    start_time = time.time()
    response = rag_service.generate_response(
        query="카카오톡 알림톡에서 변수는 어떻게 사용하나요?",
        session_id="test_call_count_002"
    )
    end_time = time.time()

    print(f"쿼리 응답 완료 (소요시간: {end_time - start_time:.2f}초)")

    # 테스트 후 토큰 사용량 확인
    time.sleep(1)  # DB 저장 대기
    stats_after = token_service.get_usage_stats()
    requests_after = stats_after.get('total_requests', 0)

    llm_calls = requests_after - requests_before

    print(f"\n=== 결과 ===")
    print(f"테스트 후 총 요청 수: {requests_after}")
    print(f"이번 테스트에서 LLM 호출 횟수: {llm_calls}회")

    if response.token_metrics:
        print(f"토큰 사용량: {response.token_metrics.total_tokens}개")
        print(f"총 비용: ${response.token_metrics.total_cost:.6f}")

    return llm_calls

if __name__ == "__main__":
    if not os.getenv('OPENAI_API_KEY'):
        print("OPENAI_API_KEY가 설정되지 않아 테스트를 건너뜁니다.")
        exit(1)

    # 템플릿 생성 테스트
    template_calls = test_llm_call_count()

    # 일반 쿼리 테스트
    query_calls = test_simple_query()

    print(f"\n=== 최종 결과 ===")
    print(f"템플릿 생성 시 LLM 호출 횟수: {template_calls}회")
    print(f"일반 쿼리 시 LLM 호출 횟수: {query_calls}회")

    print("\n=== LLM 호출 과정 분석 ===")
    print("ConversationalRetrievalChain은 일반적으로:")
    print("1. 대화 히스토리가 있는 경우:")
    print("   - 1차: 질문을 독립적인 질문으로 재구성 (Question Rephrasing)")
    print("   - 2차: 재구성된 질문으로 최종 답변 생성")
    print("   - 총 2회 호출")
    print("2. 대화 히스토리가 없는 경우:")
    print("   - 1차: 질문으로 직접 답변 생성")
    print("   - 총 1회 호출")
    print("3. 문서 압축기(LLMChainExtractor) 사용 시:")
    print("   - 추가로 문서 압축을 위한 LLM 호출 발생")