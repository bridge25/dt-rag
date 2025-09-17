"""
Chunking Strategy Module

다양한 청킹 전략을 구현하는 모듈
- Sliding window chunking (고정 크기 + 중복)
- Semantic chunking (문장/단락 단위)
- Token-based chunking (토큰 기반)
- Adaptive chunking (내용 기반 적응형)
"""

import re
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import asyncio

# 토큰 카운팅
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False

# 문장 분할
try:
    import nltk
    from nltk.tokenize import sent_tokenize, word_tokenize
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False

# 한국어 처리
try:
    from kiwipiepy import Kiwi
    KIWI_AVAILABLE = True
except ImportError:
    KIWI_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class DocumentChunk:
    """문서 청크를 나타내는 클래스"""
    text: str
    start_idx: int
    end_idx: int
    chunk_index: int
    metadata: Dict[str, Any]
    token_count: Optional[int] = None

    def __post_init__(self):
        if self.token_count is None:
            self.token_count = self._count_tokens()

    def _count_tokens(self) -> int:
        """토큰 수 계산"""
        if TIKTOKEN_AVAILABLE:
            try:
                encoding = tiktoken.get_encoding("cl100k_base")
                return len(encoding.encode(self.text))
            except Exception:
                pass

        # 폴백: 단어 수로 추정 (영어 기준 1.3배)
        words = len(self.text.split())
        return int(words * 1.3)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'text': self.text,
            'start_idx': self.start_idx,
            'end_idx': self.end_idx,
            'chunk_index': self.chunk_index,
            'token_count': self.token_count,
            'metadata': self.metadata
        }

class ChunkingStrategy(ABC):
    """청킹 전략 추상 기본 클래스"""

    @abstractmethod
    async def chunk_text(self, text: str, metadata: Dict[str, Any] = None) -> List[DocumentChunk]:
        """텍스트를 청크로 분할"""
        pass

    def _clean_text(self, text: str) -> str:
        """텍스트 정리"""
        # 연속된 공백/탭/줄바꿈 정리
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        return text

    def _count_tokens(self, text: str) -> int:
        """토큰 수 계산"""
        if TIKTOKEN_AVAILABLE:
            try:
                encoding = tiktoken.get_encoding("cl100k_base")
                return len(encoding.encode(text))
            except Exception:
                pass

        # 폴백: 단어 수 기반 추정
        words = len(text.split())
        return int(words * 1.3)

