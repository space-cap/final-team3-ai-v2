"""
템플릿 생성 관련 AI 도구들
LangChain BaseTool을 상속받은 커스텀 도구 구현
"""
import re
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from app.services.vector_store import vector_store_service

logger = logging.getLogger(__name__)

class TemplateValidatorToolInput(BaseModel):
    """템플릿 검증 도구 입력 스키마"""
    template_content: str = Field(description="검증할 템플릿 내용")
    business_type: Optional[str] = Field(None, description="비즈니스 유형")

class TemplateValidatorTool(BaseTool):
    """
    템플릿 유효성 검증 도구
    템플릿의 기본적인 형식과 구조를 검증
    """
    name: str = "template_validator"
    description: str = """
    카카오 알림톡 템플릿의 기본적인 유효성을 검증합니다.
    - 템플릿 길이 확인
    - 변수 형식 검증  
    - 기본 구조 검사
    입력: template_content (문자열), business_type (선택사항)
    """
    args_schema = TemplateValidatorToolInput
    
    def _run(self, template_content: str, business_type: Optional[str] = None) -> str:
        """
        템플릿 유효성 검증 실행
        
        Args:
            template_content: 검증할 템플릿 내용
            business_type: 비즈니스 유형
            
        Returns:
            검증 결과 JSON 문자열
        """
        try:
            # 기본 정보 추출
            char_count = len(template_content)
            variables = re.findall(r'#\{([^}]+)\}', template_content)
            variable_count = len(variables)
            
            # 검증 결과 초기화
            validation_result = {
                "is_valid": True,
                "issues": [],
                "warnings": [],
                "statistics": {
                    "character_count": char_count,
                    "variable_count": variable_count,
                    "line_count": len(template_content.split('\n')),
                    "variables": variables
                }
            }
            
            # 길이 검증
            if char_count == 0:
                validation_result["is_valid"] = False
                validation_result["issues"].append("템플릿이 비어있습니다.")
            elif char_count > 1000:
                validation_result["is_valid"] = False
                validation_result["issues"].append(f"템플릿이 1,000자를 초과했습니다. (현재: {char_count}자)")
            elif char_count > 800:
                validation_result["warnings"].append(f"템플릿이 800자를 초과했습니다. 길이를 확인해주세요. (현재: {char_count}자)")
            
            # 변수 개수 검증
            if variable_count > 40:
                validation_result["is_valid"] = False
                validation_result["issues"].append(f"변수가 40개를 초과했습니다. (현재: {variable_count}개)")
            elif variable_count > 30:
                validation_result["warnings"].append(f"변수가 30개를 초과했습니다. (현재: {variable_count}개)")
            
            # 변수명 형식 검증
            invalid_variables = []
            for var in variables:
                if not re.match(r'^[a-zA-Z0-9_]+$', var):
                    invalid_variables.append(var)
                elif len(var) > 50:
                    invalid_variables.append(f"{var} (길이 초과)")
            
            if invalid_variables:
                validation_result["is_valid"] = False
                validation_result["issues"].append(f"잘못된 변수명: {', '.join(invalid_variables)}")
            
            # 비즈니스 유형별 추가 검증
            if business_type:
                business_warnings = self._validate_business_specific(template_content, business_type)
                validation_result["warnings"].extend(business_warnings)
            
            return json.dumps(validation_result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"템플릿 검증 중 오류: {str(e)}")
            return json.dumps({
                "is_valid": False,
                "error": f"검증 중 오류가 발생했습니다: {str(e)}",
                "issues": [str(e)]
            }, ensure_ascii=False)
    
    def _validate_business_specific(self, content: str, business_type: str) -> List[str]:
        """
        비즈니스 유형별 특화 검증
        
        Args:
            content: 템플릿 내용
            business_type: 비즈니스 유형
            
        Returns:
            경고 메시지 목록
        """
        warnings = []
        
        # 금융업 특화 검증
        if "금융" in business_type or "은행" in business_type:
            if "계좌" in content or "카드" in content:
                warnings.append("금융 관련 템플릿에서는 개인정보 보호에 특히 주의하세요.")
        
        # 의료업 특화 검증
        if "의료" in business_type or "병원" in business_type:
            if "진료" in content or "처방" in content:
                warnings.append("의료 관련 템플릿은 의료광고 규정을 준수해야 합니다.")
        
        # 교육업 특화 검증
        if "교육" in business_type or "학원" in business_type:
            if "할인" in content or "무료" in content:
                warnings.append("교육 서비스 관련 광고성 표현을 확인해주세요.")
        
        return warnings

