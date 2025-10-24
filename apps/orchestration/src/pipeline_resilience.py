"""
B-O3: 재시도 로직 및 메모리 모니터링 시스템
파이프라인 안정성과 복원력 강화
"""

import asyncio
import gc
import logging
import os
import time
import tracemalloc
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Optional

import psutil

logger = logging.getLogger(__name__)


@dataclass
class RetryConfig:
    """재시도 설정"""

    max_attempts: int = 3
    base_delay: float = 1.0  # 초기 지연 시간 (초)
    max_delay: float = 60.0  # 최대 지연 시간 (초)
    exponential_base: float = 2.0  # 지수 백오프 계수
    jitter: bool = True  # 랜덤 지연 추가 여부


@dataclass
class MemoryThreshold:
    """메모리 임계값 설정"""

    warning_mb: float = 1024.0  # 1GB 경고
    critical_mb: float = 2048.0  # 2GB 크리티컬
    max_mb: float = 4096.0  # 4GB 최대


class PipelineRetryHandler:
    """파이프라인 재시도 처리기"""

    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()

    async def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """재시도 로직으로 함수 실행"""
        last_exception = None

        for attempt in range(1, self.config.max_attempts + 1):
            try:
                logger.info(f"시도 {attempt}/{self.config.max_attempts}")

                # 함수 실행
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                logger.info(f"시도 {attempt} 성공")
                return result

            except Exception as e:
                last_exception = e
                logger.warning(f"시도 {attempt} 실패: {str(e)}")

                # 마지막 시도였다면 예외 발생
                if attempt == self.config.max_attempts:
                    logger.error(f"모든 재시도 실패. 최종 오류: {str(e)}")
                    break

                # 지연 시간 계산 (Exponential Backoff with Jitter)
                delay = min(
                    self.config.base_delay
                    * (self.config.exponential_base ** (attempt - 1)),
                    self.config.max_delay,
                )

                # Jitter 추가 (랜덤성으로 thundering herd 방지)
                if self.config.jitter:
                    import random

                    delay *= 0.5 + random.random() * 0.5

                logger.info(f"재시도 대기: {delay:.2f}초")
                await asyncio.sleep(delay)

        # 모든 재시도 실패 시 마지막 예외 발생
        raise last_exception


class MemoryMonitor:
    """메모리 모니터링 시스템"""

    def __init__(self, thresholds: Optional[MemoryThreshold] = None):
        self.thresholds = thresholds or MemoryThreshold()
        self.process = psutil.Process(os.getpid())
        self.peak_memory = 0.0
        self.monitoring_active = False

    def get_memory_usage(self) -> Dict[str, float]:
        """현재 메모리 사용량 조회 (MB)"""
        memory_info = self.process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024

        # 피크 메모리 업데이트
        if memory_mb > self.peak_memory:
            self.peak_memory = memory_mb

        return {
            "current_mb": memory_mb,
            "peak_mb": self.peak_memory,
            "available_mb": psutil.virtual_memory().available / 1024 / 1024,
            "percent": self.process.memory_percent(),
        }

    def check_memory_health(self) -> Dict[str, Any]:
        """메모리 건강도 체크"""
        usage = self.get_memory_usage()
        current_mb = usage["current_mb"]

        health_status = "healthy"
        warnings = []
        actions_needed = []

        if current_mb >= self.thresholds.critical_mb:
            health_status = "critical"
            warnings.append(
                f"메모리 사용량이 크리티컬 레벨({self.thresholds.critical_mb:.0f}MB)을 초과했습니다"
            )
            actions_needed.extend(["즉시 가비지 컬렉션", "메모리 집약적 작업 중단"])

        elif current_mb >= self.thresholds.warning_mb:
            health_status = "warning"
            warnings.append(
                f"메모리 사용량이 경고 레벨({self.thresholds.warning_mb:.0f}MB)을 초과했습니다"
            )
            actions_needed.append("가비지 컬렉션 실행")

        if current_mb >= self.thresholds.max_mb:
            health_status = "emergency"
            warnings.append(
                f"메모리 사용량이 최대 허용치({self.thresholds.max_mb:.0f}MB)를 초과했습니다"
            )
            actions_needed.extend(["긴급 메모리 정리", "프로세스 재시작 검토"])

        return {
            "status": health_status,
            "usage": usage,
            "warnings": warnings,
            "actions_needed": actions_needed,
            "thresholds": {
                "warning": self.thresholds.warning_mb,
                "critical": self.thresholds.critical_mb,
                "max": self.thresholds.max_mb,
            },
        }

    async def cleanup_memory(self, force: bool = False) -> Dict[str, Any]:
        """메모리 정리 수행"""
        logger.info("메모리 정리 시작")

        before_usage = self.get_memory_usage()

        # 가비지 컬렉션 실행
        collected = gc.collect()

        # 강제 정리인 경우 추가 작업
        if force:
            # 모든 세대의 가비지 컬렉션
            for generation in range(3):
                gc.collect(generation)

            # 메모리 조각 모음 시도
            try:
                import ctypes

                libc = ctypes.CDLL("libc.so.6")
                libc.malloc_trim(0)
            except Exception as e:
                logger.debug(f"malloc_trim 실행 실패 (무시): {e}")

        # 정리 후 상태 확인
        after_usage = self.get_memory_usage()
        freed_mb = before_usage["current_mb"] - after_usage["current_mb"]

        result = {
            "collected_objects": collected,
            "memory_freed_mb": freed_mb,
            "before_usage": before_usage,
            "after_usage": after_usage,
            "force_cleanup": force,
        }

        logger.info(f"메모리 정리 완료: {freed_mb:.1f}MB 확보, {collected}개 객체 수집")
        return result

    async def start_monitoring(self, interval: float = 30.0):
        """메모리 모니터링 시작 (백그라운드)"""
        if self.monitoring_active:
            logger.warning("메모리 모니터링이 이미 활성화되어 있습니다")
            return

        self.monitoring_active = True
        logger.info(f"메모리 모니터링 시작 (간격: {interval}초)")

        try:
            while self.monitoring_active:
                health = self.check_memory_health()

                if health["status"] == "critical":
                    logger.critical(
                        f"메모리 크리티컬: {health['usage']['current_mb']:.1f}MB"
                    )
                    await self.cleanup_memory(force=True)

                elif health["status"] == "warning":
                    logger.warning(
                        f"메모리 경고: {health['usage']['current_mb']:.1f}MB"
                    )
                    await self.cleanup_memory()

                elif health["status"] == "emergency":
                    logger.emergency(
                        f"메모리 응급상황: {health['usage']['current_mb']:.1f}MB"
                    )
                    await self.cleanup_memory(force=True)
                    # 필요시 추가 응급 조치

                await asyncio.sleep(interval)

        except asyncio.CancelledError:
            logger.info("메모리 모니터링 중단됨")
        except Exception as e:
            logger.error(f"메모리 모니터링 오류: {e}")
        finally:
            self.monitoring_active = False

    def stop_monitoring(self):
        """메모리 모니터링 중단"""
        self.monitoring_active = False