class TokenBasedChunker(ChunkingStrategy):
    """토큰 기반 청킹"""

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 128,
        min_chunk_size: int = 50,
        encoding_name: str = "cl100k_base"
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        self.encoding_name = encoding_name

        # tiktoken 인코더 초기화
        if TIKTOKEN_AVAILABLE:
            try:
                self.encoder = tiktoken.get_encoding(encoding_name)
            except Exception:
                self.encoder = None
                logger.warning(f"tiktoken 인코더 '{encoding_name}' 로드 실패, 근사치 사용")
        else:
            self.encoder = None
            logger.warning("tiktoken 사용 불가, 단어 기반 근사치 사용")

    async def chunk_text(self, text: str, metadata: Dict[str, Any] = None) -> List[DocumentChunk]:
        if metadata is None:
            metadata = {}

        text = self._clean_text(text)
        if not text:
            return []

        chunks = []

        if self.encoder:
            # tiktoken 기반 정확한 토큰 청킹
            chunks = await self._chunk_by_tokens(text, metadata)
        else:
            # 단어 기반 근사 청킹
            chunks = await self._chunk_by_words(text, metadata)

        return chunks

    async def _chunk_by_tokens(self, text: str, metadata: Dict[str, Any]) -> List[DocumentChunk]:
        """tiktoken 기반 정확한 토큰 청킹"""
        tokens = self.encoder.encode(text)
        chunks = []

        start_idx = 0
        chunk_index = 0

        while start_idx < len(tokens):
            # 청크 끝 인덱스 계산
            end_idx = min(start_idx + self.chunk_size, len(tokens))

            # 토큰을 텍스트로 디코딩
            chunk_tokens = tokens[start_idx:end_idx]
            chunk_text = self.encoder.decode(chunk_tokens)

            # 문자 인덱스 계산 (근사치)
            char_start = int(start_idx / len(tokens) * len(text))
            char_end = int(end_idx / len(tokens) * len(text))

            # 최소 크기 확인
            if len(chunk_tokens) >= self.min_chunk_size:
                chunk_metadata = {
                    **metadata,
                    'chunking_strategy': 'token_based',
                    'token_start': start_idx,
                    'token_end': end_idx,
                    'original_text_length': len(text)
                }

                chunk = DocumentChunk(
                    text=chunk_text.strip(),
                    start_idx=char_start,
                    end_idx=char_end,
                    chunk_index=chunk_index,
                    metadata=chunk_metadata,
                    token_count=len(chunk_tokens)
                )
                chunks.append(chunk)
                chunk_index += 1

            # 다음 청크 시작 위치 (중복 고려)
            start_idx = max(start_idx + self.chunk_size - self.chunk_overlap, start_idx + 1)

            if start_idx >= len(tokens):
                break

        return chunks

    async def _chunk_by_words(self, text: str, metadata: Dict[str, Any]) -> List[DocumentChunk]:
        """단어 기반 근사 청킹"""
        words = text.split()
        # 토큰-단어 비율 추정 (영어 기준)
        words_per_chunk = int(self.chunk_size / 1.3)
        words_overlap = int(self.chunk_overlap / 1.3)

        chunks = []
        start_word_idx = 0
        chunk_index = 0

        while start_word_idx < len(words):
            # 청크 단어 범위
            end_word_idx = min(start_word_idx + words_per_chunk, len(words))
            chunk_words = words[start_word_idx:end_word_idx]

            if len(chunk_words) < self.min_chunk_size / 1.3:
                break

            chunk_text = ' '.join(chunk_words)

            # 문자 인덱스 계산
            char_start = len(' '.join(words[:start_word_idx]))
            if start_word_idx > 0:
                char_start += 1  # 공백 보정
            char_end = len(' '.join(words[:end_word_idx]))

            chunk_metadata = {
                **metadata,
                'chunking_strategy': 'word_based_approximation',
                'word_start': start_word_idx,
                'word_end': end_word_idx,
                'original_text_length': len(text)
            }

            chunk = DocumentChunk(
                text=chunk_text.strip(),
                start_idx=char_start,
                end_idx=char_end,
                chunk_index=chunk_index,
                metadata=chunk_metadata
            )
            chunks.append(chunk)
            chunk_index += 1

            # 다음 청크 시작 위치
            start_word_idx = max(start_word_idx + words_per_chunk - words_overlap, start_word_idx + 1)

        return chunks

