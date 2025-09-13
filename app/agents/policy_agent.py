"""
정책 준수 검증 AI 에이전트  
카카오 알림톡 정책 준수 여부를 분석하고 개선안을 제시하는 에이전트
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import re
import json

from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langchain.tools import BaseTool
from langchain_openai import ChatOpenAI

from app.services.rag_service import rag_service
from app.tools.policy_tools import (
    PolicyRuleTool,
    ComplianceCheckerTool,
    ViolationDetectorTool,
    ImprovementSuggestorTool
)

logger = logging.getLogger(__name__)

class PolicyComplianceAgent:
    """
    정책 준수 검증 AI 에이전트
    
    주요 기능:
    - 템플릿의 카카오 알림톡 정책 준수 여부 상세 분석
    - 정책 위반 사항 탐지 및 분류
    - 구체적인 개선 방안 제시
    - 정책 업데이트 반영 및 최신 규정 적용
    """
    
    def __init__(self, llm: Optional[ChatOpenAI] = None):
        """
        에이전트 초기화
        
        Args:
            llm: OpenAI LLM 인스턴스 (선택사항)
        """
        self.llm = llm or ChatOpenAI(
            model="gpt-4",
            temperature=0.1,  # 정확성 최우선 (창의성 최소화)
            max_tokens=2000
        )
        
        # 정책 규칙 로드
        self.policy_rules = self._load_policy_rules()
        
        # 도구 초기화
        self.tools = self._initialize_tools()
        
        # 프롬프트 템플릿 설정
        self.prompt = self._create_prompt_template()
        
        # 에이전트 생성
        self.agent = create_openai_functions_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
        
        # 에이전트 실행기 생성
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=3,
            max_execution_time=30
        )
        
        logger.info("PolicyComplianceAgent 초기화 완료")
    
    def _load_policy_rules(self) -> Dict[str, Any]:
        """
        카카오 알림톡 정책 규칙 로드
        
        Returns:
            정책 규칙 딕셔너리
        """
        return {
            "length_limit": {
                "max_characters": 1000,
                "description": "템플릿 전체 길이는 1,000자 이하여야 함"
            },
            "variable_limit": {
                "max_variables": 40,
                "description": "변수는 40개 이하여야 함",
                "format": "#{변수명}"
            },
            "forbidden_content": {
                "advertising": ["광고", "홍보", "할인", "무료", "이벤트", "쿠폰"],
                "illegal": ["도박", "사행성", "불법"],
                "harmful": ["성인", "폭력", "혐오"],
                "description": "광고성, 불법, 유해 콘텐츠 금지"
            },
            "personal_info": {
                "forbidden": ["주민등록번호", "여권번호", "신용카드번호", "계좌번호"],
                "description": "개인정보 직접 포함 금지"
            },
            "message_type": {
                "allowed": ["정보성", "거래성", "확인성"],
                "description": "승인된 메시지 유형만 사용 가능"
            },
            "variable_rules": {
                "naming": "영문, 숫자, 언더스코어만 사용",
                "length": "변수명은 50자 이하",
                "description": "변수 명명 규칙 준수"
            }
        }
    
    def _initialize_tools(self) -> List[BaseTool]:
        """
        에이전트가 사용할 도구들을 초기화
        
        Returns:
            도구 목록
        """
        return [
            PolicyRuleTool(),
            ComplianceCheckerTool(),
            ViolationDetectorTool(),
            ImprovementSuggestorTool()
        ]
    
    def _create_prompt_template(self) -> ChatPromptTemplate:
        """
        에이전트용 프롬프트 템플릿 생성
        
        Returns:
            프롬프트 템플릿
        """
        system_message = """
당신은 카카오 알림톡 정책 준수 검증 전문 AI 에이전트입니다.

### 주요 역할:
1. 템플릿의 카카오 알림톡 정책 준수 여부 정밀 분석
2. 정책 위반 사항의 정확한 탐지 및 분류
3. 구체적이고 실행 가능한 개선 방안 제시
4. 최신 정책 업데이트 반영

### 검증해야 할 핵심 정책:
1. **길이 제한**: 1,000자 이하
2. **변수 제한**: 40개 이하, #{변수명} 형식
3. **콘텐츠 제한**: 
   - 광고성 콘텐츠 금지 (할인, 무료, 이벤트 등)
   - 불법/유해 콘텐츠 금지
   - 개인정보 직접 포함 금지
4. **메시지 유형**: 정보성, 거래성, 확인성만 허용
5. **변수 명명 규칙**: 영문, 숫자, 언더스코어만 사용

