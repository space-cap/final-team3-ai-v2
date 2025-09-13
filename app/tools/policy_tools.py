"""
정책 검증 관련 AI 도구들
카카오 알림톡 정책 준수 검증을 위한 전문 도구 구현
"""
import re
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from app.services.vector_store import vector_store_service

logger = logging.getLogger(__name__)

class PolicyRuleToolInput(BaseModel):
    """정책 규칙 도구 입력 스키마"""
    rule_category: str = Field(description="조회할 정책 규칙 카테고리 (length, variable, content, format)")
    specific_query: Optional[str] = Field(None, description="구체적인 질의")

class PolicyRuleTool(BaseTool):
    """
    정책 규칙 조회 도구
    카카오 알림톡의 구체적인 정책 규칙을 조회하고 제공
    """
    name: str = "policy_rule"
    description: str = """
    카카오 알림톡의 구체적인 정책 규칙을 조회합니다.
    - 길이 제한 규칙 (length)
    - 변수 제한 규칙 (variable)  
    - 콘텐츠 제한 규칙 (content)
    - 형식 규칙 (format)
    입력: rule_category, specific_query (선택사항)
    """
    args_schema = PolicyRuleToolInput
    
    def _run(self, rule_category: str, specific_query: Optional[str] = None) -> str:
        """
        정책 규칙 조회 실행
        
        Args:
            rule_category: 규칙 카테고리
            specific_query: 구체적인 질의
            
        Returns:
            정책 규칙 정보 JSON 문자열
        """
        try:
            # 정책 규칙 데이터베이스
            policy_rules = self._get_policy_rules()
            
            result = {
                "category": rule_category,
                "query": specific_query,
                "rules": [],
                "examples": [],
                "enforcement_level": "",
                "last_updated": "2024-01-01"
            }
            
            # 카테고리별 규칙 조회
            if rule_category.lower() in ["length", "길이"]:
                result.update(self._get_length_rules(policy_rules))
            elif rule_category.lower() in ["variable", "변수"]:
                result.update(self._get_variable_rules(policy_rules))
            elif rule_category.lower() in ["content", "콘텐츠", "내용"]:
                result.update(self._get_content_rules(policy_rules))
            elif rule_category.lower() in ["format", "형식"]:
                result.update(self._get_format_rules(policy_rules))
            else:
                result["rules"] = ["지원되지 않는 카테고리입니다. length, variable, content, format 중 하나를 선택하세요."]
            
            # 구체적인 질의가 있는 경우 추가 정보 제공
            if specific_query:
                additional_info = self._search_specific_rule(specific_query, policy_rules)
                result["additional_info"] = additional_info
            
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"정책 규칙 조회 중 오류: {str(e)}")
            return json.dumps({
                "error": f"정책 규칙 조회 중 오류가 발생했습니다: {str(e)}",
                "category": rule_category
            }, ensure_ascii=False)
    
    def _get_policy_rules(self) -> Dict[str, Any]:
        """정책 규칙 데이터 반환"""
        return {
            "length": {
                "max_characters": 1000,
                "recommended_max": 800,
                "min_characters": 1,
                "enforcement": "strict",
                "description": "템플릿 전체 길이 제한"
            },
            "variable": {
                "max_count": 40,
                "recommended_max": 30,
                "format": "#{변수명}",
                "naming_rules": "영문, 숫자, 언더스코어만 사용",
                "max_name_length": 50,
                "enforcement": "strict"
            },
            "content": {
                "forbidden_advertising": ["광고", "홍보", "할인", "무료", "이벤트", "쿠폰", "증정"],
                "forbidden_illegal": ["도박", "사행성", "불법", "마약"],
                "forbidden_harmful": ["성인", "폭력", "혐오", "차별"],
                "forbidden_personal": ["주민등록번호", "여권번호", "신용카드번호", "계좌번호"],
                "enforcement": "strict"
            },
            "format": {
                "allowed_characters": "한글, 영문, 숫자, 기본 특수문자",
                "variable_format": "#{변수명}",
                "line_breaks": "허용",
                "encoding": "UTF-8",
                "enforcement": "moderate"
            }
        }
    
    def _get_length_rules(self, policy_rules: Dict) -> Dict[str, Any]:
        """길이 관련 규칙 반환"""
        length_rules = policy_rules["length"]
        return {
            "rules": [
                f"최대 길이: {length_rules['max_characters']}자",
                f"권장 최대 길이: {length_rules['recommended_max']}자",
                f"최소 길이: {length_rules['min_characters']}자"
            ],
            "examples": [
                "✓ 500자 템플릿 (적절)",
                "⚠ 850자 템플릿 (주의 필요)",
                "✗ 1200자 템플릿 (위반)"
            ],
            "enforcement_level": length_rules["enforcement"]
        }
    
    def _get_variable_rules(self, policy_rules: Dict) -> Dict[str, Any]:
        """변수 관련 규칙 반환"""
        variable_rules = policy_rules["variable"]
        return {
            "rules": [
                f"최대 변수 개수: {variable_rules['max_count']}개",
                f"권장 최대 개수: {variable_rules['recommended_max']}개",
                f"변수 형식: {variable_rules['format']}",
                f"변수명 규칙: {variable_rules['naming_rules']}",
                f"변수명 최대 길이: {variable_rules['max_name_length']}자"
            ],
            "examples": [
                "✓ #{user_name} (올바른 형식)",
                "✓ #{order_id} (올바른 형식)",
                "✗ ${user_name} (잘못된 형식)",
                "✗ #{사용자명} (한글 변수명 불가)",
                "✗ #{user-name} (하이픈 불가)"
            ],
            "enforcement_level": variable_rules["enforcement"]
        }
    
    def _get_content_rules(self, policy_rules: Dict) -> Dict[str, Any]:
        """콘텐츠 관련 규칙 반환"""
        content_rules = policy_rules["content"]
        return {
            "rules": [
                "광고성 콘텐츠 금지",
                "불법 콘텐츠 금지",
                "유해 콘텐츠 금지", 
                "개인정보 직접 포함 금지"
            ],
            "examples": [
                f"✗ 금지 광고 키워드: {', '.join(content_rules['forbidden_advertising'][:3])} 등",
                f"✗ 금지 불법 키워드: {', '.join(content_rules['forbidden_illegal'][:2])} 등",
                f"✗ 금지 유해 키워드: {', '.join(content_rules['forbidden_harmful'][:2])} 등",
                "✗ 개인정보: 주민등록번호, 계좌번호 등 직접 포함 금지"
            ],
            "enforcement_level": content_rules["enforcement"]
        }
    
    def _get_format_rules(self, policy_rules: Dict) -> Dict[str, Any]:
        """형식 관련 규칙 반환"""
        format_rules = policy_rules["format"]
        return {
            "rules": [
                f"허용 문자: {format_rules['allowed_characters']}",
                f"변수 형식: {format_rules['variable_format']}",
                f"줄바꿈: {format_rules['line_breaks']}",
                f"인코딩: {format_rules['encoding']}"
            ],
            "examples": [
                "✓ 한글, 영문, 숫자 사용 가능",
                "✓ 기본 특수문자 (.,!?- 등) 사용 가능",
                "✓ 줄바꿈으로 구조화 가능",
                "✗ 특수 유니코드 문자 제한적"
            ],
            "enforcement_level": format_rules["enforcement"]
        }
    
    def _search_specific_rule(self, query: str, policy_rules: Dict) -> Dict[str, Any]:
        """구체적인 질의에 대한 추가 정보 검색"""
        additional_info = {
            "matched_rules": [],
            "recommendations": []
        }
        
        query_lower = query.lower()
        
        # 길이 관련 질의
        if any(keyword in query_lower for keyword in ["길이", "글자", "문자", "length"]):
            additional_info["matched_rules"].append("길이 제한 규칙 적용")
            additional_info["recommendations"].append("1,000자 이하로 작성하세요")
        
        # 변수 관련 질의
        if any(keyword in query_lower for keyword in ["변수", "variable", "#{", "}"]):
            additional_info["matched_rules"].append("변수 사용 규칙 적용")
            additional_info["recommendations"].append("#{변수명} 형식을 사용하고 40개 이하로 제한하세요")
        
        # 광고 관련 질의
        if any(keyword in query_lower for keyword in ["광고", "할인", "무료", "이벤트"]):
            additional_info["matched_rules"].append("광고성 콘텐츠 제한 규칙 적용")
            additional_info["recommendations"].append("광고성 표현을 피하고 정보성 내용으로 작성하세요")
        
        return additional_info