class SemanticChunker(ChunkingStrategy):
    """의미 기반 청킹 (문장/단락 단위)"""

    def __init__(
        self,
        max_chunk_size: int = 500,
        min_chunk_size: int = 50,
        overlap_sentences: int = 1,
        prefer_paragraphs: bool = True,
        language: str = "english"
    ):
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.overlap_sentences = overlap_sentences
        self.prefer_paragraphs = prefer_paragraphs
        self.language = language

        # 한국어 처리기 초기화
        if language == "korean" and KIWI_AVAILABLE:
            self.kiwi = Kiwi()
        else:
            self.kiwi = None

        # NLTK 데이터 확인
        if NLTK_AVAILABLE:
            try:
                sent_tokenize("Test.")
            except LookupError:
                logger.warning("NLTK 문장 토크나이저 데이터가 없습니다. nltk.download('punkt') 실행 필요")

    async def chunk_text(self, text: str, metadata: Dict[str, Any] = None) -> List[DocumentChunk]:
        if metadata is None:
            metadata = {}

        text = self._clean_text(text)
        if not text:
            return []

        chunks = []

        if self.prefer_paragraphs:
            # 단락 기반 청킹 시도
            paragraphs = self._split_paragraphs(text)
            if len(paragraphs) > 1:
                chunks = await self._chunk_by_paragraphs(text, paragraphs, metadata)
            else:
                # 단락이 없으면 문장 기반
                chunks = await self._chunk_by_sentences(text, metadata)
        else:
            # 문장 기반 청킹
            chunks = await self._chunk_by_sentences(text, metadata)

        return chunks

    def _split_paragraphs(self, text: str) -> List[str]:
        """단락 분할"""
        # 연속된 줄바꿈을 단락 구분자로 사용
        paragraphs = re.split(r'\n\s*\n', text)
        return [p.strip() for p in paragraphs if p.strip()]

    def _split_sentences(self, text: str) -> List[str]:
        """문장 분할"""
        if self.language == "korean" and self.kiwi:
            # 한국어 문장 분할
            sentences = []
            for sent in self.kiwi.split_into_sents(text):
                sentences.append(sent.text.strip())
            return [s for s in sentences if s]

        elif NLTK_AVAILABLE:
            # NLTK 문장 분할
            try:
                sentences = sent_tokenize(text)
                return [s.strip() for s in sentences if s.strip()]
            except LookupError:
                pass

        # 폴백: 간단한 정규식 기반 문장 분할
        sentences = re.split(r'[.!?]+\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    async def _chunk_by_paragraphs(
        self,
        full_text: str,
        paragraphs: List[str],
        metadata: Dict[str, Any]
    ) -> List[DocumentChunk]:
        """단락 기반 청킹"""
        chunks = []
        current_chunk = ""
        current_start = 0
        chunk_index = 0

        for para in paragraphs:
            para_tokens = self._count_tokens(para)
            current_tokens = self._count_tokens(current_chunk)

            # 단락을 추가해도 크기 제한을 넘지 않는 경우
            if current_tokens + para_tokens <= self.max_chunk_size:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
            else:
                # 현재 청크 완료
                if current_chunk and self._count_tokens(current_chunk) >= self.min_chunk_size:
                    chunk_end = current_start + len(current_chunk)

                    chunk_metadata = {
                        **metadata,
                        'chunking_strategy': 'paragraph_based',
                        'original_text_length': len(full_text)
                    }

                    chunk = DocumentChunk(
                        text=current_chunk.strip(),
                        start_idx=current_start,
                        end_idx=chunk_end,
                        chunk_index=chunk_index,
                        metadata=chunk_metadata
                    )
                    chunks.append(chunk)
                    chunk_index += 1

                    current_start = chunk_end

                # 새 청크 시작
                current_chunk = para

        # 마지막 청크 처리
        if current_chunk and self._count_tokens(current_chunk) >= self.min_chunk_size:
            chunk_end = current_start + len(current_chunk)

            chunk_metadata = {
                **metadata,
                'chunking_strategy': 'paragraph_based',
                'original_text_length': len(full_text)
            }

            chunk = DocumentChunk(
                text=current_chunk.strip(),
                start_idx=current_start,
                end_idx=chunk_end,
                chunk_index=chunk_index,
                metadata=chunk_metadata
            )
            chunks.append(chunk)

        return chunks

    async def _chunk_by_sentences(self, text: str, metadata: Dict[str, Any]) -> List[DocumentChunk]:
        """문장 기반 청킹"""
        sentences = self._split_sentences(text)
        chunks = []

        current_sentences = []
        current_tokens = 0
        chunk_index = 0
        sent_start_idx = 0

        for i, sentence in enumerate(sentences):
            sent_tokens = self._count_tokens(sentence)

            # 문장 추가 가능한지 확인
            if current_tokens + sent_tokens <= self.max_chunk_size:
                current_sentences.append(sentence)
                current_tokens += sent_tokens
            else:
                # 현재 청크 완료
                if current_sentences and current_tokens >= self.min_chunk_size:
                    chunk_text = ' '.join(current_sentences)

                    # 문자 인덱스 계산
                    chunk_start = sent_start_idx
                    chunk_end = chunk_start + len(chunk_text)

                    chunk_metadata = {
                        **metadata,
                        'chunking_strategy': 'sentence_based',
                        'sentence_count': len(current_sentences),
                        'original_text_length': len(text)
                    }

                    chunk = DocumentChunk(
                        text=chunk_text.strip(),
                        start_idx=chunk_start,
                        end_idx=chunk_end,
                        chunk_index=chunk_index,
                        metadata=chunk_metadata,
                        token_count=current_tokens
                    )
                    chunks.append(chunk)
                    chunk_index += 1

                    # 오버랩 처리
                    if self.overlap_sentences > 0:
                        overlap_sents = current_sentences[-self.overlap_sentences:]
                        overlap_tokens = sum(self._count_tokens(s) for s in overlap_sents)
                        current_sentences = overlap_sents + [sentence]
                        current_tokens = overlap_tokens + sent_tokens
                    else:
                        current_sentences = [sentence]
                        current_tokens = sent_tokens

                    sent_start_idx = chunk_end
                else:
                    # 현재 청크가 너무 작으면 문장 추가
                    current_sentences = [sentence]
                    current_tokens = sent_tokens

        # 마지막 청크 처리
        if current_sentences and current_tokens >= self.min_chunk_size:
            chunk_text = ' '.join(current_sentences)
            chunk_end = sent_start_idx + len(chunk_text)

            chunk_metadata = {
                **metadata,
                'chunking_strategy': 'sentence_based',
                'sentence_count': len(current_sentences),
                'original_text_length': len(text)
            }

            chunk = DocumentChunk(
                text=chunk_text.strip(),
                start_idx=sent_start_idx,
                end_idx=chunk_end,
                chunk_index=chunk_index,
                metadata=chunk_metadata,
                token_count=current_tokens
            )
            chunks.append(chunk)

        return chunks

