"""
Redis 연결 관리 및 최적화 시스템
"""

import logging
import pickle
import gzip
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import os

logger = logging.getLogger(__name__)

# Redis 호환성 확인
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available - using fallback mode")

@dataclass
class RedisConfig:
    """Redis 설정"""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    username: Optional[str] = None

    # 연결 풀 설정
    max_connections: int = 50
    retry_on_timeout: bool = True
    socket_keepalive: bool = True
    socket_keepalive_options: Dict = None
    health_check_interval: int = 30

    # 타임아웃 설정
    socket_timeout: float = 5.0
    socket_connect_timeout: float = 5.0

    # 압축 및 직렬화 설정
    enable_compression: bool = True
    compression_threshold: int = 1024  # 1KB
    compression_level: int = 6

    # TTL 설정
    default_ttl: int = 3600  # 1시간
    ttl_configs: Dict[str, int] = None

    def __post_init__(self):
        if self.socket_keepalive_options is None:
            # TCP keepalive는 플랫폼 specific하므로 기본적으로 비활성화
            # 필요시 외부에서 socket.TCP_* 상수를 사용하여 설정
            self.socket_keepalive_options = {}

        if self.ttl_configs is None:
            self.ttl_configs = {
                'search_results': 3600,       # 1시간
                'embeddings': 86400 * 7,      # 1주일
                'query_suggestions': 3600,    # 1시간
                'user_preferences': 86400,    # 1일
                'health_check': 300,          # 5분
                'metrics': 900,               # 15분
            }

