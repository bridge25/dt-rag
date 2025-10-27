"""
Unit tests for main application startup and lifecycle - SPEC-ENV-VALIDATE-001

Tests environment validation logic during FastAPI application startup,
particularly focusing on OpenAI API key validation across different environments.
"""

import pytest
import os
from unittest.mock import patch, MagicMock, AsyncMock
from contextlib import asynccontextmanager


class TestStartupValidation:
    """Test cases for startup environment validation - SPEC-ENV-VALIDATE-001 Phase 2"""

    @pytest.mark.asyncio
    async def test_startup_production_missing_api_key(self):
        """Test that production startup FAILS when OpenAI API key is missing"""
        with patch.dict(
            os.environ, {"ENVIRONMENT": "production", "OPENAI_API_KEY": ""}, clear=True
        ):
            with patch(
                "apps.api.main.test_database_connection",
                new_callable=AsyncMock,
                return_value=True,
            ):
                with patch(
                    "apps.api.main.init_database",
                    new_callable=AsyncMock,
                    return_value=True,
                ):
                    with patch(
                        "apps.api.main.rate_limiter.initialize", new_callable=AsyncMock
                    ):
                        from apps.api.main import lifespan, app

                        with pytest.raises(
                            ValueError, match="OPENAI_API_KEY.*REQUIRED.*production"
                        ):
                            async with lifespan(app):
                                pass

    @pytest.mark.asyncio
    async def test_startup_production_valid_api_key(self):
        """Test that production startup SUCCEEDS with valid OpenAI API key"""
        valid_key = "sk-" + "a" * 48

        with patch.dict(
            os.environ,
            {
                "ENVIRONMENT": "production",
                "OPENAI_API_KEY": valid_key,
                "SECRET_KEY": "b" * 32,
            },
            clear=True,
        ):
            with patch(
                "apps.api.main.test_database_connection",
                new_callable=AsyncMock,
                return_value=True,
            ):
                with patch(
                    "apps.api.main.init_database",
                    new_callable=AsyncMock,
                    return_value=True,
                ):
                    with patch(
                        "apps.api.main.rate_limiter.initialize", new_callable=AsyncMock
                    ):
                        from apps.api.main import lifespan, app

                        async with lifespan(app):
                            pass

    @pytest.mark.asyncio
    async def test_startup_development_missing_api_key(self):
        """Test that development startup WARNS but continues when OpenAI API key is missing"""
        env_vars = {"ENVIRONMENT": "development"}
        if "OPENAI_API_KEY" in os.environ:
            env_vars["OPENAI_API_KEY"] = ""

        with patch.dict(os.environ, env_vars):
            with patch("apps.api.env_manager._env_manager", None):
                with patch(
                    "apps.api.main.test_database_connection",
                    new_callable=AsyncMock,
                    return_value=True,
                ):
                    with patch(
                        "apps.api.main.init_database",
                        new_callable=AsyncMock,
                        return_value=True,
                    ):
                        with patch(
                            "apps.api.main.rate_limiter.initialize",
                            new_callable=AsyncMock,
                        ):
                            with patch("apps.api.main.logger") as mock_logger:
                                from apps.api.main import lifespan, app

                                async with lifespan(app):
                                    mock_logger.warning.assert_any_call(
                                        "OPENAI_API_KEY not configured - using fallback dummy embeddings"
                                    )

    @pytest.mark.asyncio
    async def test_startup_development_valid_api_key(self):
        """Test that development startup SUCCEEDS with valid OpenAI API key"""
        valid_key = "sk-" + "c" * 48

        with patch.dict(
            os.environ,
            {"ENVIRONMENT": "development", "OPENAI_API_KEY": valid_key},
            clear=True,
        ):
            with patch(
                "apps.api.main.test_database_connection",
                new_callable=AsyncMock,
                return_value=True,
            ):
                with patch(
                    "apps.api.main.init_database",
                    new_callable=AsyncMock,
                    return_value=True,
                ):
                    with patch(
                        "apps.api.main.rate_limiter.initialize", new_callable=AsyncMock
                    ):
                        from apps.api.main import lifespan, app

                        async with lifespan(app):
                            pass

    @pytest.mark.asyncio
    async def test_startup_invalid_api_key_format(self):
        """Test that startup detects and warns about invalid API key format"""
        invalid_key = "invalid-key-format"

        with patch.dict(
            os.environ,
            {"ENVIRONMENT": "development", "OPENAI_API_KEY": invalid_key},
            clear=True,
        ):
            with patch(
                "apps.api.main.test_database_connection",
                new_callable=AsyncMock,
                return_value=True,
            ):
                with patch(
                    "apps.api.main.init_database",
                    new_callable=AsyncMock,
                    return_value=True,
                ):
                    with patch(
                        "apps.api.main.rate_limiter.initialize", new_callable=AsyncMock
                    ):
                        with patch("apps.api.main.logger") as mock_logger:
                            from apps.api.main import lifespan, app

                            async with lifespan(app):
                                mock_logger.warning.assert_any_call(
                                    "OPENAI_API_KEY format is invalid - using fallback dummy embeddings"
                                )
