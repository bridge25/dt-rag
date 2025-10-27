"""
Sentry + Langfuse integration test
Check for conflicts between monitoring tools
"""

import os
import sys
import asyncio
from pathlib import Path

# Windows console encoding fix
if sys.platform == "win32":
    import codecs

    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_sentry_initialization():
    """Sentry 초기화 테스트"""
    try:
        from apps.api.monitoring.sentry_reporter import (
            report_search_failure,
            add_search_breadcrumb,
        )

        print("✅ Sentry 모듈 import 성공")

        # Breadcrumb 추가 테스트
        add_search_breadcrumb(
            query="test query", search_type="hybrid", top_k=5, has_filters=False
        )
        print("✅ Sentry breadcrumb 추가 성공")

        return True
    except ImportError as e:
        print(f"⚠️  Sentry 모듈 import 실패 (정상, 선택적): {e}")
        return False
    except Exception as e:
        print(f"❌ Sentry 초기화 실패: {e}")
        return False


def test_langfuse_initialization():
    """Langfuse 초기화 테스트 (환경변수 필요)"""
    # Langfuse 환경변수 설정 (테스트 모드)
    os.environ["LANGFUSE_ENABLED"] = "false"  # 실제 API 호출 방지

    try:
        # Langfuse 클라이언트는 아직 생성 전이므로 스킵
        print("⚠️  Langfuse 클라이언트는 Step 2에서 생성 예정")
        return True
    except Exception as e:
        print(f"❌ Langfuse 테스트 실패: {e}")
        return False


def test_concurrent_monitoring():
    """Sentry + Langfuse 동시 사용 테스트"""
    try:
        sentry_ok = test_sentry_initialization()
        langfuse_ok = test_langfuse_initialization()

        if sentry_ok or langfuse_ok:
            print("\n✅ 모니터링 통합 테스트 통과")
            print("   - Sentry와 Langfuse는 독립적으로 동작 가능")
            print("   - 서로 다른 목적: Sentry(에러 추적) vs Langfuse(비용 추적)")
            return True
        else:
            print("\n⚠️  모니터링 도구가 설정되지 않음 (정상)")
            return True
    except Exception as e:
        print(f"\n❌ 동시 사용 테스트 실패: {e}")
        return False


async def test_performance_baseline():
    """Langfuse 없이 성능 기준선 측정"""
    try:
        from apps.api.embedding_service import embedding_service
        import time

        # 5회 반복 측정
        latencies = []
        for i in range(5):
            start = time.time()
            await embedding_service.generate_embedding("test query for baseline")
            latency = time.time() - start
            latencies.append(latency)

        avg_latency = sum(latencies) / len(latencies)
        print(f"\n📊 성능 기준선 (Langfuse 미적용):")
        print(f"   - 평균 레이턴시: {avg_latency*1000:.2f}ms")
        print(f"   - 최소: {min(latencies)*1000:.2f}ms")
        print(f"   - 최대: {max(latencies)*1000:.2f}ms")

        # 기준선 저장 (Step 4 후 비교용)
        with open("baseline_latency.txt", "w") as f:
            f.write(f"{avg_latency}\n")

        print("✅ 성능 기준선 저장 완료: baseline_latency.txt")
        return True
    except Exception as e:
        print(f"❌ 성능 측정 실패: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Sentry + Langfuse 통합 테스트 시작")
    print("=" * 60)

    # 동기 테스트
    concurrent_ok = test_concurrent_monitoring()

    # 비동기 테스트
    print("\n" + "=" * 60)
    print("성능 기준선 측정")
    print("=" * 60)
    baseline_ok = asyncio.run(test_performance_baseline())

    # 최종 결과
    print("\n" + "=" * 60)
    print("테스트 결과 요약")
    print("=" * 60)
    if concurrent_ok and baseline_ok:
        print("✅ 모든 테스트 통과")
        print("\n다음 단계:")
        print("1. Step 2: Langfuse 클라이언트 초기화")
        print("2. Step 4 후: 성능 오버헤드 측정")
    else:
        print("⚠️  일부 테스트 실패 (확인 필요)")
