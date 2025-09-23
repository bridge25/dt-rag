"""
PostgreSQL Connection Pool Optimization for AsyncPG
High-performance connection management with monitoring
"""

import asyncio
import asyncpg
import logging
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool, QueuePool
from sqlalchemy import event, text
import os

logger = logging.getLogger(__name__)


@dataclass
class ConnectionPoolConfig:
    """Connection pool configuration"""
    # Basic connection settings
    database_url: str = ""

    # Pool size settings
    min_size: int = 5          # Minimum pool size
    max_size: int = 20         # Maximum pool size

    # Connection timeouts
    command_timeout: int = 30   # Command timeout in seconds
    server_settings: Dict[str, str] = field(default_factory=lambda: {
        'jit': 'off',                    # Disable JIT for consistent performance
        'random_page_cost': '1.1',       # SSD-optimized
        'work_mem': '256MB',             # Increased for vector operations
        'maintenance_work_mem': '512MB',  # For index operations
        'shared_preload_libraries': 'vector',  # Ensure pgvector is loaded
        'hnsw.ef_search': '80',          # Default HNSW search parameter
        'max_parallel_workers_per_gather': '4'  # Parallel query execution
    })

    # Connection lifecycle
    max_cached_statement_lifetime: int = 300  # 5 minutes
    max_cacheable_statement_size: int = 1024  # 1KB

    # Monitoring settings
    enable_monitoring: bool = True
    log_slow_queries: bool = True
    slow_query_threshold: float = 1.0  # Log queries > 1 second