class PolicyCheckerToolInput(BaseModel):
    """정책 확인 도구 입력 스키마"""
    query: str = Field(description="정책 관련 질의")
    template_content: Optional[str] = Field(None, description="확인할 템플릿 내용")

class PolicyCheckerTool(BaseTool):
    """
    정책 문서 확인 도구
    벡터 데이터베이스에서 관련 정책을 검색하고 확인
    """
    name: str = "policy_checker"
    description: str = """
    카카오 알림톡 정책 문서에서 관련 규정을 검색하고 확인합니다.
    - 정책 규정 검색
    - 준수 사항 확인
    - 제한 사항 조회
    입력: query (질의), template_content (선택사항)
    """
    args_schema = PolicyCheckerToolInput
    
    def _run(self, query: str, template_content: Optional[str] = None) -> str:
        """
        정책 확인 실행
        
        Args:
            query: 정책 관련 질의
            template_content: 확인할 템플릿 내용
            
        Returns:
            정책 확인 결과 JSON 문자열
        """
        try:
            # 벡터 데이터베이스에서 관련 정책 검색
            policy_results = vector_store_service.get_relevant_policies(
                user_query=query,
                k=3
            )
            
            result = {
                "query": query,
                "relevant_policies": [],
                "compliance_check": None,
                "recommendations": []
            }
            
            # 검색된 정책 정보 구성
            if policy_results and "policies" in policy_results:
                for policy in policy_results["policies"]:
                    result["relevant_policies"].append({
                        "source": policy.get("source", ""),
                        "content": policy.get("content", "")[:500] + "..." if len(policy.get("content", "")) > 500 else policy.get("content", ""),
                        "relevance_score": policy.get("relevance_score", 0.0)
                    })
            
            # 템플릿이 제공된 경우 준수 여부 확인
            if template_content:
                compliance_check = self._check_template_compliance(template_content, policy_results)
                result["compliance_check"] = compliance_check
                
                # 권장사항 생성
                result["recommendations"] = self._generate_recommendations(template_content, policy_results)
            
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"정책 확인 중 오류: {str(e)}")
            return json.dumps({
                "error": f"정책 확인 중 오류가 발생했습니다: {str(e)}",
                "query": query
            }, ensure_ascii=False)
    
    def _check_template_compliance(self, template_content: str, policy_results: Dict) -> Dict[str, Any]:
        """
        템플릿 정책 준수 여부 확인
        
        Args:
            template_content: 템플릿 내용
            policy_results: 정책 검색 결과
            
        Returns:
            준수 여부 확인 결과
        """
        compliance = {
            "overall_compliant": True,
            "violations": [],
            "warnings": []
        }
        
        # 기본 정책 확인
        char_count = len(template_content)
        variable_count = len(re.findall(r'#\{([^}]+)\}', template_content))
        
        if char_count > 1000:
            compliance["overall_compliant"] = False
            compliance["violations"].append("1,000자 길이 제한 위반")
        
        if variable_count > 40:
            compliance["overall_compliant"] = False
            compliance["violations"].append("40개 변수 제한 위반")
        
        # 금지 키워드 확인
        forbidden_keywords = ["광고", "할인", "무료", "이벤트", "쿠폰"]
        found_keywords = [kw for kw in forbidden_keywords if kw in template_content]
        
        if found_keywords:
            compliance["warnings"].append(f"주의 필요 키워드 발견: {', '.join(found_keywords)}")
        
        return compliance
    
    def _generate_recommendations(self, template_content: str, policy_results: Dict) -> List[str]:
        """
        정책 기반 권장사항 생성
        
        Args:
            template_content: 템플릿 내용
            policy_results: 정책 검색 결과
            
        Returns:
            권장사항 목록
        """
        recommendations = []
        
        # 길이 관련 권장사항
        char_count = len(template_content)
        if char_count > 800:
            recommendations.append("템플릿 길이를 줄이는 것을 고려해보세요.")
        
        # 변수 관련 권장사항
        variable_count = len(re.findall(r'#\{([^}]+)\}', template_content))
        if variable_count > 30:
            recommendations.append("변수 개수를 줄이거나 통합하는 것을 고려해보세요.")
        
        # 내용 관련 권장사항
        if not re.search(r'[가-힣]', template_content):
            recommendations.append("한국어 내용을 포함하는 것을 권장합니다.")
        
        return recommendations