### 분석 절차:
1. 템플릿 기본 정보 추출 (길이, 변수 개수 등)
2. 각 정책 규칙별 상세 검증
3. 위반 사항 식별 및 심각도 평가
4. 개선 방안 도출 및 우선순위 설정
5. 최종 점수 산출 및 종합 평가

### 응답 형식:
- 검증 결과는 구조화된 JSON 형태로 제공
- 위반 사항은 구체적으로 명시
- 개선 방안은 단계별로 제시
- 정책 준수 점수는 0-100 스케일로 산출

정확하고 엄격한 기준으로 정책 준수를 검증하세요.
        """
        
        return ChatPromptTemplate.from_messages([
            ("system", system_message),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
    
    def analyze_compliance(
        self,
        template_content: str,
        business_type: Optional[str] = None,
        template_type: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        템플릿 정책 준수 분석 메인 메서드
        
        Args:
            template_content: 검증할 템플릿 내용
            business_type: 비즈니스 유형
            template_type: 템플릿 유형  
            additional_context: 추가 컨텍스트
            
        Returns:
            상세한 준수 분석 결과
        """
        try:
            start_time = datetime.now()
            
            # 기본 분석 수행
            basic_analysis = self._basic_analysis(template_content)
            
            # 에이전트 입력 구성
            input_data = {
                "input": self._format_compliance_input(
                    template_content=template_content,
                    basic_analysis=basic_analysis,
                    business_type=business_type,
                    template_type=template_type,
                    additional_context=additional_context
                ),
                "chat_history": []
            }
            
            # 에이전트 실행
            result = self.agent_executor.invoke(input_data)
            
            # 처리 시간 계산
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 결과 구조화
            compliance_result = self._structure_compliance_result(
                agent_result=result,
                basic_analysis=basic_analysis,
                processing_time=processing_time
            )
            
            logger.info(f"정책 준수 분석 완료 (처리시간: {processing_time:.2f}초)")
            
            return compliance_result
            
        except Exception as e:
            logger.error(f"정책 준수 분석 중 오류: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "compliance_score": 0.0,
                "violations": [{"type": "system_error", "message": f"분석 중 오류: {str(e)}"}],
                "suggestions": ["시스템 오류로 분석을 완료할 수 없습니다."]
            }
    
    def _basic_analysis(self, template_content: str) -> Dict[str, Any]:
        """
        템플릿 기본 분석 수행
        
        Args:
            template_content: 템플릿 내용
            
        Returns:
            기본 분석 결과
        """
        # 변수 추출
        variables = re.findall(r'#\{([^}]+)\}', template_content)
        
        # 기본 정보 추출
        analysis = {
            "character_count": len(template_content),
            "variable_count": len(variables),
            "variables": variables,
            "line_count": len(template_content.split('\n')),
            "word_count": len(template_content.split()),
            "has_korean": bool(re.search(r'[가-힣]', template_content)),
            "has_english": bool(re.search(r'[a-zA-Z]', template_content)),
            "has_numbers": bool(re.search(r'\d', template_content))
        }
        
        return analysis
    
    def _format_compliance_input(
        self,
        template_content: str,
        basic_analysis: Dict[str, Any],
        business_type: Optional[str],
        template_type: Optional[str],
        additional_context: Optional[Dict[str, Any]]
    ) -> str:
        """
        정책 준수 검증용 입력 포맷팅
        
        Args:
            template_content: 템플릿 내용
            basic_analysis: 기본 분석 결과
            business_type: 비즈니스 유형
            template_type: 템플릿 유형
            additional_context: 추가 컨텍스트
            
        Returns:
            포맷된 입력 텍스트
        """
        formatted_input = f"""
다음 카카오 알림톡 템플릿의 정책 준수 여부를 상세히 분석해주세요:

### 템플릿 내용:
{template_content}

### 기본 정보:
- 전체 글자 수: {basic_analysis['character_count']}자
- 변수 개수: {basic_analysis['variable_count']}개
- 변수 목록: {', '.join(basic_analysis['variables']) if basic_analysis['variables'] else '없음'}
"""
        
        if business_type:
            formatted_input += f"- 비즈니스 유형: {business_type}\n"
        
        if template_type:
            formatted_input += f"- 템플릿 유형: {template_type}\n"
        
        if additional_context:
            formatted_input += f"- 추가 정보: {additional_context}\n"
        
        formatted_input += """
### 검증 요청사항:
1. 모든 카카오 알림톡 정책 규칙 준수 여부 확인
2. 위반 사항 상세 식별 및 심각도 평가
3. 구체적인 개선 방안 제시
4. 정책 준수 점수 산출 (0-100점)

정확하고 엄격한 기준으로 분석하여 JSON 형태의 구조화된 결과를 제공해주세요.
        """
        
        return formatted_input
    
    def _structure_compliance_result(
        self,
        agent_result: Dict[str, Any],
        basic_analysis: Dict[str, Any],
        processing_time: float
    ) -> Dict[str, Any]:
        """
        에이전트 결과를 구조화된 준수 분석 결과로 변환
        
        Args:
            agent_result: 에이전트 실행 결과
            basic_analysis: 기본 분석 결과
            processing_time: 처리 시간
            
        Returns:
            구조화된 준수 분석 결과
        """
        try:
            # 기본 결과 구조 생성
            compliance_result = {
                "success": True,
                "compliance_score": 0.0,
                "analysis_summary": {
                    "total_violations": 0,
                    "critical_violations": 0,
                    "warning_violations": 0,
                    "passed_checks": 0
                },
                "detailed_analysis": {
                    "length_check": self._check_length_compliance(basic_analysis),
                    "variable_check": self._check_variable_compliance(basic_analysis),
                    "content_check": self._check_content_compliance(agent_result.get("output", "")),
                    "format_check": self._check_format_compliance(basic_analysis)
                },
                "violations": [],
                "suggestions": [],
                "processing_time": processing_time,
                "metadata": {
                    "analysis_date": datetime.now().isoformat(),
                    "agent_version": "1.0.0",
                    "policy_version": "2024.1"
                }
            }
            
            # 상세 분석 결과를 바탕으로 위반사항 및 제안사항 추출
            self._extract_violations_and_suggestions(compliance_result)
            
            # 최종 점수 계산
            compliance_result["compliance_score"] = self._calculate_final_score(compliance_result)
            
            return compliance_result
            
        except Exception as e:
            logger.error(f"준수 분석 결과 구조화 중 오류: {str(e)}")
            return {
                "success": False,
                "error": f"결과 구조화 실패: {str(e)}",
                "compliance_score": 0.0,
                "violations": [{"type": "processing_error", "message": str(e)}],
                "suggestions": ["분석 결과 처리 중 오류가 발생했습니다."]
            }
    
    def _check_length_compliance(self, basic_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        길이 제한 준수 검사
        
        Args:
            basic_analysis: 기본 분석 결과
            
        Returns:
            길이 검사 결과
        """
        character_count = basic_analysis["character_count"]
        max_length = self.policy_rules["length_limit"]["max_characters"]
        
        return {
            "passed": character_count <= max_length,
            "current_length": character_count,
            "max_allowed": max_length,
            "violation_severity": "critical" if character_count > max_length else None,
            "excess_characters": max(0, character_count - max_length)
        }
    
    def _check_variable_compliance(self, basic_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        변수 규칙 준수 검사
        
        Args:
            basic_analysis: 기본 분석 결과
            
        Returns:
            변수 검사 결과
        """
        variable_count = basic_analysis["variable_count"]
        variables = basic_analysis["variables"]
        max_variables = self.policy_rules["variable_limit"]["max_variables"]
        
        # 변수명 유효성 검사
        invalid_variables = []
        for var in variables:
            if not re.match(r'^[a-zA-Z0-9_]+$', var):
                invalid_variables.append(var)
        
        return {
            "passed": variable_count <= max_variables and not invalid_variables,
            "current_count": variable_count,
            "max_allowed": max_variables,
            "invalid_variables": invalid_variables,
            "violation_severity": "critical" if variable_count > max_variables else ("warning" if invalid_variables else None),
            "excess_variables": max(0, variable_count - max_variables)
        }
    
    def _check_content_compliance(self, content: str) -> Dict[str, Any]:
        """
        콘텐츠 규칙 준수 검사
        
        Args:
            content: 검사할 내용
            
        Returns:
            콘텐츠 검사 결과
        """
        violations = []
        forbidden_rules = self.policy_rules["forbidden_content"]
        
        # 각 금지 카테고리별 검사
        for category, keywords in forbidden_rules.items():
            if category == "description":
                continue
                
            found_keywords = []
            for keyword in keywords:
                if keyword in content:
                    found_keywords.append(keyword)
            
            if found_keywords:
                violations.append({
                    "category": category,
                    "found_keywords": found_keywords,
                    "severity": "critical"
                })
        
        return {
            "passed": not violations,
            "violations": violations,
            "violation_severity": "critical" if violations else None
        }
    
    def _check_format_compliance(self, basic_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        형식 규칙 준수 검사
        
        Args:
            basic_analysis: 기본 분석 결과
            
        Returns:
            형식 검사 결과
        """
        variables = basic_analysis["variables"]
        format_issues = []
        
        # 변수명 길이 검사
        for var in variables:
            if len(var) > 50:
                format_issues.append(f"변수명 '{var}'가 너무 깁니다 (최대 50자)")
        
        return {
            "passed": not format_issues,
            "issues": format_issues,
            "violation_severity": "warning" if format_issues else None
        }
    
    def _extract_violations_and_suggestions(self, compliance_result: Dict[str, Any]) -> None:
        """
        상세 분석 결과에서 위반사항과 개선 제안사항 추출
        
        Args:
            compliance_result: 수정할 준수 분석 결과
        """
        violations = []
        suggestions = []
        
        # 길이 검사 결과 처리
        length_check = compliance_result["detailed_analysis"]["length_check"]
        if not length_check["passed"]:
            violations.append({
                "type": "length_violation",
                "severity": length_check["violation_severity"],
                "message": f"템플릿 길이가 {length_check['excess_characters']}자 초과되었습니다.",
                "details": f"현재: {length_check['current_length']}자, 최대: {length_check['max_allowed']}자"
            })
            suggestions.append(f"{length_check['excess_characters']}자를 줄여주세요.")
        
        # 변수 검사 결과 처리
        variable_check = compliance_result["detailed_analysis"]["variable_check"]
        if not variable_check["passed"]:
            if variable_check["excess_variables"] > 0:
                violations.append({
                    "type": "variable_count_violation",
                    "severity": "critical",
                    "message": f"변수 개수가 {variable_check['excess_variables']}개 초과되었습니다.",
                    "details": f"현재: {variable_check['current_count']}개, 최대: {variable_check['max_allowed']}개"
                })
                suggestions.append(f"변수를 {variable_check['excess_variables']}개 줄여주세요.")
            
            if variable_check["invalid_variables"]:
                violations.append({
                    "type": "variable_format_violation",
                    "severity": "warning",
                    "message": "잘못된 형식의 변수명이 있습니다.",
                    "details": f"문제 변수: {', '.join(variable_check['invalid_variables'])}"
                })
                suggestions.append("변수명은 영문, 숫자, 언더스코어만 사용하세요.")
        
        # 콘텐츠 검사 결과 처리
        content_check = compliance_result["detailed_analysis"]["content_check"]
        if not content_check["passed"]:
            for violation in content_check["violations"]:
                violations.append({
                    "type": f"content_{violation['category']}_violation",
                    "severity": violation["severity"],
                    "message": f"{violation['category']} 관련 금지 키워드가 발견되었습니다.",
                    "details": f"발견된 키워드: {', '.join(violation['found_keywords'])}"
                })
                suggestions.append(f"{', '.join(violation['found_keywords'])} 키워드를 제거하거나 대체하세요.")
        
        # 결과에 반영
        compliance_result["violations"] = violations
        compliance_result["suggestions"] = suggestions
        
        # 요약 정보 업데이트
        compliance_result["analysis_summary"]["total_violations"] = len(violations)
        compliance_result["analysis_summary"]["critical_violations"] = len([v for v in violations if v.get("severity") == "critical"])
        compliance_result["analysis_summary"]["warning_violations"] = len([v for v in violations if v.get("severity") == "warning"])
        compliance_result["analysis_summary"]["passed_checks"] = len([check for check in compliance_result["detailed_analysis"].values() if check.get("passed", False)])
    
    def _calculate_final_score(self, compliance_result: Dict[str, Any]) -> float:
        """
        최종 정책 준수 점수 계산
        
        Args:
            compliance_result: 준수 분석 결과
            
        Returns:
            정책 준수 점수 (0.0 ~ 100.0)
        """
        base_score = 100.0
        
        # 위반사항별 점수 차감
        for violation in compliance_result["violations"]:
            severity = violation.get("severity", "warning")
            
            if severity == "critical":
                base_score -= 25.0  # 중대한 위반
            elif severity == "warning":
                base_score -= 10.0  # 경고 수준 위반
        
        return max(0.0, base_score)

# 전역 인스턴스 생성
policy_compliance_agent = PolicyComplianceAgent()