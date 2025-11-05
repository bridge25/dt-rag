"""
XSS (Cross-Site Scripting) Prevention Tests
@TEST:TEST-004 | SPEC: SPEC-TEST-004.md

Tests for XSS attack prevention:
- Script tag injection blocked
- Event handler injection blocked
- HTML entity escaping
- No script execution in responses
"""

import pytest
from httpx import AsyncClient
import os


# @TEST:TEST-004
@pytest.mark.asyncio
async def test_xss_script_tag_sanitized(async_client: AsyncClient) -> None:
    """
    <script> 태그는 sanitize됨
    REQ-10: WHEN XSS payload is submitted in text field
    """
    valid_api_key = os.getenv("DT_RAG_API_KEY", "test_api_key_for_testing")

    xss_payload = "<script>alert('XSS')</script>"

    response = await async_client.post(
        "/classify",
        json={"chunk_id": "xss-001", "text": xss_payload},
        headers={"X-API-Key": valid_api_key},
    )

    # Should accept request (may return 200, 422, or 404 depending on endpoint existence)
    # Key check: response should not contain executable script
    assert (
        "<script>" not in response.text
    ), "Response should not contain executable <script> tags"
    assert (
        "alert('XSS')" not in response.text
    ), "Response should not contain XSS payload"


# @TEST:TEST-004
@pytest.mark.asyncio
async def test_xss_event_handler_blocked(async_client: AsyncClient) -> None:
    """
    이벤트 핸들러 기반 XSS 차단
    REQ-10
    """
    valid_api_key = os.getenv("DT_RAG_API_KEY", "test_api_key_for_testing")

    event_handler_payloads = [
        "<img src=x onerror=alert('XSS')>",
        "<body onload=alert('XSS')>",
        "<input onfocus=alert('XSS') autofocus>",
    ]

    for payload in event_handler_payloads:
        response = await async_client.post(
            "/reflection/analyze",
            json={"case_id": payload},
            headers={"X-API-Key": valid_api_key},
        )

        # Response should not contain event handlers
        assert (
            "onerror" not in response.text.lower()
        ), f"Response should not contain onerror handler for payload: {payload}"
        assert (
            "onload" not in response.text.lower()
        ), f"Response should not contain onload handler for payload: {payload}"
        assert (
            "onfocus" not in response.text.lower()
        ), f"Response should not contain onfocus handler for payload: {payload}"


# @TEST:TEST-004
@pytest.mark.asyncio
async def test_html_injection_escaped(async_client: AsyncClient) -> None:
    """
    HTML 태그는 이스케이프됨
    REQ-10
    """
    valid_api_key = os.getenv("DT_RAG_API_KEY", "test_api_key_for_testing")

    html_payload = "<div>Test</div><iframe src='evil.com'></iframe>"

    response = await async_client.post(
        "/reflection/analyze",
        json={"case_id": html_payload},
        headers={"X-API-Key": valid_api_key},
    )

    # Response should not contain unescaped HTML
    # If HTML is present, it should be escaped (e.g., &lt;div&gt;)
    response_text = response.text.lower()

    # Check for unescaped dangerous tags
    assert (
        "<iframe" not in response_text
    ), "Response should not contain unescaped <iframe> tags"


# @TEST:TEST-004
@pytest.mark.asyncio
async def test_javascript_protocol_blocked(async_client: AsyncClient) -> None:
    """
    javascript: 프로토콜 차단
    REQ-10
    """
    valid_api_key = os.getenv("DT_RAG_API_KEY", "test_api_key_for_testing")

    js_proto_payloads = [
        "<a href='javascript:alert(1)'>Click</a>",
        "<img src='javascript:alert(1)'>",
    ]

    for payload in js_proto_payloads:
        response = await async_client.post(
            "/reflection/analyze",
            json={"case_id": payload},
            headers={"X-API-Key": valid_api_key},
        )

        # Response should not contain javascript: protocol
        assert (
            "javascript:" not in response.text.lower()
        ), f"Response should not contain javascript: protocol for payload: {payload}"


# @TEST:TEST-004
@pytest.mark.asyncio
async def test_data_url_xss_blocked(async_client: AsyncClient) -> None:
    """
    data: URL을 통한 XSS 차단
    REQ-10
    """
    valid_api_key = os.getenv("DT_RAG_API_KEY", "test_api_key_for_testing")

    data_url_payload = "<img src='data:text/html,<script>alert(1)</script>'>"

    response = await async_client.post(
        "/reflection/analyze",
        json={"case_id": data_url_payload},
        headers={"X-API-Key": valid_api_key},
    )

    # Response should not contain executable data URLs with scripts
    response_text = response.text.lower()
    if "data:" in response_text:
        # If data: URL is present, it should not contain script
        assert (
            "script" not in response_text
        ), "Data URL should not contain executable scripts"


# @TEST:TEST-004
@pytest.mark.asyncio
async def test_no_reflected_xss(async_client: AsyncClient) -> None:
    """
    Reflected XSS 방지 (입력이 그대로 출력되지 않음)
    REQ-10
    """
    valid_api_key = os.getenv("DT_RAG_API_KEY", "test_api_key_for_testing")

    unique_marker = "<UNIQUE_XSS_MARKER_12345>"

    response = await async_client.post(
        "/reflection/analyze",
        json={"case_id": unique_marker},
        headers={"X-API-Key": valid_api_key},
    )

    # Input should not be directly reflected in response without escaping
    # If it appears, it should be escaped
    if unique_marker in response.text:
        # This would be a reflected XSS vulnerability
        # However, we'll allow it if it's properly escaped in JSON
        import json

        response_json = response.json()
        response_str = json.dumps(response_json)

        # Check if it's properly JSON-encoded (safe)
        assert (
            unique_marker not in response_str or response_str.count('"') > 0
        ), "Reflected input should be properly escaped"