class ComplianceCheckerToolInput(BaseModel):
    """준수 검사 도구 입력 스키마"""
    template_content: str = Field(description="검사할 템플릿 내용")
    check_level: str = Field(default="comprehensive", description="검사 수준 (basic, standard, comprehensive)")

class ComplianceCheckerTool(BaseTool):
    """
    종합 준수 검사 도구
    템플릿의 전반적인 정책 준수 여부를 종합적으로 검사
    """
    name: str = "compliance_checker"
    description: str = """
    템플릿의 카카오 알림톡 정책 준수 여부를 종합적으로 검사합니다.
    - 모든 정책 규칙 일괄 검증
    - 준수 점수 산출
    - 우선순위별 개선사항 제시
    입력: template_content, check_level (basic/standard/comprehensive)
    """
    args_schema = ComplianceCheckerToolInput
    
    def _run(self, template_content: str, check_level: str = "comprehensive") -> str:
        """
        종합 준수 검사 실행
        
        Args:
            template_content: 검사할 템플릿 내용
            check_level: 검사 수준
            
        Returns:
            종합 준수 검사 결과 JSON 문자열
        """
        try:
            result = {
                "overall_compliance": True,
                "compliance_score": 0.0,
                "check_level": check_level,
                "detailed_results": {},
                "priority_issues": [],
                "summary": {
                    "total_checks": 0,
                    "passed_checks": 0,
                    "failed_checks": 0,
                    "warning_checks": 0
                }
            }
            
            # 검사 수준에 따른 검사 항목 결정
            checks_to_perform = self._get_checks_by_level(check_level)
            result["summary"]["total_checks"] = len(checks_to_perform)
            
            # 각 검사 수행
            for check_name in checks_to_perform:
                check_result = self._perform_individual_check(check_name, template_content)
                result["detailed_results"][check_name] = check_result
                
                # 요약 정보 업데이트
                if check_result["status"] == "passed":
                    result["summary"]["passed_checks"] += 1
                elif check_result["status"] == "failed":
                    result["summary"]["failed_checks"] += 1
                    result["overall_compliance"] = False
                elif check_result["status"] == "warning":
                    result["summary"]["warning_checks"] += 1
            
            # 우선순위 이슈 추출
            result["priority_issues"] = self._extract_priority_issues(result["detailed_results"])
            
            # 준수 점수 계산
            result["compliance_score"] = self._calculate_compliance_score(result["summary"])
            
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"준수 검사 중 오류: {str(e)}")
            return json.dumps({
                "error": f"준수 검사 중 오류가 발생했습니다: {str(e)}",
                "overall_compliance": False,
                "compliance_score": 0.0
            }, ensure_ascii=False)
    
    def _get_checks_by_level(self, check_level: str) -> List[str]:
        """검사 수준에 따른 검사 항목 반환"""
        basic_checks = ["length_check", "variable_count_check"]
        standard_checks = basic_checks + ["content_check", "variable_format_check"]
        comprehensive_checks = standard_checks + ["advanced_content_check", "business_compliance_check", "accessibility_check"]
        
        if check_level == "basic":
            return basic_checks
        elif check_level == "standard":
            return standard_checks
        else:  # comprehensive
            return comprehensive_checks
    
    def _perform_individual_check(self, check_name: str, template_content: str) -> Dict[str, Any]:
        """개별 검사 수행"""
        try:
            if check_name == "length_check":
                return self._check_length(template_content)
            elif check_name == "variable_count_check":
                return self._check_variable_count(template_content)
            elif check_name == "variable_format_check":
                return self._check_variable_format(template_content)
            elif check_name == "content_check":
                return self._check_basic_content(template_content)
            elif check_name == "advanced_content_check":
                return self._check_advanced_content(template_content)
            elif check_name == "business_compliance_check":
                return self._check_business_compliance(template_content)
            elif check_name == "accessibility_check":
                return self._check_accessibility(template_content)
            else:
                return {"status": "failed", "message": f"알 수 없는 검사: {check_name}"}
        except Exception as e:
            return {"status": "failed", "message": f"검사 실행 오류: {str(e)}"}
    
    def _check_length(self, content: str) -> Dict[str, Any]:
        """길이 검사"""
        char_count = len(content)
        if char_count > 1000:
            return {
                "status": "failed",
                "message": f"길이 제한 위반 ({char_count}/1000자)",
                "severity": "critical",
                "recommendation": f"{char_count - 1000}자를 줄여주세요"
            }
        elif char_count > 800:
            return {
                "status": "warning", 
                "message": f"길이 주의 필요 ({char_count}/1000자)",
                "severity": "medium",
                "recommendation": "길이를 줄이는 것을 권장합니다"
            }
        else:
            return {
                "status": "passed",
                "message": f"길이 적절 ({char_count}/1000자)",
                "severity": "none"
            }
    
    def _check_variable_count(self, content: str) -> Dict[str, Any]:
        """변수 개수 검사"""
        variables = re.findall(r'#\{([^}]+)\}', content)
        var_count = len(variables)
        
        if var_count > 40:
            return {
                "status": "failed",
                "message": f"변수 개수 제한 위반 ({var_count}/40개)",
                "severity": "critical", 
                "recommendation": f"{var_count - 40}개 변수를 줄여주세요"
            }
        elif var_count > 30:
            return {
                "status": "warning",
                "message": f"변수 개수 주의 필요 ({var_count}/40개)",
                "severity": "medium",
                "recommendation": "변수 개수를 줄이는 것을 권장합니다"
            }
        else:
            return {
                "status": "passed",
                "message": f"변수 개수 적절 ({var_count}/40개)",
                "severity": "none"
            }
    
    def _check_variable_format(self, content: str) -> Dict[str, Any]:
        """변수 형식 검사"""
        variables = re.findall(r'#\{([^}]+)\}', content)
        invalid_vars = []
        
        for var in variables:
            if not re.match(r'^[a-zA-Z0-9_]+$', var) or len(var) > 50:
                invalid_vars.append(var)
        
        if invalid_vars:
            return {
                "status": "failed",
                "message": f"잘못된 변수 형식: {', '.join(invalid_vars)}",
                "severity": "high",
                "recommendation": "변수명은 영문, 숫자, 언더스코어만 사용하고 50자 이하로 작성하세요"
            }
        else:
            return {
                "status": "passed",
                "message": "모든 변수 형식이 올바릅니다",
                "severity": "none"
            }
    
    def _check_basic_content(self, content: str) -> Dict[str, Any]:
        """기본 콘텐츠 검사"""
        forbidden_keywords = ["광고", "할인", "무료", "이벤트", "쿠폰"]
        found_keywords = [kw for kw in forbidden_keywords if kw in content]
        
        if found_keywords:
            return {
                "status": "warning",
                "message": f"주의 필요 키워드: {', '.join(found_keywords)}",
                "severity": "medium",
                "recommendation": "광고성 표현을 정보성 표현으로 변경하세요"
            }
        else:
            return {
                "status": "passed",
                "message": "기본 콘텐츠 검사 통과",
                "severity": "none"
            }
    
    def _check_advanced_content(self, content: str) -> Dict[str, Any]:
        """고급 콘텐츠 검사"""
        # 개인정보 패턴 검사
        personal_patterns = [
            r'\d{6}-\d{7}',  # 주민등록번호 패턴
            r'\d{4}-\d{4}-\d{4}-\d{4}',  # 카드번호 패턴
            r'\d{3}-\d{2}-\d{6}'  # 계좌번호 패턴
        ]
        
        violations = []
        for pattern in personal_patterns:
            if re.search(pattern, content):
                violations.append("개인정보 유사 패턴 발견")
        
        if violations:
            return {
                "status": "failed",
                "message": "; ".join(violations),
                "severity": "critical",
                "recommendation": "개인정보가 직접 포함되지 않도록 변수를 사용하세요"
            }
        else:
            return {
                "status": "passed",
                "message": "고급 콘텐츠 검사 통과",
                "severity": "none"
            }
    
    def _check_business_compliance(self, content: str) -> Dict[str, Any]:
        """비즈니스 준수 검사"""
        # 업종별 특별 규정 확인 (간단한 예시)
        compliance_issues = []
        
        # 금융업 관련
        if any(keyword in content for keyword in ["금융", "은행", "투자", "대출"]):
            if "수익률" in content or "보장" in content:
                compliance_issues.append("금융업 광고 규정 위반 가능성")
        
        # 의료업 관련
        if any(keyword in content for keyword in ["치료", "효과", "질병"]):
            compliance_issues.append("의료광고 규정 확인 필요")
        
        if compliance_issues:
            return {
                "status": "warning",
                "message": "; ".join(compliance_issues),
                "severity": "medium",
                "recommendation": "업종별 특별 규정을 확인하고 수정하세요"
            }
        else:
            return {
                "status": "passed",
                "message": "비즈니스 준수 검사 통과",
                "severity": "none"
            }
    
    def _check_accessibility(self, content: str) -> Dict[str, Any]:
        """접근성 검사"""
        accessibility_issues = []
        
        # 가독성 검사
        if len(content.split('\n')) == 1 and len(content) > 200:
            accessibility_issues.append("긴 텍스트에 줄바꿈이 없어 가독성이 떨어질 수 있습니다")
        
        # 특수문자 과다 사용 검사
        special_char_count = len(re.findall(r'[!@#$%^&*(),.?":{}|<>]', content))
        if special_char_count > len(content) * 0.1:
            accessibility_issues.append("특수문자 사용이 과도할 수 있습니다")
        
        if accessibility_issues:
            return {
                "status": "warning",
                "message": "; ".join(accessibility_issues),
                "severity": "low",
                "recommendation": "가독성을 위해 구조를 개선하세요"
            }
        else:
            return {
                "status": "passed",
                "message": "접근성 검사 통과",
                "severity": "none"
            }
    
    def _extract_priority_issues(self, detailed_results: Dict) -> List[Dict[str, Any]]:
        """우선순위 이슈 추출"""
        priority_issues = []
        
        for check_name, result in detailed_results.items():
            if result["status"] in ["failed", "warning"]:
                priority = self._get_issue_priority(result.get("severity", "medium"))
                priority_issues.append({
                    "check": check_name,
                    "severity": result.get("severity", "medium"),
                    "priority": priority,
                    "message": result["message"],
                    "recommendation": result.get("recommendation", "")
                })
        
        # 우선순위 순으로 정렬
        priority_order = {"critical": 1, "high": 2, "medium": 3, "low": 4}
        priority_issues.sort(key=lambda x: priority_order.get(x["severity"], 5))
        
        return priority_issues
    
    def _get_issue_priority(self, severity: str) -> str:
        """심각도에 따른 우선순위 반환"""
        priority_map = {
            "critical": "즉시 수정 필요",
            "high": "수정 권장",
            "medium": "개선 권장",
            "low": "선택적 개선"
        }
        return priority_map.get(severity, "검토 필요")
    
    def _calculate_compliance_score(self, summary: Dict) -> float:
        """준수 점수 계산"""
        total = summary["total_checks"]
        if total == 0:
            return 0.0
        
        passed = summary["passed_checks"]
        warning = summary["warning_checks"]
        failed = summary["failed_checks"]
        
        # 점수 계산 (통과: 100%, 경고: 70%, 실패: 0%)
        score = (passed * 100 + warning * 70 + failed * 0) / total
        return round(score, 1)

