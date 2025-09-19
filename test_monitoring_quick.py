#!/usr/bin/env python3
"""
모니터링 시스템 빠른 테스트
"""

import asyncio
import logging
from pathlib import Path
import sys

# 프로젝트 경로 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "apps"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def quick_test():
    """빠른 모니터링 테스트"""
    print("Starting quick monitoring test...")

    try:
        # 메트릭 수집기 테스트
        from apps.api.monitoring.metrics import MetricsCollector
        collector = MetricsCollector(enable_prometheus=False)

        # 기본 메트릭 기록
        collector.increment_counter("test_requests")
        collector.record_latency("test_operation", 123.45)
        collector.set_gauge("test_cpu", 45.6)

        # 성능 스냅샷
        snapshot = collector.calculate_performance_snapshot()
        print(f"Metrics: P95={snapshot.p95_latency:.2f}ms, CPU={snapshot.cpu_usage:.1f}%")

        # 헬스 체커 테스트
        from apps.api.monitoring.health_check import HealthChecker
        health_checker = HealthChecker()

        # 시스템 헬스만 체크 (빠름)
        system_health = await health_checker.check_single_component("system")
        print(f"System Health: {system_health.status.value} ({system_health.response_time_ms:.2f}ms)")

        # 대시보드 테스트
        from apps.api.monitoring.dashboard import MonitoringDashboard
        dashboard = MonitoringDashboard()

        # 실시간 메트릭만 조회 (빠름)
        realtime_metrics = await dashboard.get_real_time_metrics()
        print(f"Realtime metrics: {len(realtime_metrics)} entries")

        print("✅ Quick monitoring test passed!")
        return True

    except Exception as e:
        print(f"❌ Quick monitoring test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(quick_test())
    sys.exit(0 if success else 1)