class VariableExtractorToolInput(BaseModel):
    """변수 추출 도구 입력 스키마"""
    template_content: str = Field(description="변수를 추출할 템플릿 내용")

class VariableExtractorTool(BaseTool):
    """
    템플릿 변수 추출 및 분석 도구
    템플릿에서 변수를 추출하고 분석
    """
    name: str = "variable_extractor" 
    description: str = """
    템플릿에서 변수를 추출하고 분석합니다.
    - 변수 목록 추출
    - 변수 형식 검증
    - 변수 사용 패턴 분석
    입력: template_content (문자열)
    """
    args_schema = VariableExtractorToolInput
    
    def _run(self, template_content: str) -> str:
        """
        변수 추출 및 분석 실행
        
        Args:
            template_content: 분석할 템플릿 내용
            
        Returns:
            변수 분석 결과 JSON 문자열
        """
        try:
            # 변수 추출
            variables = re.findall(r'#\{([^}]+)\}', template_content)
            
            # 변수 분석
            analysis = {
                "total_variables": len(variables),
                "unique_variables": len(set(variables)),
                "duplicate_variables": [],
                "valid_variables": [],
                "invalid_variables": [],
                "variable_details": []
            }
            
            # 중복 변수 찾기
            variable_counts = {}
            for var in variables:
                variable_counts[var] = variable_counts.get(var, 0) + 1
            
            analysis["duplicate_variables"] = [var for var, count in variable_counts.items() if count > 1]
            
            # 변수별 상세 분석
            for var in set(variables):
                detail = {
                    "name": var,
                    "usage_count": variable_counts[var],
                    "is_valid": True,
                    "issues": []
                }
                
                # 변수명 형식 검증
                if not re.match(r'^[a-zA-Z0-9_]+$', var):
                    detail["is_valid"] = False
                    detail["issues"].append("영문, 숫자, 언더스코어만 사용 가능")
                    analysis["invalid_variables"].append(var)
                else:
                    analysis["valid_variables"].append(var)
                
                # 변수명 길이 검증
                if len(var) > 50:
                    detail["is_valid"] = False
                    detail["issues"].append("변수명이 50자를 초과")
                
                # 변수명 컨벤션 검증
                if var.upper() == var:
                    detail["issues"].append("상수 스타일 변수명 (권장하지 않음)")
                elif not re.match(r'^[a-z][a-zA-Z0-9_]*$', var):
                    detail["issues"].append("camelCase 또는 snake_case 권장")
                
                analysis["variable_details"].append(detail)
            
            # 권장사항 생성
            recommendations = []
            if analysis["total_variables"] > 30:
                recommendations.append("변수 개수가 많습니다. 통합 가능한 변수를 확인해보세요.")
            
            if analysis["duplicate_variables"]:
                recommendations.append(f"중복 사용 변수: {', '.join(analysis['duplicate_variables'])}")
            
            if analysis["invalid_variables"]:
                recommendations.append(f"형식 오류 변수: {', '.join(analysis['invalid_variables'])}")
            
            analysis["recommendations"] = recommendations
            
            return json.dumps(analysis, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"변수 추출 중 오류: {str(e)}")
            return json.dumps({
                "error": f"변수 추출 중 오류가 발생했습니다: {str(e)}",
                "total_variables": 0
            }, ensure_ascii=False)

class BusinessTypeSuggestorToolInput(BaseModel):
    """비즈니스 유형 제안 도구 입력 스키마"""
    template_content: str = Field(description="분석할 템플릿 내용")
    user_description: Optional[str] = Field(None, description="사용자 설명")

