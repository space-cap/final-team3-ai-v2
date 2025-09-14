"""
Template Generation Service
카카오 알림톡 템플릿 생성을 위한 AI 서비스
"""

import os
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

from langchain.schema import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.services.template_vector_store import template_vector_store_service
from app.services.rag_service import rag_service


class TemplateGenerationService:
    """
    카카오 알림톡 템플릿 생성 서비스
    승인받은 템플릿 패턴을 분석하여 새로운 템플릿 생성
    """

    def __init__(self):
        """Initialize template generation service"""
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,  # 창의성과 일관성 균형
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )

    def generate_template(
        self,
        user_request: str,
        business_type: Optional[str] = None,
        category_1: Optional[str] = None,
        category_2: Optional[str] = None,
        target_length: Optional[int] = None,
        include_variables: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        사용자 요청에 맞는 카카오 알림톡 템플릿 생성
        """
        try:
            # 1. 유사한 승인받은 템플릿 검색
            similar_templates = template_vector_store_service.find_similar_templates(
                user_request,
                category_filter=category_1,
                business_type_filter=business_type,
                k=3
            )

            # 2. 카테고리별 패턴 정보 수집
            category_patterns = []
            if category_1:
                category_patterns = template_vector_store_service.find_category_patterns(
                    category_1, k=2
                )

            # 3. 정책 문서 검색 (기존 벡터 스토어 활용)
            try:
                from app.services.vector_store_simple import simple_vector_store_service
                policy_context = simple_vector_store_service.get_relevant_policies(user_request, k=3)
            except Exception as e:
                print(f"정책 검색 오류: {e}")
                policy_context = {"policies": []}

            # 4. AI를 사용한 템플릿 생성
            generated_template = self._generate_with_ai(
                user_request=user_request,
                similar_templates=similar_templates,
                category_patterns=category_patterns,
                policy_context=policy_context,
                target_length=target_length,
                include_variables=include_variables,
                business_type=business_type,
                category_1=category_1,
                category_2=category_2
            )

            # 5. 생성된 템플릿 검증
            validation_result = self._validate_template(generated_template)

            # 6. 개선 제안 생성
            suggestions = self._generate_suggestions(
                generated_template, validation_result, similar_templates
            )

            return {
                "success": True,
                "generated_template": generated_template,
                "validation": validation_result,
                "suggestions": suggestions,
                "reference_data": {
                    "similar_templates": len(similar_templates),
                    "category_patterns": len(category_patterns),
                    "policy_references": len(policy_context.get("policies", []))
                },
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "business_type": business_type,
                    "category_1": category_1,
                    "category_2": category_2,
                    "user_request": user_request
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"템플릿 생성 중 오류 발생: {str(e)}",
                "generated_template": "",
                "validation": {},
                "suggestions": [],
                "reference_data": {},
                "metadata": {}
            }

    def _generate_with_ai(
        self,
        user_request: str,
        similar_templates: List,
        category_patterns: List,
        policy_context: Dict,
        target_length: Optional[int],
        include_variables: Optional[List[str]],
        business_type: Optional[str],
        category_1: Optional[str],
        category_2: Optional[str]
    ) -> str:
        """AI를 사용하여 템플릿 생성"""

        # 유사 템플릿 정보 구성
        similar_examples = ""
        if similar_templates:
            similar_examples = "\n\n승인받은 유사 템플릿 예시:\n"
            for i, doc in enumerate(similar_templates[:3], 1):
                original_text = doc.metadata.get('original_text', '')
                variables = doc.metadata.get('variables', [])
                button = doc.metadata.get('button', '')

                similar_examples += f"""
예시 {i}:
- 텍스트: {original_text}
- 사용변수: {', '.join(f'#{{{var}}}' for var in variables)}
- 버튼: {button}
"""

        # 카테고리 패턴 정보 구성
        pattern_info = ""
        if category_patterns:
            for doc in category_patterns:
                metadata = doc.metadata
                common_variables = metadata.get('common_variables', {})
                common_buttons = metadata.get('common_buttons', {})
                avg_length = metadata.get('avg_length', 0)

                pattern_info += f"""
카테고리 '{metadata.get('category')}' 패턴 정보:
- 일반적 변수: {', '.join(f'#{{{var}}}' for var in list(common_variables.keys())[:5])}
- 일반적 버튼: {', '.join(list(common_buttons.keys())[:3])}
- 평균 길이: {avg_length}자
"""

        # 정책 정보 구성
        policy_info = ""
        policies = policy_context.get("policies", [])
        if policies:
            policy_info = "\n\n준수해야 할 정책:\n"
            for i, policy in enumerate(policies[:3], 1):
                policy_info += f"- {policy['content']}\n"

        # 변수 요구사항
        variable_requirements = ""
        if include_variables:
            variable_requirements = f"\n\n필수 포함 변수: {', '.join(f'#{{{var}}}' for var in include_variables)}"

        # 길이 요구사항
        length_requirement = ""
        if target_length:
            length_requirement = f"\n목표 길이: {target_length}자 내외"
        else:
            length_requirement = "\n권장 길이: 80-150자"

        # 시스템 프롬프트
        system_message = SystemMessage(content=f"""
당신은 카카오 알림톡 템플릿 생성 전문가입니다.
승인받은 템플릿들의 패턴을 분석하여 정책을 준수하는 새로운 템플릿을 생성합니다.

카카오 알림톡 템플릿 생성 규칙:
1. 정보성 메시지만 가능 (광고성 내용 금지)
2. 변수는 #{{변수명}} 형태로 사용
3. 친근하고 정중한 톤앤매너
4. 명확하고 구체적인 정보 제공
5. 적절한 버튼 텍스트 제안

생성 시 고려사항:
- 업무분류: {business_type or '일반'}
- 1차분류: {category_1 or '서비스이용'}
- 2차분류: {category_2 or '이용안내/정보'}
{length_requirement}
{variable_requirements}

{similar_examples}
{pattern_info}
{policy_info}

응답 형식:
템플릿 텍스트만 생성해주세요. 추가 설명이나 주석은 포함하지 마세요.
""")

        # 사용자 메시지
        human_message = HumanMessage(content=f"""
다음 요청에 맞는 카카오 알림톡 템플릿을 생성해주세요:

사용자 요청: {user_request}

위의 승인받은 템플릿 패턴과 정책을 참고하여, 정책을 완벽히 준수하면서도 사용자 요청에 맞는 템플릿을 생성해주세요.
""")

        # AI를 통한 템플릿 생성
        response = self.llm.invoke([system_message, human_message])
        return response.content.strip()

    def _validate_template(self, template: str) -> Dict[str, Any]:
        """생성된 템플릿 검증"""
        validation = {
            "length": len(template),
            "length_appropriate": 50 <= len(template) <= 300,
            "has_greeting": bool(re.search(r'안녕하세요|고객님|회원님', template)),
            "variables": re.findall(r'#\{([^}]+)\}', template),
            "variable_count": len(re.findall(r'#\{([^}]+)\}', template)),
            "has_politeness": bool(re.search(r'습니다|하세요|주세요|바랍니다', template)),
            "potential_ad_content": bool(re.search(r'할인|이벤트|프로모션|세일|특가|무료', template)),
            "has_contact_info": bool(re.search(r'연락|문의|전화', template)),
            "sentence_count": len([s for s in template.split('.') if s.strip()]),
            "compliance_score": 0.0
        }

        # 컴플라이언스 점수 계산
        score = 0
        max_score = 7

        if validation["length_appropriate"]:
            score += 1
        if validation["has_greeting"]:
            score += 1
        if validation["has_politeness"]:
            score += 1
        if not validation["potential_ad_content"]:
            score += 1
        if validation["variable_count"] <= 10:  # 변수 10개 이하
            score += 1
        if validation["variable_count"] >= 1:  # 최소 1개 변수 사용
            score += 1
        if 2 <= validation["sentence_count"] <= 5:  # 적절한 문장 수
            score += 1

        validation["compliance_score"] = (score / max_score) * 100

        return validation

    def _generate_suggestions(
        self,
        template: str,
        validation: Dict,
        similar_templates: List
    ) -> List[str]:
        """개선 제안 생성"""
        suggestions = []

        # 길이 관련 제안
        if validation["length"] < 80:
            suggestions.append("템플릿이 너무 짧습니다. 더 구체적인 정보를 추가해보세요.")
        elif validation["length"] > 150:
            suggestions.append("템플릿이 너무 깁니다. 핵심 정보만 간결하게 표현해보세요.")

        # 인사말 관련 제안
        if not validation["has_greeting"]:
            suggestions.append("'안녕하세요 #{고객성명}님,' 형태의 인사말을 추가하면 더 친근합니다.")

        # 변수 관련 제안
        if validation["variable_count"] == 0:
            suggestions.append("개인화를 위해 최소 1개 이상의 변수(#{고객성명} 등)를 사용하세요.")
        elif validation["variable_count"] > 10:
            suggestions.append("변수가 너무 많습니다. 10개 이하로 줄여주세요.")

        # 정중함 관련 제안
        if not validation["has_politeness"]:
            suggestions.append("'습니다', '바랍니다' 등 정중한 표현을 사용하세요.")

        # 광고성 내용 관련 제안
        if validation["potential_ad_content"]:
            suggestions.append("할인, 이벤트 등 광고성 표현은 알림톡에서 사용할 수 없습니다.")

        # 유사 템플릿과의 비교 제안
        if similar_templates:
            common_variables = set()
            for doc in similar_templates:
                common_variables.update(doc.metadata.get('variables', []))

            template_variables = set(validation["variables"])
            missing_common = common_variables - template_variables
            if missing_common:
                missing_vars = list(missing_common)[:3]
                suggestions.append(f"이 분류에서 자주 사용되는 변수를 고려해보세요: {', '.join(f'#{{{var}}}' for var in missing_vars)}")

        # 컴플라이언스 점수 관련 제안
        if validation["compliance_score"] < 70:
            suggestions.append("정책 준수도가 낮습니다. 위의 제안사항들을 반영해보세요.")
        elif validation["compliance_score"] >= 85:
            suggestions.append("훌륭합니다! 정책을 잘 준수하는 템플릿입니다.")

        return suggestions

    def optimize_template(
        self,
        template: str,
        target_improvements: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """기존 템플릿 최적화"""
        try:
            # 현재 템플릿 검증
            current_validation = self._validate_template(template)

            # 최적화 프롬프트 생성
            system_message = SystemMessage(content="""
당신은 카카오 알림톡 템플릿 최적화 전문가입니다.
주어진 템플릿을 카카오 정책에 더 적합하도록 개선하세요.

최적화 목표:
1. 정책 준수도 향상
2. 사용자 경험 개선
3. 승인 가능성 증대
4. 명확성과 친근함 균형

응답 형식: 최적화된 템플릿 텍스트만 제공하세요.
""")

            improvements_text = ""
            if target_improvements:
                improvements_text = f"특히 다음 사항을 개선해주세요: {', '.join(target_improvements)}"

            human_message = HumanMessage(content=f"""
다음 템플릿을 최적화해주세요:

원본 템플릿:
{template}

현재 문제점:
- 길이: {current_validation['length']}자
- 변수 개수: {current_validation['variable_count']}개
- 정책 준수도: {current_validation['compliance_score']:.1f}점

{improvements_text}
""")

            # AI를 통한 최적화
            response = self.llm.invoke([system_message, human_message])
            optimized_template = response.content.strip()

            # 최적화된 템플릿 검증
            optimized_validation = self._validate_template(optimized_template)

            return {
                "success": True,
                "original_template": template,
                "optimized_template": optimized_template,
                "original_validation": current_validation,
                "optimized_validation": optimized_validation,
                "improvement": {
                    "compliance_score_change": optimized_validation["compliance_score"] - current_validation["compliance_score"],
                    "length_change": optimized_validation["length"] - current_validation["length"],
                    "variable_count_change": optimized_validation["variable_count"] - current_validation["variable_count"]
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"템플릿 최적화 중 오류 발생: {str(e)}",
                "original_template": template,
                "optimized_template": "",
                "original_validation": {},
                "optimized_validation": {},
                "improvement": {}
            }


# Global instance
template_generation_service = TemplateGenerationService()