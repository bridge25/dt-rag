"""
메모리 최적화 시스템
HYBRID_SEARCH_OPTIMIZATION_GUIDE.md 메모리 최적화 구현

핵심 기능:
- 임베딩 양자화 (Float32 → Int8)
- 결과 스트리밍 처리
- 가비지 컬렉션 최적화
- 메모리 사용량 모니터링
"""

import numpy as np
import gc
import time
import logging
from typing import List, Dict, Any, Optional, AsyncGenerator, Tuple
from dataclasses import dataclass
import asyncio
from contextlib import asynccontextmanager
import json

logger = logging.getLogger(__name__)

@dataclass
class MemoryStats:
    """메모리 통계"""
    before_mb: float
    after_mb: float
    saved_mb: float
    compression_ratio: float
    processing_time_ms: float

class EmbeddingQuantizer:
    """임베딩 벡터 양자화 처리"""

    def __init__(self, quantization_bits: int = 8):
        """
        Args:
            quantization_bits: 양자화 비트 수 (8=Int8, 16=Int16)
        """
        self.quantization_bits = quantization_bits
        self.quantization_stats = []

    def quantize_embedding(
        self,
        embedding: np.ndarray
    ) -> Tuple[np.ndarray, Dict[str, float]]:
        """
        임베딩 벡터 양자화 (Float32 → Int8)

        Returns:
            Tuple[quantized_embedding, metadata]
        """
        start_time = time.time()
        original_size = embedding.nbytes

        try:
            if self.quantization_bits == 8:
                # Float32 → Int8 양자화
                min_val = embedding.min()
                max_val = embedding.max()

                # 스케일 계산
                scale = (max_val - min_val) / 255.0 if max_val != min_val else 1.0

                # 양자화
                quantized = ((embedding - min_val) / scale).astype(np.uint8)

                metadata = {
                    "min_val": float(min_val),
                    "max_val": float(max_val),
                    "scale": float(scale),
                    "dtype": "uint8"
                }

            elif self.quantization_bits == 16:
                # Float32 → Int16 양자화
                min_val = embedding.min()
                max_val = embedding.max()

                scale = (max_val - min_val) / 65535.0 if max_val != min_val else 1.0
                quantized = ((embedding - min_val) / scale).astype(np.uint16)

                metadata = {
                    "min_val": float(min_val),
                    "max_val": float(max_val),
                    "scale": float(scale),
                    "dtype": "uint16"
                }
            else:
                # 양자화 없음
                quantized = embedding
                metadata = {"dtype": "float32"}

            processing_time = (time.time() - start_time) * 1000
            quantized_size = quantized.nbytes

            # 통계 수집
            stats = MemoryStats(
                before_mb=original_size / 1024 / 1024,
                after_mb=quantized_size / 1024 / 1024,
                saved_mb=(original_size - quantized_size) / 1024 / 1024,
                compression_ratio=original_size / quantized_size if quantized_size > 0 else 1.0,
                processing_time_ms=processing_time
            )

            self.quantization_stats.append(stats)

            # 최근 100개 통계만 유지
            if len(self.quantization_stats) > 100:
                self.quantization_stats = self.quantization_stats[-100:]

            logger.debug(
                f"Quantization: {original_size}→{quantized_size} bytes "
                f"({stats.compression_ratio:.1f}x compression) in {processing_time:.1f}ms"
            )

            return quantized, metadata

        except Exception as e:
            logger.error(f"Quantization failed: {e}")
            return embedding, {"dtype": "float32", "error": str(e)}

    def dequantize_embedding(
        self,
        quantized: np.ndarray,
        metadata: Dict[str, Any]
    ) -> np.ndarray:
        """양자화된 임베딩을 원래 형태로 복원"""
        try:
            dtype = metadata.get("dtype", "float32")

            if dtype == "uint8":
                min_val = metadata["min_val"]
                scale = metadata["scale"]
                return quantized.astype(np.float32) * scale + min_val

            elif dtype == "uint16":
                min_val = metadata["min_val"]
                scale = metadata["scale"]
                return quantized.astype(np.float32) * scale + min_val

            else:
                return quantized.astype(np.float32)

        except Exception as e:
            logger.error(f"Dequantization failed: {e}")
            return quantized.astype(np.float32)

    def get_quantization_stats(self) -> Dict[str, Any]:
        """양자화 통계 반환"""
        if not self.quantization_stats:
            return {"no_data": True}

        recent_stats = self.quantization_stats[-10:]

        return {
            "total_quantizations": len(self.quantization_stats),
            "avg_compression_ratio": sum(s.compression_ratio for s in recent_stats) / len(recent_stats),
            "avg_saved_mb": sum(s.saved_mb for s in recent_stats) / len(recent_stats),
            "avg_processing_time_ms": sum(s.processing_time_ms for s in recent_stats) / len(recent_stats),
            "total_memory_saved_mb": sum(s.saved_mb for s in self.quantization_stats)
        }

