"""
템플릿 생성 AI 에이전트
카카오 알림톡 정책을 준수하는 템플릿을 자동으로 생성하는 에이전트
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langchain.tools import BaseTool
from langchain_openai import ChatOpenAI

from app.services.rag_service import rag_service
from app.tools.template_tools import (
    TemplateValidatorTool,
    PolicyCheckerTool, 
    VariableExtractorTool,
    BusinessTypeSuggestorTool
)

logger = logging.getLogger(__name__)

class TemplateGenerationAgent:
    """
    템플릿 생성 AI 에이전트
    
    주요 기능:
    - 사용자 요청을 분석하여 알림톡 템플릿 생성
    - 카카오 알림톡 정책 준수 확인
    - 템플릿 품질 분석 및 개선 제안
    - 비즈니스 유형에 맞는 템플릿 최적화
    """
    
    def __init__(self, llm: Optional[ChatOpenAI] = None):
        """
        에이전트 초기화
        
        Args:
            llm: OpenAI LLM 인스턴스 (선택사항)
        """
        self.llm = llm or ChatOpenAI(
            model="gpt-4",
            temperature=0.2,  # 창의성 낮게 설정 (정확성 중시)
            max_tokens=2000
        )
        
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
            max_iterations=5,
            max_execution_time=60
        )
        
        logger.info("TemplateGenerationAgent 초기화 완료")
    
    def _initialize_tools(self) -> List[BaseTool]:
        """
        에이전트가 사용할 도구들을 초기화
        
        Returns:
            도구 목록
        """
        return [
            TemplateValidatorTool(),
            PolicyCheckerTool(),
            VariableExtractorTool(),
            BusinessTypeSuggestorTool()
        ]
    
    def _create_prompt_template(self) -> ChatPromptTemplate:
        """
        에이전트용 프롬프트 템플릿 생성
        
        Returns:
            프롬프트 템플릿
        """
        system_message = """
당신은 카카오 알림톡 템플릿 생성 전문 AI 에이전트입니다.

### 주요 역할:
1. 사용자 요청을 분석하여 적절한 알림톡 템플릿 생성
2. 카카오 알림톡 정책 완전 준수 확인
3. 비즈니스 유형에 최적화된 템플릿 제공
4. 템플릿 품질 분석 및 개선 제안

### 카카오 알림톡 핵심 정책:
- 템플릿 길이: 1,000자 이하
- 변수 개수: 40개 이하
- 변수 형식: #{변수명} 사용
- 광고성 내용 금지
- 불법/유해 콘텐츠 금지
- 개인정보 직접 포함 금지

### 템플릿 생성 과정:
1. 사용자 요청 분석 (비즈니스 유형, 메시지 목적 파악)
2. 관련 정책 문서 검색 및 확인
3. 초안 템플릿 작성
4. 정책 준수 검증
5. 품질 개선 및 최종 템플릿 제공

### 응답 형식:
- 명확하고 정확한 정보 제공
- 정책 위반 사항이 있다면 명시적으로 경고
- 개선 제안 포함

