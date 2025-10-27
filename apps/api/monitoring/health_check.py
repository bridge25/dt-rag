"""
시스템 헬스 체크 및 의존성 모니터링
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import aiohttp
import psutil

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """헬스 상태"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ComponentHealth:
    """컴포넌트 헬스 상태"""

    name: str
    status: HealthStatus
    response_time_ms: Optional[float] = None
    last_check: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["status"] = self.status.value
        if self.last_check:
            result["last_check"] = self.last_check.isoformat()
        return result


@dataclass
class SystemHealth:
    """전체 시스템 헬스"""

    overall_status: HealthStatus
    components: List[ComponentHealth]
    timestamp: datetime
    uptime_seconds: float
    version: str = "1.8.1"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_status": self.overall_status.value,
            "components": [comp.to_dict() for comp in self.components],
            "timestamp": self.timestamp.isoformat(),
            "uptime_seconds": self.uptime_seconds,
            "version": self.version,
        }


class HealthChecker:
    """헬스 체크 관리자"""

    def __init__(self):
        self.start_time = datetime.now()
        self.health_checks: Dict[str, Callable] = {}
        self.last_results: Dict[str, ComponentHealth] = {}
        self.check_interval = 30  # 30초 간격
        self.timeout = 5  # 5초 타임아웃

        # 기본 헬스 체크 등록
        self._register_default_checks()

        logger.info("HealthChecker initialized")

    def _register_default_checks(self):
        """기본 헬스 체크 등록"""
        self.register_check("system", self._check_system_health)
        self.register_check("database", self._check_database_health)
        self.register_check("cache", self._check_cache_health)
        self.register_check("storage", self._check_storage_health)

    def register_check(self, name: str, check_function: Callable):
        """헬스 체크 함수 등록"""
        self.health_checks[name] = check_function
        logger.info(f"Health check '{name}' registered")

    async def _check_system_health(self) -> ComponentHealth:
        """시스템 리소스 헬스 체크"""
        try:
            start_time = time.time()

            # CPU 사용률 체크
            cpu_percent = psutil.cpu_percent(interval=0.1)

            # 메모리 사용률 체크
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # 디스크 사용률 체크
            disk = psutil.disk_usage("/")
            disk_percent = disk.percent

            response_time = (time.time() - start_time) * 1000

            # 상태 판단
            if cpu_percent > 90 or memory_percent > 90 or disk_percent > 95:
                status = HealthStatus.UNHEALTHY
                error_msg = f"High resource usage: CPU {cpu_percent}%, Memory {memory_percent}%, Disk {disk_percent}%"
            elif cpu_percent > 70 or memory_percent > 80 or disk_percent > 85:
                status = HealthStatus.DEGRADED
                error_msg = f"Elevated resource usage: CPU {cpu_percent}%, Memory {memory_percent}%, Disk {disk_percent}%"
            else:
                status = HealthStatus.HEALTHY
                error_msg = None

            return ComponentHealth(
                name="system",
                status=status,
                response_time_ms=response_time,
                last_check=datetime.now(),
                error_message=error_msg,
                metadata={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                    "disk_percent": disk_percent,
                    "load_average": (
                        psutil.getloadavg()[0]
                        if hasattr(psutil, "getloadavg")
                        else None
                    ),
                },
            )

        except Exception as e:
            logger.error(f"System health check failed: {e}")
            return ComponentHealth(
                name="system",
                status=HealthStatus.UNHEALTHY,
                last_check=datetime.now(),
                error_message=str(e),
            )

    async def _check_database_health(self) -> ComponentHealth:
        """데이터베이스 헬스 체크"""
        try:
            start_time = time.time()

            # 데이터베이스 연결 체크
            try:
                from apps.api.database import db_manager
                from sqlalchemy import text

                async with db_manager.async_session() as session:
                    # 간단한 쿼리 실행
                    result = await session.execute(text("SELECT 1"))
                    await result.fetchone()

                response_time = (time.time() - start_time) * 1000

                return ComponentHealth(
                    name="database",
                    status=HealthStatus.HEALTHY,
                    response_time_ms=response_time,
                    last_check=datetime.now(),
                    metadata={"connection_test": "passed", "query_test": "passed"},
                )
            except ImportError:
                # 데이터베이스 매니저를 사용할 수 없는 경우
                response_time = (time.time() - start_time) * 1000
                return ComponentHealth(
                    name="database",
                    status=HealthStatus.DEGRADED,
                    response_time_ms=response_time,
                    last_check=datetime.now(),
                    error_message="Database manager not available",
                    metadata={"connection_test": "skipped", "reason": "testing_mode"},
                )

        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return ComponentHealth(
                name="database",
                status=HealthStatus.UNHEALTHY,
                last_check=datetime.now(),
                error_message=str(e),
            )

    async def _check_cache_health(self) -> ComponentHealth:
        """캐시 시스템 헬스 체크"""
        try:
            start_time = time.time()

            # 캐시 연결 체크
            from apps.api.cache.search_cache import get_search_cache

            cache = await get_search_cache()

            # 캐시 통계 확인
            stats = await cache.get_cache_stats()

            response_time = (time.time() - start_time) * 1000

            # 캐시 히트율 기반 상태 판단
            hit_rate = stats.get("hit_rates", {}).get("overall_hit_rate", 0)
            if hit_rate >= 0.7:  # 70% 이상
                status = HealthStatus.HEALTHY
            elif hit_rate >= 0.5:  # 50% 이상
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.DEGRADED

            return ComponentHealth(
                name="cache",
                status=status,
                response_time_ms=response_time,
                last_check=datetime.now(),
                metadata={"hit_rate": hit_rate, "cache_stats": stats},
            )

        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return ComponentHealth(
                name="cache",
                status=HealthStatus.DEGRADED,  # 캐시는 필수가 아니므로 DEGRADED
                last_check=datetime.now(),
                error_message=str(e),
            )

    async def _check_storage_health(self) -> ComponentHealth:
        """스토리지 헬스 체크"""
        try:
            start_time = time.time()

            # 스토리지 디렉토리 체크
            from pathlib import Path

            storage_path = Path("./storage")
            if not storage_path.exists():
                storage_path.mkdir(parents=True)

            # 쓰기 테스트
            test_file = storage_path / "health_check.txt"
            test_file.write_text(f"Health check at {datetime.now()}")

            # 읽기 테스트
            test_file.read_text()

            # 정리
            test_file.unlink()

            response_time = (time.time() - start_time) * 1000

            return ComponentHealth(
                name="storage",
                status=HealthStatus.HEALTHY,
                response_time_ms=response_time,
                last_check=datetime.now(),
                metadata={
                    "write_test": "passed",
                    "read_test": "passed",
                    "storage_path": str(storage_path.absolute()),
                },
            )

        except Exception as e:
            logger.error(f"Storage health check failed: {e}")
            return ComponentHealth(
                name="storage",
                status=HealthStatus.UNHEALTHY,
                last_check=datetime.now(),
                error_message=str(e),
            )

    async def _check_external_service(
        self, name: str, url: str, timeout: int = 5
    ) -> ComponentHealth:
        """외부 서비스 헬스 체크"""
        try:
            start_time = time.time()

            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as session:
                async with session.get(url) as response:
                    status_code = response.status

            response_time = (time.time() - start_time) * 1000

            if 200 <= status_code < 300:
                status = HealthStatus.HEALTHY
                error_msg = None
            elif 400 <= status_code < 500:
                status = HealthStatus.DEGRADED
                error_msg = f"Client error: {status_code}"
            else:
                status = HealthStatus.UNHEALTHY
                error_msg = f"Server error: {status_code}"

            return ComponentHealth(
                name=name,
                status=status,
                response_time_ms=response_time,
                last_check=datetime.now(),
                error_message=error_msg,
                metadata={"url": url, "status_code": status_code},
            )

        except asyncio.TimeoutError:
            logger.warning(f"External service {name} health check timed out")
            return ComponentHealth(
                name=name,
                status=HealthStatus.UNHEALTHY,
                last_check=datetime.now(),
                error_message="Request timeout",
            )
        except Exception as e:
            logger.error(f"External service {name} health check failed: {e}")
            return ComponentHealth(
                name=name,
                status=HealthStatus.UNHEALTHY,
                last_check=datetime.now(),
                error_message=str(e),
            )

    async def check_single_component(self, name: str) -> ComponentHealth:
        """단일 컴포넌트 헬스 체크"""
        if name not in self.health_checks:
            return ComponentHealth(
                name=name,
                status=HealthStatus.UNKNOWN,
                last_check=datetime.now(),
                error_message="Unknown component",
            )

        try:
            result = await asyncio.wait_for(
                self.health_checks[name](), timeout=self.timeout
            )
            self.last_results[name] = result
            return result

        except asyncio.TimeoutError:
            logger.warning(f"Health check for {name} timed out")
            result = ComponentHealth(
                name=name,
                status=HealthStatus.UNHEALTHY,
                last_check=datetime.now(),
                error_message="Health check timeout",
            )
            self.last_results[name] = result
            return result

        except Exception as e:
            logger.error(f"Health check for {name} failed: {e}")
            result = ComponentHealth(
                name=name,
                status=HealthStatus.UNHEALTHY,
                last_check=datetime.now(),
                error_message=str(e),
            )
            self.last_results[name] = result
            return result

    async def check_all_components(self) -> List[ComponentHealth]:
        """모든 컴포넌트 헬스 체크"""
        tasks = [
            self.check_single_component(name) for name in self.health_checks.keys()
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        component_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                name = list(self.health_checks.keys())[i]
                component_results.append(
                    ComponentHealth(
                        name=name,
                        status=HealthStatus.UNHEALTHY,
                        last_check=datetime.now(),
                        error_message=str(result),
                    )
                )
            else:
                component_results.append(result)

        return component_results

    def _calculate_overall_status(
        self, components: List[ComponentHealth]
    ) -> HealthStatus:
        """전체 시스템 상태 계산"""
        if not components:
            return HealthStatus.UNKNOWN

        # 상태별 가중치
        status_weights = {
            HealthStatus.HEALTHY: 1.0,
            HealthStatus.DEGRADED: 0.5,
            HealthStatus.UNHEALTHY: 0.0,
            HealthStatus.UNKNOWN: 0.0,
        }

        # 컴포넌트별 중요도 (필수 컴포넌트는 높은 가중치)
        component_importance = {
            "system": 1.0,
            "database": 1.0,  # 필수
            "cache": 0.5,  # 선택적
            "storage": 0.8,  # 중요하지만 필수는 아님
        }

        total_weight = 0
        weighted_score = 0

        for component in components:
            importance = component_importance.get(component.name, 0.5)
            status_weight = status_weights.get(component.status, 0.0)

            total_weight += importance
            weighted_score += importance * status_weight

        if total_weight == 0:
            return HealthStatus.UNKNOWN

        average_score = weighted_score / total_weight

        # 점수에 따른 상태 결정
        if average_score >= 0.8:
            return HealthStatus.HEALTHY
        elif average_score >= 0.5:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.UNHEALTHY

    async def get_system_health(self) -> SystemHealth:
        """전체 시스템 헬스 조회"""
        components = await self.check_all_components()
        overall_status = self._calculate_overall_status(components)
        uptime = (datetime.now() - self.start_time).total_seconds()

        return SystemHealth(
            overall_status=overall_status,
            components=components,
            timestamp=datetime.now(),
            uptime_seconds=uptime,
        )

    def get_cached_health(self) -> Dict[str, Any]:
        """캐시된 헬스 정보 조회 (빠른 응답용)"""
        if not self.last_results:
            return {
                "overall_status": HealthStatus.UNKNOWN.value,
                "components": [],
                "last_check": None,
                "message": "No health checks performed yet",
            }

        components = list(self.last_results.values())
        overall_status = self._calculate_overall_status(components)

        return {
            "overall_status": overall_status.value,
            "components": [comp.to_dict() for comp in components],
            "last_check": max(
                comp.last_check for comp in components if comp.last_check
            ).isoformat(),
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
        }

    async def start_background_monitoring(self):
        """백그라운드 헬스 모니터링 시작"""
        logger.info("Starting background health monitoring")

        while True:
            try:
                await self.check_all_components()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Background health monitoring error: {e}")
                await asyncio.sleep(self.check_interval)


# 전역 헬스 체커 인스턴스
_health_checker: Optional[HealthChecker] = None


def get_health_checker() -> HealthChecker:
    """전역 헬스 체커 조회"""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker


def initialize_health_checker() -> HealthChecker:
    """헬스 체커 초기화"""
    global _health_checker
    _health_checker = HealthChecker()
    return _health_checker
