"""
Gemini LLM Answer Generation Service

Generates natural language answers from search results using Google's Gemini 2.0 Flash model.
Supports multilingual question answering, summarization, and key point extraction.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import time

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class AnswerResult:
    """Generated answer with metadata"""
    answer: str
    source_count: int
    generation_time: float
    model: str
    language_detected: str


class GeminiLLMService:
    """
    Gemini-based LLM service for RAG answer generation

    Features:
    - Multilingual question answering (Korean/English)
    - Context-aware summarization
    - Key point extraction
    - Source attribution
    """

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.5-flash"):
        """Initialize Gemini LLM service"""
        if not GEMINI_AVAILABLE:
            raise ImportError("google-generativeai package not installed. Run: pip install google-generativeai")

        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")

        # Configure Gemini API
        genai.configure(api_key=self.api_key)

        self.model_name = model_name
        self.model = genai.GenerativeModel(model_name)

        logger.info(f"Gemini LLM service initialized: {model_name}")

    def _detect_language(self, question: str) -> str:
        """Detect question language (Korean or English)"""
        # Simple heuristic: check for Korean characters
        korean_chars = sum(1 for c in question if '\uac00' <= c <= '\ud7a3')
        return "ko" if korean_chars > 0 else "en"

    def _build_rag_prompt(
        self,
        question: str,
        search_results: List[Dict[str, Any]],
        language: str,
        mode: str = "answer"
    ) -> str:
        """Build RAG prompt for Gemini"""

        # Build context from search results
        context_parts = []
        for idx, result in enumerate(search_results, 1):
            text = result.get("text", "")
            source = result.get("source_url") or result.get("title", "Unknown")
            score = result.get("hybrid_score", 0.0)

            context_parts.append(
                f"[Document {idx}] (Relevance: {score:.2f})\n"
                f"Source: {source}\n"
                f"Content: {text}\n"
            )

        context = "\n".join(context_parts)

        # Language-specific prompts
        if language == "ko":
            if mode == "answer":
                system_prompt = """당신은 검색된 문서를 바탕으로 정확하고 유용한 답변을 제공하는 AI 어시스턴트입니다.

주어진 문서들을 분석하여 사용자의 질문에 명확하게 답변하세요.

답변 작성 가이드:
1. **직접 답변**: 질문에 직접적으로 답하세요
2. **근거 제시**: 문서의 내용을 바탕으로 설명하세요
3. **구조화**: 복잡한 답변은 번호나 불릿 포인트로 정리하세요
4. **출처 표시**: 어느 문서에서 정보를 가져왔는지 표시하세요
5. **한국어 사용**: 모든 답변은 자연스러운 한국어로 작성하세요

문서에 정보가 없으면 "제공된 문서에서 해당 정보를 찾을 수 없습니다"라고 답하세요."""

            elif mode == "summary":
                system_prompt = """당신은 문서를 간결하게 요약하는 AI 어시스턴트입니다.

검색된 문서들의 핵심 내용을 3-5줄로 요약하세요.
중요한 개념과 키워드를 포함하되, 불필요한 세부사항은 제외하세요."""

            else:  # keypoints
                system_prompt = """당신은 문서의 핵심 포인트를 추출하는 AI 어시스턴트입니다.

검색된 문서들에서 가장 중요한 3-5개 포인트를 불릿 포인트로 정리하세요.
각 포인트는 한 줄로 간결하게 작성하세요."""

        else:  # English
            if mode == "answer":
                system_prompt = """You are an AI assistant that provides accurate and helpful answers based on retrieved documents.

Analyze the provided documents and answer the user's question clearly.

Answer Guidelines:
1. **Direct Answer**: Address the question directly
2. **Evidence**: Support your answer with information from the documents
3. **Structure**: Use bullet points or numbering for complex answers
4. **Attribution**: Indicate which document(s) the information comes from
5. **Language**: Write naturally in English

If the documents don't contain relevant information, state "The provided documents don't contain information about this topic." """

            elif mode == "summary":
                system_prompt = """You are an AI assistant that creates concise summaries.

Summarize the key content from the retrieved documents in 3-5 sentences.
Include important concepts and keywords, but exclude unnecessary details."""

            else:  # keypoints
                system_prompt = """You are an AI assistant that extracts key points from documents.

Extract the 3-5 most important points from the retrieved documents as bullet points.
Keep each point concise (one line)."""

        # Combine system prompt, context, and question
        full_prompt = f"""{system_prompt}

검색된 문서:
{context}

질문: {question}

답변:"""

        return full_prompt

    async def generate_answer(
        self,
        question: str,
        search_results: List[Dict[str, Any]],
        mode: str = "answer"
    ) -> AnswerResult:
        """
        Generate answer from search results

        Args:
            question: User question
            search_results: List of search result dicts with 'text', 'source_url', 'hybrid_score'
            mode: Generation mode - "answer", "summary", or "keypoints"

        Returns:
            AnswerResult with generated answer
        """
        start_time = time.time()

        if not search_results:
            return AnswerResult(
                answer="검색 결과가 없어 답변을 생성할 수 없습니다." if self._detect_language(question) == "ko"
                       else "No search results found to generate an answer.",
                source_count=0,
                generation_time=0.0,
                model=self.model_name,
                language_detected=self._detect_language(question)
            )

        # Detect language
        language = self._detect_language(question)

        # Build prompt
        prompt = self._build_rag_prompt(question, search_results, language, mode)

        try:
            # Generate answer using Gemini
            response = self.model.generate_content(prompt)
            answer = response.text

            generation_time = time.time() - start_time

            logger.info(
                f"Generated {mode} answer in {generation_time:.2f}s "
                f"(language: {language}, sources: {len(search_results)})"
            )

            return AnswerResult(
                answer=answer,
                source_count=len(search_results),
                generation_time=generation_time,
                model=self.model_name,
                language_detected=language
            )

        except Exception as e:
            logger.error(f"Answer generation failed: {e}")
            raise


# Global LLM service instance
_llm_service: Optional[GeminiLLMService] = None


def get_llm_service() -> GeminiLLMService:
    """Get or create global LLM service instance"""
    global _llm_service

    if _llm_service is None:
        _llm_service = GeminiLLMService()

    return _llm_service
