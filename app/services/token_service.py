"""
토큰 사용량 및 비용 추적 서비스
"""
import os
import uuid
import time
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.token_usage import TokenUsage, TokenPricing
from config.database import SessionLocal


@dataclass
class TokenMetrics:
    """토큰 메트릭 데이터 클래스"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    prompt_cost: float = 0.0
    completion_cost: float = 0.0
    total_cost: float = 0.0
    processing_time: float = 0.0
    model_name: str = ""
    provider: str = "openai"


class TokenService:
    """토큰 사용량 및 비용 관리 서비스"""

    def __init__(self):
        """초기화"""
        self.db_session: Optional[Session] = None
        self.pricing_cache: Dict[str, TokenPricing] = {}
        self._load_pricing_cache()

    def _get_db_session(self) -> Session:
        """데이터베이스 세션 획득"""
        if not self.db_session:
            self.db_session = SessionLocal()
        return self.db_session

    def _close_db_session(self):
        """데이터베이스 세션 종료"""
        if self.db_session:
            self.db_session.close()
            self.db_session = None

    def _load_pricing_cache(self):
        """가격 정보 캐시 로드"""
        try:
            db = self._get_db_session()
            active_pricings = db.query(TokenPricing).filter(
                TokenPricing.is_active == True
            ).all()

            for pricing in active_pricings:
                key = f"{pricing.provider}:{pricing.model_name}"
                self.pricing_cache[key] = pricing

        except Exception as e:
            print(f"가격 정보 캐시 로드 중 오류: {e}")
        finally:
            self._close_db_session()

    def get_pricing(self, provider: str, model_name: str) -> Optional[TokenPricing]:
        """모델별 가격 정보 조회"""
        key = f"{provider}:{model_name}"

        # 캐시에서 먼저 확인
        if key in self.pricing_cache:
            return self.pricing_cache[key]

        # DB에서 조회
        try:
            db = self._get_db_session()
            pricing = db.query(TokenPricing).filter(
                TokenPricing.provider == provider,
                TokenPricing.model_name == model_name,
                TokenPricing.is_active == True
            ).first()

            if pricing:
                self.pricing_cache[key] = pricing
                return pricing

        except Exception as e:
            print(f"가격 정보 조회 중 오류: {e}")
        finally:
            self._close_db_session()

        return None

    def calculate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        model_name: str,
        provider: str = "openai"
    ) -> Tuple[float, float, float]:
        """토큰 사용량 기반 비용 계산"""
        pricing = self.get_pricing(provider, model_name)

        if not pricing:
            # 기본 가격 설정 (GPT-4o-mini 기준)
            prompt_price_per_1k = 0.00015
            completion_price_per_1k = 0.0006
        else:
            prompt_price_per_1k = pricing.prompt_price_per_1k
            completion_price_per_1k = pricing.completion_price_per_1k

        # 비용 계산 (1000 토큰당 가격 기준)
        prompt_cost = (prompt_tokens / 1000) * prompt_price_per_1k
        completion_cost = (completion_tokens / 1000) * completion_price_per_1k
        total_cost = prompt_cost + completion_cost

        return prompt_cost, completion_cost, total_cost

    def create_token_metrics(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        model_name: str,
        provider: str = "openai",
        processing_time: float = 0.0
    ) -> TokenMetrics:
        """토큰 메트릭 생성"""
        total_tokens = prompt_tokens + completion_tokens
        prompt_cost, completion_cost, total_cost = self.calculate_cost(
            prompt_tokens, completion_tokens, model_name, provider
        )

        return TokenMetrics(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            prompt_cost=prompt_cost,
            completion_cost=completion_cost,
            total_cost=total_cost,
            processing_time=processing_time,
            model_name=model_name,
            provider=provider
        )

    def save_token_usage(
        self,
        metrics: TokenMetrics,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        request_type: Optional[str] = None,
        user_query: Optional[str] = None,
        response_length: Optional[int] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> TokenUsage:
        """토큰 사용량 데이터베이스 저장"""
        try:
            db = self._get_db_session()

            # 고유 ID 생성
            if not request_id:
                request_id = str(uuid.uuid4())

            # TokenUsage 인스턴스 생성
            token_usage = TokenUsage(
                session_id=session_id,
                request_id=request_id,
                model_name=metrics.model_name,
                provider=metrics.provider,
                prompt_tokens=metrics.prompt_tokens,
                completion_tokens=metrics.completion_tokens,
                total_tokens=metrics.total_tokens,
                prompt_cost=metrics.prompt_cost,
                completion_cost=metrics.completion_cost,
                total_cost=metrics.total_cost,
                request_type=request_type,
                user_query=user_query,
                response_length=response_length,
                processing_time=metrics.processing_time,
                success=success,
                error_message=error_message
            )

            # 데이터베이스에 저장
            db.add(token_usage)
            db.commit()
            db.refresh(token_usage)

            return token_usage

        except Exception as e:
            print(f"토큰 사용량 저장 중 오류: {e}")
            db.rollback()
            raise
        finally:
            self._close_db_session()

    def get_usage_stats(
        self,
        session_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        model_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """사용량 통계 조회"""
        try:
            db = self._get_db_session()
            query = db.query(TokenUsage)

            # 필터 적용
            if session_id:
                query = query.filter(TokenUsage.session_id == session_id)
            if start_date:
                query = query.filter(TokenUsage.created_at >= start_date)
            if end_date:
                query = query.filter(TokenUsage.created_at <= end_date)
            if model_name:
                query = query.filter(TokenUsage.model_name == model_name)

            usages = query.all()

            if not usages:
                return {
                    "total_requests": 0,
                    "total_tokens": 0,
                    "total_cost": 0.0,
                    "avg_tokens_per_request": 0,
                    "avg_cost_per_request": 0.0,
                    "models_used": [],
                    "success_rate": 100.0
                }

            # 통계 계산
            total_requests = len(usages)
            total_tokens = sum(u.total_tokens for u in usages)
            total_cost = sum(u.total_cost for u in usages)
            successful_requests = sum(1 for u in usages if u.success)

            models_used = list(set(u.model_name for u in usages))

            return {
                "total_requests": total_requests,
                "total_tokens": total_tokens,
                "total_cost": round(total_cost, 4),
                "avg_tokens_per_request": round(total_tokens / total_requests if total_requests > 0 else 0),
                "avg_cost_per_request": round(total_cost / total_requests if total_requests > 0 else 0, 4),
                "models_used": models_used,
                "success_rate": round((successful_requests / total_requests) * 100 if total_requests > 0 else 100.0, 2)
            }

        except Exception as e:
            print(f"사용량 통계 조회 중 오류: {e}")
            return {}
        finally:
            self._close_db_session()

    def add_pricing(
        self,
        provider: str,
        model_name: str,
        prompt_price_per_1k: float,
        completion_price_per_1k: float,
        currency: str = "USD"
    ) -> TokenPricing:
        """새 가격 정보 추가"""
        try:
            db = self._get_db_session()

            # 기존 가격 정보 비활성화
            existing_pricings = db.query(TokenPricing).filter(
                TokenPricing.provider == provider,
                TokenPricing.model_name == model_name,
                TokenPricing.is_active == True
            ).all()

            for pricing in existing_pricings:
                pricing.is_active = False

            # 새 가격 정보 추가
            new_pricing = TokenPricing(
                provider=provider,
                model_name=model_name,
                prompt_price_per_1k=prompt_price_per_1k,
                completion_price_per_1k=completion_price_per_1k,
                currency=currency,
                is_active=True
            )

            db.add(new_pricing)
            db.commit()
            db.refresh(new_pricing)

            # 캐시 업데이트
            cache_key = f"{provider}:{model_name}"
            self.pricing_cache[cache_key] = new_pricing

            return new_pricing

        except Exception as e:
            print(f"가격 정보 추가 중 오류: {e}")
            db.rollback()
            raise
        finally:
            self._close_db_session()

    def track_llm_call(
        self,
        llm_response: Any,
        model_name: str,
        provider: str = "openai",
        session_id: Optional[str] = None,
        request_type: Optional[str] = None,
        user_query: Optional[str] = None,
        processing_time: float = 0.0
    ) -> Tuple[TokenMetrics, TokenUsage]:
        """LLM 호출 추적"""
        try:
            # OpenAI response에서 토큰 정보 추출
            if hasattr(llm_response, 'usage'):
                usage = llm_response.usage
                prompt_tokens = usage.prompt_tokens
                completion_tokens = usage.completion_tokens
            elif hasattr(llm_response, 'response_metadata'):
                usage = llm_response.response_metadata.get('token_usage', {})
                prompt_tokens = usage.get('prompt_tokens', 0)
                completion_tokens = usage.get('completion_tokens', 0)
            else:
                # 기본값 설정
                prompt_tokens = len(str(user_query).split()) * 1.5 if user_query else 100
                completion_tokens = len(str(llm_response).split()) * 1.5 if llm_response else 50
                prompt_tokens = int(prompt_tokens)
                completion_tokens = int(completion_tokens)

            # 메트릭 생성
            metrics = self.create_token_metrics(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                model_name=model_name,
                provider=provider,
                processing_time=processing_time
            )

            # 응답 길이 계산
            response_length = len(str(llm_response)) if llm_response else 0

            # 데이터베이스에 저장
            token_usage = self.save_token_usage(
                metrics=metrics,
                session_id=session_id,
                request_type=request_type,
                user_query=user_query,
                response_length=response_length,
                success=True
            )

            return metrics, token_usage

        except Exception as e:
            print(f"LLM 호출 추적 중 오류: {e}")
            # 오류 발생 시 기본 메트릭 반환
            metrics = TokenMetrics(model_name=model_name, provider=provider)
            token_usage = self.save_token_usage(
                metrics=metrics,
                session_id=session_id,
                request_type=request_type,
                user_query=user_query,
                success=False,
                error_message=str(e)
            )
            return metrics, token_usage


# 전역 토큰 서비스 인스턴스
token_service = TokenService()


def initialize_default_pricing():
    """기본 가격 정보 초기화"""
    default_pricings = [
        # OpenAI GPT 모델들
        {"provider": "openai", "model": "gpt-4o", "prompt": 0.005, "completion": 0.015},
        {"provider": "openai", "model": "gpt-4o-mini", "prompt": 0.00015, "completion": 0.0006},
        {"provider": "openai", "model": "gpt-4", "prompt": 0.03, "completion": 0.06},
        {"provider": "openai", "model": "gpt-4-turbo", "prompt": 0.01, "completion": 0.03},
        {"provider": "openai", "model": "gpt-3.5-turbo", "prompt": 0.0015, "completion": 0.002},
        {"provider": "openai", "model": "gpt-3.5-turbo-instruct", "prompt": 0.0015, "completion": 0.002},
    ]

    try:
        for pricing_info in default_pricings:
            try:
                token_service.add_pricing(
                    provider=pricing_info["provider"],
                    model_name=pricing_info["model"],
                    prompt_price_per_1k=pricing_info["prompt"],
                    completion_price_per_1k=pricing_info["completion"]
                )
                print(f"가격 정보 추가됨: {pricing_info['provider']}:{pricing_info['model']}")
            except Exception as e:
                print(f"가격 정보 추가 실패: {pricing_info['model']} - {e}")

    except Exception as e:
        print(f"기본 가격 정보 초기화 중 오류: {e}")