"""
Rule-based Classification Module
===============================

Fast first-stage classification using:
- Keyword pattern matching
- Regular expression rules
- Domain-specific heuristics
- Hierarchical classification rules
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass
import json
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class RuleMatch:
    """Rule matching result"""
    rule_id: str
    pattern: str
    match_text: str
    confidence: float
    weight: float
    path: List[str]

@dataclass
class RuleResult:
    """Rule-based classification result"""
    candidates: List[Dict[str, Any]]
    total_score: float
    matched_rules: List[RuleMatch]
    processing_time: float

class RuleBasedClassifier:
    """Rule-based text classifier using patterns and heuristics"""

    def __init__(self, rules_config: Optional[Dict] = None):
        self.rules = self._load_rules(rules_config)
        self.stopwords = self._load_stopwords()

    def _load_rules(self, config: Optional[Dict]) -> Dict[str, Any]:
        """Load classification rules from config or defaults"""
        if config:
            return config

        # Default rule configuration
        return {
            "domain_rules": {
                "ai": {
                    "patterns": [
                        r"\b(artificial intelligence|AI|machine learning|ML|deep learning|neural network)\b",
                        r"\b(chatgpt|llm|large language model|transformer|bert|gpt)\b",
                        r"\b(reinforcement learning|supervised learning|unsupervised learning)\b"
                    ],
                    "keywords": ["artificial", "intelligence", "machine", "learning", "neural", "model"],
                    "weight": 1.0,
                    "path": ["AI"]
                },
                "rag": {
                    "patterns": [
                        r"\b(retrieval augmented generation|RAG|vector database|embedding)\b",
                        r"\b(document retrieval|semantic search|knowledge base)\b",
                        r"\b(langchain|llamaindex|chromadb|pinecone|weaviate)\b"
                    ],
                    "keywords": ["retrieval", "augmented", "generation", "vector", "embedding", "semantic"],
                    "weight": 1.2,
                    "path": ["AI", "RAG"]
                },
                "ml": {
                    "patterns": [
                        r"\b(classification|regression|clustering|prediction|algorithm)\b",
                        r"\b(random forest|svm|decision tree|gradient boosting)\b",
                        r"\b(scikit-learn|tensorflow|pytorch|keras)\b"
                    ],
                    "keywords": ["classification", "model", "training", "algorithm", "prediction"],
                    "weight": 1.1,
                    "path": ["AI", "ML"]
                },
                "taxonomy": {
                    "patterns": [
                        r"\b(taxonomy|classification system|hierarchy|ontology)\b",
                        r"\b(categorization|tagging|labeling|annotation)\b",
                        r"\b(tree structure|parent|child|node|category)\b"
                    ],
                    "keywords": ["taxonomy", "classification", "hierarchy", "category", "structure"],
                    "weight": 1.0,
                    "path": ["AI", "Taxonomy"]
                }
            },
            "priority_rules": {
                "exact_matches": {
                    "weight": 2.0,
                    "patterns": [
                        (r"\bRAG system\b", ["AI", "RAG"]),
                        (r"\bmachine learning model\b", ["AI", "ML"]),
                        (r"\btaxonomy tree\b", ["AI", "Taxonomy"])
                    ]
                },
                "technical_terms": {
                    "weight": 1.5,
                    "patterns": [
                        (r"\bvector embedding\b", ["AI", "RAG"]),
                        (r"\bneural network\b", ["AI", "ML"]),
                        (r"\bhierarchical classification\b", ["AI", "Taxonomy"])
                    ]
                }
            },
            "exclusion_rules": {
                "generic_ai": {
                    "threshold": 0.3,
                    "patterns": [r"\bAI\b", r"\bmachine\b"],
                    "description": "Too generic, needs more specific context"
                }
            }
        }

    def _load_stopwords(self) -> Set[str]:
        """Load stopwords for text preprocessing"""
        return {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of',
            'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had',
            '은', '는', '이', '가', '을', '를', '에', '의', '와', '과', '도', '로', '으로',
            'this', 'that', 'these', 'those', 'here', 'there', 'when', 'where', 'how', 'why'
        }

    def classify(self, text: str, taxonomy_version: str = "1") -> RuleResult:
        """
        Perform rule-based classification

        Args:
            text: Input text to classify
            taxonomy_version: Version of taxonomy to use

        Returns:
            RuleResult with classification candidates
        """
        import time
        start_time = time.time()

        try:
            # Preprocess text
            processed_text = self._preprocess_text(text)

            # Apply domain rules
            domain_matches = self._apply_domain_rules(processed_text)

            # Apply priority rules
            priority_matches = self._apply_priority_rules(processed_text)

            # Apply exclusion rules
            filtered_matches = self._apply_exclusion_rules(
                domain_matches + priority_matches, processed_text
            )

            # Calculate scores and generate candidates
            candidates = self._generate_candidates(filtered_matches)

            # Calculate total score
            total_score = sum(match.confidence * match.weight for match in filtered_matches)

            processing_time = time.time() - start_time

            return RuleResult(
                candidates=candidates,
                total_score=total_score,
                matched_rules=filtered_matches,
                processing_time=processing_time
            )

        except Exception as e:
            logger.error(f"Rule-based classification failed: {e}")
            processing_time = time.time() - start_time

            # Return fallback result
            return RuleResult(
                candidates=[{
                    "path": ["AI", "General"],
                    "confidence": 0.5,
                    "source": "fallback",
                    "reasoning": [f"Rule classification failed: {str(e)}"]
                }],
                total_score=0.5,
                matched_rules=[],
                processing_time=processing_time
            )

    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for rule matching"""
        # Convert to lowercase
        text = text.lower()

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        # Remove stopwords while preserving technical terms
        words = text.split()
        filtered_words = []

        for i, word in enumerate(words):
            # Keep word if it's part of a technical term or not a stopword
            if (word not in self.stopwords or
                self._is_technical_context(words, i) or
                len(word) > 8):  # Keep longer words even if they're stopwords
                filtered_words.append(word)

        return ' '.join(filtered_words)

    def _is_technical_context(self, words: List[str], index: int) -> bool:
        """Check if word is in technical context"""
        technical_indicators = [
            'machine', 'neural', 'deep', 'artificial', 'language', 'vector',
            'embedding', 'retrieval', 'augmented', 'classification', 'taxonomy'
        ]

        # Check surrounding words
        start = max(0, index - 2)
        end = min(len(words), index + 3)
        context = words[start:end]

        return any(indicator in context for indicator in technical_indicators)

    def _apply_domain_rules(self, text: str) -> List[RuleMatch]:
        """Apply domain-specific classification rules"""
        matches = []

        for domain, config in self.rules["domain_rules"].items():
            domain_score = 0.0
            matched_patterns = []

            # Pattern matching
            for pattern in config["patterns"]:
                pattern_matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in pattern_matches:
                    confidence = 0.8  # Base confidence for pattern match
                    matched_patterns.append(match.group())
                    domain_score += confidence

            # Keyword scoring
            keywords_found = []
            for keyword in config["keywords"]:
                if keyword in text:
                    keywords_found.append(keyword)
                    domain_score += 0.3  # Lower score for individual keywords

            # Create match if significant score
            if domain_score > 0.5:
                final_confidence = min(0.95, domain_score / len(config["patterns"]))

                matches.append(RuleMatch(
                    rule_id=f"domain_{domain}",
                    pattern=f"Domain: {domain}",
                    match_text=f"Patterns: {matched_patterns}, Keywords: {keywords_found}",
                    confidence=final_confidence,
                    weight=config["weight"],
                    path=config["path"]
                ))

        return matches

    def _apply_priority_rules(self, text: str) -> List[RuleMatch]:
        """Apply high-priority rules with exact matching"""
        matches = []

        for rule_type, config in self.rules["priority_rules"].items():
            for pattern, path in config["patterns"]:
                pattern_matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in pattern_matches:
                    matches.append(RuleMatch(
                        rule_id=f"priority_{rule_type}",
                        pattern=pattern,
                        match_text=match.group(),
                        confidence=0.9,  # High confidence for priority rules
                        weight=config["weight"],
                        path=path
                    ))

        return matches

    def _apply_exclusion_rules(self, matches: List[RuleMatch], text: str) -> List[RuleMatch]:
        """Apply exclusion rules to filter out low-quality matches"""
        filtered_matches = []

        for match in matches:
            should_exclude = False

            for exclusion_name, config in self.rules["exclusion_rules"].items():
                if match.confidence < config["threshold"]:
                    # Check if match is too generic
                    for pattern in config["patterns"]:
                        if re.search(pattern, match.match_text, re.IGNORECASE):
                            # Count context words to determine if it's truly generic
                            context_words = len([w for w in text.split()
                                               if w not in self.stopwords])
                            if context_words < 5:  # Very short context
                                should_exclude = True
                                logger.debug(f"Excluding match {match.rule_id}: {config['description']}")
                                break

            if not should_exclude:
                filtered_matches.append(match)

        return filtered_matches

    def _generate_candidates(self, matches: List[RuleMatch]) -> List[Dict[str, Any]]:
        """Generate classification candidates from rule matches"""
        # Group matches by path
        path_groups = {}
        for match in matches:
            path_key = ' -> '.join(match.path)
            if path_key not in path_groups:
                path_groups[path_key] = []
            path_groups[path_key].append(match)

        candidates = []

        # Create candidate for each path group
        for path_key, group_matches in path_groups.items():
            # Calculate combined confidence
            combined_confidence = 0.0
            combined_weight = 0.0
            reasoning = []

            for match in group_matches:
                weighted_confidence = match.confidence * match.weight
                combined_confidence += weighted_confidence
                combined_weight += match.weight
                reasoning.append(f"Rule {match.rule_id}: {match.match_text}")

            # Normalize confidence
            if combined_weight > 0:
                final_confidence = min(0.95, combined_confidence / combined_weight)
            else:
                final_confidence = 0.5

            # Apply path-specific adjustments
            path = group_matches[0].path
            if len(path) > 2:  # More specific paths get slight boost
                final_confidence = min(0.98, final_confidence * 1.1)

            candidates.append({
                "path": path,
                "confidence": final_confidence,
                "source": "rule_based",
                "reasoning": reasoning,
                "rule_count": len(group_matches),
                "total_weight": combined_weight
            })

        # Sort by confidence
        candidates.sort(key=lambda x: x["confidence"], reverse=True)

        # Limit to top 5 candidates
        return candidates[:5]

    def get_rule_statistics(self) -> Dict[str, Any]:
        """Get statistics about loaded rules"""
        stats = {
            "total_domains": len(self.rules["domain_rules"]),
            "total_priority_rules": sum(len(config["patterns"])
                                      for config in self.rules["priority_rules"].values()),
            "total_exclusion_rules": len(self.rules["exclusion_rules"]),
            "domain_breakdown": {}
        }

        for domain, config in self.rules["domain_rules"].items():
            stats["domain_breakdown"][domain] = {
                "patterns": len(config["patterns"]),
                "keywords": len(config["keywords"]),
                "weight": config["weight"],
                "path_depth": len(config["path"])
            }

        return stats

    def validate_rules(self) -> List[str]:
        """Validate rule configuration and return issues"""
        issues = []

        # Check domain rules
        for domain, config in self.rules["domain_rules"].items():
            if not config.get("patterns"):
                issues.append(f"Domain {domain} has no patterns")
            if not config.get("keywords"):
                issues.append(f"Domain {domain} has no keywords")
            if not config.get("path"):
                issues.append(f"Domain {domain} has no path")

            # Validate regex patterns
            for pattern in config.get("patterns", []):
                try:
                    re.compile(pattern)
                except re.error as e:
                    issues.append(f"Invalid regex in domain {domain}: {pattern} - {e}")

        return issues

    def add_custom_rule(self, domain: str, patterns: List[str],
                       keywords: List[str], path: List[str], weight: float = 1.0):
        """Add custom classification rule"""
        self.rules["domain_rules"][domain] = {
            "patterns": patterns,
            "keywords": keywords,
            "weight": weight,
            "path": path
        }

        logger.info(f"Added custom rule for domain: {domain}")

    def update_rule_weights(self, weight_updates: Dict[str, float]):
        """Update rule weights based on performance feedback"""
        for domain, new_weight in weight_updates.items():
            if domain in self.rules["domain_rules"]:
                old_weight = self.rules["domain_rules"][domain]["weight"]
                self.rules["domain_rules"][domain]["weight"] = new_weight
                logger.info(f"Updated weight for {domain}: {old_weight} -> {new_weight}")