class RedisManager:
    """Redis 연결 및 작업 관리자"""

    def __init__(self, config: RedisConfig = None):
        self.config = config or RedisConfig()
        self.client: Optional[redis.Redis] = None
        self.connection_pool: Optional[redis.ConnectionPool] = None
        self.is_connected = False
        self.connection_attempts = 0
        self.max_retry_attempts = 3

        # 성능 통계
        self.stats = {
            'operations_total': 0,
            'operations_success': 0,
            'operations_failed': 0,
            'bytes_compressed': 0,
            'bytes_uncompressed': 0,
            'compression_ratio': 0.0
        }

    async def initialize(self) -> bool:
        """Redis 연결 초기화"""
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available, operating in fallback mode")
            return False

        try:
            # 연결 풀 생성
            self.connection_pool = redis.ConnectionPool(
                host=self.config.host,
                port=self.config.port,
                db=self.config.db,
                password=self.config.password,
                username=self.config.username,
                max_connections=self.config.max_connections,
                retry_on_timeout=self.config.retry_on_timeout,
                socket_keepalive=self.config.socket_keepalive,
                socket_keepalive_options=self.config.socket_keepalive_options,
                health_check_interval=self.config.health_check_interval,
                socket_timeout=self.config.socket_timeout,
                socket_connect_timeout=self.config.socket_connect_timeout,
                decode_responses=False  # 바이너리 데이터 처리용
            )

            # Redis 클라이언트 생성
            self.client = redis.Redis(connection_pool=self.connection_pool)

            # 연결 테스트
            await self.client.ping()
            self.is_connected = True
            self.connection_attempts = 0

            logger.info(f"Redis connected successfully to {self.config.host}:{self.config.port}")
            return True

        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            self.is_connected = False
            self.connection_attempts += 1
            return False

    async def ensure_connection(self) -> bool:
        """연결 상태 확인 및 재연결"""
        if not REDIS_AVAILABLE:
            return False

        if self.is_connected and self.client:
            try:
                await self.client.ping()
                return True
            except Exception:
                self.is_connected = False

        # 재연결 시도
        if self.connection_attempts < self.max_retry_attempts:
            return await self.initialize()
        else:
            logger.error("Maximum Redis reconnection attempts exceeded")
            return False

    def _serialize_data(self, data: Any) -> bytes:
        """데이터 직렬화 및 압축"""
        try:
            # 객체 직렬화
            serialized = pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)
            self.stats['bytes_uncompressed'] += len(serialized)

            # 압축 적용 (설정된 임계값 이상인 경우)
            if (self.config.enable_compression and
                len(serialized) > self.config.compression_threshold):

                compressed = gzip.compress(serialized, compresslevel=self.config.compression_level)
                self.stats['bytes_compressed'] += len(compressed)

                # 압축 효율성 체크 (압축률이 10% 미만이면 원본 사용)
                if len(compressed) < len(serialized) * 0.9:
                    return b'COMPRESSED:' + compressed

            return b'RAW:' + serialized

        except Exception as e:
            logger.error(f"Data serialization failed: {e}")
            raise

    def _deserialize_data(self, data: bytes) -> Any:
        """데이터 압축 해제 및 역직렬화"""
        try:
            if data.startswith(b'COMPRESSED:'):
                # 압축 해제
                compressed_data = data[11:]  # 'COMPRESSED:' 제거
                decompressed = gzip.decompress(compressed_data)
                return pickle.loads(decompressed)  # nosec B301 - trusted internal cache data
            elif data.startswith(b'RAW:'):
                # 원본 데이터
                raw_data = data[4:]  # 'RAW:' 제거
                return pickle.loads(raw_data)  # nosec B301 - trusted internal cache data
            else:
                # 호환성을 위한 레거시 형식
                return pickle.loads(data)  # nosec B301 - trusted internal cache data

        except Exception as e:
            logger.error(f"Data deserialization failed: {e}")
            raise

    def _get_ttl_for_key(self, key: str) -> int:
        """키에 따른 TTL 결정"""
        for prefix, ttl in self.config.ttl_configs.items():
            if key.startswith(prefix):
                return ttl
        return self.config.default_ttl

    async def get(self, key: str) -> Optional[Any]:
        """값 조회"""
        if not await self.ensure_connection():
            return None

        try:
            self.stats['operations_total'] += 1

            data = await self.client.get(key)
            if data is None:
                return None

            result = self._deserialize_data(data)
            self.stats['operations_success'] += 1
            return result

        except Exception as e:
            logger.warning(f"Redis GET failed for key {key}: {e}")
            self.stats['operations_failed'] += 1
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """값 저장"""
        if not await self.ensure_connection():
            return False

        try:
            self.stats['operations_total'] += 1

            # TTL 결정
            if ttl is None:
                ttl = self._get_ttl_for_key(key)

            # 데이터 직렬화
            data = self._serialize_data(value)

            # Redis에 저장
            await self.client.setex(key, ttl, data)

            self.stats['operations_success'] += 1
            return True

        except Exception as e:
            logger.warning(f"Redis SET failed for key {key}: {e}")
            self.stats['operations_failed'] += 1
            return False

    async def delete(self, key: str) -> bool:
        """값 삭제"""
        if not await self.ensure_connection():
            return False

        try:
            self.stats['operations_total'] += 1
            result = await self.client.delete(key)
            self.stats['operations_success'] += 1
            return result > 0

        except Exception as e:
            logger.warning(f"Redis DELETE failed for key {key}: {e}")
            self.stats['operations_failed'] += 1
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """패턴 매칭으로 키 삭제"""
        if not await self.ensure_connection():
            return 0

        try:
            self.stats['operations_total'] += 1

            # 키 검색
            keys = await self.client.keys(pattern)
            if not keys:
                return 0

            # 키 삭제
            deleted_count = await self.client.delete(*keys)
            self.stats['operations_success'] += 1
            return deleted_count

        except Exception as e:
            logger.warning(f"Redis DELETE pattern failed for {pattern}: {e}")
            self.stats['operations_failed'] += 1
            return 0

    async def exists(self, key: str) -> bool:
        """키 존재 확인"""
        if not await self.ensure_connection():
            return False

        try:
            result = await self.client.exists(key)
            return result > 0
        except Exception as e:
            logger.warning(f"Redis EXISTS failed for key {key}: {e}")
            return False

    async def expire(self, key: str, ttl: int) -> bool:
        """TTL 설정"""
        if not await self.ensure_connection():
            return False

        try:
            result = await self.client.expire(key, ttl)
            return result
        except Exception as e:
            logger.warning(f"Redis EXPIRE failed for key {key}: {e}")
            return False

    async def ttl(self, key: str) -> int:
        """TTL 조회"""
        if not await self.ensure_connection():
            return -1

        try:
            return await self.client.ttl(key)
        except Exception as e:
            logger.warning(f"Redis TTL failed for key {key}: {e}")
            return -1

    async def keys(self, pattern: str = "*") -> List[str]:
        """키 목록 조회"""
        if not await self.ensure_connection():
            return []

        try:
            keys = await self.client.keys(pattern)
            return [key.decode() if isinstance(key, bytes) else key for key in keys]
        except Exception as e:
            logger.warning(f"Redis KEYS failed for pattern {pattern}: {e}")
            return []

    async def flushdb(self) -> bool:
        """현재 DB 전체 삭제"""
        if not await self.ensure_connection():
            return False

        try:
            await self.client.flushdb()
            return True
        except Exception as e:
            logger.error(f"Redis FLUSHDB failed: {e}")
            return False

    async def info(self) -> Dict[str, Any]:
        """Redis 서버 정보"""
        if not await self.ensure_connection():
            return {}

        try:
            info = await self.client.info()
            return dict(info)
        except Exception as e:
            logger.warning(f"Redis INFO failed: {e}")
            return {}

    async def memory_usage(self, key: str) -> Optional[int]:
        """키의 메모리 사용량 (바이트)"""
        if not await self.ensure_connection():
            return None

        try:
            return await self.client.memory_usage(key)
        except Exception as e:
            logger.warning(f"Redis MEMORY USAGE failed for key {key}: {e}")
            return None

    async def lpush(self, key: str, *values: Any) -> Optional[int]:
        """List 왼쪽에 값 추가"""
        if not await self.ensure_connection():
            return None

        try:
            self.stats['operations_total'] += 1
            result = await self.client.lpush(key, *values)
            self.stats['operations_success'] += 1
            return result
        except Exception as e:
            logger.warning(f"Redis LPUSH failed for key {key}: {e}")
            self.stats['operations_failed'] += 1
            return None

    async def brpop(self, *keys: str, timeout: int = 0) -> Optional[tuple]:
        """List 오른쪽에서 값 블로킹 팝"""
        if not await self.ensure_connection():
            return None

        try:
            self.stats['operations_total'] += 1
            result = await self.client.brpop(*keys, timeout=timeout)
            self.stats['operations_success'] += 1
            return result
        except Exception as e:
            logger.warning(f"Redis BRPOP failed: {e}")
            self.stats['operations_failed'] += 1
            return None

    async def llen(self, key: str) -> int:
        """List 길이 조회"""
        if not await self.ensure_connection():
            return 0

        try:
            self.stats['operations_total'] += 1
            result = await self.client.llen(key)
            self.stats['operations_success'] += 1
            return result
        except Exception as e:
            logger.warning(f"Redis LLEN failed for key {key}: {e}")
            self.stats['operations_failed'] += 1
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """성능 통계"""
        total_ops = self.stats['operations_total']
        success_rate = (
            (self.stats['operations_success'] / total_ops * 100)
            if total_ops > 0 else 0
        )

        # 압축률 계산
        if self.stats['bytes_uncompressed'] > 0:
            compression_ratio = (
                1.0 - self.stats['bytes_compressed'] / self.stats['bytes_uncompressed']
            )
        else:
            compression_ratio = 0.0

        return {
            'connection_status': self.is_connected,
            'connection_attempts': self.connection_attempts,
            'operations_total': total_ops,
            'operations_success': self.stats['operations_success'],
            'operations_failed': self.stats['operations_failed'],
            'success_rate_percent': round(success_rate, 2),
            'bytes_compressed': self.stats['bytes_compressed'],
            'bytes_uncompressed': self.stats['bytes_uncompressed'],
            'compression_ratio': round(compression_ratio, 3),
            'compression_enabled': self.config.enable_compression
        }

    async def health_check(self) -> Dict[str, Any]:
        """헬스 체크"""
        if not REDIS_AVAILABLE:
            return {
                'status': 'unavailable',
                'message': 'Redis client not installed'
            }

        try:
            start_time = datetime.now()

            # 연결 확인
            if not await self.ensure_connection():
                return {
                    'status': 'unhealthy',
                    'message': 'Connection failed',
                    'connection_attempts': self.connection_attempts
                }

            # PING 테스트
            await self.client.ping()

            # 간단한 SET/GET 테스트
            test_key = f"health_check:{datetime.now().timestamp()}"
            test_value = {'timestamp': datetime.now().isoformat()}

            await self.set(test_key, test_value, ttl=60)
            retrieved_value = await self.get(test_key)
            await self.delete(test_key)

            response_time = (datetime.now() - start_time).total_seconds() * 1000

            if retrieved_value == test_value:
                return {
                    'status': 'healthy',
                    'response_time_ms': round(response_time, 2),
                    'stats': self.get_stats()
                }
            else:
                return {
                    'status': 'degraded',
                    'message': 'Data consistency check failed',
                    'response_time_ms': round(response_time, 2)
                }

        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': str(e),
                'connection_attempts': self.connection_attempts
            }

    async def close(self):
        """연결 종료"""
        if self.client:
            await self.client.close()
        if self.connection_pool:
            await self.connection_pool.disconnect()

        self.is_connected = False
        logger.info("Redis connection closed")

# 전역 Redis 매니저 인스턴스
_redis_manager: Optional[RedisManager] = None

async def get_redis_manager() -> RedisManager:
    """전역 Redis 매니저 조회"""
    global _redis_manager
    if _redis_manager is None:
        # 환경변수에서 설정 읽기
        config = RedisConfig(
            host=os.getenv('REDIS_HOST', 'redis'),
            port=int(os.getenv('REDIS_PORT', '6379')),
            db=int(os.getenv('REDIS_DB', '0')),
            password=os.getenv('REDIS_PASSWORD'),
            max_connections=int(os.getenv('REDIS_MAX_CONNECTIONS', '50')),
            enable_compression=os.getenv('REDIS_ENABLE_COMPRESSION', 'true').lower() == 'true'
        )
        _redis_manager = RedisManager(config)
        await _redis_manager.initialize()

    return _redis_manager

async def initialize_redis_manager(config: RedisConfig = None) -> RedisManager:
    """Redis 매니저 초기화"""
    global _redis_manager
    _redis_manager = RedisManager(config)
    await _redis_manager.initialize()
    return _redis_manager