class OptimizedConnectionPool:
    """High-performance AsyncPG connection pool with monitoring"""

    def __init__(self, config: ConnectionPoolConfig):
        self.config = config
        self.pool: Optional[asyncpg.Pool] = None
        self.engine = None
        self.async_session_maker = None

        # Monitoring data
        self.stats = {
            'total_connections': 0,
            'active_connections': 0,
            'total_queries': 0,
            'slow_queries': 0,
            'avg_query_time': 0.0,
            'pool_acquisitions': 0,
            'pool_releases': 0,
            'connection_errors': 0
        }

        self.query_times = []
        self.slow_queries = []

    async def initialize(self):
        """Initialize optimized connection pool"""
        try:
            # Parse database URL
            if not self.config.database_url:
                self.config.database_url = os.getenv("DATABASE_URL", "")

            if not self.config.database_url:
                raise ValueError("DATABASE_URL not provided")

            # Create AsyncPG pool
            await self._create_asyncpg_pool()

            # Create SQLAlchemy engine with optimizations
            await self._create_sqlalchemy_engine()

            logger.info(f"Connection pool initialized with {self.config.min_size}-{self.config.max_size} connections")

        except Exception as e:
            logger.error(f"Connection pool initialization failed: {e}")
            raise

    async def _create_asyncpg_pool(self):
        """Create optimized AsyncPG connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                self.config.database_url,
                min_size=self.config.min_size,
                max_size=self.config.max_size,
                command_timeout=self.config.command_timeout,
                server_settings=self.config.server_settings,
                max_cached_statement_lifetime=self.config.max_cached_statement_lifetime,
                max_cacheable_statement_size=self.config.max_cacheable_statement_size,
                init=self._init_connection
            )

        except Exception as e:
            logger.error(f"AsyncPG pool creation failed: {e}")
            raise

    async def _create_sqlalchemy_engine(self):
        """Create SQLAlchemy engine with pool optimization"""
        try:
            # Configure for high performance
            engine_args = {
                'echo': False,
                'future': True,
                'poolclass': QueuePool,
                'pool_size': self.config.max_size,
                'max_overflow': 0,  # No overflow connections
                'pool_pre_ping': True,  # Validate connections
                'pool_recycle': 3600,   # Recycle connections every hour
                'connect_args': {
                    'command_timeout': self.config.command_timeout,
                    'server_settings': self.config.server_settings
                }
            }

            # Use AsyncPG dialect for better performance
            url = self.config.database_url.replace('postgresql://', 'postgresql+asyncpg://')

            self.engine = create_async_engine(url, **engine_args)

            # Set up event listeners for monitoring
            if self.config.enable_monitoring:
                self._setup_monitoring()

            # Create session maker
            self.async_session_maker = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )

        except Exception as e:
            logger.error(f"SQLAlchemy engine creation failed: {e}")
            raise

    async def _init_connection(self, connection):
        """Initialize each new connection"""
        try:
            # Set connection-level optimizations
            await connection.execute('''
                SET default_transaction_isolation = 'read committed';
                SET timezone = 'UTC';
                SET datestyle = 'iso, mdy';
                SET lock_timeout = '30s';
                SET statement_timeout = '60s';
                SET idle_in_transaction_session_timeout = '300s';
            ''')

            # Enable pgvector if available
            try:
                await connection.execute('SET search_path = public, vector;')
            except Exception:
                pass  # pgvector might not be available

            self.stats['total_connections'] += 1

        except Exception as e:
            logger.error(f"Connection initialization failed: {e}")
            self.stats['connection_errors'] += 1

    def _setup_monitoring(self):
        """Set up SQLAlchemy event monitoring"""

        @event.listens_for(self.engine.sync_engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            context._query_start_time = time.time()
            self.stats['total_queries'] += 1

        @event.listens_for(self.engine.sync_engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            if hasattr(context, '_query_start_time'):
                elapsed = time.time() - context._query_start_time

                # Update statistics
                self.query_times.append(elapsed)
                if len(self.query_times) > 1000:  # Keep only recent 1000 queries
                    self.query_times = self.query_times[-1000:]

                self.stats['avg_query_time'] = sum(self.query_times) / len(self.query_times)

                # Log slow queries
                if self.config.log_slow_queries and elapsed > self.config.slow_query_threshold:
                    self.stats['slow_queries'] += 1
                    self.slow_queries.append({
                        'query': statement[:200] + '...' if len(statement) > 200 else statement,
                        'time': elapsed,
                        'timestamp': time.time()
                    })
                    # Keep only recent 100 slow queries
                    if len(self.slow_queries) > 100:
                        self.slow_queries = self.slow_queries[-100:]

                    logger.warning(f"Slow query detected: {elapsed:.3f}s - {statement[:100]}...")

    @asynccontextmanager
    async def get_session(self):
        """Get optimized database session with monitoring"""
        if not self.async_session_maker:
            raise RuntimeError("Connection pool not initialized")

        session = None
        try:
            session = self.async_session_maker()
            self.stats['active_connections'] += 1
            yield session

        except Exception as e:
            if session:
                await session.rollback()
            logger.error(f"Session error: {e}")
            raise
        finally:
            if session:
                await session.close()
                self.stats['active_connections'] -= 1

    @asynccontextmanager
    async def get_connection(self):
        """Get raw AsyncPG connection for high-performance operations"""
        if not self.pool:
            raise RuntimeError("AsyncPG pool not initialized")

        connection = None
        try:
            connection = await self.pool.acquire()
            self.stats['pool_acquisitions'] += 1
            yield connection

        except Exception as e:
            logger.error(f"Connection error: {e}")
            self.stats['connection_errors'] += 1
            raise
        finally:
            if connection:
                await self.pool.release(connection)
                self.stats['pool_releases'] += 1

    async def execute_optimized_query(
        self,
        query: str,
        parameters: Dict[str, Any] = None,
        fetch_mode: str = "all"
    ) -> Any:
        """Execute query with optimizations"""
        start_time = time.time()

        async with self.get_connection() as conn:
            try:
                if parameters:
                    if fetch_mode == "all":
                        result = await conn.fetch(query, *parameters.values())
                    elif fetch_mode == "one":
                        result = await conn.fetchrow(query, *parameters.values())
                    elif fetch_mode == "scalar":
                        result = await conn.fetchval(query, *parameters.values())
                    else:
                        await conn.execute(query, *parameters.values())
                        result = None
                else:
                    if fetch_mode == "all":
                        result = await conn.fetch(query)
                    elif fetch_mode == "one":
                        result = await conn.fetchrow(query)
                    elif fetch_mode == "scalar":
                        result = await conn.fetchval(query)
                    else:
                        await conn.execute(query)
                        result = None

                # Monitor performance
                elapsed = time.time() - start_time
                self.query_times.append(elapsed)

                return result

            except Exception as e:
                logger.error(f"Query execution failed: {e}")
                self.stats['connection_errors'] += 1
                raise

    async def get_pool_status(self) -> Dict[str, Any]:
        """Get detailed pool status"""
        if not self.pool:
            return {"error": "Pool not initialized"}

        pool_stats = {
            "size": self.pool.get_size(),
            "min_size": self.pool.get_min_size(),
            "max_size": self.pool.get_max_size(),
            "idle_connections": self.pool.get_idle_size(),
            "active_connections": self.pool.get_size() - self.pool.get_idle_size()
        }

        return {
            "pool": pool_stats,
            "stats": self.stats,
            "recent_performance": {
                "avg_query_time": self.stats['avg_query_time'],
                "slow_query_count": len(self.slow_queries),
                "error_rate": self.stats['connection_errors'] / max(1, self.stats['total_queries'])
            }
        }

    async def optimize_pool(self):
        """Optimize connection pool performance"""
        try:
            if not self.pool:
                return

            # Clear idle connections periodically
            current_size = self.pool.get_size()
            idle_size = self.pool.get_idle_size()

            if idle_size > self.config.min_size:
                # Close excess idle connections
                for _ in range(min(5, idle_size - self.config.min_size)):
                    try:
                        conn = await self.pool.acquire()
                        await self.pool.release(conn, discard=True)
                    except Exception:
                        break

            # Reset prepared statement cache periodically
            async with self.get_connection() as conn:
                await conn.execute("DISCARD PLANS")

            logger.info(f"Pool optimized: {current_size} -> {self.pool.get_size()} connections")

        except Exception as e:
            logger.error(f"Pool optimization failed: {e}")

    async def get_slow_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent slow queries"""
        return sorted(
            self.slow_queries,
            key=lambda x: x['time'],
            reverse=True
        )[:limit]

    async def close(self):
        """Close connection pool"""
        try:
            if self.pool:
                await self.pool.close()
                self.pool = None

            if self.engine:
                await self.engine.dispose()
                self.engine = None

            logger.info("Connection pool closed")

        except Exception as e:
            logger.error(f"Error closing connection pool: {e}")


# Global connection pool instance
_connection_pool = None

async def get_connection_pool(config: ConnectionPoolConfig = None) -> OptimizedConnectionPool:
    """Get global connection pool instance"""
    global _connection_pool

    if _connection_pool is None:
        if config is None:
            config = ConnectionPoolConfig(
                database_url=os.getenv("DATABASE_URL", "")
            )

        _connection_pool = OptimizedConnectionPool(config)
        await _connection_pool.initialize()

    return _connection_pool


async def close_connection_pool():
    """Close global connection pool"""
    global _connection_pool
    if _connection_pool:
        await _connection_pool.close()
        _connection_pool = None