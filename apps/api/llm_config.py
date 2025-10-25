"""
LLM Configuration Manager
"""
# @CODE:MYPY-001:PHASE2:BATCH5 | SPEC: .moai/specs/SPEC-MYPY-001/spec.md

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class LLMConfigManager:
    """LLM Configuration Manager"""

    def __init__(self) -> None:
        self.services = {
            "openai": {"status": "available", "models": ["gpt-3.5-turbo", "gpt-4"]},
            "anthropic": {
                "status": "available",
                "models": ["claude-3-sonnet", "claude-3-haiku"],
            },
            "gemini": {
                "status": "available",
                "models": ["gemini-pro", "gemini-pro-vision"],
            },
        }

    def get_service_status(self) -> Dict[str, Any]:
        """Get LLM service status"""
        available_services = [
            k for k, v in self.services.items() if v["status"] == "available"
        ]

        return {
            "system_operational": len(available_services) > 0,
            "available_services": available_services,
            "total_services": len(self.services),
            "service_details": self.services,
        }

    def get_available_models(self, service: Optional[str] = None) -> List[str]:
        """Get available models"""
        if service and service in self.services:
            service_models = self.services[service].get("models", [])
            return list(service_models) if service_models else []

        models: List[str] = []
        for svc in self.services.values():
            if svc["status"] == "available":
                svc_models = svc.get("models", [])
                if svc_models:
                    models.extend(list(svc_models))
        return models

    def is_service_available(self, service: str) -> bool:
        """Check if service is available"""
        return self.services.get(service, {}).get("status") == "available"


# Global instance
_llm_config_manager = LLMConfigManager()


def get_llm_config() -> LLMConfigManager:
    """Get LLM config manager instance"""
    return _llm_config_manager
