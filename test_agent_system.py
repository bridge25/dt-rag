"""
Agent System 테스트 스크립트

Agent Factory와 Pipeline 통합 시스템 테스트
"""

import asyncio
import json
from apps.agent_system.src import (
    AgentCategory, 
    create_agent_for_query,
    get_pipeline_adapter,
    get_agent_factory
)


async def test_agent_creation():
    """Agent 생성 테스트"""
    print("=== Agent 생성 테스트 ===")
    
    test_queries = [
        "Python으로 API를 개발하는 방법을 알려주세요",
        "비즈니스 전략 수립을 위한 시장 분석 방법",
        "머신러닝 기초를 배우고 싶어요",
        "일반적인 질문입니다"
    ]
    
    for query in test_queries:
        print(f"\n쿼리: {query}")
        
        # Agent 생성
        agent_profile, pipeline_config = await create_agent_for_query(query)
        
        print(f"카테고리: {agent_profile.category.value}")
        print(f"Agent 이름: {agent_profile.name}")
        print(f"검색 가중치: {agent_profile.retrieval_config.weights}")
        print(f"활성화된 도구: {agent_profile.tool_config.enabled_tools}")
        print(f"응답 스타일: {agent_profile.prompt_config.response_style}")


async def test_pipeline_integration():
    """Pipeline 통합 테스트"""
    print("\n\n=== Pipeline 통합 테스트 ===")
    
    # Mock Pipeline State
    initial_state = {
        "query": "Python AI 개발 프레임워크 추천해주세요",
        "chunk_id": None,
        "taxonomy_version": "v1.0"
    }
    
    # Pipeline Adapter 사용
    adapter = get_pipeline_adapter()
    
    enhanced_state = await adapter.enhance_pipeline_state(
        initial_state["query"], 
        initial_state
    )
    
    print(f"Agent 카테고리: {enhanced_state.get('agent_category')}")
    print(f"검색 가중치: {enhanced_state.get('retrieval_weights')}")
    print(f"최대 검색 결과: {enhanced_state.get('max_retrieval_results')}")
    print(f"활성화된 도구: {enhanced_state.get('enabled_tools')}")


def test_retrieval_weights():
    """검색 가중치 적용 테스트"""
    print("\n\n=== 검색 가중치 적용 테스트 ===")
    
    # Mock 검색 결과
    vector_results = [
        {"content": "AI 프레임워크 TensorFlow", "score": 0.9, "id": "v1"},
        {"content": "딥러닝 라이브러리 PyTorch", "score": 0.8, "id": "v2"}
    ]
    
    bm25_results = [
        {"content": "Python 웹 프레임워크 Django", "score": 0.7, "id": "b1"},
        {"content": "API 개발 FastAPI", "score": 0.6, "id": "b2"}
    ]
    
    # Technology AI 가중치 (벡터 검색 중심)
    tech_weights = {"vector": 0.8, "bm25": 0.2}
    
    adapter = get_pipeline_adapter()
    weighted_results = adapter.apply_retrieval_weights(
        vector_results, bm25_results, tech_weights
    )
    
    print("가중치 적용 결과:")
    for result in weighted_results:
        print(f"- {result['content']}: {result['weighted_score']:.2f} ({result['source']})")


def test_system_status():
    """시스템 상태 테스트"""
    print("\n\n=== 시스템 상태 테스트 ===")
    
    factory = get_agent_factory()
    status = factory.get_system_status()
    
    print("시스템 상태:")
    print(json.dumps(status, indent=2, ensure_ascii=False))


async def main():
    """메인 테스트 함수"""
    print("Agent System 통합 테스트 시작\n")
    
    await test_agent_creation()
    await test_pipeline_integration()
    test_retrieval_weights()
    test_system_status()
    
    print("\n\n=== 테스트 완료 ===")


if __name__ == "__main__":
    asyncio.run(main())
