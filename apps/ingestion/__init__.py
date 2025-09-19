"""
Document Ingestion Pipeline Package

문서 처리 파이프라인 패키지:
- 다중 포맷 문서 파싱
- 지능형 청킹 전략
- PII 필터링 및 데이터 보안
- 임베딩 생성 및 저장
- 메타데이터 추출
"""

from .document_parser import DocumentParserFactory, DocumentParser
from .chunking_strategy import ChunkingStrategy, SemanticChunker, TokenBasedChunker
from .pii_filter import PIIFilter, PIIDetector
from .ingestion_pipeline import IngestionPipeline, ProcessingResult

__version__ = "1.0.0"
__all__ = [
    "DocumentParserFactory",
    "DocumentParser",
    "ChunkingStrategy",
    "SemanticChunker",
    "TokenBasedChunker",
    "PIIFilter",
    "PIIDetector",
    "IngestionPipeline",
    "ProcessingResult"
]