class StreamingResultProcessor:
    """대용량 검색 결과 스트리밍 처리"""

    def __init__(self, chunk_size: int = 10):
        """
        Args:
            chunk_size: 스트리밍 청크 크기
        """
        self.chunk_size = chunk_size
        self.streaming_stats = {
            "total_streams": 0,
            "total_items_streamed": 0,
            "avg_chunk_processing_time": 0.0
        }

    async def stream_search_results(
        self,
        search_results: List[Dict[str, Any]]
    ) -> AsyncGenerator[List[Dict[str, Any]], None]:
        """
        검색 결과를 청크 단위로 스트리밍

        Yields:
            청크 단위 검색 결과
        """
        try:
            total_items = len(search_results)
            chunks_processed = 0

            for i in range(0, total_items, self.chunk_size):
                start_time = time.time()

                chunk = search_results[i:i + self.chunk_size]

                # 청크 전처리 (메모리 최적화)
                optimized_chunk = await self._optimize_chunk(chunk)

                processing_time = (time.time() - start_time) * 1000
                chunks_processed += 1

                # 통계 업데이트
                self._update_streaming_stats(len(chunk), processing_time)

                yield optimized_chunk

                # 청크 간 짧은 대기 (메모리 압박 완화)
                if i + self.chunk_size < total_items:
                    await asyncio.sleep(0.01)

            logger.debug(
                f"Streamed {total_items} items in {chunks_processed} chunks"
            )

        except Exception as e:
            logger.error(f"Streaming failed: {e}")
            # 폴백: 전체 결과 반환
            yield search_results

    async def _optimize_chunk(
        self,
        chunk: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """청크 메모리 최적화"""
        optimized = []

        for item in chunk:
            # 텍스트 길이 제한 (메모리 절약)
            if "text" in item and len(item["text"]) > 1000:
                item["text"] = item["text"][:1000] + "..."

            # 불필요한 메타데이터 제거
            if "metadata" in item:
                metadata = item["metadata"]
                essential_keys = ["bm25_score", "vector_score", "source"]
                item["metadata"] = {
                    k: v for k, v in metadata.items()
                    if k in essential_keys
                }

            optimized.append(item)

        return optimized

    def _update_streaming_stats(self, items_count: int, processing_time: float):
        """스트리밍 통계 업데이트"""
        self.streaming_stats["total_streams"] += 1
        self.streaming_stats["total_items_streamed"] += items_count

        # 이동 평균 계산
        total_streams = self.streaming_stats["total_streams"]
        current_avg = self.streaming_stats["avg_chunk_processing_time"]
        self.streaming_stats["avg_chunk_processing_time"] = (
            (current_avg * (total_streams - 1) + processing_time) / total_streams
        )

    def get_streaming_stats(self) -> Dict[str, Any]:
        """스트리밍 통계 반환"""
        return self.streaming_stats.copy()

class GarbageCollectionOptimizer:
    """가비지 컬렉션 최적화"""

    def __init__(self, gc_threshold: int = 100):
        """
        Args:
            gc_threshold: GC 트리거 임계치
        """
        self.gc_threshold = gc_threshold
        self.operation_count = 0
        self.gc_stats = []

    @asynccontextmanager
    async def optimized_gc_context(self):
        """최적화된 GC 컨텍스트"""
        initial_memory = await self._get_memory_usage()

        try:
            yield
        finally:
            self.operation_count += 1

            # 임계치 도달 시 GC 실행
            if self.operation_count >= self.gc_threshold:
                await self._force_garbage_collection()
                self.operation_count = 0

            final_memory = await self._get_memory_usage()

            # GC 통계 수집
            if len(self.gc_stats) > 50:  # 최근 50개만 유지
                self.gc_stats = self.gc_stats[-50:]

    async def _force_garbage_collection(self):
        """강제 가비지 컬렉션"""
        start_time = time.time()
        before_memory = await self._get_memory_usage()

        # 단계적 GC 실행
        collected = []
        for generation in range(3):
            collected.append(gc.collect(generation))

        after_memory = await self._get_memory_usage()
        gc_time = (time.time() - start_time) * 1000

        stats = {
            "timestamp": time.time(),
            "before_memory_mb": before_memory.get("rss_mb", 0),
            "after_memory_mb": after_memory.get("rss_mb", 0),
            "memory_freed_mb": before_memory.get("rss_mb", 0) - after_memory.get("rss_mb", 0),
            "gc_time_ms": gc_time,
            "objects_collected": sum(collected)
        }

        self.gc_stats.append(stats)

        logger.debug(
            f"GC completed: freed {stats['memory_freed_mb']:.1f}MB, "
            f"collected {stats['objects_collected']} objects in {gc_time:.1f}ms"
        )

    async def _get_memory_usage(self) -> Dict[str, float]:
        """메모리 사용량 조회"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()

            return {
                "rss_mb": memory_info.rss / 1024 / 1024,
                "vms_mb": memory_info.vms / 1024 / 1024,
                "percent": process.memory_percent()
            }
        except ImportError:
            return {"rss_mb": 0, "vms_mb": 0, "percent": 0}

    def get_gc_stats(self) -> Dict[str, Any]:
        """GC 통계 반환"""
        if not self.gc_stats:
            return {"no_data": True}

        recent_stats = self.gc_stats[-10:]

        return {
            "total_gc_cycles": len(self.gc_stats),
            "avg_memory_freed_mb": sum(s["memory_freed_mb"] for s in recent_stats) / len(recent_stats),
            "avg_gc_time_ms": sum(s["gc_time_ms"] for s in recent_stats) / len(recent_stats),
            "total_objects_collected": sum(s["objects_collected"] for s in self.gc_stats),
            "operation_count_since_last_gc": self.operation_count
        }

class MemoryMonitor:
    """메모리 사용량 모니터링"""

    def __init__(self, alert_threshold_mb: int = 1024):
        """
        Args:
            alert_threshold_mb: 알람 임계치 (MB)
        """
        self.alert_threshold = alert_threshold_mb
        self.memory_history = []
        self.alerts_sent = []

    async def check_memory_usage(self) -> Dict[str, Any]:
        """메모리 사용량 체크 및 알람"""
        try:
            current_usage = await self._get_current_usage()

            # 히스토리 업데이트
            current_usage["timestamp"] = time.time()
            self.memory_history.append(current_usage)

            # 최근 100개 기록만 유지
            if len(self.memory_history) > 100:
                self.memory_history = self.memory_history[-100:]

            # 알람 체크
            if current_usage["rss_mb"] > self.alert_threshold:
                await self._send_memory_alert(current_usage)

            return {
                "current_usage": current_usage,
                "status": "normal" if current_usage["rss_mb"] <= self.alert_threshold else "high",
                "trend": self._calculate_memory_trend()
            }

        except Exception as e:
            logger.error(f"Memory monitoring failed: {e}")
            return {"error": str(e)}

    async def _get_current_usage(self) -> Dict[str, float]:
        """현재 메모리 사용량"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()

            return {
                "rss_mb": memory_info.rss / 1024 / 1024,
                "vms_mb": memory_info.vms / 1024 / 1024,
                "percent": process.memory_percent(),
                "available_mb": psutil.virtual_memory().available / 1024 / 1024
            }
        except ImportError:
            return {"rss_mb": 0, "vms_mb": 0, "percent": 0, "available_mb": 0}

    async def _send_memory_alert(self, usage: Dict[str, float]):
        """메모리 알람 발송"""
        alert_time = time.time()

        # 최근 5분 내 동일 알람 방지
        recent_alerts = [
            alert for alert in self.alerts_sent
            if alert_time - alert["timestamp"] < 300
        ]

        if not recent_alerts:
            alert = {
                "timestamp": alert_time,
                "memory_mb": usage["rss_mb"],
                "threshold_mb": self.alert_threshold,
                "percent": usage["percent"]
            }

            self.alerts_sent.append(alert)

            logger.warning(
                f"Memory usage high: {usage['rss_mb']:.1f}MB "
                f"({usage['percent']:.1f}%) exceeds threshold {self.alert_threshold}MB"
            )

            # 자동 가비지 컬렉션 트리거
            gc.collect()

    def _calculate_memory_trend(self) -> str:
        """메모리 사용량 트렌드 계산"""
        if len(self.memory_history) < 2:
            return "insufficient_data"

        recent_5 = self.memory_history[-5:]
        if len(recent_5) < 2:
            return "insufficient_data"

        # 선형 회귀로 트렌드 계산
        x_values = list(range(len(recent_5)))
        y_values = [entry["rss_mb"] for entry in recent_5]

        n = len(recent_5)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x2 = sum(x * x for x in x_values)

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)

        if slope > 5:  # 5MB 이상 증가 추세
            return "increasing"
        elif slope < -5:  # 5MB 이상 감소 추세
            return "decreasing"
        else:
            return "stable"

    def get_memory_summary(self) -> Dict[str, Any]:
        """메모리 모니터링 요약"""
        if not self.memory_history:
            return {"no_data": True}

        recent_usage = self.memory_history[-10:]

        return {
            "current_usage": self.memory_history[-1] if self.memory_history else {},
            "avg_usage_mb": sum(entry["rss_mb"] for entry in recent_usage) / len(recent_usage),
            "peak_usage_mb": max(entry["rss_mb"] for entry in self.memory_history),
            "trend": self._calculate_memory_trend(),
            "alerts_count": len(self.alerts_sent),
            "last_alert": self.alerts_sent[-1] if self.alerts_sent else None
        }

