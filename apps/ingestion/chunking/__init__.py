"""
Chunking module for document processing.

@CODE:INGESTION-001
"""
from .intelligent_chunker import IntelligentChunker, Chunk, ChunkingError

__all__ = ["IntelligentChunker", "Chunk", "ChunkingError"]
