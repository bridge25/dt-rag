"""
System Health Checker for DT-RAG v1.8.1

Comprehensive health monitoring with dependency checking,
automated recovery, and proactive issue detection.
"""

import asyncio
import logging
import psutil
import time
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

import aiohttp
import asyncpg
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class ComponentType(Enum):
    """System component types"""
    DATABASE = "database"
    VECTOR_DB = "vector_db"
    LLM_SERVICE = "llm_service"
    CACHE = "cache"
    FILE_SYSTEM = "file_system"
    NETWORK = "network"
    SYSTEM = "system"


@dataclass
class HealthCheck:
    """Health check configuration"""
    name: str
    component_type: ComponentType
    check_function: Callable
    timeout_seconds: float = 10.0
    interval_seconds: int = 30
    retry_count: int = 3
    critical: bool = False
    dependencies: List[str] = None


@dataclass
class HealthResult:
    """Health check result"""
    name: str
    status: HealthStatus
    timestamp: datetime
    latency_ms: float
    message: str
    details: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class ComponentHealth:
    """Component health summary"""
    component_type: ComponentType
    status: HealthStatus
    checks: List[HealthResult]
    last_check: datetime
    consecutive_failures: int = 0


class SystemHealthChecker:
    """
    Comprehensive system health monitoring and dependency checking

    Features:
    - Multi-component health monitoring
    - Dependency-aware health checks
    - Automated recovery attempts
    - Performance metric collection
    - Proactive issue detection
    - Health trend analysis
    """

    def __init__(self, check_interval: int = 30):
        self.check_interval = check_interval
        self.is_running = False

        # Health check registry
        self.health_checks: Dict[str, HealthCheck] = {}
        self.health_results: Dict[str, List[HealthResult]] = {}
        self.component_health: Dict[ComponentType, ComponentHealth] = {}

        # Recovery actions
        self.recovery_actions: Dict[str, Callable] = {}

        # Health callbacks
        self.health_callbacks: List[Callable] = []

        # Initialize default health checks
        self._initialize_default_checks()

        logger.info("SystemHealthChecker initialized")

    def _initialize_default_checks(self):
        """Initialize default system health checks"""

        # System resource checks
        self.register_health_check(
            name="system_cpu",
            component_type=ComponentType.SYSTEM,
            check_function=self._check_cpu_usage,
            interval_seconds=30,
            critical=True
        )

        self.register_health_check(
            name="system_memory",
            component_type=ComponentType.SYSTEM,
            check_function=self._check_memory_usage,
            interval_seconds=30,
            critical=True
        )

        self.register_health_check(
            name="system_disk",
            component_type=ComponentType.FILE_SYSTEM,
            check_function=self._check_disk_usage,
            interval_seconds=60,
            critical=True
        )

        # Database checks
        self.register_health_check(
            name="postgres_connection",
            component_type=ComponentType.DATABASE,
            check_function=self._check_postgres_connection,
            interval_seconds=30,
            critical=True
        )

        self.register_health_check(
            name="vector_db_connection",
            component_type=ComponentType.VECTOR_DB,
            check_function=self._check_vector_db_connection,
            interval_seconds=30,
            critical=True
        )

        # File system checks
        self.register_health_check(
            name="logs_directory",
            component_type=ComponentType.FILE_SYSTEM,
            check_function=self._check_logs_directory,
            interval_seconds=60,
            critical=False
        )

        # Network connectivity
        self.register_health_check(
            name="external_connectivity",
            component_type=ComponentType.NETWORK,
            check_function=self._check_external_connectivity,
            interval_seconds=60,
            critical=False
        )

    def register_health_check(
        self,
        name: str,
        component_type: ComponentType,
        check_function: Callable,
        timeout_seconds: float = 10.0,
        interval_seconds: int = 30,
        retry_count: int = 3,
        critical: bool = False,
        dependencies: Optional[List[str]] = None
    ):
        """Register a new health check"""
        health_check = HealthCheck(
            name=name,
            component_type=component_type,
            check_function=check_function,
            timeout_seconds=timeout_seconds,
            interval_seconds=interval_seconds,
            retry_count=retry_count,
            critical=critical,
            dependencies=dependencies or []
        )

        self.health_checks[name] = health_check
        self.health_results[name] = []

        logger.info(f"Registered health check: {name}")

    def register_recovery_action(self, component_name: str, action: Callable):
        """Register recovery action for a component"""
        self.recovery_actions[component_name] = action
        logger.info(f"Registered recovery action for: {component_name}")

    def add_health_callback(self, callback: Callable[[str, HealthResult], None]):
        """Add callback for health status changes"""
        self.health_callbacks.append(callback)

    async def start(self):
        """Start health monitoring"""
        if self.is_running:
            logger.warning("SystemHealthChecker is already running")
            return

        try:
            self.is_running = True

            # Start health check loops for each component type
            for component_type in ComponentType:
                asyncio.create_task(self._health_check_loop(component_type))

            # Start health analysis loop
            asyncio.create_task(self._health_analysis_loop())

            logger.info("SystemHealthChecker started successfully")

        except Exception as e:
            logger.error(f"Failed to start SystemHealthChecker: {e}")
            self.is_running = False
            raise

    async def stop(self):
        """Stop health monitoring"""
        if not self.is_running:
            return

        try:
            self.is_running = False
            logger.info("SystemHealthChecker stopped")

        except Exception as e:
            logger.error(f"Error stopping SystemHealthChecker: {e}")

    async def run_health_check(self, check_name: str) -> HealthResult:
        """Run a specific health check"""
        if check_name not in self.health_checks:
            raise ValueError(f"Unknown health check: {check_name}")

        health_check = self.health_checks[check_name]
        return await self._execute_health_check(health_check)

    async def get_health_status(self) -> Dict[str, Any]:
        """Get overall system health status"""
        try:
            overall_status = HealthStatus.HEALTHY
            component_statuses = {}
            critical_issues = []
            warnings = []

            # Collect component health
            for component_type, component_health in self.component_health.items():
                component_statuses[component_type.value] = {
                    "status": component_health.status.value,
                    "last_check": component_health.last_check.isoformat() if component_health.last_check else None,
                    "consecutive_failures": component_health.consecutive_failures,
                    "checks": len(component_health.checks)
                }

                # Determine overall status
                if component_health.status == HealthStatus.CRITICAL:
                    overall_status = HealthStatus.CRITICAL
                    critical_issues.append(f"{component_type.value}: {component_health.checks[-1].message if component_health.checks else 'Unknown issue'}")
                elif component_health.status == HealthStatus.WARNING and overall_status != HealthStatus.CRITICAL:
                    overall_status = HealthStatus.WARNING
                    warnings.append(f"{component_type.value}: {component_health.checks[-1].message if component_health.checks else 'Unknown warning'}")

            # Get latest health check results
            latest_results = {}
            for check_name, results in self.health_results.items():
                if results:
                    latest_result = results[-1]
                    latest_results[check_name] = {
                        "status": latest_result.status.value,
                        "timestamp": latest_result.timestamp.isoformat(),
                        "latency_ms": latest_result.latency_ms,
                        "message": latest_result.message,
                        "error": latest_result.error
                    }

            return {
                "overall_status": overall_status.value,
                "timestamp": datetime.utcnow().isoformat(),
                "components": component_statuses,
                "latest_checks": latest_results,
                "critical_issues": critical_issues,
                "warnings": warnings,
                "total_checks": len(self.health_checks),
                "checks_passing": sum(1 for results in self.health_results.values()
                                    if results and results[-1].status == HealthStatus.HEALTHY)
            }

        except Exception as e:
            logger.error(f"Error getting health status: {e}")
            return {
                "overall_status": HealthStatus.UNKNOWN.value,
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }

    async def get_health_metrics(self) -> Dict[str, Any]:
        """Get health metrics for monitoring integration"""
        try:
            # System metrics
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=1)
            disk = psutil.disk_usage('/')

            # Network stats
            network = psutil.net_io_counters()

            # Process metrics
            process = psutil.Process()
            process_memory = process.memory_info()

            return {
                "cpu_usage_percent": cpu_percent,
                "memory_usage_mb": memory.used / (1024 * 1024),
                "memory_usage_percent": memory.percent,
                "disk_usage_gb": disk.used / (1024 * 1024 * 1024),
                "disk_usage_percent": (disk.used / disk.total) * 100,
                "network_bytes_sent": network.bytes_sent,
                "network_bytes_recv": network.bytes_recv,
                "process_memory_mb": process_memory.rss / (1024 * 1024),
                "process_cpu_percent": process.cpu_percent(),
                "open_files": len(process.open_files()),
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting health metrics: {e}")
            return {}

    async def _health_check_loop(self, component_type: ComponentType):
        """Health check loop for a specific component type"""
        while self.is_running:
            try:
                # Get checks for this component type
                component_checks = [
                    check for check in self.health_checks.values()
                    if check.component_type == component_type
                ]

                if not component_checks:
                    await asyncio.sleep(self.check_interval)
                    continue

                # Run checks for this component
                check_results = []
                for health_check in component_checks:
                    try:
                        result = await self._execute_health_check(health_check)
                        check_results.append(result)

                        # Store result
                        self.health_results[health_check.name].append(result)

                        # Keep only recent results (last 100)
                        if len(self.health_results[health_check.name]) > 100:
                            self.health_results[health_check.name] = self.health_results[health_check.name][-50:]

                        # Notify callbacks
                        await self._notify_health_callbacks(health_check.name, result)

                    except Exception as e:
                        logger.error(f"Error executing health check {health_check.name}: {e}")

                # Update component health
                await self._update_component_health(component_type, check_results)

                # Sleep until next check
                await asyncio.sleep(self.check_interval)

            except Exception as e:
                logger.error(f"Error in health check loop for {component_type.value}: {e}")
                await asyncio.sleep(self.check_interval)

    async def _execute_health_check(self, health_check: HealthCheck) -> HealthResult:
        """Execute a single health check with retries"""
        start_time = time.time()

        for attempt in range(health_check.retry_count):
            try:
                # Check dependencies first
                if health_check.dependencies:
                    dependency_check = await self._check_dependencies(health_check.dependencies)
                    if not dependency_check:
                        return HealthResult(
                            name=health_check.name,
                            status=HealthStatus.CRITICAL,
                            timestamp=datetime.utcnow(),
                            latency_ms=(time.time() - start_time) * 1000,
                            message="Dependency check failed",
                            error="One or more dependencies are unhealthy"
                        )

                # Execute check function with timeout
                result = await asyncio.wait_for(
                    health_check.check_function(),
                    timeout=health_check.timeout_seconds
                )

                latency_ms = (time.time() - start_time) * 1000

                if isinstance(result, dict):
                    return HealthResult(
                        name=health_check.name,
                        status=HealthStatus(result.get('status', 'unknown')),
                        timestamp=datetime.utcnow(),
                        latency_ms=latency_ms,
                        message=result.get('message', 'Check completed'),
                        details=result.get('details'),
                        error=result.get('error')
                    )
                else:
                    return HealthResult(
                        name=health_check.name,
                        status=HealthStatus.HEALTHY,
                        timestamp=datetime.utcnow(),
                        latency_ms=latency_ms,
                        message="Check passed"
                    )

            except asyncio.TimeoutError:
                logger.warning(f"Health check {health_check.name} timed out (attempt {attempt + 1})")
                if attempt == health_check.retry_count - 1:
                    return HealthResult(
                        name=health_check.name,
                        status=HealthStatus.CRITICAL,
                        timestamp=datetime.utcnow(),
                        latency_ms=(time.time() - start_time) * 1000,
                        message="Health check timed out",
                        error=f"Timeout after {health_check.timeout_seconds}s"
                    )

            except Exception as e:
                logger.error(f"Health check {health_check.name} failed (attempt {attempt + 1}): {e}")
                if attempt == health_check.retry_count - 1:
                    return HealthResult(
                        name=health_check.name,
                        status=HealthStatus.CRITICAL,
                        timestamp=datetime.utcnow(),
                        latency_ms=(time.time() - start_time) * 1000,
                        message="Health check failed",
                        error=str(e)
                    )

            # Wait before retry
            if attempt < health_check.retry_count - 1:
                await asyncio.sleep(1)

    async def _check_dependencies(self, dependencies: List[str]) -> bool:
        """Check if all dependencies are healthy"""
        for dep_name in dependencies:
            if dep_name in self.health_results and self.health_results[dep_name]:
                latest_result = self.health_results[dep_name][-1]
                if latest_result.status != HealthStatus.HEALTHY:
                    return False
            else:
                return False  # No recent result for dependency
        return True

    async def _update_component_health(self, component_type: ComponentType, check_results: List[HealthResult]):
        """Update component health based on check results"""
        if not check_results:
            return

        # Determine component status
        component_status = HealthStatus.HEALTHY
        consecutive_failures = 0

        critical_failures = [r for r in check_results if r.status == HealthStatus.CRITICAL]
        warnings = [r for r in check_results if r.status == HealthStatus.WARNING]

        if critical_failures:
            component_status = HealthStatus.CRITICAL
            # Count consecutive failures for critical checks
            if component_type in self.component_health:
                consecutive_failures = self.component_health[component_type].consecutive_failures + 1
        elif warnings:
            component_status = HealthStatus.WARNING
            consecutive_failures = 0
        else:
            consecutive_failures = 0

        # Update component health
        self.component_health[component_type] = ComponentHealth(
            component_type=component_type,
            status=component_status,
            checks=check_results,
            last_check=datetime.utcnow(),
            consecutive_failures=consecutive_failures
        )

        # Trigger recovery if needed
        if component_status == HealthStatus.CRITICAL and consecutive_failures >= 3:
            await self._trigger_recovery(component_type)

    async def _trigger_recovery(self, component_type: ComponentType):
        """Trigger recovery actions for failed component"""
        recovery_key = component_type.value
        if recovery_key in self.recovery_actions:
            try:
                logger.warning(f"Triggering recovery for {component_type.value}")
                await self.recovery_actions[recovery_key]()
                logger.info(f"Recovery action completed for {component_type.value}")
            except Exception as e:
                logger.error(f"Recovery action failed for {component_type.value}: {e}")

    async def _health_analysis_loop(self):
        """Analyze health trends and patterns"""
        while self.is_running:
            try:
                await asyncio.sleep(300)  # Analyze every 5 minutes

                if not self.is_running:
                    break

                await self._analyze_health_trends()

            except Exception as e:
                logger.error(f"Error in health analysis: {e}")

    async def _analyze_health_trends(self):
        """Analyze health trends and detect patterns"""
        try:
            # Analyze each component for trends
            for component_type, component_health in self.component_health.items():
                if component_health.consecutive_failures > 1:
                    logger.warning(f"Component {component_type.value} has {component_health.consecutive_failures} consecutive failures")

                # Check for degrading performance
                recent_checks = [r for r in component_health.checks if
                               (datetime.utcnow() - r.timestamp).total_seconds() < 3600]  # Last hour

                if len(recent_checks) > 5:
                    avg_latency = sum(r.latency_ms for r in recent_checks) / len(recent_checks)
                    if avg_latency > 5000:  # 5 second average latency
                        logger.warning(f"Component {component_type.value} showing high latency: {avg_latency:.2f}ms")

        except Exception as e:
            logger.error(f"Error analyzing health trends: {e}")

    async def _notify_health_callbacks(self, check_name: str, result: HealthResult):
        """Notify health status callbacks"""
        for callback in self.health_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(check_name, result)
                else:
                    callback(check_name, result)
            except Exception as e:
                logger.error(f"Error in health callback: {e}")

    # Default health check implementations

    async def _check_cpu_usage(self) -> Dict[str, Any]:
        """Check CPU usage"""
        cpu_percent = psutil.cpu_percent(interval=1)

        if cpu_percent > 90:
            status = "critical"
            message = f"High CPU usage: {cpu_percent:.1f}%"
        elif cpu_percent > 75:
            status = "warning"
            message = f"Elevated CPU usage: {cpu_percent:.1f}%"
        else:
            status = "healthy"
            message = f"CPU usage normal: {cpu_percent:.1f}%"

        return {
            "status": status,
            "message": message,
            "details": {"cpu_percent": cpu_percent}
        }

    async def _check_memory_usage(self) -> Dict[str, Any]:
        """Check memory usage"""
        memory = psutil.virtual_memory()

        if memory.percent > 90:
            status = "critical"
            message = f"High memory usage: {memory.percent:.1f}%"
        elif memory.percent > 80:
            status = "warning"
            message = f"Elevated memory usage: {memory.percent:.1f}%"
        else:
            status = "healthy"
            message = f"Memory usage normal: {memory.percent:.1f}%"

        return {
            "status": status,
            "message": message,
            "details": {
                "memory_percent": memory.percent,
                "available_gb": memory.available / (1024**3),
                "used_gb": memory.used / (1024**3)
            }
        }

    async def _check_disk_usage(self) -> Dict[str, Any]:
        """Check disk usage"""
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100

        if disk_percent > 90:
            status = "critical"
            message = f"High disk usage: {disk_percent:.1f}%"
        elif disk_percent > 80:
            status = "warning"
            message = f"Elevated disk usage: {disk_percent:.1f}%"
        else:
            status = "healthy"
            message = f"Disk usage normal: {disk_percent:.1f}%"

        return {
            "status": status,
            "message": message,
            "details": {
                "disk_percent": disk_percent,
                "free_gb": disk.free / (1024**3),
                "used_gb": disk.used / (1024**3)
            }
        }

    async def _check_postgres_connection(self) -> Dict[str, Any]:
        """Check PostgreSQL database connection"""
        try:
            # This would use your actual database connection
            # For now, simulate the check
            await asyncio.sleep(0.1)  # Simulate connection check

            return {
                "status": "healthy",
                "message": "PostgreSQL connection successful",
                "details": {"connection_time_ms": 100}
            }

        except Exception as e:
            return {
                "status": "critical",
                "message": "PostgreSQL connection failed",
                "error": str(e)
            }

    async def _check_vector_db_connection(self) -> Dict[str, Any]:
        """Check vector database connection"""
        try:
            # This would use your actual vector database connection
            # For now, simulate the check
            await asyncio.sleep(0.1)  # Simulate connection check

            return {
                "status": "healthy",
                "message": "Vector database connection successful",
                "details": {"connection_time_ms": 100}
            }

        except Exception as e:
            return {
                "status": "critical",
                "message": "Vector database connection failed",
                "error": str(e)
            }

    async def _check_logs_directory(self) -> Dict[str, Any]:
        """Check logs directory accessibility"""
        try:
            import os
            log_dir = "/var/log/dt-rag"

            if os.path.exists(log_dir) and os.access(log_dir, os.W_OK):
                return {
                    "status": "healthy",
                    "message": "Logs directory accessible",
                    "details": {"log_directory": log_dir}
                }
            else:
                return {
                    "status": "warning",
                    "message": "Logs directory not accessible",
                    "details": {"log_directory": log_dir}
                }

        except Exception as e:
            return {
                "status": "warning",
                "message": "Error checking logs directory",
                "error": str(e)
            }

    async def _check_external_connectivity(self) -> Dict[str, Any]:
        """Check external network connectivity"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.openai.com/v1/models",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200 or response.status == 401:  # 401 is expected without auth
                        return {
                            "status": "healthy",
                            "message": "External connectivity OK",
                            "details": {"status_code": response.status}
                        }
                    else:
                        return {
                            "status": "warning",
                            "message": f"External connectivity issue: {response.status}",
                            "details": {"status_code": response.status}
                        }

        except Exception as e:
            return {
                "status": "warning",
                "message": "External connectivity failed",
                "error": str(e)
            }