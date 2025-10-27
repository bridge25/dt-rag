"""
@TEST:AGENT-GROWTH-004:UNIT - WebhookService Unit Tests

RED Phase: Unit tests for WebhookService
Tests webhook delivery, retry logic with exponential backoff
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from apps.api.background.webhook_service import WebhookService


class TestWebhookService:
    """Unit tests for WebhookService"""

    @pytest.fixture
    def webhook_service(self):
        """Create WebhookService instance"""
        return WebhookService(timeout=10, max_retries=3)

    @pytest.fixture
    def mock_httpx_client(self):
        """Mock httpx AsyncClient"""
        with patch(
            "apps.api.background.webhook_service.httpx.AsyncClient"
        ) as MockClient:
            mock_response = MagicMock()
            mock_response.status_code = 200

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()

            MockClient.return_value = mock_client
            yield mock_client

    @pytest.mark.asyncio
    async def test_send_webhook_succeeds_on_first_attempt(
        self, webhook_service, mock_httpx_client
    ):
        """
        RED Test: Verify send_webhook() succeeds with 200 response

        Expected:
        - Returns True on successful delivery
        - Makes single POST request
        - No retries needed
        """
        url = "https://example.com/webhook"
        payload = {
            "task_id": "test-123",
            "agent_id": "agent-456",
            "status": "completed",
        }

        result = await webhook_service.send_webhook(url, payload)

        assert result is True, "send_webhook should return True on success"
        mock_httpx_client.post.assert_called_once()

        # Verify POST arguments
        call_args = mock_httpx_client.post.call_args
        assert call_args.args[0] == url, "Should POST to correct URL"
        assert call_args.kwargs["json"] == payload, "Should send correct payload"

    @pytest.mark.asyncio
    async def test_send_webhook_retries_on_5xx_error(
        self, webhook_service, mock_httpx_client
    ):
        """
        RED Test: Verify send_webhook() retries on 5xx server error

        Expected:
        - Retries up to max_retries=3 times
        - Uses exponential backoff (2^retry_count seconds)
        - Returns False after max retries
        """
        # Mock 503 Service Unavailable responses
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_httpx_client.post = AsyncMock(return_value=mock_response)

        url = "https://example.com/webhook"
        payload = {"status": "completed"}

        # Patch asyncio.sleep to avoid actual delays
        with patch(
            "apps.api.background.webhook_service.asyncio.sleep", new_callable=AsyncMock
        ) as mock_sleep:
            result = await webhook_service.send_webhook(url, payload)

            assert result is False, "send_webhook should return False after max retries"

            # Verify retried 3 times (total 3 attempts)
            assert (
                mock_httpx_client.post.call_count == 3
            ), f"Should make 3 attempts, got {mock_httpx_client.post.call_count}"

            # Verify exponential backoff delays
            assert (
                mock_sleep.call_count == 2
            ), "Should sleep 2 times (before retry 2 and 3)"

            # Check delay values: 2^0=1, 2^1=2 seconds
            sleep_calls = [call.args[0] for call in mock_sleep.call_args_list]
            assert (
                sleep_calls[0] == 1
            ), f"First delay should be 1s, got {sleep_calls[0]}"
            assert (
                sleep_calls[1] == 2
            ), f"Second delay should be 2s, got {sleep_calls[1]}"

    @pytest.mark.asyncio
    async def test_send_webhook_succeeds_on_third_retry(
        self, webhook_service, mock_httpx_client
    ):
        """
        RED Test: Verify send_webhook() succeeds after retries

        Expected:
        - Returns True when retry succeeds
        - First 2 attempts fail with 500
        - Third attempt succeeds with 200
        """
        # Mock responses: fail, fail, success
        responses = [
            MagicMock(status_code=500),
            MagicMock(status_code=500),
            MagicMock(status_code=200),
        ]
        mock_httpx_client.post = AsyncMock(side_effect=responses)

        url = "https://example.com/webhook"
        payload = {"status": "completed"}

        with patch(
            "apps.api.background.webhook_service.asyncio.sleep", new_callable=AsyncMock
        ):
            result = await webhook_service.send_webhook(url, payload)

            assert result is True, "send_webhook should return True when retry succeeds"
            assert mock_httpx_client.post.call_count == 3, "Should make 3 attempts"

    @pytest.mark.asyncio
    async def test_send_webhook_handles_timeout_exception(
        self, webhook_service, mock_httpx_client
    ):
        """
        RED Test: Verify send_webhook() retries on timeout

        Expected:
        - Catches httpx.TimeoutException
        - Retries with exponential backoff
        - Returns False after max retries
        """
        import httpx

        mock_httpx_client.post = AsyncMock(
            side_effect=httpx.TimeoutException("Request timeout")
        )

        url = "https://example.com/webhook"
        payload = {"status": "completed"}

        with patch(
            "apps.api.background.webhook_service.asyncio.sleep", new_callable=AsyncMock
        ):
            result = await webhook_service.send_webhook(url, payload)

            assert (
                result is False
            ), "send_webhook should return False on repeated timeouts"
            assert mock_httpx_client.post.call_count == 3, "Should retry 3 times"

    @pytest.mark.asyncio
    async def test_send_webhook_includes_content_type_header(
        self, webhook_service, mock_httpx_client
    ):
        """
        RED Test: Verify webhook POST includes Content-Type: application/json header

        Expected:
        - Headers include 'Content-Type': 'application/json'
        """
        url = "https://example.com/webhook"
        payload = {"status": "completed"}

        await webhook_service.send_webhook(url, payload)

        call_args = mock_httpx_client.post.call_args
        headers = call_args.kwargs.get("headers", {})

        assert "Content-Type" in headers, "Should include Content-Type header"
        assert (
            headers["Content-Type"] == "application/json"
        ), "Content-Type should be application/json"

    @pytest.mark.asyncio
    async def test_send_webhook_with_signature_adds_hmac_header(
        self, webhook_service, mock_httpx_client
    ):
        """
        RED Test: Verify send_webhook() adds HMAC signature header when secret provided

        Expected:
        - Includes X-Agent-Signature header
        - Format: sha256={hex_digest}
        """
        url = "https://example.com/webhook"
        payload = {"status": "completed"}
        secret = "test-secret-key"

        await webhook_service.send_webhook(url, payload, secret=secret)

        call_args = mock_httpx_client.post.call_args
        headers = call_args.kwargs.get("headers", {})

        assert (
            "X-Agent-Signature" in headers
        ), "Should include X-Agent-Signature header when secret provided"

        signature = headers["X-Agent-Signature"]
        assert signature.startswith("sha256="), "Signature should start with 'sha256='"
        assert len(signature) > 10, "Signature should contain hash digest"

    @pytest.mark.asyncio
    async def test_send_webhook_respects_timeout_setting(
        self, webhook_service, mock_httpx_client
    ):
        """
        RED Test: Verify WebhookService respects timeout configuration

        Expected:
        - httpx.AsyncClient created with timeout parameter
        - Default timeout=10 seconds
        """
        custom_service = WebhookService(timeout=5, max_retries=2)

        url = "https://example.com/webhook"
        payload = {"status": "completed"}

        with patch(
            "apps.api.background.webhook_service.httpx.AsyncClient"
        ) as MockClient:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=MagicMock(status_code=200))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            MockClient.return_value = mock_client

            await custom_service.send_webhook(url, payload)

            # Verify AsyncClient was created with timeout
            MockClient.assert_called_once()
            call_kwargs = MockClient.call_args.kwargs
            assert "timeout" in call_kwargs, "Should pass timeout to AsyncClient"
            assert (
                call_kwargs["timeout"] == 5
            ), f"Expected timeout=5, got {call_kwargs['timeout']}"

    @pytest.mark.asyncio
    async def test_send_webhook_exponential_backoff_formula(
        self, webhook_service, mock_httpx_client
    ):
        """
        RED Test: Verify exponential backoff uses formula delay = 2^retry_count

        Expected:
        - Retry 1: delay = 2^0 = 1 second
        - Retry 2: delay = 2^1 = 2 seconds
        - Retry 3: delay = 2^2 = 4 seconds
        """
        # Mock all responses as failures
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_httpx_client.post = AsyncMock(return_value=mock_response)

        url = "https://example.com/webhook"
        payload = {"status": "completed"}

        with patch(
            "apps.api.background.webhook_service.asyncio.sleep", new_callable=AsyncMock
        ) as mock_sleep:
            await webhook_service.send_webhook(url, payload)

            # Extract all sleep delays
            sleep_delays = [call.args[0] for call in mock_sleep.call_args_list]

            # Verify exponential backoff: 1s, 2s
            assert (
                len(sleep_delays) == 2
            ), f"Should have 2 delays, got {len(sleep_delays)}"
            assert (
                sleep_delays[0] == 1
            ), f"First delay should be 1s (2^0), got {sleep_delays[0]}"
            assert (
                sleep_delays[1] == 2
            ), f"Second delay should be 2s (2^1), got {sleep_delays[1]}"