class BusinessTypeSuggestorTool(BaseTool):
    """
    비즈니스 유형 제안 도구
    템플릿 내용을 분석하여 적합한 비즈니스 유형 제안
    """
    name: str = "business_type_suggestor"
    description: str = """
    템플릿 내용을 분석하여 적합한 비즈니스 유형을 제안합니다.
    - 템플릿 내용 분석
    - 키워드 기반 분류
    - 비즈니스 유형 추천
    입력: template_content (문자열), user_description (선택사항)
    """
    args_schema = BusinessTypeSuggestorToolInput
    
    def _run(self, template_content: str, user_description: Optional[str] = None) -> str:
        """
        비즈니스 유형 제안 실행
        
        Args:
            template_content: 분석할 템플릿 내용
            user_description: 사용자 설명
            
        Returns:
            비즈니스 유형 제안 결과 JSON 문자열
        """
        try:
            # 비즈니스 키워드 매핑
            business_keywords = {
                "전자상거래": ["주문", "배송", "결제", "상품", "쇼핑", "구매", "판매"],
                "금융": ["계좌", "카드", "대출", "투자", "보험", "은행", "금융"],
                "의료": ["진료", "예약", "병원", "치료", "건강", "의료", "진단"],
                "교육": ["수업", "강의", "학습", "교육", "학원", "과정", "시험"],
                "여행": ["예약", "호텔", "항공", "여행", "숙박", "관광", "티켓"],
                "음식": ["주문", "배달", "음식", "식당", "메뉴", "요리", "레스토랑"],
                "부동산": ["매물", "임대", "부동산", "아파트", "매매", "전세", "월세"],
                "IT/소프트웨어": ["서비스", "앱", "소프트웨어", "시스템", "플랫폼", "기술"],
                "소매": ["매장", "판매", "상품", "고객", "서비스", "할인", "이벤트"],
                "물류": ["배송", "운송", "물류", "택배", "배달", "창고", "운반"]
            }
            
            # 텍스트 분석
            analysis_text = template_content.lower()
            if user_description:
                analysis_text += " " + user_description.lower()
            
            # 각 비즈니스 유형별 점수 계산
            business_scores = {}
            for business_type, keywords in business_keywords.items():
                score = 0
                matched_keywords = []
                
                for keyword in keywords:
                    if keyword in analysis_text:
                        score += 1
                        matched_keywords.append(keyword)
                
                if score > 0:
                    business_scores[business_type] = {
                        "score": score,
                        "matched_keywords": matched_keywords,
                        "confidence": min(score / len(keywords), 1.0)
                    }
            
            # 결과 정렬 (점수 기준)
            sorted_businesses = sorted(
                business_scores.items(),
                key=lambda x: x[1]["score"],
                reverse=True
            )
            
            # 결과 구성
            result = {
                "suggested_types": [],
                "analysis_summary": {
                    "total_candidates": len(sorted_businesses),
                    "high_confidence": 0,
                    "medium_confidence": 0,
                    "low_confidence": 0
                },
                "recommendations": []
            }
            
            # 상위 5개 결과 포함
            for business_type, data in sorted_businesses[:5]:
                confidence_level = "높음" if data["confidence"] >= 0.6 else "보통" if data["confidence"] >= 0.3 else "낮음"
                
                suggestion = {
                    "business_type": business_type,
                    "confidence_score": data["confidence"],
                    "confidence_level": confidence_level,
                    "matched_keywords": data["matched_keywords"],
                    "reasoning": f"{len(data['matched_keywords'])}개의 관련 키워드가 발견되었습니다."
                }
                
                result["suggested_types"].append(suggestion)
                
                # 신뢰도별 카운트
                if data["confidence"] >= 0.6:
                    result["analysis_summary"]["high_confidence"] += 1
                elif data["confidence"] >= 0.3:
                    result["analysis_summary"]["medium_confidence"] += 1
                else:
                    result["analysis_summary"]["low_confidence"] += 1
            
            # 권장사항 생성
            if not result["suggested_types"]:
                result["recommendations"].append("명확한 비즈니스 유형을 파악하기 어렵습니다. 더 구체적인 내용을 포함해주세요.")
            elif result["analysis_summary"]["high_confidence"] == 0:
                result["recommendations"].append("비즈니스 유형이 명확하지 않습니다. 구체적인 서비스 내용을 추가해주세요.")
            else:
                top_suggestion = result["suggested_types"][0]
                result["recommendations"].append(f"'{top_suggestion['business_type']}' 유형이 가장 적합해 보입니다.")
            
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"비즈니스 유형 제안 중 오류: {str(e)}")
            return json.dumps({
                "error": f"비즈니스 유형 제안 중 오류가 발생했습니다: {str(e)}",
                "suggested_types": []
            }, ensure_ascii=False)