class ViolationDetectorToolInput(BaseModel):
    """위반 탐지 도구 입력 스키마"""
    template_content: str = Field(description="위반 사항을 탐지할 템플릿 내용")
    detection_mode: str = Field(default="strict", description="탐지 모드 (strict, moderate, lenient)")

class ViolationDetectorTool(BaseTool):
    """
    정책 위반 탐지 도구
    템플릿에서 정책 위반 사항을 정밀하게 탐지하고 분류
    """
    name: str = "violation_detector"
    description: str = """
    템플릿에서 카카오 알림톡 정책 위반 사항을 정밀하게 탐지합니다.
    - 위반 유형별 분류
    - 위반 심각도 평가
    - 구체적인 위반 내용 식별
    입력: template_content, detection_mode (strict/moderate/lenient)
    """
    args_schema = ViolationDetectorToolInput
    
    def _run(self, template_content: str, detection_mode: str = "strict") -> str:
        """
        정책 위반 탐지 실행
        
        Args:
            template_content: 탐지할 템플릿 내용
            detection_mode: 탐지 모드
            
        Returns:
            위반 탐지 결과 JSON 문자열
        """
        try:
            result = {
                "detection_mode": detection_mode,
                "violations_found": [],
                "violation_summary": {
                    "total_violations": 0,
                    "critical_violations": 0,
                    "major_violations": 0,
                    "minor_violations": 0
                },
                "clean_areas": [],
                "risk_assessment": ""
            }
            
            # 위반 탐지 실행
            violations = self._detect_all_violations(template_content, detection_mode)
            result["violations_found"] = violations
            
            # 요약 정보 계산
            result["violation_summary"] = self._calculate_violation_summary(violations)
            
            # 정상 영역 식별
            result["clean_areas"] = self._identify_clean_areas(template_content, violations)
            
            # 위험도 평가
            result["risk_assessment"] = self._assess_risk_level(result["violation_summary"])
            
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"위반 탐지 중 오류: {str(e)}")
            return json.dumps({
                "error": f"위반 탐지 중 오류가 발생했습니다: {str(e)}",
                "violations_found": [],
                "detection_mode": detection_mode
            }, ensure_ascii=False)
    
    def _detect_all_violations(self, content: str, mode: str) -> List[Dict[str, Any]]:
        """모든 위반 사항 탐지"""
        violations = []
        
        # 길이 위반 탐지
        violations.extend(self._detect_length_violations(content, mode))
        
        # 변수 위반 탐지
        violations.extend(self._detect_variable_violations(content, mode))
        
        # 콘텐츠 위반 탐지
        violations.extend(self._detect_content_violations(content, mode))
        
        # 형식 위반 탐지
        violations.extend(self._detect_format_violations(content, mode))
        
        # 고급 위반 탐지
        if mode == "strict":
            violations.extend(self._detect_advanced_violations(content))
        
        return violations
    
    def _detect_length_violations(self, content: str, mode: str) -> List[Dict[str, Any]]:
        """길이 관련 위반 탐지"""
        violations = []
        char_count = len(content)
        
        if char_count > 1000:
            violations.append({
                "type": "length_violation",
                "severity": "critical",
                "message": f"최대 길이 초과: {char_count}/1000자",
                "location": "전체",
                "excess_amount": char_count - 1000,
                "suggestion": f"{char_count - 1000}자를 줄여주세요"
            })
        elif char_count > 800 and mode == "strict":
            violations.append({
                "type": "length_warning",
                "severity": "minor",
                "message": f"권장 길이 초과: {char_count}/800자",
                "location": "전체",
                "excess_amount": char_count - 800,
                "suggestion": "길이를 줄이는 것을 권장합니다"
            })
        
        return violations
    
    def _detect_variable_violations(self, content: str, mode: str) -> List[Dict[str, Any]]:
        """변수 관련 위반 탐지"""
        violations = []
        variables = re.findall(r'#\{([^}]+)\}', content)
        
        # 변수 개수 위반
        if len(variables) > 40:
            violations.append({
                "type": "variable_count_violation",
                "severity": "critical",
                "message": f"변수 개수 초과: {len(variables)}/40개",
                "location": "전체",
                "excess_amount": len(variables) - 40,
                "suggestion": f"{len(variables) - 40}개 변수를 줄여주세요"
            })
        
        # 변수명 형식 위반
        invalid_vars = []
        for var in variables:
            if not re.match(r'^[a-zA-Z0-9_]+$', var):
                invalid_vars.append(var)
            elif len(var) > 50:
                invalid_vars.append(f"{var} (길이초과)")
        
        if invalid_vars:
            violations.append({
                "type": "variable_format_violation",
                "severity": "major",
                "message": f"잘못된 변수명: {', '.join(invalid_vars)}",
                "location": "변수명",
                "invalid_variables": invalid_vars,
                "suggestion": "변수명은 영문, 숫자, 언더스코어만 사용하고 50자 이하로 작성하세요"
            })
        
        return violations
    
    def _detect_content_violations(self, content: str, mode: str) -> List[Dict[str, Any]]:
        """콘텐츠 관련 위반 탐지"""
        violations = []
        
        # 광고성 키워드 탐지
        ad_keywords = ["광고", "할인", "무료", "이벤트", "쿠폰", "증정", "혜택"]
        found_ad_keywords = [kw for kw in ad_keywords if kw in content]
        
        if found_ad_keywords:
            severity = "major" if mode == "strict" else "minor"
            violations.append({
                "type": "advertising_content_violation",
                "severity": severity,
                "message": f"광고성 키워드 발견: {', '.join(found_ad_keywords)}",
                "location": "내용",
                "found_keywords": found_ad_keywords,
                "suggestion": "광고성 표현을 정보성 표현으로 변경하세요"
            })
        
        # 불법 키워드 탐지
        illegal_keywords = ["도박", "사행성", "불법", "마약"]
        found_illegal_keywords = [kw for kw in illegal_keywords if kw in content]
        
        if found_illegal_keywords:
            violations.append({
                "type": "illegal_content_violation",
                "severity": "critical",
                "message": f"불법 키워드 발견: {', '.join(found_illegal_keywords)}",
                "location": "내용",
                "found_keywords": found_illegal_keywords,
                "suggestion": "불법적 내용을 즉시 제거하세요"
            })
        
        # 개인정보 패턴 탐지
        personal_info_patterns = [
            (r'\d{6}-\d{7}', "주민등록번호 패턴"),
            (r'\d{4}-\d{4}-\d{4}-\d{4}', "카드번호 패턴"),
            (r'\d{3}-\d{2}-\d{6}', "계좌번호 패턴")
        ]
        
        for pattern, description in personal_info_patterns:
            if re.search(pattern, content):
                violations.append({
                    "type": "personal_info_violation",
                    "severity": "critical",
                    "message": f"{description} 발견",
                    "location": "내용",
                    "pattern": description,
                    "suggestion": "개인정보를 변수로 대체하세요"
                })
        
        return violations
    
    def _detect_format_violations(self, content: str, mode: str) -> List[Dict[str, Any]]:
        """형식 관련 위반 탐지"""
        violations = []
        
        # 잘못된 변수 형식 탐지
        wrong_variable_formats = [
            (r'\$\{[^}]+\}', "잘못된 변수 형식 ${} 사용"),
            (r'\%\{[^}]+\}', "잘못된 변수 형식 %{} 사용"),
            (r'\#\[[^\]]+\]', "잘못된 변수 형식 #[] 사용")
        ]
        
        for pattern, description in wrong_variable_formats:
            matches = re.findall(pattern, content)
            if matches:
                violations.append({
                    "type": "format_violation",
                    "severity": "major",
                    "message": f"{description}: {', '.join(matches)}",
                    "location": "변수 형식",
                    "wrong_formats": matches,
                    "suggestion": "#{변수명} 형식을 사용하세요"
                })
        
        return violations
    
    def _detect_advanced_violations(self, content: str) -> List[Dict[str, Any]]:
        """고급 위반 탐지 (strict 모드에서만)"""
        violations = []
        
        # 과도한 특수문자 사용
        special_chars = re.findall(r'[!@#$%^&*(),.?":{}|<>]', content)
        if len(special_chars) > len(content) * 0.15:
            violations.append({
                "type": "excessive_special_chars",
                "severity": "minor",
                "message": f"특수문자 과다 사용: {len(special_chars)}개",
                "location": "전체",
                "count": len(special_chars),
                "suggestion": "특수문자 사용을 줄여주세요"
            })
        
        # 반복되는 내용 탐지
        lines = content.split('\n')
        duplicate_lines = []
        for i, line in enumerate(lines):
            if line.strip() and lines.count(line) > 1:
                duplicate_lines.append(line.strip())
        
        if duplicate_lines:
            violations.append({
                "type": "duplicate_content",
                "severity": "minor",
                "message": f"중복 내용 발견: {len(set(duplicate_lines))}건",
                "location": "전체",
                "duplicates": list(set(duplicate_lines)),
                "suggestion": "중복 내용을 정리하세요"
            })
        
        return violations
    
    def _calculate_violation_summary(self, violations: List[Dict]) -> Dict[str, int]:
        """위반 요약 정보 계산"""
        summary = {
            "total_violations": len(violations),
            "critical_violations": 0,
            "major_violations": 0,
            "minor_violations": 0
        }
        
        for violation in violations:
            severity = violation.get("severity", "minor")
            if severity == "critical":
                summary["critical_violations"] += 1
            elif severity == "major":
                summary["major_violations"] += 1
            else:
                summary["minor_violations"] += 1
        
        return summary
    
    def _identify_clean_areas(self, content: str, violations: List[Dict]) -> List[str]:
        """위반이 없는 정상 영역 식별"""
        clean_areas = []
        
        if not any(v["type"].startswith("length") for v in violations):
            clean_areas.append("적절한 길이")
        
        if not any(v["type"].startswith("variable") for v in violations):
            clean_areas.append("올바른 변수 사용")
        
        if not any(v["type"].startswith("content") for v in violations):
            clean_areas.append("적절한 콘텐츠")
        
        if not any(v["type"].startswith("format") for v in violations):
            clean_areas.append("올바른 형식")
        
        return clean_areas
    
    def _assess_risk_level(self, summary: Dict) -> str:
        """위험도 평가"""
        critical = summary["critical_violations"]
        major = summary["major_violations"] 
        minor = summary["minor_violations"]
        
        if critical > 0:
            return "높음 - 즉시 수정 필요"
        elif major > 2:
            return "보통 - 수정 권장"
        elif major > 0 or minor > 3:
            return "낮음 - 개선 권장"
        else:
            return "매우 낮음 - 양호"

