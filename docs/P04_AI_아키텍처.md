# P04_AI_아키텍처

## AI 시스템 개요

카카오톡 알림톡 템플릿 자동 생성을 위한 다중 에이전트 기반 AI 시스템

### 핵심 구성요소
- **LangChain**: AI 애플리케이션 개발 프레임워크
- **LangGraph**: 복잡한 AI 워크플로우 관리
- **RAG (Retrieval-Augmented Generation)**: 정책 기반 정보 검색
- **Multi-Agent System**: 전문화된 AI 에이전트들의 협업
- **Vector Database (Chroma)**: 정책 문서 임베딩 저장소

## 시스템 아키텍처

### 1. 전체 시스템 구조
```
┌─────────────────────────────────────────────────────────────┐
│                    사용자 인터페이스                        │
│                   (FastAPI + Web UI)                       │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┼───────────────────────────────────────┐
│                 오케스트레이터                              │
│              (LangGraph Workflow)                          │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┼───────────────────────────────────────┐
│                 AI 에이전트 레이어                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │ 템플릿 생성  │ │ 정책 검증    │ │ 개선 제안    │          │
│  │   에이전트   │ │   에이전트   │ │   에이전트   │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┼───────────────────────────────────────┐
│                 데이터 레이어                               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │   벡터DB    │ │   MySQL     │ │  정책문서    │          │
│  │  (Chroma)   │ │             │ │  (로컬)     │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

## AI 에이전트 구성

### 1. 템플릿 생성 에이전트 (Template Generator Agent)
**역할**: 사용자 요구사항을 바탕으로 초기 템플릿 생성

**입력**:
- 사용자 비즈니스 정보
- 메시지 목적 및 내용 요구사항
- 대상 고객층 정보

**처리 과정**:
```python
class TemplateGeneratorAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4")
        self.retriever = self.setup_policy_retriever()

    def generate_template(self, user_input):
        # 1. 관련 정책 검색
        relevant_policies = self.retriever.get_relevant_documents(
            user_input.business_type + " " + user_input.message_purpose
        )

        # 2. 컨텍스트 구성
        context = self.build_context(user_input, relevant_policies)

        # 3. 프롬프트 생성
        prompt = TemplateGenerationPrompt.format(
            context=context,
            user_requirements=user_input
        )

        # 4. LLM을 통한 템플릿 생성
        return self.llm.invoke(prompt)
```

**출력**:
- 기본 템플릿 구조
- 필요한 변수 목록
- 추천 카테고리

### 2. 정책 검증 에이전트 (Policy Validation Agent)
**역할**: 생성된 템플릿의 정책 준수성 검증

**검증 항목**:
```python
class PolicyValidationAgent:
    def __init__(self):
        self.validation_rules = [
            CharacterLimitValidator(max_length=1000),
            BlacklistContentValidator(),
            VariableFormatValidator(),
            BusinessTypeComplianceValidator(),
            AdvertisingContentValidator()
        ]

    def validate_template(self, template):
        results = []
        for validator in self.validation_rules:
            result = validator.validate(template)
            results.append(result)

        return ValidationReport(results)
```

**검증 세부사항**:
- **글자 수 제한**: 1,000자 이내 확인
- **금지 콘텐츠**: 블랙리스트 단어/문구 검출
- **변수 형식**: `#{변수명}` 형식 준수 확인
- **업종별 규정**: 특정 업종별 특수 요구사항 검증
- **광고성 요소**: 정보성 vs 광고성 분류 및 규정 준수

### 3. 개선 제안 에이전트 (Improvement Suggestion Agent)
**역할**: 정책 위반 사항에 대한 구체적인 개선 방안 제시

```python
class ImprovementSuggestionAgent:
    def __init__(self):
        self.improvement_strategies = {
            'character_limit': self.suggest_content_reduction,
            'blacklist_violation': self.suggest_alternative_expressions,
            'variable_format': self.suggest_format_correction,
            'advertising_content': self.suggest_content_neutralization
        }

    def generate_suggestions(self, validation_report):
        suggestions = []
        for violation in validation_report.violations:
            strategy = self.improvement_strategies.get(violation.type)
            if strategy:
                suggestion = strategy(violation)
                suggestions.append(suggestion)

        return ImprovementPlan(suggestions)
```

## RAG (Retrieval-Augmented Generation) 시스템

### 1. 문서 처리 파이프라인
```python
class DocumentProcessor:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", ".", " "]
        )
        self.embeddings = OpenAIEmbeddings()
        self.vectorstore = Chroma(
            persist_directory="./chroma_db",
            embedding_function=self.embeddings
        )

    def process_policy_documents(self):
        # 정책 문서 로드
        documents = self.load_policy_documents()

        # 청킹
        chunks = self.text_splitter.split_documents(documents)

        # 메타데이터 추가
        enriched_chunks = self.add_metadata(chunks)

        # 벡터 저장소에 저장
        self.vectorstore.add_documents(enriched_chunks)
```

### 2. 검색 전략
```python
class PolicyRetriever:
    def __init__(self, vectorstore):
        self.vectorstore = vectorstore
        self.retriever = vectorstore.as_retriever(
            search_type="mmr",  # Maximum Marginal Relevance
            search_kwargs={"k": 5, "lambda_mult": 0.7}
        )

    def get_relevant_policies(self, query, business_type=None):
        # 기본 검색
        results = self.retriever.get_relevant_documents(query)

        # 비즈니스 타입별 필터링
        if business_type:
            filtered_results = self.filter_by_business_type(
                results, business_type
            )

        return filtered_results
```