class PipelineResilienceManager:
    """파이프라인 복원력 통합 관리자"""

    def __init__(
        self,
        retry_config: Optional[RetryConfig] = None,
        memory_thresholds: Optional[MemoryThreshold] = None,
    ):
        self.retry_handler = PipelineRetryHandler(retry_config)
        self.memory_monitor = MemoryMonitor(memory_thresholds)
        self.monitoring_task: Optional[asyncio.Task] = None

    async def start(self):
        """복원력 시스템 시작"""
        logger.info("파이프라인 복원력 시스템 시작")

        # 메모리 모니터링 시작
        self.monitoring_task = asyncio.create_task(
            self.memory_monitor.start_monitoring(interval=30.0)
        )

    async def stop(self):
        """복원력 시스템 중단"""
        logger.info("파이프라인 복원력 시스템 중단")

        # 메모리 모니터링 중단
        self.memory_monitor.stop_monitoring()
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass

    async def execute_with_resilience(self, func: Callable, *args, **kwargs) -> Any:
        """복원력 기능을 적용하여 함수 실행"""

        # 실행 전 메모리 상태 확인
        health_before = self.memory_monitor.check_memory_health()
        if health_before["status"] in ["critical", "emergency"]:
            logger.warning("실행 전 메모리 정리 수행")
            await self.memory_monitor.cleanup_memory(force=True)

        # 재시도 로직으로 실행
        try:
            result = await self.retry_handler.execute_with_retry(func, *args, **kwargs)

            # 실행 후 메모리 상태 확인
            health_after = self.memory_monitor.check_memory_health()
            if health_after["status"] == "warning":
                await self.memory_monitor.cleanup_memory()

            return result

        except Exception as e:
            # 실행 실패 후 메모리 정리
            await self.memory_monitor.cleanup_memory()
            raise

    def get_system_health(self) -> Dict[str, Any]:
        """전체 시스템 건강도 조회"""
        memory_health = self.memory_monitor.check_memory_health()

        return {
            "timestamp": datetime.now().isoformat(),
            "memory": memory_health,
            "retry_config": {
                "max_attempts": self.retry_handler.config.max_attempts,
                "base_delay": self.retry_handler.config.base_delay,
                "max_delay": self.retry_handler.config.max_delay,
            },
            "monitoring_active": self.memory_monitor.monitoring_active,
            "overall_status": memory_health["status"],
        }


# 전역 복원력 관리자 (싱글톤)
_global_resilience_manager: Optional[PipelineResilienceManager] = None


def get_resilience_manager() -> PipelineResilienceManager:
    """전역 복원력 관리자 조회/생성"""
    global _global_resilience_manager
    if _global_resilience_manager is None:
        _global_resilience_manager = PipelineResilienceManager()
    return _global_resilience_manager


# 데코레이터 함수들
def with_retry(retry_config: Optional[RetryConfig] = None):
    """재시도 데코레이터"""

    def decorator(func):
        handler = PipelineRetryHandler(retry_config)

        async def wrapper(*args, **kwargs):
            return await handler.execute_with_retry(func, *args, **kwargs)

        return wrapper

    return decorator


def with_memory_monitoring(thresholds: Optional[MemoryThreshold] = None):
    """메모리 모니터링 데코레이터"""

    def decorator(func):
        monitor = MemoryMonitor(thresholds)

        async def wrapper(*args, **kwargs):
            # 실행 전 메모리 체크
            health_before = monitor.check_memory_health()
            if health_before["status"] in ["critical", "emergency"]:
                await monitor.cleanup_memory(force=True)

            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                # 실행 후 메모리 정리
                health_after = monitor.check_memory_health()
                if health_after["status"] == "warning":
                    await monitor.cleanup_memory()

        return wrapper

    return decorator


# 테스트용 함수
async def test_resilience_system():
    """복원력 시스템 테스트"""
    manager = get_resilience_manager()
    await manager.start()

    try:
        # 시스템 상태 출력
        health = manager.get_system_health()
        print(f"시스템 건강도: {health['overall_status']}")
        print(f"메모리 사용량: {health['memory']['usage']['current_mb']:.1f}MB")

        # 테스트 함수 실행
        async def test_function():
            await asyncio.sleep(1)
            return "테스트 성공"

        result = await manager.execute_with_resilience(test_function)
        print(f"테스트 결과: {result}")

    finally:
        await manager.stop()


if __name__ == "__main__":
    asyncio.run(test_resilience_system())