class ImprovementSuggestorToolInput(BaseModel):
    """개선 제안 도구 입력 스키마"""
    template_content: str = Field(description="개선할 템플릿 내용")
    violation_results: Optional[str] = Field(None, description="위반 탐지 결과 (JSON)")
    target_business: Optional[str] = Field(None, description="대상 비즈니스 유형")

class ImprovementSuggestorTool(BaseTool):
    """
    개선 제안 도구
    탐지된 위반사항을 바탕으로 구체적인 개선 방안 제시
    """
    name: str = "improvement_suggestor"
    description: str = """
    템플릿의 정책 위반 사항에 대한 구체적인 개선 방안을 제시합니다.
    - 위반별 맞춤 개선안
    - 단계별 수정 가이드
    - 대안 표현 제시
    입력: template_content, violation_results (선택), target_business (선택)
    """
    args_schema = ImprovementSuggestorToolInput
    
    def _run(
        self, 
        template_content: str, 
        violation_results: Optional[str] = None,
        target_business: Optional[str] = None
    ) -> str:
        """
        개선 제안 실행
        
        Args:
            template_content: 개선할 템플릿 내용
            violation_results: 위반 탐지 결과
            target_business: 대상 비즈니스 유형
            
        Returns:
            개선 제안 결과 JSON 문자열
        """
        try:
            result = {
                "improvement_plan": {
                    "priority_fixes": [],
                    "optional_improvements": [],
                    "business_optimizations": []
                },
                "step_by_step_guide": [],
                "alternative_expressions": {},
                "estimated_effort": "",
                "expected_compliance_score": 0.0
            }
            
            # 위반 결과 파싱
            violations = self._parse_violation_results(violation_results) if violation_results else []
            
            # 개선 계획 생성
            result["improvement_plan"] = self._generate_improvement_plan(
                template_content, violations, target_business
            )
            
            # 단계별 가이드 생성
            result["step_by_step_guide"] = self._generate_step_guide(
                template_content, violations
            )
            
            # 대안 표현 제시
            result["alternative_expressions"] = self._suggest_alternatives(
                template_content, violations
            )
            
            # 작업량 추정
            result["estimated_effort"] = self._estimate_effort(violations)
            
            # 예상 점수 계산
            result["expected_compliance_score"] = self._estimate_compliance_score(violations)
            
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"개선 제안 중 오류: {str(e)}")
            return json.dumps({
                "error": f"개선 제안 중 오류가 발생했습니다: {str(e)}",
                "improvement_plan": {"priority_fixes": [], "optional_improvements": []}
            }, ensure_ascii=False)
    
    def _parse_violation_results(self, violation_json: str) -> List[Dict]:
        """위반 결과 JSON 파싱"""
        try:
            data = json.loads(violation_json)
            return data.get("violations_found", [])
        except:
            return []
    
    def _generate_improvement_plan(
        self, 
        content: str, 
        violations: List[Dict], 
        business: Optional[str]
    ) -> Dict[str, List]:
        """개선 계획 생성"""
        plan = {
            "priority_fixes": [],
            "optional_improvements": [],
            "business_optimizations": []
        }
        
        # 위반사항별 수정 계획
        for violation in violations:
            severity = violation.get("severity", "minor")
            fix_item = {
                "issue": violation.get("message", ""),
                "action": violation.get("suggestion", ""),
                "severity": severity
            }
            
            if severity in ["critical", "major"]:
                plan["priority_fixes"].append(fix_item)
            else:
                plan["optional_improvements"].append(fix_item)
        
        # 비즈니스별 최적화 제안
        if business:
            business_opts = self._generate_business_optimizations(content, business)
            plan["business_optimizations"].extend(business_opts)
        
        return plan
    
    def _generate_business_optimizations(self, content: str, business: str) -> List[Dict]:
        """비즈니스 유형별 최적화 제안"""
        optimizations = []
        
        business_lower = business.lower()
        
        if "전자상거래" in business_lower or "쇼핑" in business_lower:
            optimizations.append({
                "category": "전자상거래",
                "suggestion": "주문번호, 배송정보 변수 활용",
                "example": "#{order_number}, #{delivery_status}"
            })
        
        if "금융" in business_lower:
            optimizations.append({
                "category": "금융",
                "suggestion": "개인정보 보호를 위한 변수 사용 강화",
                "example": "계좌번호 대신 #{masked_account} 사용"
            })
        
        if "의료" in business_lower:
            optimizations.append({
                "category": "의료",
                "suggestion": "의료광고 규정 준수 표현 사용",
                "example": "진료 안내용 정보성 메시지로 작성"
            })
        
        return optimizations
    
    def _generate_step_guide(self, content: str, violations: List[Dict]) -> List[Dict]:
        """단계별 수정 가이드 생성"""
        steps = []
        step_num = 1
        
        # 중요도 순으로 정렬
        sorted_violations = sorted(
            violations, 
            key=lambda x: {"critical": 1, "major": 2, "minor": 3}.get(x.get("severity", "minor"), 4)
        )
        
        for violation in sorted_violations:
            if violation.get("severity") in ["critical", "major"]:
                steps.append({
                    "step": step_num,
                    "title": f"{violation.get('type', '').replace('_', ' ').title()} 수정",
                    "description": violation.get("message", ""),
                    "action": violation.get("suggestion", ""),
                    "priority": "높음" if violation.get("severity") == "critical" else "보통"
                })
                step_num += 1
        
        # 최종 검증 단계 추가
        if steps:
            steps.append({
                "step": step_num,
                "title": "최종 검증",
                "description": "모든 수정사항 적용 후 재검사",
                "action": "수정된 템플릿으로 정책 준수 검사 재실행",
                "priority": "필수"
            })
        
        return steps
    
    def _suggest_alternatives(self, content: str, violations: List[Dict]) -> Dict[str, List]:
        """대안 표현 제시"""
        alternatives = {}
        
        # 광고성 표현 대안
        ad_alternatives = {
            "할인": ["특가", "혜택", "안내"],
            "무료": ["제공", "지원", "포함"],
            "이벤트": ["행사", "프로그램", "서비스"],
            "쿠폰": ["혜택", "적립", "포인트"]
        }
        
        for violation in violations:
            if violation.get("type") == "advertising_content_violation":
                found_keywords = violation.get("found_keywords", [])
                for keyword in found_keywords:
                    if keyword in ad_alternatives:
                        alternatives[keyword] = ad_alternatives[keyword]
        
        # 변수명 대안
        var_alternatives = {}
        for violation in violations:
            if violation.get("type") == "variable_format_violation":
                invalid_vars = violation.get("invalid_variables", [])
                for var in invalid_vars:
                    # 간단한 변수명 수정 제안
                    clean_var = re.sub(r'[^a-zA-Z0-9_]', '_', var)
                    if clean_var != var:
                        var_alternatives[var] = [clean_var, f"{clean_var}_value"]
        
        if var_alternatives:
            alternatives["변수명"] = var_alternatives
        
        return alternatives
    
    def _estimate_effort(self, violations: List[Dict]) -> str:
        """작업량 추정"""
        critical_count = len([v for v in violations if v.get("severity") == "critical"])
        major_count = len([v for v in violations if v.get("severity") == "major"])
        minor_count = len([v for v in violations if v.get("severity") == "minor"])
        
        total_score = critical_count * 3 + major_count * 2 + minor_count * 1
        
        if total_score == 0:
            return "작업 불필요 - 이미 정책을 준수합니다"
        elif total_score <= 3:
            return "소규모 작업 - 5-10분 소요 예상"
        elif total_score <= 8:
            return "중간 규모 작업 - 15-30분 소요 예상"
        else:
            return "대규모 작업 - 1시간 이상 소요 예상"
    
    def _estimate_compliance_score(self, violations: List[Dict]) -> float:
        """개선 후 예상 준수 점수"""
        critical_count = len([v for v in violations if v.get("severity") == "critical"])
        major_count = len([v for v in violations if v.get("severity") == "major"])
        minor_count = len([v for v in violations if v.get("severity") == "minor"])
        
        # 현재 점수에서 개선 후 점수 추정
        current_penalty = critical_count * 30 + major_count * 20 + minor_count * 10
        improved_score = 100 - max(0, current_penalty - 50)  # 개선으로 50% 페널티 감소 가정
        
        return round(min(100.0, improved_score), 1)