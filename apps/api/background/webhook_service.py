"""
@CODE:AGENT-GROWTH-004:SERVICE - WebhookService

Webhook delivery service with retry logic and exponential backoff.
Supports HMAC signature authentication.
"""

import asyncio
import hashlib
import hmac
import json
import logging
from typing import Dict, Any, Optional
import httpx

logger = logging.getLogger(__name__)


class WebhookService:
    """
    Webhook delivery service with retry and exponential backoff

    Features:
    - Configurable timeout and max retries
    - Exponential backoff: delay = 2^retry_count seconds
    - HMAC-SHA256 signature support (X-Agent-Signature header)
    - Retry on 5xx errors and timeout exceptions
    - Fire-and-forget: returns bool status without raising exceptions
    """

    def __init__(self, timeout: int = 10, max_retries: int = 3):
        """
        Initialize WebhookService

        Args:
            timeout: HTTP request timeout in seconds (default: 10)
            max_retries: Maximum retry attempts on failure (default: 3)
        """
        self.timeout = timeout
        self.max_retries = max_retries
        logger.info(f"WebhookService initialized: timeout={timeout}s, max_retries={max_retries}")

    async def send_webhook(
        self,
        url: str,
        payload: Dict[str, Any],
        secret: Optional[str] = None
    ) -> bool:
        """
        Send webhook POST request with retry logic

        Args:
            url: Webhook URL
            payload: JSON payload dictionary
            secret: Optional HMAC secret for signature

        Returns:
            True if delivery succeeded (200-299 status), False otherwise
        """
        headers = {
            "Content-Type": "application/json"
        }

        if secret:
            signature = self._generate_signature(payload, secret)
            headers["X-Agent-Signature"] = signature

        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(url, json=payload, headers=headers)

                    if 200 <= response.status_code < 300:
                        logger.info(
                            f"Webhook delivered successfully: url={url}, "
                            f"status={response.status_code}, attempt={attempt + 1}"
                        )
                        return True

                    if response.status_code >= 500:
                        logger.warning(
                            f"Webhook 5xx error: url={url}, "
                            f"status={response.status_code}, attempt={attempt + 1}/{self.max_retries}"
                        )

                        if attempt < self.max_retries - 1:
                            await self._backoff(attempt)
                            continue
                        else:
                            logger.error(
                                f"Webhook max retries exhausted: url={url}, "
                                f"status={response.status_code}"
                            )
                            return False

                    logger.warning(
                        f"Webhook non-retryable error: url={url}, "
                        f"status={response.status_code}"
                    )
                    return False

            except httpx.TimeoutException as e:
                logger.warning(
                    f"Webhook timeout: url={url}, attempt={attempt + 1}/{self.max_retries}, error={e}"
                )

                if attempt < self.max_retries - 1:
                    await self._backoff(attempt)
                else:
                    logger.error(f"Webhook timeout - max retries exhausted: url={url}")
                    return False

            except Exception as e:
                logger.error(
                    f"Webhook unexpected error: url={url}, attempt={attempt + 1}, error={e}"
                )
                return False

        return False

    def _generate_signature(self, payload: Dict[str, Any], secret: str) -> str:
        """
        Generate HMAC-SHA256 signature for webhook payload

        Args:
            payload: JSON payload dictionary
            secret: HMAC secret key

        Returns:
            Signature string in format "sha256={hex_digest}"
        """
        payload_bytes = json.dumps(payload, sort_keys=True).encode('utf-8')
        secret_bytes = secret.encode('utf-8')

        signature = hmac.new(secret_bytes, payload_bytes, hashlib.sha256).hexdigest()

        return f"sha256={signature}"

    async def _backoff(self, retry_count: int):
        """
        Exponential backoff delay

        Args:
            retry_count: Current retry attempt (0-indexed)

        Delay formula: 2^retry_count seconds (1s, 2s, 4s, 8s, ...)
        """
        delay = 2 ** retry_count
        logger.debug(f"Webhook backoff: retry={retry_count}, delay={delay}s")
        await asyncio.sleep(delay)