사용 가능한 도구들을 적극 활용하여 최고 품질의 템플릿을 생성하세요.
        """
        
        return ChatPromptTemplate.from_messages([
            ("system", system_message),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
    
    def generate_template(
        self,
        user_request: str,
        business_type: Optional[str] = None,
        template_type: Optional[str] = None,
        session_id: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        템플릿 생성 메인 메서드
        
        Args:
            user_request: 사용자 요청 텍스트
            business_type: 비즈니스 유형
            template_type: 템플릿 유형
            session_id: 세션 ID
            additional_context: 추가 컨텍스트
            
        Returns:
            생성된 템플릿 및 분석 결과
        """
        try:
            start_time = datetime.now()
            
            # 입력 데이터 구성
            input_data = {
                "input": self._format_user_input(
                    user_request=user_request,
                    business_type=business_type,
                    template_type=template_type,
                    additional_context=additional_context
                ),
                "chat_history": self._get_chat_history(session_id)
            }
            
            # 에이전트 실행
            result = self.agent_executor.invoke(input_data)
            
            # 처리 시간 계산
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 결과 파싱 및 구조화
            structured_result = self._parse_agent_result(result)
            structured_result["processing_time"] = processing_time
            structured_result["session_id"] = session_id
            
            logger.info(f"템플릿 생성 완료 (처리시간: {processing_time:.2f}초)")
            
            return structured_result
            
        except Exception as e:
            logger.error(f"템플릿 생성 중 오류: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "template_content": None,
                "analysis": {
                    "quality_score": 0.0,
                    "compliance_score": 0.0,
                    "suggestions": [f"생성 중 오류 발생: {str(e)}"]
                }
            }
    
    def _format_user_input(
        self,
        user_request: str,
        business_type: Optional[str],
        template_type: Optional[str],
        additional_context: Optional[Dict[str, Any]]
    ) -> str:
        """
        사용자 입력을 에이전트용 형식으로 포맷팅
        
        Args:
            user_request: 사용자 요청
            business_type: 비즈니스 유형
            template_type: 템플릿 유형
            additional_context: 추가 컨텍스트
            
        Returns:
            포맷된 입력 텍스트
        """
        formatted_input = f"사용자 요청: {user_request}\n"
        
        if business_type:
            formatted_input += f"비즈니스 유형: {business_type}\n"
        
        if template_type:
            formatted_input += f"템플릿 유형: {template_type}\n"
        
        if additional_context:
            formatted_input += f"추가 컨텍스트: {additional_context}\n"
        
        formatted_input += "\n위 정보를 바탕으로 카카오 알림톡 정책을 완전히 준수하는 고품질 템플릿을 생성해주세요."
        
        return formatted_input
    
    def _get_chat_history(self, session_id: Optional[str]) -> List[BaseMessage]:
        """
        세션 기반 대화 히스토리 조회
        
        Args:
            session_id: 세션 ID
            
        Returns:
            대화 히스토리 메시지 목록
        """
        if not session_id:
            return []
        
        try:
            # TODO: 실제 구현에서는 데이터베이스에서 세션 히스토리 조회
            # 현재는 빈 리스트 반환
            return []
            
        except Exception as e:
            logger.warning(f"대화 히스토리 조회 실패: {str(e)}")
            return []
    
    def _parse_agent_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        에이전트 실행 결과를 구조화된 형태로 파싱
        
        Args:
            result: 에이전트 실행 결과
            
        Returns:
            구조화된 결과
        """
        try:
            output = result.get("output", "")
            
            # 기본 응답 구조 생성
            parsed_result = {
                "success": True,
                "template_content": output,
                "analysis": {
                    "template_type": "기본형",
                    "message_type": "정보성",
                    "character_count": len(output),
                    "variable_count": output.count("#{"),
                    "variables": [],
                    "quality_score": 0.8,
                    "compliance_score": 0.8,
                    "suggestions": []
                },
                "metadata": {
                    "agent_steps": len(result.get("intermediate_steps", [])),
                    "tools_used": []
                }
            }
            
            # 변수 추출
            import re
            variables = re.findall(r'#\{([^}]+)\}', output)
            parsed_result["analysis"]["variables"] = variables
            parsed_result["analysis"]["variable_count"] = len(variables)
            
            # 품질 점수 계산
            parsed_result["analysis"]["quality_score"] = self._calculate_quality_score(output, variables)
            parsed_result["analysis"]["compliance_score"] = self._calculate_compliance_score(output, variables)
            
            return parsed_result
            
        except Exception as e:
            logger.error(f"결과 파싱 중 오류: {str(e)}")
            return {
                "success": False,
                "error": f"결과 파싱 실패: {str(e)}",
                "template_content": result.get("output", ""),
                "analysis": {
                    "quality_score": 0.5,
                    "compliance_score": 0.5,
                    "suggestions": ["결과 분석 중 오류가 발생했습니다."]
                }
            }
    
    def _calculate_quality_score(self, content: str, variables: List[str]) -> float:
        """
        템플릿 품질 점수 계산
        
        Args:
            content: 템플릿 내용
            variables: 변수 목록
            
        Returns:
            품질 점수 (0.0 ~ 1.0)
        """
        score = 1.0
        
        # 길이 체크
        if len(content) < 10:
            score -= 0.3  # 너무 짧음
        elif len(content) > 1000:
            score -= 0.4  # 너무 김
        
        # 변수 개수 체크
        if len(variables) > 40:
            score -= 0.3
        
        # 내용 품질 체크
        if not content.strip():
            score -= 0.5
        
        return max(0.0, score)
    
    def _calculate_compliance_score(self, content: str, variables: List[str]) -> float:
        """
        정책 준수 점수 계산
        
        Args:
            content: 템플릿 내용
            variables: 변수 목록
            
        Returns:
            준수 점수 (0.0 ~ 1.0)
        """
        score = 1.0
        
        # 기본 정책 체크
        if len(content) > 1000:
            score -= 0.3  # 길이 제한 위반
        
        if len(variables) > 40:
            score -= 0.3  # 변수 개수 제한 위반
        
        # 금지 키워드 체크 (간단한 예시)
        forbidden_keywords = ["광고", "홍보", "할인", "무료", "이벤트"]
        for keyword in forbidden_keywords:
            if keyword in content:
                score -= 0.1
        
        return max(0.0, score)

# 전역 인스턴스 생성
template_generation_agent = TemplateGenerationAgent()