class SlidingWindowChunker(ChunkingStrategy):
    """슬라이딩 윈도우 청킹"""

    def __init__(
        self,
        window_size: int = 500,
        step_size: int = 372,  # 500 - 128 overlap
        min_chunk_size: int = 50
    ):
        self.window_size = window_size
        self.step_size = step_size
        self.min_chunk_size = min_chunk_size

    async def chunk_text(self, text: str, metadata: Dict[str, Any] = None) -> List[DocumentChunk]:
        if metadata is None:
            metadata = {}

        text = self._clean_text(text)
        if not text:
            return []

        chunks = []
        chunk_index = 0

        # 문자 단위로 슬라이딩
        for start in range(0, len(text), self.step_size):
            end = min(start + self.window_size, len(text))
            chunk_text = text[start:end].strip()

            # 최소 크기 확인
            if len(chunk_text) < self.min_chunk_size:
                continue

            # 단어 경계 조정 (마지막이 아닌 경우)
            if end < len(text):
                # 마지막 공백까지 포함하도록 조정
                last_space = chunk_text.rfind(' ')
                if last_space > len(chunk_text) * 0.8:  # 80% 이상 지점에서 찾은 경우만
                    chunk_text = chunk_text[:last_space]
                    end = start + last_space

            chunk_metadata = {
                **metadata,
                'chunking_strategy': 'sliding_window',
                'window_size': self.window_size,
                'step_size': self.step_size,
                'original_text_length': len(text)
            }

            chunk = DocumentChunk(
                text=chunk_text,
                start_idx=start,
                end_idx=end,
                chunk_index=chunk_index,
                metadata=chunk_metadata
            )
            chunks.append(chunk)
            chunk_index += 1

            # 텍스트 끝에 도달하면 종료
            if end >= len(text):
                break

        return chunks

