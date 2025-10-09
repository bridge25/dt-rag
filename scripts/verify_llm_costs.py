"""
LLM Cost Verification Script
Compares Langfuse tracked costs vs manual calculation

Usage:
    python scripts/verify_llm_costs.py
"""
import os
import sys
import asyncio
from pathlib import Path
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from apps.api.monitoring.langfuse_client import (
    get_langfuse_client,
    get_langfuse_status,
    calculate_cost,
    MODEL_COSTS
)


async def verify_costs() -> Dict[str, Any]:
    """
    Verify Langfuse cost tracking accuracy

    Returns:
        Verification result with comparison metrics
    """
    print("=" * 70)
    print("LLM Cost Verification")
    print("=" * 70)

    # Check Langfuse status
    status = get_langfuse_status()
    print(f"\nLangfuse Status:")
    print(f"  Available: {status.get('available')}")
    print(f"  Enabled: {status.get('enabled')}")
    print(f"  Configured: {status.get('configured')}")
    print(f"  Client Initialized: {status.get('client_initialized')}")

    if not status.get('available'):
        print("\n❌ Langfuse not available. Install: pip install langfuse>=3.6.0")
        return {"status": "unavailable"}

    if not status.get('enabled'):
        print("\n⚠️  Langfuse disabled. Set LANGFUSE_ENABLED=true")
        return {"status": "disabled"}

    if not status.get('configured'):
        print("\n⚠️  Langfuse not configured. Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY")
        return {"status": "not_configured"}

    try:
        client = get_langfuse_client()
        if not client:
            print("\n❌ Langfuse client initialization failed")
            return {"status": "client_error"}

        print(f"\n✅ Langfuse client ready: {status.get('host')}")

        # Get traces (Note: Actual API depends on Langfuse SDK version)
        print("\nFetching traces from Langfuse...")
        # traces = client.get_traces(limit=1000)  # Uncomment when Langfuse is configured
        traces = []  # Placeholder

        if not traces:
            print("⚠️  No traces found. Run some queries first.")
            return {
                "status": "no_data",
                "message": "No LLM usage data available for verification"
            }

        print(f"Found {len(traces)} traces")

        # Manual cost calculation
        print("\n" + "=" * 70)
        print("Manual Cost Calculation")
        print("=" * 70)

        gemini_manual_cost = 0.0
        embedding_manual_cost = 0.0
        langfuse_total_cost = 0.0

        for trace in traces:
            model_name = getattr(trace, "model", "unknown").lower()
            input_tokens = getattr(trace, "input_tokens", 0)
            output_tokens = getattr(trace, "output_tokens", 0)
            langfuse_cost = getattr(trace, "calculated_total_cost", 0.0)

            langfuse_total_cost += langfuse_cost

            # Manual calculation
            if "gemini" in model_name:
                cost_info = calculate_cost("gemini-2.5-flash-latest", input_tokens, output_tokens)
                gemini_manual_cost += cost_info["cost_usd"]
                print(f"  Gemini: {input_tokens} in + {output_tokens} out = ${cost_info['cost_usd']:.6f}")
            elif "embedding" in model_name:
                cost_info = calculate_cost("text-embedding-3-large", input_tokens, 0)
                embedding_manual_cost += cost_info["cost_usd"]
                print(f"  Embedding: {input_tokens} tokens = ${cost_info['cost_usd']:.6f}")

        manual_total_cost = gemini_manual_cost + embedding_manual_cost

        # Comparison
        print("\n" + "=" * 70)
        print("Cost Comparison")
        print("=" * 70)

        print(f"\nLangfuse Tracked Cost: ${langfuse_total_cost:.6f}")
        print(f"Manual Calculation:    ${manual_total_cost:.6f}")

        diff_usd = abs(langfuse_total_cost - manual_total_cost)
        diff_percent = (diff_usd / manual_total_cost * 100) if manual_total_cost > 0 else 0

        print(f"\nDifference: ${diff_usd:.6f} ({diff_percent:.2f}%)")

        # Validation
        ACCEPTABLE_ERROR_PERCENT = 5.0

        if diff_percent <= ACCEPTABLE_ERROR_PERCENT:
            print(f"\n✅ PASS: Cost verification within {ACCEPTABLE_ERROR_PERCENT}% tolerance")
            result_status = "pass"
        else:
            print(f"\n❌ FAIL: Cost verification exceeds {ACCEPTABLE_ERROR_PERCENT}% tolerance")
            result_status = "fail"

        # Exchange rate conversion
        exchange_rate = float(os.getenv("USD_TO_KRW", "1300"))
        print(f"\n" + "=" * 70)
        print(f"Cost in KRW (Exchange Rate: ₩{exchange_rate}/USD)")
        print("=" * 70)
        print(f"Langfuse: ₩{langfuse_total_cost * exchange_rate:.2f}")
        print(f"Manual:   ₩{manual_total_cost * exchange_rate:.2f}")

        # Per-query cost
        if len(traces) > 0:
            avg_cost_krw = (manual_total_cost / len(traces)) * exchange_rate
            print(f"\nAverage cost per query: ₩{avg_cost_krw:.2f}")
            print(f"Target budget: ₩10.00")
            print(f"Budget utilization: {(avg_cost_krw / 10.0) * 100:.1f}%")

        return {
            "status": result_status,
            "langfuse_cost_usd": langfuse_total_cost,
            "manual_cost_usd": manual_total_cost,
            "difference_usd": diff_usd,
            "difference_percent": diff_percent,
            "acceptable_error_percent": ACCEPTABLE_ERROR_PERCENT,
            "total_traces": len(traces),
            "exchange_rate": exchange_rate
        }

    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "error": str(e)}


async def main():
    """Main entry point"""
    result = await verify_costs()

    print("\n" + "=" * 70)
    print("Verification Result")
    print("=" * 70)
    print(f"Status: {result.get('status')}")

    if result.get('status') == 'pass':
        print("✅ LLM cost tracking is accurate")
    elif result.get('status') == 'fail':
        print("❌ LLM cost tracking has significant discrepancies")
        print("   Please check Langfuse configuration and pricing data")
    else:
        print(f"⚠️  Verification could not be completed: {result.get('status')}")

    return result


if __name__ == "__main__":
    asyncio.run(main())
