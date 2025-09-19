"""
LLM-based Classification Module
==============================

High-accuracy second-stage classification using:
- GPT-4/Claude API integration
- Chain-of-thought reasoning
- Few-shot learning with examples
- Multiple validation strategies
"""

import asyncio
import json
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import httpx
import re
from enum import Enum

logger = logging.getLogger(__name__)

class LLMProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    FALLBACK = "fallback"

@dataclass
class LLMResult:
    """LLM classification result"""
    candidates: List[Dict[str, Any]]
    reasoning: List[str]
    confidence: float
    processing_time: float
    provider: str
    model: str
    tokens_used: Optional[int] = None

class LLMClassifier:
    """LLM-based text classifier with multiple provider support"""

    def __init__(self, config: Optional[Dict] = None):
        self.config = self._load_config(config)
        self.client = httpx.AsyncClient(timeout=30.0)

    def _load_config(self, config: Optional[Dict]) -> Dict[str, Any]:
        """Load LLM configuration"""
        default_config = {
            "providers": {
                "openai": {
                    "model": "gpt-4-1106-preview",
                    "api_key_env": "OPENAI_API_KEY",
                    "max_tokens": 1000,
                    "temperature": 0.3
                },
                "anthropic": {
                    "model": "claude-3-sonnet-20240229",
                    "api_key_env": "ANTHROPIC_API_KEY",
                    "max_tokens": 1000,
                    "temperature": 0.3
                }
            },
            "prompt_templates": {
                "classification": """You are an expert at classifying text into hierarchical taxonomy categories.

Given the text below, classify it into the most appropriate category path from this taxonomy:

TAXONOMY STRUCTURE:
- AI (Artificial Intelligence)
  - RAG (Retrieval-Augmented Generation)
  - ML (Machine Learning)
  - Taxonomy (Classification Systems)
  - General (General AI Topics)

CLASSIFICATION RULES:
1. Choose the most specific applicable category
2. Provide 1-3 alternative classifications with confidence scores
3. Give detailed reasoning for your choice
4. Consider the context and technical depth of the content

TEXT TO CLASSIFY:
{text}

RESPONSE FORMAT (JSON):
{{
  "primary_classification": {{
    "path": ["AI", "Category"],
    "confidence": 0.85,
    "reasoning": "Detailed explanation..."
  }},
  "alternatives": [
    {{
      "path": ["AI", "Alternative"],
      "confidence": 0.70,
      "reasoning": "Alternative explanation..."
    }}
  ],
  "analysis": {{
    "technical_depth": "high|medium|low",
    "domain_specificity": "specific|general",
    "key_concepts": ["concept1", "concept2"],
    "uncertainty_factors": ["factor1", "factor2"]
  }}
}}

Response:"""
            },
            "few_shot_examples": [
                {
                    "text": "This paper presents a novel approach to retrieval-augmented generation using dense vector representations.",
                    "classification": {
                        "path": ["AI", "RAG"],
                        "confidence": 0.92,
                        "reasoning": "Clear discussion of RAG methodology with technical details about vector representations"
                    }
                },
                {
                    "text": "We implement a machine learning model for predicting customer behavior using ensemble methods.",
                    "classification": {
                        "path": ["AI", "ML"],
                        "confidence": 0.88,
                        "reasoning": "Focuses on ML model implementation and prediction, specific use of ensemble methods"
                    }
                }
            ],
            "validation": {
                "min_confidence": 0.6,
                "max_alternatives": 3,
                "required_reasoning_length": 20
            }
        }

        if config:
            # Merge with provided config
            for key, value in config.items():
                if key in default_config and isinstance(value, dict):
                    default_config[key].update(value)
                else:
                    default_config[key] = value

        return default_config

    async def classify(self, text: str, taxonomy_version: str = "1",
                      rule_candidates: Optional[List[Dict]] = None) -> LLMResult:
        """
        Perform LLM-based classification

        Args:
            text: Input text to classify
            taxonomy_version: Version of taxonomy to use
            rule_candidates: Candidates from rule-based classifier

        Returns:
            LLMResult with classification results
        """
        start_time = time.time()

        try:
            # Try providers in order of preference
            providers = ["openai", "anthropic"]

            for provider_name in providers:
                try:
                    result = await self._classify_with_provider(
                        provider_name, text, rule_candidates
                    )
                    if result:
                        result.processing_time = time.time() - start_time
                        return result
                except Exception as e:
                    logger.warning(f"Provider {provider_name} failed: {e}")
                    continue

            # Fallback to simple heuristic-based classification
            logger.warning("All LLM providers failed, using fallback classification")
            return await self._fallback_classification(text, time.time() - start_time)

        except Exception as e:
            logger.error(f"LLM classification failed: {e}")
            return await self._fallback_classification(text, time.time() - start_time)

    async def _classify_with_provider(self, provider: str, text: str,
                                    rule_candidates: Optional[List[Dict]]) -> Optional[LLMResult]:
        """Classify using specific LLM provider"""
        import os

        provider_config = self.config["providers"][provider]
        api_key = os.getenv(provider_config["api_key_env"])

        if not api_key:
            logger.warning(f"No API key found for {provider}")
            return None

        # Build prompt with context
        prompt = self._build_prompt(text, rule_candidates)

        if provider == "openai":
            return await self._classify_openai(prompt, provider_config, api_key)
        elif provider == "anthropic":
            return await self._classify_anthropic(prompt, provider_config, api_key)

        return None

    def _build_prompt(self, text: str, rule_candidates: Optional[List[Dict]]) -> str:
        """Build classification prompt with context"""
        base_prompt = self.config["prompt_templates"]["classification"]

        # Add rule-based context if available
        context_addition = ""
        if rule_candidates:
            context_addition = f"""

RULE-BASED SUGGESTIONS:
The rule-based classifier suggests these categories:
{json.dumps(rule_candidates, indent=2)}

Consider these suggestions but make your own analysis based on the content."""

        # Add few-shot examples
        examples_text = "\n\nEXAMPLES:\n"
        for i, example in enumerate(self.config["few_shot_examples"]):
            examples_text += f"\nExample {i+1}:\nText: {example['text']}\n"
            examples_text += f"Classification: {json.dumps(example['classification'], indent=2)}\n"

        final_prompt = base_prompt.format(text=text) + context_addition + examples_text

        return final_prompt

    async def _classify_openai(self, prompt: str, config: Dict, api_key: str) -> LLMResult:
        """Classify using OpenAI GPT-4"""
        try:
            response = await self.client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": config["model"],
                    "messages": [
                        {"role": "system", "content": "You are an expert text classifier. Always respond with valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": config["max_tokens"],
                    "temperature": config["temperature"],
                    "response_format": {"type": "json_object"}
                }
            )

            if response.status_code != 200:
                logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                return None

            result = response.json()
            content = result["choices"][0]["message"]["content"]
            tokens_used = result.get("usage", {}).get("total_tokens", 0)

            # Parse JSON response
            classification_data = json.loads(content)

            return self._parse_llm_response(classification_data, "openai", config["model"], tokens_used)

        except Exception as e:
            logger.error(f"OpenAI classification error: {e}")
            return None

    async def _classify_anthropic(self, prompt: str, config: Dict, api_key: str) -> LLMResult:
        """Classify using Anthropic Claude"""
        try:
            response = await self.client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01"
                },
                json={
                    "model": config["model"],
                    "max_tokens": config["max_tokens"],
                    "temperature": config["temperature"],
                    "messages": [
                        {"role": "user", "content": prompt}
                    ]
                }
            )

            if response.status_code != 200:
                logger.error(f"Anthropic API error: {response.status_code} - {response.text}")
                return None

            result = response.json()
            content = result["content"][0]["text"]
            tokens_used = result.get("usage", {}).get("output_tokens", 0)

            # Extract JSON from response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if not json_match:
                logger.error("No JSON found in Anthropic response")
                return None

            classification_data = json.loads(json_match.group())

            return self._parse_llm_response(classification_data, "anthropic", config["model"], tokens_used)

        except Exception as e:
            logger.error(f"Anthropic classification error: {e}")
            return None

    def _parse_llm_response(self, data: Dict, provider: str, model: str,
                           tokens_used: int) -> LLMResult:
        """Parse LLM response into standardized format"""
        try:
            # Extract primary classification
            primary = data.get("primary_classification", {})
            primary_candidate = {
                "path": primary.get("path", ["AI", "General"]),
                "confidence": primary.get("confidence", 0.7),
                "source": "llm",
                "reasoning": [primary.get("reasoning", "LLM classification")],
                "provider": provider,
                "model": model
            }

            # Extract alternatives
            alternatives = data.get("alternatives", [])
            alternative_candidates = []

            for alt in alternatives[:self.config["validation"]["max_alternatives"]]:
                alt_candidate = {
                    "path": alt.get("path", ["AI", "General"]),
                    "confidence": alt.get("confidence", 0.5),
                    "source": "llm_alternative",
                    "reasoning": [alt.get("reasoning", "Alternative classification")],
                    "provider": provider,
                    "model": model
                }
                alternative_candidates.append(alt_candidate)

            # All candidates
            all_candidates = [primary_candidate] + alternative_candidates

            # Extract analysis for reasoning
            analysis = data.get("analysis", {})
            reasoning = [
                primary.get("reasoning", ""),
                f"Technical depth: {analysis.get('technical_depth', 'unknown')}",
                f"Domain specificity: {analysis.get('domain_specificity', 'unknown')}",
                f"Key concepts: {', '.join(analysis.get('key_concepts', []))}"
            ]

            # Overall confidence (weighted by primary)
            overall_confidence = primary.get("confidence", 0.7)

            return LLMResult(
                candidates=all_candidates,
                reasoning=reasoning,
                confidence=overall_confidence,
                processing_time=0.0,  # Set by caller
                provider=provider,
                model=model,
                tokens_used=tokens_used
            )

        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            raise

    async def _fallback_classification(self, text: str, processing_time: float) -> LLMResult:
        """Fallback classification when LLM providers fail"""
        # Simple keyword-based fallback
        text_lower = text.lower()

        candidates = []

        # RAG detection
        if any(term in text_lower for term in ["rag", "retrieval", "augmented", "vector", "embedding"]):
            candidates.append({
                "path": ["AI", "RAG"],
                "confidence": 0.7,
                "source": "fallback",
                "reasoning": ["Detected RAG-related keywords"],
                "provider": "fallback",
                "model": "keyword_matching"
            })

        # ML detection
        elif any(term in text_lower for term in ["machine learning", "model", "training", "algorithm"]):
            candidates.append({
                "path": ["AI", "ML"],
                "confidence": 0.7,
                "source": "fallback",
                "reasoning": ["Detected ML-related keywords"],
                "provider": "fallback",
                "model": "keyword_matching"
            })

        # Taxonomy detection
        elif any(term in text_lower for term in ["taxonomy", "classification", "hierarchy", "category"]):
            candidates.append({
                "path": ["AI", "Taxonomy"],
                "confidence": 0.7,
                "source": "fallback",
                "reasoning": ["Detected taxonomy-related keywords"],
                "provider": "fallback",
                "model": "keyword_matching"
            })

        # Default to General AI
        if not candidates:
            candidates.append({
                "path": ["AI", "General"],
                "confidence": 0.6,
                "source": "fallback",
                "reasoning": ["No specific domain detected, defaulting to General AI"],
                "provider": "fallback",
                "model": "default"
            })

        return LLMResult(
            candidates=candidates,
            reasoning=["Fallback classification used due to LLM provider failures"],
            confidence=candidates[0]["confidence"],
            processing_time=processing_time,
            provider="fallback",
            model="keyword_heuristics"
        )

    async def validate_response(self, result: LLMResult) -> Tuple[bool, List[str]]:
        """Validate LLM response quality"""
        issues = []

        # Check confidence levels
        if result.confidence < self.config["validation"]["min_confidence"]:
            issues.append(f"Low confidence: {result.confidence}")

        # Check reasoning quality
        reasoning_text = ' '.join(result.reasoning)
        if len(reasoning_text) < self.config["validation"]["required_reasoning_length"]:
            issues.append("Insufficient reasoning provided")

        # Check path validity
        for candidate in result.candidates:
            path = candidate.get("path", [])
            if not path or path[0] != "AI":
                issues.append(f"Invalid taxonomy path: {path}")

        return len(issues) == 0, issues

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

    def get_provider_stats(self) -> Dict[str, Any]:
        """Get statistics about provider usage"""
        # This would track usage stats in a real implementation
        return {
            "available_providers": list(self.config["providers"].keys()),
            "fallback_rate": 0.0,  # Would track actual fallback usage
            "average_tokens": 0,   # Would track token usage
            "average_latency": 0.0 # Would track response times
        }