class AdaptiveChunker(ChunkingStrategy):
    """적응형 청킹 (내용 기반)"""

    def __init__(
        self,
        target_chunk_size: int = 500,
        size_tolerance: float = 0.3,  # 30% 허용 오차
        min_chunk_size: int = 50,
        max_chunk_size: int = 800
    ):
        self.target_chunk_size = target_chunk_size
        self.size_tolerance = size_tolerance
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size

        # 섹션 헤딩 패턴
        self.heading_patterns = [
            r'^#{1,6}\s+.+$',  # Markdown 헤딩
            r'^\d+\.\s+.+$',   # 번호 목록
            r'^[A-Z][^.!?]*:$', # 대문자로 시작하는 제목
            r'^[-=]{3,}$',     # 구분선
        ]

    async def chunk_text(self, text: str, metadata: Dict[str, Any] = None) -> List[DocumentChunk]:
        if metadata is None:
            metadata = {}

        text = self._clean_text(text)
        if not text:
            return []

        # 구조적 경계 찾기
        boundaries = self._find_structural_boundaries(text)

        # 경계를 기반으로 청킹
        chunks = await self._chunk_by_boundaries(text, boundaries, metadata)

        return chunks

    def _find_structural_boundaries(self, text: str) -> List[int]:
        """구조적 경계점 찾기"""
        lines = text.split('\n')
        boundaries = [0]  # 텍스트 시작

        current_pos = 0
        for line in lines:
            current_pos += len(line) + 1  # +1 for newline

            # 헤딩 패턴 확인
            for pattern in self.heading_patterns:
                if re.match(pattern, line.strip(), re.MULTILINE):
                    boundaries.append(current_pos - len(line) - 1)
                    break

            # 빈 줄 연속 (단락 구분)
            if not line.strip():
                # 다음 비어있지 않은 줄까지 찾기
                next_pos = current_pos
                for next_line in lines[lines.index(line) + 1:]:
                    if next_line.strip():
                        boundaries.append(next_pos)
                        break
                    next_pos += len(next_line) + 1

        boundaries.append(len(text))  # 텍스트 끝

        # 중복 제거 및 정렬
        boundaries = sorted(list(set(boundaries)))
        return boundaries

    async def _chunk_by_boundaries(
        self,
        text: str,
        boundaries: List[int],
        metadata: Dict[str, Any]
    ) -> List[DocumentChunk]:
        """경계점 기반 청킹"""
        chunks = []
        chunk_index = 0

        i = 0
        while i < len(boundaries) - 1:
            start = boundaries[i]
            end = boundaries[i + 1]

            # 현재 섹션
            section_text = text[start:end].strip()
            section_tokens = self._count_tokens(section_text)

            # 목표 크기와 비교
            min_size = int(self.target_chunk_size * (1 - self.size_tolerance))
            max_size = int(self.target_chunk_size * (1 + self.size_tolerance))

            if section_tokens <= max_size and section_tokens >= min_size:
                # 적절한 크기: 그대로 사용
                if section_text:
                    chunk = self._create_chunk(
                        section_text, start, end, chunk_index, metadata, 'boundary_perfect'
                    )
                    chunks.append(chunk)
                    chunk_index += 1
                i += 1

            elif section_tokens < min_size:
                # 너무 작음: 다음 섹션과 병합
                combined_text = section_text
                combined_end = end
                j = i + 1

                while j < len(boundaries) - 1:
                    next_start = boundaries[j]
                    next_end = boundaries[j + 1]
                    next_text = text[next_start:next_end].strip()

                    if combined_text:
                        test_combined = combined_text + "\n\n" + next_text
                    else:
                        test_combined = next_text

                    test_tokens = self._count_tokens(test_combined)

                    if test_tokens <= self.max_chunk_size:
                        combined_text = test_combined
                        combined_end = next_end
                        j += 1
                    else:
                        break

                if combined_text and self._count_tokens(combined_text) >= self.min_chunk_size:
                    chunk = self._create_chunk(
                        combined_text, start, combined_end, chunk_index, metadata, 'boundary_merged'
                    )
                    chunks.append(chunk)
                    chunk_index += 1

                i = j

            else:
                # 너무 큼: 세분화
                sub_chunks = await self._split_large_section(
                    section_text, start, chunk_index, metadata
                )
                chunks.extend(sub_chunks)
                chunk_index += len(sub_chunks)
                i += 1

        return chunks

    async def _split_large_section(
        self,
        text: str,
        start_offset: int,
        start_chunk_index: int,
        metadata: Dict[str, Any]
    ) -> List[DocumentChunk]:
        """큰 섹션 분할"""
        # 문장 기준으로 분할
        semantic_chunker = SemanticChunker(
            max_chunk_size=self.target_chunk_size,
            min_chunk_size=self.min_chunk_size
        )

        sub_chunks = await semantic_chunker.chunk_text(text, metadata)

        # 인덱스 및 오프셋 조정
        result_chunks = []
        for i, chunk in enumerate(sub_chunks):
            adjusted_chunk = DocumentChunk(
                text=chunk.text,
                start_idx=chunk.start_idx + start_offset,
                end_idx=chunk.end_idx + start_offset,
                chunk_index=start_chunk_index + i,
                metadata={
                    **chunk.metadata,
                    'parent_strategy': 'adaptive',
                    'split_reason': 'oversized_section'
                },
                token_count=chunk.token_count
            )
            result_chunks.append(adjusted_chunk)

        return result_chunks

    def _create_chunk(
        self,
        text: str,
        start: int,
        end: int,
        chunk_index: int,
        metadata: Dict[str, Any],
        strategy_detail: str
    ) -> DocumentChunk:
        """청크 생성 헬퍼"""
        chunk_metadata = {
            **metadata,
            'chunking_strategy': 'adaptive',
            'strategy_detail': strategy_detail,
            'original_text_length': metadata.get('original_text_length', len(text))
        }

        return DocumentChunk(
            text=text,
            start_idx=start,
            end_idx=end,
            chunk_index=chunk_index,
            metadata=chunk_metadata
        )

