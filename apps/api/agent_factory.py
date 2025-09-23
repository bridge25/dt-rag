"""
Agent Factory Core Implementation
PRD v1.8.1 요구사항을 충족하는 Agent Factory 시스템
"""

import asyncio
import yaml
import json
import uuid
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class AgentProfile:
    """Agent 프로파일 - 카테고리별 특화 설정"""
    id: str
    name: str
    category: str

    # PRD 요구사항: retrieval 설정
    retrieval_config: Dict[str, Any]

    # PRD 요구사항: canonical path 필터링
    canonical_paths: List[List[str]]

    # 프롬프트 설정
    prompt_config: Dict[str, Any]

    # 도구 설정
    tools_config: Dict[str, Any]

    # PRD 요구사항: debate/HITL 토글
    debate_enabled: bool = True
    hitl_enabled: bool = True

    # 비용/성능 가드
    cost_guard: Dict[str, Any] = None

    # 메타데이터
    created_at: str = None
    version: str = "1.0.0"

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc).isoformat()

        if self.cost_guard is None:
            self.cost_guard = {
                "max_cost_per_query": 10.0,  # PRD: ≤₩10/쿼리
                "max_latency_seconds": 4.0,  # PRD: p95≤4s
                "max_tokens": 2000
            }

    def to_manifest(self) -> Dict[str, Any]:
        """Agent Manifest YAML 생성 (PRD 요구사항)"""
        return {
            "apiVersion": "dt-rag/v1",
            "kind": "Agent",
            "metadata": {
                "name": self.name,
                "id": self.id,
                "category": self.category,
                "version": self.version,
                "created_at": self.created_at
            },
            "spec": {
                "retrieval": self.retrieval_config,
                "canonical_paths": self.canonical_paths,  # PRD: 범위 제한
                "prompt": self.prompt_config,
                "tools": self.tools_config,
                "features": {
                    "debate_enabled": self.debate_enabled,
                    "hitl_enabled": self.hitl_enabled
                },
                "guards": self.cost_guard
            }
        }


class PromptTemplateManager:
    """PRD 요구사항: Agent별 프롬프트 관리"""

    TEMPLATES = {
        "technology_ai": {
            "system": """당신은 AI/ML 기술 전문가입니다.
제공된 문서들을 기반으로 기술적으로 정확하고 근거가 명확한 답변을 제공하세요.

중요 지침:
- 반드시 2개 이상의 출처를 인용하세요
- 각 주장에 대해 근거를 명시하세요
- 기술적 정확성을 최우선으로 하세요
- 불확실한 정보는 명시적으로 표기하세요""",
            "user": """질문: {query}

참고 문서:
{context}

taxonomy_version: {taxonomy_version}
검색 범위: {canonical_paths}

위 문서들을 기반으로 답변해주세요. 반드시 다음 형식을 따라주세요:

[답변 내용]

📚 출처:
1. [문서 제목] - [URL] (신뢰도: X.X)
2. [문서 제목] - [URL] (신뢰도: X.X)

🔍 검색 정보: {taxonomy_version} 버전 기준, 범위: {canonical_paths}
⭐ 신뢰도: [전체 답변 신뢰도]"""
        },
        "business": {
            "system": """당신은 비즈니스 전문가입니다.
제공된 문서들을 기반으로 실용적이고 실행 가능한 비즈니스 답변을 제공하세요.""",
            "user": """질문: {query}

참고 문서:
{context}

비즈니스 관점에서 실용적인 답변을 제공해주세요."""
        },
        "education": {
            "system": """당신은 교육 전문가입니다.
학습자가 이해하기 쉽도록 단계별로 설명해주세요.""",
            "user": """질문: {query}

참고 문서:
{context}

교육적 관점에서 단계별로 설명해주세요."""
        },
        "general": {
            "system": """당신은 도움이 되는 AI 어시스턴트입니다.
제공된 문서들을 기반으로 정확하고 유용한 답변을 제공하세요.""",
            "user": """질문: {query}

참고 문서:
{context}

위 문서들을 참고하여 답변해주세요."""
        }
    }

    @classmethod
    def get_template(cls, category: str) -> Dict[str, str]:
        """카테고리별 프롬프트 템플릿 반환"""
        return cls.TEMPLATES.get(category, cls.TEMPLATES["general"])

    @classmethod
    def format_prompt(cls, category: str, query: str, context: str,
                     taxonomy_version: str, canonical_paths: List[List[str]]) -> Dict[str, str]:
        """프롬프트 포맷팅"""
        template = cls.get_template(category)

        return {
            "system": template["system"],
            "user": template["user"].format(
                query=query,
                context=context,
                taxonomy_version=taxonomy_version,
                canonical_paths=canonical_paths
            )
        }


