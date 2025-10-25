"""
Hybrid Classification Pipeline
Implements 3-stage classification: Rule-based → LLM → Cross-validation

PRD Reference: Line 131-132
- Stage 1: Rule-based (sensitivity/format patterns)
- Stage 2: LLM classification (candidates + reasoning ≥2)
- Stage 3: Cross-validation and confidence calculation
- HITL queue when Conf < 0.70 or drift detected
"""

# @CODE:CLASS-001 | SPEC: .moai/specs/SPEC-CLASS-001/spec.md | TEST: tests/e2e/test_complete_workflow.py

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class HybridClassifier:
    """3-stage hybrid classification pipeline"""

    def __init__(
        self,
        embedding_service: Any,
        taxonomy_dao: Any,
        llm_service: Any,
        confidence_threshold: float = 0.70,
    ) -> None:
        """
        Initialize hybrid classifier

        Args:
            embedding_service: Service for generating embeddings
            taxonomy_dao: DAO for taxonomy operations
            llm_service: LLM service for classification
            confidence_threshold: Minimum confidence for auto-approval (default 0.70)
        """
        self.embedding_service = embedding_service
        self.taxonomy_dao = taxonomy_dao
        self.llm_service = llm_service
        self.confidence_threshold = confidence_threshold
        logger.info(
            f"HybridClassifier initialized with threshold={confidence_threshold}"
        )

    async def classify(
        self,
        chunk_id: str,
        text: str,
        taxonomy_version: str = "1.0.0",
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute 3-stage classification pipeline

        Args:
            chunk_id: Chunk identifier
            text: Text content to classify
            taxonomy_version: Taxonomy version to use
            correlation_id: Correlation ID for tracing

        Returns:
            Classification result with canonical path, candidates, confidence, hitl_required
        """
        import time

        start_time = time.time()

        # Stage 1: Rule-based classification
        rule_result = await self._stage1_rule_based(text, taxonomy_version)

        if rule_result and rule_result["confidence"] >= 0.90:
            # High-confidence rule match, skip LLM
            logger.info(
                f"Rule-based classification succeeded with conf={rule_result['confidence']}"
            )
            return self._build_response(
                chunk_id=chunk_id,
                canonical=rule_result["canonical_path"],
                candidates=rule_result.get("candidates", []),
                confidence=rule_result["confidence"],
                hitl_required=False,
                method="rule_based",
                processing_time_ms=(time.time() - start_time) * 1000,
            )

        # Stage 2: LLM classification
        llm_result = await self._stage2_llm_classification(
            text, taxonomy_version, correlation_id
        )

        # Stage 3: Cross-validation and confidence calculation
        final_result = await self._stage3_cross_validation(
            chunk_id=chunk_id,
            text=text,
            rule_result=rule_result,
            llm_result=llm_result,
            taxonomy_version=taxonomy_version,
        )

        # Calculate processing time
        final_result["processing_time_ms"] = (time.time() - start_time) * 1000

        # Determine HITL requirement
        final_result["hitl_required"] = final_result[
            "confidence"
        ] < self.confidence_threshold or self._detect_drift(rule_result, llm_result)

        return final_result

    async def _stage1_rule_based(
        self, text: str, taxonomy_version: str
    ) -> Optional[Dict[str, Any]]:
        """
        Stage 1: Rule-based classification

        Pattern matching for:
        - Sensitivity patterns (e.g., "confidential", "private")
        - Format patterns (e.g., email, phone, SSN)
        - Domain-specific keywords

        Returns:
            Classification result or None if no rule matched
        """
        text_lower = text.lower()

        # Sensitivity rules
        if any(
            keyword in text_lower for keyword in ["confidential", "secret", "private"]
        ):
            return {
                "canonical_path": ["Security", "Confidential"],
                "candidates": [["Security", "Confidential"]],
                "confidence": 0.95,
                "method": "sensitivity_rule",
            }

        # Technical domain rules
        if "machine learning" in text_lower or "neural network" in text_lower:
            return {
                "canonical_path": ["AI", "ML"],
                "candidates": [["AI", "ML"], ["AI", "Deep Learning"]],
                "confidence": 0.85,
                "method": "keyword_rule",
            }

        if "taxonomy" in text_lower and "classification" in text_lower:
            return {
                "canonical_path": ["AI", "Taxonomy"],
                "candidates": [["AI", "Taxonomy"]],
                "confidence": 0.80,
                "method": "keyword_rule",
            }

        # No rule matched
        return None

    async def _stage2_llm_classification(
        self, text: str, taxonomy_version: str, correlation_id: Optional[str]
    ) -> Dict[str, Any]:
        """
        Stage 2: LLM-based classification

        PRD Line 277: Classifier JSON prompt with reasoning ≥2 and DAG candidates

        Returns:
            LLM classification result with candidates and reasoning
        """
        try:
            # Get taxonomy nodes for context
            taxonomy_tree = await self.taxonomy_dao.get_tree(taxonomy_version)

            # Build prompt with taxonomy context
            taxonomy_context = self._build_taxonomy_context(taxonomy_tree)

            prompt = f"""Classify the following text into the appropriate taxonomy category.

Available taxonomy paths:
{taxonomy_context}

Text to classify:
{text[:500]}

Provide classification with:
1. Primary classification path (as array)
2. Alternative candidate paths (up to 3)
3. Reasoning (at least 2 reasons)
4. Confidence score (0.0-1.0)

Respond in JSON format:
{{
  "canonical_path": ["Category", "Subcategory"],
  "candidates": [["Alt1", "Sub1"], ["Alt2", "Sub2"]],
  "reasoning": ["Reason 1", "Reason 2"],
  "confidence": 0.85
}}"""

            # Call LLM service
            llm_response = await self.llm_service.generate(
                prompt=prompt, temperature=0.3, max_tokens=500, response_format="json"
            )

            # Parse LLM response
            import json

            result = json.loads(llm_response)

            return {
                "canonical_path": result.get("canonical_path", ["General"]),
                "candidates": result.get("candidates", []),
                "reasoning": result.get("reasoning", []),
                "confidence": result.get("confidence", 0.5),
                "method": "llm",
            }

        except Exception as e:
            logger.error(f"LLM classification failed: {e}")
            # Fallback to semantic similarity
            return await self._fallback_semantic_classification(text, taxonomy_version)

    def _build_taxonomy_context(self, taxonomy_tree: List[Dict[str, Any]]) -> str:
        """Build taxonomy context string for LLM prompt"""
        paths = []
        for node in taxonomy_tree[:20]:  # Limit to 20 nodes
            path = " > ".join(node.get("canonical_path", []))
            paths.append(f"- {path}")
        return "\n".join(paths)

    async def _fallback_semantic_classification(
        self, text: str, taxonomy_version: str
    ) -> Dict[str, Any]:
        """Fallback semantic similarity classification when LLM fails"""
        try:
            await self.embedding_service.generate_embedding(text)
            taxonomy_nodes = await self.taxonomy_dao.get_all_leaf_nodes()

            if not taxonomy_nodes:
                return {
                    "canonical_path": ["General"],
                    "candidates": [],
                    "confidence": 0.3,
                    "method": "fallback",
                }

            # Simple cosine similarity (placeholder)
            best_match = taxonomy_nodes[0]

            return {
                "canonical_path": best_match.get("canonical_path", ["General"]),
                "candidates": [
                    node.get("canonical_path", []) for node in taxonomy_nodes[:3]
                ],
                "confidence": 0.5,
                "method": "semantic_fallback",
            }

        except Exception as e:
            logger.error(f"Fallback classification failed: {e}")
            return {
                "canonical_path": ["General"],
                "candidates": [],
                "confidence": 0.3,
                "method": "error_fallback",
            }

    async def _stage3_cross_validation(
        self,
        chunk_id: str,
        text: str,
        rule_result: Optional[Dict[str, Any]],
        llm_result: Dict[str, Any],
        taxonomy_version: str,
    ) -> Dict[str, Any]:
        """
        Stage 3: Cross-validation and confidence calculation

        Combines rule-based and LLM results
        Confidence formula (PRD line 270 - temporary): rerank_score * 0.8

        Returns:
            Final classification result
        """
        # If both rule and LLM agree, boost confidence
        if (
            rule_result
            and rule_result["canonical_path"] == llm_result["canonical_path"]
        ):
            confidence = min(
                (rule_result["confidence"] + llm_result["confidence"]) / 2 * 1.1, 1.0
            )
            canonical = rule_result["canonical_path"]
            method = "cross_validated"

        # LLM only
        elif not rule_result:
            confidence = (
                llm_result["confidence"] * 0.8
            )  # Apply discount for single method
            canonical = llm_result["canonical_path"]
            method = "llm_only"

        # Rule and LLM disagree - use LLM but lower confidence
        else:
            confidence = llm_result["confidence"] * 0.7
            canonical = llm_result["canonical_path"]
            method = "llm_disagreement"

        # Collect all candidates
        all_candidates = []
        if rule_result:
            all_candidates.extend(rule_result.get("candidates", []))
        all_candidates.extend(llm_result.get("candidates", []))

        # Deduplicate candidates
        unique_candidates = []
        seen = set()
        for candidate in all_candidates:
            key = tuple(candidate)
            if key not in seen:
                unique_candidates.append(candidate)
                seen.add(key)

        return self._build_response(
            chunk_id=chunk_id,
            canonical=canonical,
            candidates=unique_candidates[:5],  # Top 5 candidates
            confidence=confidence,
            hitl_required=False,  # Will be set by caller
            method=method,
            processing_time_ms=0,  # Will be set by caller
        )

    def _detect_drift(
        self, rule_result: Optional[Dict[str, Any]], llm_result: Dict[str, Any]
    ) -> bool:
        """
        Detect classification drift

        Returns True if rule and LLM results significantly disagree
        """
        if not rule_result:
            return False

        # Check if paths are completely different
        rule_path = rule_result.get("canonical_path", [])
        llm_path = llm_result.get("canonical_path", [])

        # If no common prefix, consider it drift
        common_prefix_len = 0
        for i in range(min(len(rule_path), len(llm_path))):
            if rule_path[i] == llm_path[i]:
                common_prefix_len += 1
            else:
                break

        # Drift if less than 50% overlap
        return common_prefix_len < len(rule_path) * 0.5

    def _build_response(
        self,
        chunk_id: str,
        canonical: List[str],
        candidates: List[List[str]],
        confidence: float,
        hitl_required: bool,
        method: str,
        processing_time_ms: float,
    ) -> Dict[str, Any]:
        """Build standardized classification response"""
        return {
            "chunk_id": chunk_id,
            "canonical_path": canonical,
            "candidates": candidates,
            "confidence": round(confidence, 3),
            "hitl_required": hitl_required,
            "metadata": {
                "method": method,
                "timestamp": datetime.utcnow().isoformat(),
                "processing_time_ms": round(processing_time_ms, 2),
            },
        }