## LangGraph 워크플로우

### 1. 전체 프로세스 정의
```python
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END

class TemplateGenerationState(TypedDict):
    user_input: dict
    generated_template: str
    validation_results: dict
    improvement_suggestions: list
    final_template: str
    iteration_count: int

def create_template_workflow():
    workflow = StateGraph(TemplateGenerationState)

    # 노드 추가
    workflow.add_node("generate", generate_template_node)
    workflow.add_node("validate", validate_template_node)
    workflow.add_node("improve", improve_template_node)
    workflow.add_node("finalize", finalize_template_node)

    # 엣지 추가
    workflow.add_edge("generate", "validate")
    workflow.add_conditional_edges(
        "validate",
        should_improve,
        {
            "improve": "improve",
            "finalize": "finalize"
        }
    )
    workflow.add_edge("improve", "validate")
    workflow.add_edge("finalize", END)

    workflow.set_entry_point("generate")

    return workflow.compile()
```

### 2. 조건부 분기 로직
```python
def should_improve(state: TemplateGenerationState) -> str:
    validation_results = state["validation_results"]

    # 심각한 위반사항이 있는 경우
    if validation_results["critical_violations"]:
        return "improve"

    # 최대 반복 횟수 도달
    if state["iteration_count"] >= 3:
        return "finalize"

    # 모든 검증 통과
    if validation_results["overall_score"] > 0.85:
        return "finalize"

    return "improve"
```

## 프롬프트 엔지니어링

### 1. 템플릿 생성 프롬프트
```python
TEMPLATE_GENERATION_PROMPT = """
당신은 카카오톡 알림톡 템플릿 생성 전문가입니다.

다음 정책 가이드라인을 반드시 준수하여 템플릿을 생성하세요:
{policy_guidelines}

사용자 요구사항:
- 비즈니스 유형: {business_type}
- 메시지 목적: {message_purpose}
- 포함할 내용: {content_requirements}
- 대상 고객: {target_audience}

생성 규칙:
1. 1,000자 이내로 작성
2. 변수는 #{변수명} 형식 사용
3. 정보성 메시지 우선, 광고성 요소 최소화
4. 고객 친화적이고 명확한 표현 사용
5. 법적 준수사항 포함

템플릿을 생성해주세요:
"""

POLICY_VALIDATION_PROMPT = """
다음 템플릿이 카카오톡 알림톡 정책을 준수하는지 검증하세요:

템플릿:
{template}

검증 항목:
1. 글자 수 제한 (1,000자)
2. 금지 콘텐츠 포함 여부
3. 변수 형식 준수
4. 광고성 콘텐츠 비율
5. 업종별 특수 규정 준수

각 항목에 대해 점수(0-100)와 구체적인 피드백을 제공하세요.
"""
```

## 성능 최적화

### 1. 캐싱 전략
```python
from functools import lru_cache
import redis

class CacheManager:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
        self.local_cache = {}

    @lru_cache(maxsize=1000)
    def get_policy_embeddings(self, query_hash):
        """정책 검색 결과 캐싱"""
        return self.vectorstore.similarity_search(query_hash)

    def cache_template_result(self, user_input_hash, result):
        """생성 결과 Redis 캐싱"""
        self.redis_client.setex(
            f"template:{user_input_hash}",
            3600,  # 1시간
            json.dumps(result)
        )
```

### 2. 배치 처리
```python
class BatchProcessor:
    def __init__(self, batch_size=10):
        self.batch_size = batch_size
        self.processing_queue = []

    async def process_batch_templates(self, requests):
        """여러 템플릿 요청을 배치로 처리"""
        results = []
        for batch in self.chunk_requests(requests, self.batch_size):
            batch_results = await self.process_single_batch(batch)
            results.extend(batch_results)
        return results
```

## 모니터링 및 로깅

### 1. 성능 메트릭
```python
class MetricsCollector:
    def __init__(self):
        self.metrics = {
            'template_generation_time': [],
            'validation_accuracy': [],
            'user_satisfaction': [],
            'policy_compliance_rate': []
        }

    def record_generation_metrics(self, start_time, end_time,
                                  template_quality_score):
        duration = end_time - start_time
        self.metrics['template_generation_time'].append(duration)
        self.metrics['validation_accuracy'].append(template_quality_score)
```

### 2. 오류 처리 및 복구
```python
class ErrorHandler:
    def __init__(self):
        self.retry_config = {
            'max_retries': 3,
            'backoff_factor': 2
        }

    async def handle_llm_failure(self, error, user_input):
        """LLM 호출 실패 시 fallback 전략"""
        if isinstance(error, RateLimitError):
            return await self.use_fallback_model(user_input)
        elif isinstance(error, ContextLimitError):
            return await self.reduce_context_and_retry(user_input)
        else:
            return self.generate_template_from_cache(user_input)
```

## 확장 가능성

### 1. 새로운 에이전트 추가
- **다국어 지원 에이전트**: 템플릿 번역 및 현지화
- **A/B 테스트 에이전트**: 템플릿 효과 분석
- **개인화 에이전트**: 사용자 히스토리 기반 맞춤형 생성

### 2. 모델 업그레이드 경로
- GPT-4 → GPT-5 마이그레이션 계획
- 오픈소스 모델 통합 (Llama, Claude)
- 한국어 특화 모델 도입 검토