"""
LLM Service Layer Implementation
Agent 설정을 적용한 실제 LLM API 호출 시스템
PRD v1.8.1 요구사항 충족 (비용/성능 가드 포함)
"""

import asyncio
import httpx
import json
import time
import os
import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

# Agent Factory 관련 import
try:
    from apps.api.agent_factory import AgentProfile, PromptTemplateManager
    AGENT_FACTORY_AVAILABLE = True
except ImportError:
    AGENT_FACTORY_AVAILABLE = False
    logging.warning("Agent Factory not available")

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """지원되는 LLM 제공자"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    MOCK = "mock"


@dataclass
class LLMRequest:
    """LLM 요청 구조"""
    prompt: str
    system_prompt: Optional[str] = None
    max_tokens: int = 1000
    temperature: float = 0.7
    top_p: float = 0.9
    presence_penalty: float = 0.0
    stop_sequences: Optional[List[str]] = None


@dataclass
class LLMResponse:
    """LLM 응답 구조"""
    content: str
    usage: Dict[str, int]
    cost: float
    latency: float
    provider: str
    model: str
    finish_reason: str
    metadata: Dict[str, Any]


class CostCalculator:
    """LLM API 비용 계산기 (PRD 요구사항: ≤₩10/쿼리)"""

    # 토큰당 비용 (원화, 2024년 기준)
    PRICING = {
        "openai": {
            "gpt-4": {"input": 0.04, "output": 0.12},
            "gpt-4-turbo": {"input": 0.013, "output": 0.04},
            "gpt-3.5-turbo": {"input": 0.0007, "output": 0.002}
        },
        "anthropic": {
            "claude-3-opus": {"input": 0.02, "output": 0.08},
            "claude-3-sonnet": {"input": 0.004, "output": 0.016},
            "claude-3-haiku": {"input": 0.0003, "output": 0.002}
        },
        "gemini": {
            "gemini-pro": {"input": 0.0007, "output": 0.002},
            "gemini-ultra": {"input": 0.013, "output": 0.04}
        }
    }

    @classmethod
    def calculate_cost(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """토큰 사용량 기반 비용 계산"""
        if provider not in self.PRICING:
            return 0.0

        model_pricing = self.PRICING[provider].get(model, {"input": 0.001, "output": 0.003})

        input_cost = input_tokens * model_pricing["input"]
        output_cost = output_tokens * model_pricing["output"]

        return input_cost + output_cost

    @classmethod
    def get_recommended_model_for_budget(
        self,
        provider: str,
        max_cost: float = 10.0,
        estimated_tokens: int = 2000
    ) -> str:
        """예산 내 권장 모델 반환"""
        if provider not in self.PRICING:
            return "unknown"

        for model, pricing in self.PRICING[provider].items():
            estimated_cost = estimated_tokens * (pricing["input"] + pricing["output"]) / 2
            if estimated_cost <= max_cost:
                return model

        # 가장 저렴한 모델 반환
        cheapest_model = min(
            self.PRICING[provider].items(),
            key=lambda x: x[1]["input"] + x[1]["output"]
        )
        return cheapest_model[0]


class PerformanceGuard:
    """성능 가드 (PRD 요구사항: p95≤4s)"""

    def __init__(self, max_latency: float = 4.0, max_cost: float = 10.0):
        self.max_latency = max_latency
        self.max_cost = max_cost
        self.request_history: List[Tuple[float, float]] = []  # (latency, cost)

    def check_constraints(self, estimated_latency: float, estimated_cost: float) -> Tuple[bool, str]:
        """제약사항 확인"""
        violations = []

        if estimated_latency > self.max_latency:
            violations.append(f"예상 지연시간 초과: {estimated_latency:.2f}s > {self.max_latency}s")

        if estimated_cost > self.max_cost:
            violations.append(f"예상 비용 초과: ₩{estimated_cost:.2f} > ₩{self.max_cost}")

        if violations:
            return False, "; ".join(violations)

        return True, "OK"

    def record_performance(self, latency: float, cost: float):
        """성능 기록"""
        self.request_history.append((latency, cost))

        # 최근 100개 요청만 유지
        if len(self.request_history) > 100:
            self.request_history = self.request_history[-100:]

    def get_p95_latency(self) -> float:
        """p95 지연시간 계산"""
        if not self.request_history:
            return 0.0

        latencies = [record[0] for record in self.request_history]
        latencies.sort()

        p95_index = int(len(latencies) * 0.95)
        return latencies[min(p95_index, len(latencies) - 1)]

    def get_average_cost(self) -> float:
        """평균 비용 계산"""
        if not self.request_history:
            return 0.0

        costs = [record[1] for record in self.request_history]
        return sum(costs) / len(costs)


class LLMService:
    """LLM 서비스 메인 클래스"""

    def __init__(
        self,
        provider: LLMProvider = LLMProvider.OPENAI,
        model: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        self.provider = provider
        self.model = model or self._get_default_model(provider)
        self.api_key = api_key or self._get_api_key(provider)
        self.client = httpx.AsyncClient(timeout=30.0)

        # 성능 가드
        self.performance_guard = PerformanceGuard()

        # 통계
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "provider_distribution": {}
        }

    def _get_default_model(self, provider: LLMProvider) -> str:
        """제공자별 기본 모델"""
        defaults = {
            LLMProvider.OPENAI: "gpt-3.5-turbo",
            LLMProvider.ANTHROPIC: "claude-3-haiku",
            LLMProvider.GEMINI: "gemini-pro",
            LLMProvider.MOCK: "mock-model"
        }
        return defaults.get(provider, "unknown")

    def _get_api_key(self, provider: LLMProvider) -> Optional[str]:
        """환경변수에서 API 키 조회"""
        key_names = {
            LLMProvider.OPENAI: "OPENAI_API_KEY",
            LLMProvider.ANTHROPIC: "ANTHROPIC_API_KEY",
            LLMProvider.GEMINI: "GOOGLE_API_KEY",
            LLMProvider.MOCK: None
        }

        key_name = key_names.get(provider)
        return os.getenv(key_name) if key_name else None

    async def generate(
        self,
        request: LLMRequest,
        agent_profile: Optional[AgentProfile] = None
    ) -> LLMResponse:
        """Agent 설정을 적용한 LLM 생성"""
        start_time = time.time()
        self.stats["total_requests"] += 1

        try:
            # 1. Agent 설정 적용
            enhanced_request = await self._apply_agent_config(request, agent_profile)

            # 2. 성능 가드 확인
            estimated_latency = self._estimate_latency(enhanced_request)
            estimated_cost = self._estimate_cost(enhanced_request)

            guard_ok, guard_message = self.performance_guard.check_constraints(
                estimated_latency, estimated_cost
            )

            if not guard_ok:
                logger.warning(f"성능 가드 위반: {guard_message}")
                # 설정 다운그레이드
                enhanced_request = await self._downgrade_request(enhanced_request)

            # 3. LLM API 호출
            response = await self._call_llm_api(enhanced_request)

            # 4. 성능 기록
            actual_latency = time.time() - start_time
            self.performance_guard.record_performance(actual_latency, response.cost)

            # 5. 통계 업데이트
            self._update_stats(response, True)

            return response

        except Exception as e:
            logger.error(f"LLM 생성 실패: {str(e)}")
            self._update_stats(None, False)

            # 폴백 응답
            return await self._generate_fallback_response(request, time.time() - start_time)

    async def _apply_agent_config(
        self,
        request: LLMRequest,
        agent_profile: Optional[AgentProfile]
    ) -> LLMRequest:
        """Agent 설정을 요청에 적용"""
        if not agent_profile:
            return request

        prompt_config = agent_profile.prompt_config

        # Agent 설정 적용
        enhanced_request = LLMRequest(
            prompt=request.prompt,
            system_prompt=request.system_prompt,
            max_tokens=min(request.max_tokens, prompt_config.get("max_tokens", 1000)),
            temperature=prompt_config.get("temperature", request.temperature),
            top_p=prompt_config.get("top_p", request.top_p),
            presence_penalty=prompt_config.get("presence_penalty", request.presence_penalty),
            stop_sequences=request.stop_sequences
        )

        # 비용 가드 적용
        cost_guard = agent_profile.cost_guard
        if cost_guard:
            max_tokens_by_cost = int(cost_guard["max_tokens"])
            enhanced_request.max_tokens = min(enhanced_request.max_tokens, max_tokens_by_cost)

        logger.debug(f"Agent 설정 적용: {agent_profile.category}")
        return enhanced_request

    def _estimate_latency(self, request: LLMRequest) -> float:
        """지연시간 추정"""
        # 토큰 수 기반 간단한 추정
        base_latency = 0.5  # 기본 지연시간
        token_latency = request.max_tokens * 0.001  # 토큰당 추가 지연

        return base_latency + token_latency

    def _estimate_cost(self, request: LLMRequest) -> float:
        """비용 추정"""
        estimated_input_tokens = len(request.prompt.split()) * 1.3  # 대략적 추정
        estimated_output_tokens = request.max_tokens * 0.8  # 평균 출력 길이

        return CostCalculator.calculate_cost(
            self.provider.value,
            self.model,
            int(estimated_input_tokens),
            int(estimated_output_tokens)
        )

    async def _downgrade_request(self, request: LLMRequest) -> LLMRequest:
        """성능 가드 위반 시 요청 다운그레이드"""
        # 토큰 수 줄이기
        request.max_tokens = min(request.max_tokens, 500)

        # 더 빠른 모델로 변경
        if self.provider == LLMProvider.OPENAI and self.model == "gpt-4":
            self.model = "gpt-3.5-turbo"
        elif self.provider == LLMProvider.ANTHROPIC and self.model == "claude-3-opus":
            self.model = "claude-3-haiku"

        logger.info(f"요청 다운그레이드: max_tokens={request.max_tokens}, model={self.model}")
        return request

    async def _call_llm_api(self, request: LLMRequest) -> LLMResponse:
        """실제 LLM API 호출"""
        if self.provider == LLMProvider.OPENAI:
            return await self._call_openai_api(request)
        elif self.provider == LLMProvider.ANTHROPIC:
            return await self._call_anthropic_api(request)
        elif self.provider == LLMProvider.GEMINI:
            return await self._call_gemini_api(request)
        else:
            return await self._call_mock_api(request)

    async def _call_openai_api(self, request: LLMRequest) -> LLMResponse:
        """OpenAI API 호출"""
        if not self.api_key:
            raise ValueError("OpenAI API key not provided")

        start_time = time.time()

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "top_p": request.top_p,
            "presence_penalty": request.presence_penalty
        }

        if request.stop_sequences:
            payload["stop"] = request.stop_sequences

        response = await self.client.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload
        )
        response.raise_for_status()

        data = response.json()
        content = data["choices"][0]["message"]["content"]
        usage = data["usage"]

        latency = time.time() - start_time
        cost = CostCalculator.calculate_cost(
            "openai", self.model,
            usage["prompt_tokens"],
            usage["completion_tokens"]
        )

        return LLMResponse(
            content=content,
            usage=usage,
            cost=cost,
            latency=latency,
            provider="openai",
            model=self.model,
            finish_reason=data["choices"][0]["finish_reason"],
            metadata={"raw_response": data}
        )

    async def _call_anthropic_api(self, request: LLMRequest) -> LLMResponse:
        """Anthropic API 호출"""
        if not self.api_key:
            raise ValueError("Anthropic API key not provided")

        start_time = time.time()

        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }

        prompt = f"Human: {request.prompt}\n\nAssistant:"
        if request.system_prompt:
            prompt = f"System: {request.system_prompt}\n\n{prompt}"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "max_tokens_to_sample": request.max_tokens,
            "temperature": request.temperature,
            "top_p": request.top_p
        }

        response = await self.client.post(
            "https://api.anthropic.com/v1/complete",
            headers=headers,
            json=payload
        )
        response.raise_for_status()

        data = response.json()
        content = data["completion"]

        latency = time.time() - start_time

        # Anthropic은 토큰 사용량을 제공하지 않으므로 추정
        estimated_input_tokens = len(prompt.split()) * 1.3
        estimated_output_tokens = len(content.split()) * 1.3

        usage = {
            "prompt_tokens": int(estimated_input_tokens),
            "completion_tokens": int(estimated_output_tokens),
            "total_tokens": int(estimated_input_tokens + estimated_output_tokens)
        }

        cost = CostCalculator.calculate_cost(
            "anthropic", self.model,
            usage["prompt_tokens"],
            usage["completion_tokens"]
        )

        return LLMResponse(
            content=content,
            usage=usage,
            cost=cost,
            latency=latency,
            provider="anthropic",
            model=self.model,
            finish_reason=data.get("stop_reason", "stop"),
            metadata={"raw_response": data}
        )

    async def _call_gemini_api(self, request: LLMRequest) -> LLMResponse:
        """Google Gemini API 호출"""
        if not self.api_key:
            raise ValueError("Google API key not provided")

        start_time = time.time()

        # Gemini API는 다른 형식을 사용
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": f"{request.system_prompt}\n\n{request.prompt}" if request.system_prompt else request.prompt}
                    ]
                }
            ],
            "generationConfig": {
                "maxOutputTokens": request.max_tokens,
                "temperature": request.temperature,
                "topP": request.top_p
            }
        }

        response = await self.client.post(url, json=payload)
        response.raise_for_status()

        data = response.json()
        content = data["candidates"][0]["content"]["parts"][0]["text"]

        latency = time.time() - start_time

        # Gemini도 토큰 사용량 추정
        estimated_input_tokens = len(request.prompt.split()) * 1.3
        estimated_output_tokens = len(content.split()) * 1.3

        usage = {
            "prompt_tokens": int(estimated_input_tokens),
            "completion_tokens": int(estimated_output_tokens),
            "total_tokens": int(estimated_input_tokens + estimated_output_tokens)
        }

        cost = CostCalculator.calculate_cost(
            "gemini", self.model,
            usage["prompt_tokens"],
            usage["completion_tokens"]
        )

        return LLMResponse(
            content=content,
            usage=usage,
            cost=cost,
            latency=latency,
            provider="gemini",
            model=self.model,
            finish_reason="stop",
            metadata={"raw_response": data}
        )

    async def _call_mock_api(self, request: LLMRequest) -> LLMResponse:
        """Mock API 호출 (테스트용)"""
        start_time = time.time()

        # 시뮬레이션 지연
        await asyncio.sleep(0.1)

        # Mock 응답 생성
        content = f"Mock 응답: '{request.prompt}'에 대한 답변입니다. "
        content += "이는 테스트용 Mock 응답으로, 실제 LLM API가 호출되지 않았습니다."

        usage = {
            "prompt_tokens": len(request.prompt.split()),
            "completion_tokens": len(content.split()),
            "total_tokens": len(request.prompt.split()) + len(content.split())
        }

        latency = time.time() - start_time
        cost = usage["total_tokens"] * 0.001  # Mock 비용

        return LLMResponse(
            content=content,
            usage=usage,
            cost=cost,
            latency=latency,
            provider="mock",
            model="mock-model",
            finish_reason="stop",
            metadata={"is_mock": True}
        )

    async def _generate_fallback_response(
        self,
        request: LLMRequest,
        elapsed_time: float
    ) -> LLMResponse:
        """폴백 응답 생성"""
        content = f"죄송합니다. '{request.prompt}'에 대한 응답을 생성하는 중 오류가 발생했습니다. "
        content += "나중에 다시 시도해주세요."

        usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }

        return LLMResponse(
            content=content,
            usage=usage,
            cost=0.0,
            latency=elapsed_time,
            provider=self.provider.value,
            model=self.model,
            finish_reason="error",
            metadata={"is_fallback": True}
        )

    def _update_stats(self, response: Optional[LLMResponse], success: bool):
        """통계 업데이트"""
        if success and response:
            self.stats["successful_requests"] += 1
            self.stats["total_tokens"] += response.usage["total_tokens"]
            self.stats["total_cost"] += response.cost

            # 제공자별 분포
            provider = response.provider
            if provider not in self.stats["provider_distribution"]:
                self.stats["provider_distribution"][provider] = 0
            self.stats["provider_distribution"][provider] += 1
        else:
            self.stats["failed_requests"] += 1

    async def generate_with_agent_prompt(
        self,
        query: str,
        context: str,
        agent_profile: Optional[AgentProfile] = None,
        taxonomy_version: str = "1.8.1"
    ) -> LLMResponse:
        """Agent 프롬프트 템플릿을 사용한 생성"""
        if not AGENT_FACTORY_AVAILABLE or not agent_profile:
            # 기본 프롬프트 사용
            prompt = f"질문: {query}\n\n참고 문서:\n{context}\n\n위 문서들을 참고하여 답변해주세요:"
            system_prompt = "당신은 도움이 되는 AI 어시스턴트입니다."
        else:
            # Agent 프롬프트 템플릿 사용
            formatted_prompts = PromptTemplateManager.format_prompt(
                category=agent_profile.category,
                query=query,
                context=context,
                taxonomy_version=taxonomy_version,
                canonical_paths=agent_profile.canonical_paths
            )
            prompt = formatted_prompts["user"]
            system_prompt = formatted_prompts["system"]

        request = LLMRequest(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=agent_profile.prompt_config.get("max_tokens", 1000) if agent_profile else 1000,
            temperature=agent_profile.prompt_config.get("temperature", 0.7) if agent_profile else 0.7
        )

        return await self.generate(request, agent_profile)

    def get_stats(self) -> Dict[str, Any]:
        """서비스 통계 반환"""
        total_requests = self.stats["total_requests"]
        success_rate = (self.stats["successful_requests"] / total_requests * 100) if total_requests > 0 else 0

        return {
            "provider": self.provider.value,
            "model": self.model,
            "total_requests": total_requests,
            "successful_requests": self.stats["successful_requests"],
            "failed_requests": self.stats["failed_requests"],
            "success_rate_percent": success_rate,
            "total_tokens": self.stats["total_tokens"],
            "total_cost": self.stats["total_cost"],
            "average_cost_per_request": self.stats["total_cost"] / self.stats["successful_requests"] if self.stats["successful_requests"] > 0 else 0,
            "p95_latency": self.performance_guard.get_p95_latency(),
            "average_cost": self.performance_guard.get_average_cost(),
            "provider_distribution": self.stats["provider_distribution"]
        }


# 전역 인스턴스들
_llm_services: Dict[str, LLMService] = {}

def get_llm_service(provider: LLMProvider = LLMProvider.OPENAI) -> LLMService:
    """LLM 서비스 인스턴스 반환"""
    provider_key = provider.value

    if provider_key not in _llm_services:
        _llm_services[provider_key] = LLMService(provider=provider)

    return _llm_services[provider_key]


# 편의 함수들
async def generate_with_openai(prompt: str, **kwargs) -> LLMResponse:
    """OpenAI로 생성"""
    service = get_llm_service(LLMProvider.OPENAI)
    request = LLMRequest(prompt=prompt, **kwargs)
    return await service.generate(request)


async def generate_with_agent(
    query: str,
    context: str,
    agent_profile: Optional[AgentProfile] = None,
    provider: LLMProvider = LLMProvider.OPENAI
) -> LLMResponse:
    """Agent 설정을 적용하여 생성"""
    service = get_llm_service(provider)
    return await service.generate_with_agent_prompt(query, context, agent_profile)


# 사용 예시
if __name__ == "__main__":
    async def main():
        # LLM 서비스 테스트
        service = get_llm_service(LLMProvider.MOCK)  # Mock 사용

        request = LLMRequest(
            prompt="RAG 시스템에 대해 설명해주세요",
            max_tokens=500,
            temperature=0.3
        )

        response = await service.generate(request)

        print(f"응답: {response.content}")
        print(f"비용: ₩{response.cost:.3f}")
        print(f"지연시간: {response.latency:.3f}초")
        print(f"토큰 사용: {response.usage}")

        # 통계 확인
        stats = service.get_stats()
        print(f"서비스 통계: {stats}")

    asyncio.run(main())