class ChunkingStrategyFactory:
    """청킹 전략 팩토리"""

    STRATEGIES = {
        'token_based': TokenBasedChunker,
        'semantic': SemanticChunker,
        'sliding_window': SlidingWindowChunker,
        'adaptive': AdaptiveChunker
    }

    @classmethod
    def create_strategy(
        self,
        strategy_type: str,
        **kwargs
    ) -> ChunkingStrategy:
        """청킹 전략 생성"""
        if strategy_type not in self.STRATEGIES:
            raise ValueError(f"지원되지 않는 청킹 전략: {strategy_type}")

        strategy_class = self.STRATEGIES[strategy_type]
        return strategy_class(**kwargs)

    @classmethod
    def get_recommended_strategy(
        self,
        text_length: int,
        content_type: str = 'general'
    ) -> Tuple[str, Dict[str, Any]]:
        """콘텐츠 타입과 길이에 따른 추천 전략"""
        if content_type == 'code':
            return 'semantic', {
                'max_chunk_size': 800,
                'prefer_paragraphs': False,
                'language': 'english'
            }
        elif content_type == 'structured':
            return 'adaptive', {
                'target_chunk_size': 600,
                'size_tolerance': 0.2
            }
        elif text_length < 2000:
            return 'semantic', {
                'max_chunk_size': 400,
                'min_chunk_size': 100
            }
        elif text_length < 10000:
            return 'token_based', {
                'chunk_size': 500,
                'chunk_overlap': 128
            }
        else:
            return 'adaptive', {
                'target_chunk_size': 500,
                'size_tolerance': 0.3
            }

    @classmethod
    def get_available_strategies(self) -> List[str]:
        """사용 가능한 전략 목록"""
        return list(self.STRATEGIES.keys())

# 기본 청킹 전략 인스턴스
default_chunker = TokenBasedChunker()