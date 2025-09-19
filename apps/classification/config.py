"""
Classification Pipeline Configuration
====================================

Configuration management for the hybrid classification system
"""

import os
from typing import Dict, Any, Optional

class ClassificationConfig:
    """Configuration manager for classification pipeline"""

    @staticmethod
    def get_default_config() -> Dict[str, Any]:
        """Get default configuration for classification pipeline"""
        return {
            "performance_targets": {
                "faithfulness_threshold": 0.85,
                "accuracy_threshold": 0.90,
                "hitl_rate_target": 0.30,
                "latency_p95_target": 2.0,  # seconds
                "cost_target": 5.0  # Korean Won
            },

            "pipeline": {
                "enable_rule_classifier": True,
                "enable_llm_classifier": True,
                "enable_cross_validation": True,
                "parallel_execution": True,
                "cache_results": True
            },

            "quality_gates": {
                "min_rule_confidence": 0.3,
                "min_llm_confidence": 0.5,
                "hitl_confidence_threshold": 0.70,
                "auto_approval_threshold": 0.95
            },

            "cost_optimization": {
                "llm_token_limit": 1000,
                "cache_ttl_hours": 24,
                "batch_processing": False
            },

            # Rule classifier configuration
            "rule_classifier": {
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
                }
            },

            # LLM classifier configuration
            "llm_classifier": {
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
                "validation": {
                    "min_confidence": 0.6,
                    "max_alternatives": 3,
                    "required_reasoning_length": 20
                }
            },

            # Confidence scorer configuration
            "confidence_scorer": {
                "weights": {
                    "rerank_score": 0.40,
                    "source_agreement": 0.30,
                    "answer_consistency": 0.30
                },
                "bonus_weights": {
                    "path_depth": 0.05,
                    "reasoning_quality": 0.05,
                    "provider_reliability": 0.03
                },
                "thresholds": {
                    "high_confidence": 0.85,
                    "medium_confidence": 0.70,
                    "low_confidence": 0.50,
                    "hitl_threshold": 0.70
                },
                "provider_reliability": {
                    "openai": 0.95,
                    "anthropic": 0.93,
                    "rule_based": 0.80,
                    "fallback": 0.60
                }
            },

            # HITL queue configuration
            "hitl_queue": {
                "queue_limits": {
                    "max_pending": 1000,
                    "max_per_reviewer": 20,
                    "auto_escalate_hours": 24
                },
                "priority_rules": {
                    "high_confidence_disagreement": 3,  # HIGH
                    "business_critical_path": 4,        # URGENT
                    "new_domain_detection": 2,          # MEDIUM
                    "low_confidence": 1                 # LOW
                },
                "auto_approval": {
                    "enabled": False,
                    "confidence_threshold": 0.95,
                    "agreement_threshold": 0.9
                },
                "feedback_learning": {
                    "enabled": True,
                    "min_feedback_length": 10,
                    "update_rules_threshold": 0.8
                }
            }
        }

    @staticmethod
    def get_production_config() -> Dict[str, Any]:
        """Get production-optimized configuration"""
        config = ClassificationConfig.get_default_config()

        # Production optimizations
        config["pipeline"]["parallel_execution"] = True
        config["pipeline"]["cache_results"] = True
        config["cost_optimization"]["batch_processing"] = True
        config["hitl_queue"]["auto_approval"]["enabled"] = True

        # Tighter quality gates for production
        config["quality_gates"]["hitl_confidence_threshold"] = 0.75
        config["quality_gates"]["auto_approval_threshold"] = 0.92

        return config

    @staticmethod
    def get_development_config() -> Dict[str, Any]:
        """Get development/testing configuration"""
        config = ClassificationConfig.get_default_config()

        # Development settings
        config["pipeline"]["parallel_execution"] = False  # Easier debugging
        config["cost_optimization"]["llm_token_limit"] = 500  # Lower cost
        config["hitl_queue"]["queue_limits"]["max_pending"] = 100  # Smaller queue

        # More lenient for testing
        config["quality_gates"]["hitl_confidence_threshold"] = 0.60

        return config

    @staticmethod
    def get_config_for_environment(env: str = None) -> Dict[str, Any]:
        """Get configuration based on environment"""
        if env is None:
            env = os.getenv("CLASSIFICATION_ENV", "development")

        if env.lower() == "production":
            return ClassificationConfig.get_production_config()
        elif env.lower() == "testing":
            return ClassificationConfig.get_development_config()
        else:
            return ClassificationConfig.get_default_config()

    @staticmethod
    def validate_config(config: Dict[str, Any]) -> tuple[bool, list[str]]:
        """Validate configuration for required fields and sensible values"""
        errors = []

        # Required top-level sections
        required_sections = [
            "performance_targets", "pipeline", "quality_gates",
            "rule_classifier", "llm_classifier", "confidence_scorer", "hitl_queue"
        ]

        for section in required_sections:
            if section not in config:
                errors.append(f"Missing required section: {section}")

        # Validate performance targets
        if "performance_targets" in config:
            targets = config["performance_targets"]
            if targets.get("faithfulness_threshold", 0) < 0.5:
                errors.append("Faithfulness threshold too low (< 0.5)")
            if targets.get("accuracy_threshold", 0) < 0.7:
                errors.append("Accuracy threshold too low (< 0.7)")
            if targets.get("hitl_rate_target", 1.0) > 0.5:
                errors.append("HITL rate target too high (> 50%)")

        # Validate confidence weights
        if "confidence_scorer" in config and "weights" in config["confidence_scorer"]:
            weights = config["confidence_scorer"]["weights"]
            total_weight = sum(weights.values())
            if abs(total_weight - 1.0) > 0.01:
                errors.append(f"Confidence weights don't sum to 1.0 (sum: {total_weight})")

        # Validate API key environment variables
        if "llm_classifier" in config and "providers" in config["llm_classifier"]:
            for provider, settings in config["llm_classifier"]["providers"].items():
                api_key_env = settings.get("api_key_env")
                if api_key_env and not os.getenv(api_key_env):
                    errors.append(f"API key environment variable not set: {api_key_env}")

        return len(errors) == 0, errors

    @staticmethod
    def override_config(base_config: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
        """Apply configuration overrides to base config"""
        import copy
        config = copy.deepcopy(base_config)

        def update_nested_dict(d: Dict[str, Any], u: Dict[str, Any]):
            for k, v in u.items():
                if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                    update_nested_dict(d[k], v)
                else:
                    d[k] = v

        update_nested_dict(config, overrides)
        return config

# Environment-specific configurations
def get_config() -> Dict[str, Any]:
    """Get configuration for current environment"""
    return ClassificationConfig.get_config_for_environment()

def get_test_config() -> Dict[str, Any]:
    """Get configuration optimized for testing"""
    config = ClassificationConfig.get_development_config()

    # Test-specific overrides
    test_overrides = {
        "llm_classifier": {
            "providers": {
                "openai": {
                    "max_tokens": 500,  # Reduce cost for testing
                    "temperature": 0.1  # More deterministic for testing
                }
            }
        },
        "hitl_queue": {
            "queue_limits": {
                "max_pending": 50,
                "max_per_reviewer": 5
            }
        }
    }

    return ClassificationConfig.override_config(config, test_overrides)