class ToolSelector:
    """PRD 요구사항: Agent별 도구 선택"""

    TOOL_CATEGORIES = {
        "technology_ai": {
            "primary": ["search", "classification", "code_analysis"],
            "secondary": ["web_search", "calculator"],
            "restricted": []
        },
        "business": {
            "primary": ["search", "classification", "market_analysis"],
            "secondary": ["web_search", "calculator", "chart_generator"],
            "restricted": ["code_analysis"]
        },
        "education": {
            "primary": ["search", "classification", "explanation"],
            "secondary": ["web_search", "quiz_generator"],
            "restricted": ["code_analysis", "market_analysis"]
        },
        "general": {
            "primary": ["search", "classification"],
            "secondary": ["web_search"],
            "restricted": []
        }
    }

    @classmethod
    def get_tools_for_category(cls, category: str) -> Dict[str, List[str]]:
        """카테고리별 도구 목록 반환"""
        return cls.TOOL_CATEGORIES.get(category, cls.TOOL_CATEGORIES["general"])

    @classmethod
    def is_tool_allowed(cls, category: str, tool_name: str) -> bool:
        """특정 도구 사용 가능 여부 확인"""
        tools = cls.get_tools_for_category(category)
        return tool_name not in tools["restricted"]


class AgentConfigBuilder:
    """동적 Agent 설정 생성"""

    @staticmethod
    def build_retrieval_config(category: str) -> Dict[str, Any]:
        """카테고리별 검색 설정 생성"""
        configs = {
            "technology_ai": {
                "bm25_weight": 0.3,
                "vector_weight": 0.7,
                "bm25_topk": 12,
                "vector_topk": 12,
                "rerank_candidates": 50,
                "final_topk": 5,
                "rerank_threshold": 0.8
            },
            "business": {
                "bm25_weight": 0.5,
                "vector_weight": 0.5,
                "bm25_topk": 15,
                "vector_topk": 10,
                "rerank_candidates": 40,
                "final_topk": 6,
                "rerank_threshold": 0.7
            },
            "education": {
                "bm25_weight": 0.6,
                "vector_weight": 0.4,
                "bm25_topk": 10,
                "vector_topk": 8,
                "rerank_candidates": 30,
                "final_topk": 4,
                "rerank_threshold": 0.75
            },
            "general": {
                "bm25_weight": 0.5,
                "vector_weight": 0.5,
                "bm25_topk": 12,
                "vector_topk": 12,
                "rerank_candidates": 50,
                "final_topk": 5,
                "rerank_threshold": 0.7
            }
        }

        return configs.get(category, configs["general"])

    @staticmethod
    def build_prompt_config(category: str) -> Dict[str, Any]:
        """카테고리별 프롬프트 설정 생성"""
        configs = {
            "technology_ai": {
                "temperature": 0.3,  # 정확성 중시
                "max_tokens": 1500,
                "top_p": 0.9,
                "presence_penalty": 0.1
            },
            "business": {
                "temperature": 0.5,  # 균형
                "max_tokens": 1200,
                "top_p": 0.95,
                "presence_penalty": 0.0
            },
            "education": {
                "temperature": 0.4,  # 설명 중시
                "max_tokens": 1800,
                "top_p": 0.92,
                "presence_penalty": 0.05
            },
            "general": {
                "temperature": 0.4,
                "max_tokens": 1000,
                "top_p": 0.9,
                "presence_penalty": 0.0
            }
        }

        return configs.get(category, configs["general"])


class CanonicalPathValidator:
    """PRD 요구사항: canonical path 필터링 검증"""

    @staticmethod
    def validate_paths(paths: List[List[str]]) -> bool:
        """canonical path 유효성 검증"""
        if not paths:
            return False

        for path in paths:
            if not isinstance(path, list) or len(path) == 0:
                return False
            if len(path) > 8:  # PRD: 길이 1~8
                return False
            for segment in path:
                if not isinstance(segment, str) or not segment.strip():
                    return False

        return True

    @staticmethod
    def normalize_paths(paths: List[List[str]]) -> List[List[str]]:
        """canonical path 정규화"""
        normalized = []
        for path in paths:
            normalized_path = [segment.strip() for segment in path if segment.strip()]
            if normalized_path:
                normalized.append(normalized_path)

        return normalized


