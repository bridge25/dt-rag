# Agent Factory & LangGraph Pipeline 통합 시스템

## 구현 완료 컴포넌트

### 1. 핵심 클래스들
- **AgentProfile**: 카테고리별 특화 설정 (Technology AI, Business, Education, General)
- **AgentConfigBuilder**: 동적 Agent 설정 생성 및 커스터마이징
- **PromptTemplateManager**: 카테고리별 프롬프트 템플릿 관리
- **ToolSelector**: Agent별 최적 도구 선택
- **IntegratedAgentFactory**: 전체 시스템 통합 팩토리
- **PipelineAdapter**: LangGraph Pipeline 통합 어댑터

### 2. 핵심 기능

#### 카테고리별 차별화
- **Technology AI**: Vector 80% + 기술 도구 + 토론 활성화
- **Business**: BM25 70% + 비즈니스 도구 + 빠른 의사결정
- **Education**: 균형 검색 + 교육 도구 + 단계별 설명
- **General**: 하이브리드 검색 + 범용 도구

#### Agent가 Pipeline 제어
- Step 0: Agent Enhancement (새로 추가)
- Step 1-7: 기존 Pipeline에 Agent 설정 적용
- 검색 가중치, 도구 선택, 프롬프트 모두 Agent가 결정

### 3. 사용 방법

```python
# 간단한 사용법
from apps.agent_system.src import create_agent_for_query

agent_profile, pipeline_config = await create_agent_for_query(
    "Python으로 API 개발하는 방법"
)

# Enhanced Pipeline 실행
from apps.orchestration.src.enhanced_langgraph_pipeline import execute_enhanced_pipeline

result = await execute_enhanced_pipeline(query)
print(f"Agent 카테고리: {result['agent_category']}")
```

### 4. 구현된 파일들
- `apps/agent_system/src/agent_profile.py` (270 lines)
- `apps/agent_system/src/agent_config_builder.py` (152 lines)
- `apps/agent_system/src/prompt_template_manager.py` (132 lines)
- `apps/agent_system/src/tool_selector.py` (100 lines)
- `apps/agent_system/src/integrated_agent_factory.py` (173 lines)
- `apps/agent_system/src/pipeline_adapter.py` (116 lines)
- `apps/orchestration/src/enhanced_langgraph_pipeline.py` (Pipeline 통합)

### 5. 확장 가능한 아키텍처
- 새 카테고리 쉽게 추가 가능
- 새 도구/템플릿 플러그인 방식으로 확장
- 성능 피드백 기반 지속적 학습
- 사용자 컨텍스트 기반 개인화

## 핵심 혁신

1. **실제 제어**: Agent Factory가 Pipeline 동작을 실제로 제어
2. **카테고리별 특화**: 각 분야에 최적화된 차별화된 처리
3. **동적 최적화**: 쿼리와 사용자에 맞는 실시간 설정 조정
4. **통합 인터페이스**: 단일 함수로 Agent 생성부터 Pipeline 실행까지

Agent Factory와 LangGraph Pipeline이 완전 통합되어 카테고리별로 특화된 Agent가 Pipeline의 모든 동작을 제어하는 시스템이 구축되었습니다.