# 전역 메모리 최적화 인스턴스들
_global_quantizer = None
_global_streaming_processor = None
_global_gc_optimizer = None
_global_memory_monitor = None

def get_embedding_quantizer() -> EmbeddingQuantizer:
    """전역 임베딩 양자화 인스턴스"""
    global _global_quantizer
    if _global_quantizer is None:
        _global_quantizer = EmbeddingQuantizer(quantization_bits=8)
    return _global_quantizer

def get_streaming_processor() -> StreamingResultProcessor:
    """전역 스트리밍 프로세서 인스턴스"""
    global _global_streaming_processor
    if _global_streaming_processor is None:
        _global_streaming_processor = StreamingResultProcessor(chunk_size=10)
    return _global_streaming_processor

def get_gc_optimizer() -> GarbageCollectionOptimizer:
    """전역 GC 최적화 인스턴스"""
    global _global_gc_optimizer
    if _global_gc_optimizer is None:
        _global_gc_optimizer = GarbageCollectionOptimizer(gc_threshold=100)
    return _global_gc_optimizer

async def get_memory_monitor() -> MemoryMonitor:
    """전역 메모리 모니터 인스턴스"""
    global _global_memory_monitor
    if _global_memory_monitor is None:
        _global_memory_monitor = MemoryMonitor(alert_threshold_mb=1024)
    return _global_memory_monitor