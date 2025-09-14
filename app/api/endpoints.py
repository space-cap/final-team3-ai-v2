"""
FastAPI 엔드포인트 정의
알림톡 템플릿 생성 API
"""
import os
import time
from typing import List, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from config.database import get_db
from app.api.schemas import *
from app.models import Session as DBSession, Query, Template, Prompt
from app.models.queries import QueryStatus
from app.services.rag_service import rag_service
from app.services.token_service import token_service
from app.services.template_generation_service import template_generation_service
from app.services.template_vector_store import template_vector_store_service
try:
    from app.services.vector_store_simple import simple_vector_store_service as vector_store_service
except ImportError:
    from app.services.vector_store import vector_store_service

# 라우터 생성
router = APIRouter()

# 애플리케이션 시작 시간 (헬스체크용)
app_start_time = time.time()

@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    request: SessionCreate,
    db: Session = Depends(get_db)
):
    """
    새로운 세션 생성
    """
    try:
        # 새 세션 생성
        new_session = DBSession(
            user_id=request.user_id,
            session_name=request.session_name,
            session_description=request.session_description,
            client_info=str(request.client_info) if request.client_info else None,
            is_active=True
        )
        
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        
        return SessionResponse(
            success=True,
            message="세션이 성공적으로 생성되었습니다.",
            session_id=new_session.session_id,
            user_id=new_session.user_id,
            session_name=new_session.session_name,
            is_active=new_session.is_active,
            created_at=new_session.created_at
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"세션 생성 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/templates/generate", response_model=TemplateGenerationResponse)
async def generate_template(
    request: TemplateGenerationRequest,
    db: Session = Depends(get_db)
):
    """
    알림톡 템플릿 생성 (세션 검증 제거)
    """
    try:
        # 세션 검증 제거 - 직접 템플릿 생성 허용
        # 항상 자동 생성된 ID 사용 (검증 없이)
        current_time = int(time.time())
        session_id = f"anonymous_session_{current_time}"
        user_id = f"anonymous_{current_time}"
        
        # 먼저 익명 세션 생성 (외래키 제약 조건 만족)
        anonymous_session = DBSession(
            session_id=session_id,
            user_id=user_id,
            session_name="Anonymous Template Generation",
            session_description="Auto-generated session for template creation",
            is_active=True
        )
        db.add(anonymous_session)
        db.commit()
        
        # 질의 기록 생성 (검증 없이 바로 저장)
        new_query = Query(
            session_id=session_id,
            user_id=user_id,
            query_text=request.query_text,
            business_type=request.business_type,
            template_type=request.template_type,
            status=QueryStatus.PROCESSING,
            processing_started_at=datetime.now(),
            additional_context=str(request.additional_context) if request.additional_context else None
        )
        
        db.add(new_query)
        db.commit()
        db.refresh(new_query)
        
        try:
            # RAG 서비스를 통한 템플릿 생성
            rag_response = rag_service.generate_template(
                user_request=request.query_text,
                business_type=request.business_type,
                template_type=request.template_type,
                session_id=session_id
            )
            
            # 템플릿 내용 정리 (마크다운, 코드블록 등 제거)
            clean_template_content = _clean_template_content(rag_response.answer)
            
            # 템플릿 분석
            analysis = _analyze_template_content(clean_template_content)
            
            # 템플릿 저장
            new_template = Template(
                query_id=new_query.query_id,
                session_id=session_id,
                user_id=user_id,
                template_content=clean_template_content,
                template_type=analysis.get("template_type"),
                message_type=analysis.get("message_type", "정보성"),
                business_category=request.business_type,
                quality_score=analysis.get("quality_score", 0.8),
                compliance_score=analysis.get("compliance_score", 0.8),
                has_variables=analysis.get("variable_count", 0) > 0,
                variable_count=analysis.get("variable_count", 0),
                character_count=len(rag_response.answer),
                ai_model_used=rag_service.llm.model_name,
                generation_context=str(rag_response.metadata)
            )
            
            db.add(new_template)
            
            # 질의 상태 업데이트
            new_query.status = QueryStatus.COMPLETED
            new_query.processing_completed_at = datetime.now()
            new_query.processing_duration = int(rag_response.processing_time)
            
            db.commit()
            db.refresh(new_template)
            
            # TokenMetrics 객체를 스키마 모델로 변환
            token_metrics_dict = None
            if rag_response.token_metrics:
                from dataclasses import asdict
                token_metrics_dict = TokenMetrics(**asdict(rag_response.token_metrics))

            return TemplateGenerationResponse(
                success=True,
                message="템플릿이 성공적으로 생성되었습니다.",
                query_id=new_query.query_id,
                template_id=new_template.template_id,
                template_content=clean_template_content,
                template_analysis=analysis,
                processing_time=rag_response.processing_time,
                token_metrics=token_metrics_dict
            )
            
        except Exception as e:
            # 질의 상태를 실패로 업데이트
            new_query.status = QueryStatus.FAILED
            new_query.error_message = str(e)
            new_query.processing_completed_at = datetime.now()
            db.commit()
            raise e
            
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"템플릿 생성 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/query", response_model=QueryResponse)
async def query_policies(
    request: QueryRequest,
    db: Session = Depends(get_db)
):
    """
    정책 관련 질의응답 (세션 검증 제거)
    """
    try:
        # 세션 검증 제거 - 직접 질의 허용
        # 항상 자동 생성된 ID 사용 (검증 없이)
        current_time = int(time.time())
        session_id = f"anonymous_session_{current_time}"
        user_id = f"anonymous_{current_time}"
        
        # 먼저 익명 세션 생성 (외래키 제약 조건 만족)
        anonymous_session = DBSession(
            session_id=session_id,
            user_id=user_id,
            session_name="Anonymous Query Session",
            session_description="Auto-generated session for policy query",
            is_active=True
        )
        db.add(anonymous_session)
        db.commit()
        
        # 질의 기록 생성 (검증 없이 바로 저장)
        new_query = Query(
            session_id=session_id,
            user_id=user_id,
            query_text=request.query_text,
            status=QueryStatus.PROCESSING,
            processing_started_at=datetime.now(),
            additional_context=str(request.context) if request.context else None
        )
        
        db.add(new_query)
        db.commit()
        db.refresh(new_query)
        
        try:
            # RAG 서비스를 통한 응답 생성
            rag_response = rag_service.generate_response(
                query=request.query_text,
                session_id=request.session_id,
                context=request.context
            )
            
            # 질의 상태 업데이트
            new_query.status = QueryStatus.COMPLETED
            new_query.processing_completed_at = datetime.now()
            new_query.processing_duration = int(rag_response.processing_time)
            
            db.commit()
            
            # TokenMetrics 객체를 스키마 모델로 변환
            token_metrics_dict = None
            if rag_response.token_metrics:
                from dataclasses import asdict
                token_metrics_dict = TokenMetrics(**asdict(rag_response.token_metrics))

            return QueryResponse(
                success=True,
                message="질의에 대한 응답이 생성되었습니다.",
                query_id=new_query.query_id,
                answer=rag_response.answer,
                source_documents=rag_response.source_documents,
                confidence_score=rag_response.confidence_score,
                processing_time=rag_response.processing_time,
                token_metrics=token_metrics_dict
            )
            
        except Exception as e:
            # 질의 상태를 실패로 업데이트
            new_query.status = QueryStatus.FAILED
            new_query.error_message = str(e)
            new_query.processing_completed_at = datetime.now()
            db.commit()
            raise e
            
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"질의 처리 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/templates", response_model=TemplateListResponse)
async def get_templates(
    user_id: str,
    session_id: str = None,
    business_category: str = None,
    template_type: str = None,
    is_favorite: bool = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    템플릿 목록 조회
    """
    try:
        # 쿼리 구성
        query = db.query(Template).filter(
            Template.user_id == user_id,
            Template.is_deleted == False
        )
        
        if session_id:
            query = query.filter(Template.session_id == session_id)
        if business_category:
            query = query.filter(Template.business_category == business_category)
        if template_type:
            query = query.filter(Template.template_type == template_type)
        if is_favorite is not None:
            query = query.filter(Template.is_favorite == is_favorite)
        
        # 전체 개수 조회
        total_count = query.count()
        
        # 페이징 적용
        templates = query.order_by(desc(Template.created_at)).offset(offset).limit(limit).all()
        
        # 응답 데이터 구성
        template_list = []
        for template in templates:
            template_info = TemplateInfo(
                template_id=template.template_id,
                template_name=template.template_name,
                template_content=template.template_content,
                template_type=template.template_type,
                business_category=template.business_category,
                quality_score=template.quality_score,
                is_favorite=template.is_favorite,
                created_at=template.created_at
            )
            template_list.append(template_info)
        
        return TemplateListResponse(
            success=True,
            message="템플릿 목록을 성공적으로 조회했습니다.",
            templates=template_list,
            total_count=total_count,
            has_more=offset + limit < total_count
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"템플릿 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/templates/feedback", response_model=FeedbackResponse)
async def submit_template_feedback(
    feedback: TemplateFeedback,
    db: Session = Depends(get_db)
):
    """
    템플릿 피드백 제출
    """
    try:
        # 템플릿 조회
        template = db.query(Template).filter(
            Template.template_id == feedback.template_id,
            Template.user_id == feedback.user_id
        ).first()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="템플릿을 찾을 수 없습니다."
            )
        
        # 피드백 업데이트
        template.user_rating = feedback.rating
        template.user_feedback = feedback.feedback
        
        if feedback.is_favorite is not None:
            template.is_favorite = feedback.is_favorite
        
        template.updated_at = datetime.now()
        
        db.commit()
        
        return FeedbackResponse(
            success=True,
            message="피드백이 성공적으로 등록되었습니다.",
            template_id=feedback.template_id,
            updated=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"피드백 등록 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/policies/search", response_model=PolicySearchResponse)
async def search_policies(request: PolicySearchRequest):
    """
    정책 문서 검색
    """
    try:
        # 벡터 스토어를 통한 검색
        policy_results = vector_store_service.get_relevant_policies(
            user_query=request.query,
            k=request.limit
        )
        
        # 응답 데이터 구성
        documents = []
        for policy in policy_results["policies"]:
            doc = PolicyDocument(
                source=policy["source"],
                content=policy["content"],
                relevance_score=policy["relevance_score"],
                metadata=policy["metadata"]
            )
            documents.append(doc)
        
        return PolicySearchResponse(
            success=True,
            message="정책 문서 검색이 완료되었습니다.",
            query=request.query,
            documents=documents,
            total_results=len(documents)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"정책 검색 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/tokens/usage", response_model=TokenUsageResponse)
async def get_token_usage(
    request: TokenUsageRequest,
    db: Session = Depends(get_db)
):
    """
    토큰 사용량 통계 조회
    """
    try:
        # 토큰 서비스를 통한 사용량 통계 조회
        stats = token_service.get_usage_stats(
            session_id=request.session_id,
            start_date=request.start_date,
            end_date=request.end_date,
            model_name=request.model_name
        )

        # 통계 모델로 변환
        token_stats = TokenUsageStats(**stats)

        return TokenUsageResponse(
            success=True,
            message="토큰 사용량 통계를 성공적으로 조회했습니다.",
            stats=token_stats
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"토큰 사용량 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """
    시스템 헬스체크
    """
    try:
        # 데이터베이스 연결 확인
        db_connected = True
        try:
            db.execute("SELECT 1")
        except:
            db_connected = False
        
        # 벡터DB 상태 확인
        vectordb_loaded = False
        vectordb_count = 0
        try:
            vectordb_info = vector_store_service.get_collection_info()
            vectordb_loaded = bool(vectordb_info)
            vectordb_count = vectordb_info.get("count", 0)
        except:
            pass
        
        # AI 모델 상태 확인
        ai_available = True
        try:
            # 간단한 테스트 질의
            test_response = rag_service.generate_response("테스트", context={"test": True})
            ai_available = bool(test_response.answer)
        except:
            ai_available = False
        
        # 시스템 상태 구성
        system_status = SystemStatus(
            database_connected=db_connected,
            vectordb_loaded=vectordb_loaded,
            vectordb_document_count=vectordb_count,
            ai_model_available=ai_available,
            uptime=time.time() - app_start_time
        )
        
        return HealthResponse(
            success=True,
            message="시스템이 정상적으로 동작하고 있습니다.",
            status=system_status,
            version="1.0.0",
            environment=os.getenv("APP_ENVIRONMENT", "development")
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"헬스체크 중 오류가 발생했습니다: {str(e)}"
        )

def _clean_template_content(content: str) -> str:
    """
    템플릿 내용에서 마크다운, 코드블록 등 제거하여 순수 템플릿만 추출
    """
    try:
        import re
        
        # 원본 내용
        cleaned = content.strip()
        
        # 마크다운 코드블록 제거 (```로 감싸진 부분 내용만 추출)
        code_blocks = re.findall(r'```[^`\n]*\n(.*?)```', cleaned, flags=re.DOTALL)
        if code_blocks:
            # 코드 블록이 있다면 첫 번째 코드 블록 내용을 사용
            cleaned = code_blocks[0].strip()
        
        # 마크다운 헤더 제거 (### 등)
        cleaned = re.sub(r'^#+\s*.*$', '', cleaned, flags=re.MULTILINE)
        
        # 마크다운 볼드/이탤릭 제거
        cleaned = re.sub(r'\*\*(.*?)\*\*', r'\1', cleaned)
        cleaned = re.sub(r'\*(.*?)\*', r'\1', cleaned)
        
        # 대괄호로 감싸진 변수를 #{} 형식으로 변경
        cleaned = re.sub(r'\[([^\]]+)\]', r'#{\1}', cleaned)
        
        # 이모지 제거 (유니코드 범위)
        cleaned = re.sub(r'[\U00010000-\U0010ffff]', '', cleaned)
        cleaned = re.sub(r'[\u2600-\u26FF\u2700-\u27BF]', '', cleaned)
        
        # 연속된 공백 정리
        cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned)
        cleaned = re.sub(r'^\s+', '', cleaned, flags=re.MULTILINE)
        
        # 앞뒤 공백 제거
        cleaned = cleaned.strip()
        
        return cleaned
        
    except Exception as e:
        print(f"템플릿 내용 정리 중 오류: {e}")
        return content.strip()

def _analyze_template_content(content: str) -> Dict[str, Any]:
    """
    템플릿 내용 분석
    """
    try:
        import re
        
        # 변수 추출 (#{변수명} 형식)
        variables = re.findall(r'#\{([^}]+)\}', content)
        
        # 기본 분석 결과
        analysis = {
            "template_type": "기본형",
            "message_type": "정보성",
            "character_count": len(content),
            "variable_count": len(variables),
            "variables": variables,
            "quality_score": 0.8,
            "compliance_score": 0.8,
            "suggestions": []
        }
        
        # 글자 수 체크
        if len(content) > 1000:
            analysis["suggestions"].append("템플릿이 1,000자를 초과합니다. 내용을 줄여주세요.")
            analysis["compliance_score"] -= 0.2
        
        # 변수 개수 체크
        if len(variables) > 40:
            analysis["suggestions"].append("변수가 40개를 초과합니다. 변수 수를 줄여주세요.")
            analysis["compliance_score"] -= 0.3
        
        return analysis
        
    except Exception as e:
        print(f"템플릿 분석 중 오류: {e}")
        return {
            "template_type": "기본형",
            "message_type": "정보성", 
            "character_count": len(content),
            "variable_count": 0,
            "variables": [],
            "quality_score": 0.5,
            "compliance_score": 0.5,
            "suggestions": ["템플릿 분석 중 오류가 발생했습니다."]
        }

# 새로운 스마트 템플릿 생성 API 엔드포인트들

@router.post("/templates/smart-generate", response_model=SmartTemplateGenerationResponse)
async def smart_generate_template(
    request: SmartTemplateGenerationRequest
):
    """
    스마트 템플릿 생성 - 승인받은 패턴 기반 AI 생성
    """
    try:
        # 템플릿 생성 서비스 호출
        result = template_generation_service.generate_template(
            user_request=request.user_request,
            business_type=request.business_type,
            category_1=request.category_1,
            category_2=request.category_2,
            target_length=request.target_length,
            include_variables=request.include_variables
        )

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "템플릿 생성에 실패했습니다.")
            )

        # 응답 데이터 변환
        validation_data = result["validation"]
        validation = TemplateValidation(
            length=validation_data["length"],
            length_appropriate=validation_data["length_appropriate"],
            has_greeting=validation_data["has_greeting"],
            variables=validation_data["variables"],
            variable_count=validation_data["variable_count"],
            has_politeness=validation_data["has_politeness"],
            potential_ad_content=validation_data["potential_ad_content"],
            has_contact_info=validation_data["has_contact_info"],
            sentence_count=validation_data["sentence_count"],
            compliance_score=validation_data["compliance_score"]
        )

        return SmartTemplateGenerationResponse(
            success=True,
            message="스마트 템플릿이 성공적으로 생성되었습니다.",
            generated_template=result["generated_template"],
            validation=validation,
            suggestions=result["suggestions"],
            reference_data=result["reference_data"],
            metadata=result["metadata"]
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"스마트 템플릿 생성 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/templates/optimize", response_model=TemplateOptimizationResponse)
async def optimize_template(
    request: TemplateOptimizationRequest
):
    """
    템플릿 최적화 - 기존 템플릿을 정책에 맞게 개선
    """
    try:
        # 템플릿 최적화 서비스 호출
        result = template_generation_service.optimize_template(
            template=request.template,
            target_improvements=request.target_improvements
        )

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "템플릿 최적화에 실패했습니다.")
            )

        # 검증 데이터 변환
        def convert_validation(validation_data):
            return TemplateValidation(
                length=validation_data["length"],
                length_appropriate=validation_data["length_appropriate"],
                has_greeting=validation_data["has_greeting"],
                variables=validation_data["variables"],
                variable_count=validation_data["variable_count"],
                has_politeness=validation_data["has_politeness"],
                potential_ad_content=validation_data["potential_ad_content"],
                has_contact_info=validation_data["has_contact_info"],
                sentence_count=validation_data["sentence_count"],
                compliance_score=validation_data["compliance_score"]
            )

        return TemplateOptimizationResponse(
            success=True,
            message="템플릿이 성공적으로 최적화되었습니다.",
            original_template=result["original_template"],
            optimized_template=result["optimized_template"],
            original_validation=convert_validation(result["original_validation"]),
            optimized_validation=convert_validation(result["optimized_validation"]),
            improvement=result["improvement"]
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"템플릿 최적화 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/templates/similar-search", response_model=TemplateSimilarSearchResponse)
async def search_similar_templates(
    request: TemplateSimilarSearchRequest
):
    """
    유사한 승인받은 템플릿 검색
    """
    try:
        # 템플릿 추천 서비스 호출
        recommendations = template_vector_store_service.get_template_recommendations(
            user_input=request.query,
            category_1=request.category_filter,
            business_type=request.business_type_filter
        )

        # 템플릿 정보 변환
        similar_templates = []
        for template in recommendations['similar_templates'][:request.limit]:
            template_info = TemplateInfo(
                template_id=template.get('template_id', ''),
                text=template.get('text', ''),
                category_1=template.get('category_1'),
                category_2=template.get('category_2'),
                business_type=template.get('business_type'),
                variables=template.get('variables', []),
                button=template.get('button'),
                length=template.get('length', 0)
            )
            similar_templates.append(template_info)

        return TemplateSimilarSearchResponse(
            success=True,
            message=f"{len(similar_templates)}개의 유사한 템플릿을 찾았습니다.",
            query=request.query,
            similar_templates=similar_templates,
            category_patterns=recommendations['category_patterns'],
            suggestions=recommendations['suggestions']
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"유사 템플릿 검색 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/templates/vector-store-info", response_model=TemplateVectorStoreInfoResponse)
async def get_template_vector_store_info():
    """
    템플릿 벡터 스토어 정보 조회
    """
    try:
        store_info = template_vector_store_service.get_store_info()

        return TemplateVectorStoreInfoResponse(
            success=True,
            message="템플릿 벡터 스토어 정보를 성공적으로 조회했습니다.",
            templates_count=store_info['templates_count'],
            patterns_count=store_info['patterns_count'],
            status=store_info['status'],
            persist_directory=store_info.get('persist_directory')
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"벡터 스토어 정보 조회 중 오류가 발생했습니다: {str(e)}"
        )