class IntegratedAgentFactory:
    """통합 Agent Factory - PRD 요구사항 완전 구현"""

    def __init__(self):
        self.agents: Dict[str, AgentProfile] = {}
        self.agent_catalog: Dict[str, Dict[str, Any]] = {}

    async def create_agent_from_category(
        self,
        categories: List[str],
        canonical_paths: List[List[str]],
        taxonomy_version: str = "1.8.1",
        options: Optional[Dict[str, Any]] = None
    ) -> AgentProfile:
        """
        PRD 요구사항: 카테고리와 canonical path로 Agent 생성

        Args:
            categories: Agent 카테고리 (예: ["Technology", "AI"])
            canonical_paths: 검색 범위 제한 경로
            taxonomy_version: 택소노미 버전
            options: 추가 설정
        """
        # 1. canonical path 검증 (PRD 요구사항)
        if not CanonicalPathValidator.validate_paths(canonical_paths):
            raise ValueError("Invalid canonical paths provided")

        canonical_paths = CanonicalPathValidator.normalize_paths(canonical_paths)

        # 2. 카테고리 결정
        primary_category = self._determine_primary_category(categories)

        # 3. Agent ID 생성
        agent_id = str(uuid.uuid4())
        agent_name = f"{primary_category}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 4. 설정 구성
        retrieval_config = AgentConfigBuilder.build_retrieval_config(primary_category)
        prompt_config = AgentConfigBuilder.build_prompt_config(primary_category)
        tools_config = {
            "allowed_tools": ToolSelector.get_tools_for_category(primary_category),
            "mcp_tools": self._get_mcp_tools_for_category(primary_category)
        }

        # 5. 옵션 적용
        if options:
            self._apply_options(retrieval_config, prompt_config, tools_config, options)

        # 6. Agent 프로파일 생성
        agent = AgentProfile(
            id=agent_id,
            name=agent_name,
            category=primary_category,
            retrieval_config=retrieval_config,
            canonical_paths=canonical_paths,
            prompt_config=prompt_config,
            tools_config=tools_config,
            debate_enabled=options.get("debate_enabled", True) if options else True,
            hitl_enabled=options.get("hitl_enabled", True) if options else True
        )

        # 7. Agent 등록
        self.agents[agent_id] = agent

        # 8. 카탈로그 등록 (PRD 요구사항)
        await self._register_to_catalog(agent, taxonomy_version)

        logger.info(f"Agent 생성 완료: {agent_name} (ID: {agent_id})")
        return agent

    def _determine_primary_category(self, categories: List[str]) -> str:
        """카테고리 우선순위에 따른 주 카테고리 결정"""
        category_priority = {
            "AI": "technology_ai",
            "Technology": "technology_ai",
            "Machine Learning": "technology_ai",
            "RAG": "technology_ai",
            "Business": "business",
            "Marketing": "business",
            "Strategy": "business",
            "Education": "education",
            "Learning": "education"
        }

        for category in categories:
            if category in category_priority:
                return category_priority[category]

        return "general"

    def _get_mcp_tools_for_category(self, category: str) -> List[str]:
        """카테고리별 MCP 도구 목록"""
        mcp_tools = {
            "technology_ai": ["context7", "sequential-thinking", "code-analysis"],
            "business": ["context7", "market-analysis", "chart-generator"],
            "education": ["context7", "explanation-formatter", "quiz-generator"],
            "general": ["context7", "fallback-search"]
        }

        return mcp_tools.get(category, mcp_tools["general"])

    def _apply_options(self, retrieval_config: Dict, prompt_config: Dict,
                      tools_config: Dict, options: Dict[str, Any]):
        """사용자 옵션 적용"""
        if "cost_priority" in options and options["cost_priority"]:
            # 비용 우선 모드
            retrieval_config["final_topk"] = min(retrieval_config["final_topk"], 3)
            prompt_config["max_tokens"] = min(prompt_config["max_tokens"], 800)

        if "accuracy_priority" in options and options["accuracy_priority"]:
            # 정확도 우선 모드 (PRD 시나리오 8)
            retrieval_config["rerank_candidates"] = 80
            retrieval_config["final_topk"] = min(retrieval_config["final_topk"] + 2, 8)
            prompt_config["temperature"] = max(prompt_config["temperature"] - 0.1, 0.1)

    async def _register_to_catalog(self, agent: AgentProfile, taxonomy_version: str):
        """Agent 카탈로그 등록 (PRD 요구사항)"""
        catalog_entry = {
            "agent_id": agent.id,
            "name": agent.name,
            "category": agent.category,
            "taxonomy_version": taxonomy_version,
            "canonical_paths": agent.canonical_paths,
            "manifest": agent.to_manifest(),
            "created_at": agent.created_at,
            "status": "active"
        }

        self.agent_catalog[agent.id] = catalog_entry

    async def get_agent(self, agent_id: str) -> Optional[AgentProfile]:
        """Agent 조회"""
        return self.agents.get(agent_id)

    async def list_agents(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Agent 목록 조회"""
        agents = []
        for agent_id, catalog_entry in self.agent_catalog.items():
            if category is None or catalog_entry["category"] == category:
                agents.append(catalog_entry)

        return agents

    async def save_manifest(self, agent_id: str, file_path: Optional[str] = None) -> str:
        """Agent Manifest YAML 저장 (PRD 요구사항)"""
        agent = await self.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")

        manifest = agent.to_manifest()
        yaml_content = yaml.dump(manifest, default_flow_style=False, allow_unicode=True)

        if file_path:
            Path(file_path).write_text(yaml_content, encoding='utf-8')
            return file_path
        else:
            # 기본 경로에 저장
            default_path = f"./agent_manifests/{agent.name}.yaml"
            Path(default_path).parent.mkdir(parents=True, exist_ok=True)
            Path(default_path).write_text(yaml_content, encoding='utf-8')
            return default_path

    async def validate_agent_constraints(self, agent: AgentProfile) -> Dict[str, Any]:
        """Agent 제약사항 검증 (PRD 요구사항)"""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }

        # canonical path 검증
        if not CanonicalPathValidator.validate_paths(agent.canonical_paths):
            validation_result["valid"] = False
            validation_result["errors"].append("Invalid canonical paths")

        # 비용 가드 검증
        cost_guard = agent.cost_guard
        if cost_guard["max_cost_per_query"] > 10.0:
            validation_result["warnings"].append("Cost per query exceeds PRD limit (₩10)")

        if cost_guard["max_latency_seconds"] > 4.0:
            validation_result["warnings"].append("Latency limit exceeds PRD target (4s)")

        # 도구 검증
        category = agent.category
        for tool in agent.tools_config.get("allowed_tools", {}).get("primary", []):
            if not ToolSelector.is_tool_allowed(category, tool):
                validation_result["valid"] = False
                validation_result["errors"].append(f"Tool '{tool}' not allowed for category '{category}'")

        return validation_result


# 전역 인스턴스
_factory_instance: Optional[IntegratedAgentFactory] = None

def get_agent_factory() -> IntegratedAgentFactory:
    """Agent Factory 싱글톤 인스턴스 반환"""
    global _factory_instance
    if _factory_instance is None:
        _factory_instance = IntegratedAgentFactory()
    return _factory_instance


# 편의 함수들
async def create_agent_from_categories(
    categories: List[str],
    canonical_paths: List[List[str]],
    **kwargs
) -> AgentProfile:
    """간편 Agent 생성 함수"""
    factory = get_agent_factory()
    return await factory.create_agent_from_category(categories, canonical_paths, **kwargs)


async def get_agent_manifest_yaml(agent_id: str) -> str:
    """Agent Manifest YAML 반환"""
    factory = get_agent_factory()
    agent = await factory.get_agent(agent_id)
    if not agent:
        raise ValueError(f"Agent not found: {agent_id}")

    manifest = agent.to_manifest()
    return yaml.dump(manifest, default_flow_style=False, allow_unicode=True)


# 사용 예시
if __name__ == "__main__":
    async def main():
        # Agent Factory 생성
        factory = get_agent_factory()

        # Technology AI Agent 생성
        agent = await factory.create_agent_from_category(
            categories=["Technology", "AI"],
            canonical_paths=[["AI", "RAG"], ["AI", "Machine Learning"]],
            taxonomy_version="1.8.1",
            options={
                "accuracy_priority": True,
                "debate_enabled": True
            }
        )

        print(f"Agent 생성됨: {agent.name}")
        print(f"검색 범위: {agent.canonical_paths}")

        # Manifest 저장
        manifest_path = await factory.save_manifest(agent.id)
        print(f"Manifest 저장: {manifest_path}")

        # 검증
        validation = await factory.validate_agent_constraints(agent)
        print(f"검증 결과: {validation}")

    asyncio.run(main())