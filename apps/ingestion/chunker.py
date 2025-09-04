"""
문서 청킹 시스템
500자 청크, 128자 오버랩으로 문장 경계 보존
"""

import re
import logging
from typing import List, Tuple
from uuid import uuid4

from .models import ChunkResult, DocumentMetadata

logger = logging.getLogger(__name__)


class DocumentChunker:
    """문서 청킹 클래스"""
    
    def __init__(self, chunk_size: int = 500, overlap_size: int = 128):
        self.chunk_size = chunk_size
        self.overlap_size = overlap_size
        self.logger = logger
        
        # 문장 구분 패턴 (한국어와 영어 모두 고려)
        self.sentence_pattern = re.compile(
            r'[.!?…]+\s+|[。！？]+\s*|[\n]{2,}',
            re.UNICODE
        )
    
    def chunk_document(self, text: str, metadata: DocumentMetadata) -> List[ChunkResult]:
        """문서를 청크로 분할"""
        try:
            if not text.strip():
                return []
            
            # 문장 단위 분할
            sentences = self._split_into_sentences(text)
            
            # 청크 생성
            chunks = self._create_chunks(sentences, text)
            
            # ChunkResult 객체로 변환
            chunk_results = []
            for i, (chunk_text, start_pos, end_pos) in enumerate(chunks):
                chunk_result = ChunkResult(
                    chunk_id=uuid4(),
                    text=chunk_text,
                    start_char=start_pos,
                    end_char=end_pos,
                    chunk_index=i,
                    metadata={
                        "doc_hash": metadata.doc_hash,
                        "doc_type": metadata.doc_type.value,
                        "filename": metadata.filename,
                        "chunk_size": len(chunk_text),
                        "sentence_count": len(self._split_into_sentences(chunk_text))
                    }
                )
                chunk_results.append(chunk_result)
            
            self.logger.info(f"문서 청킹 완료: {metadata.filename} -> {len(chunk_results)}개 청크")
            return chunk_results
            
        except Exception as e:
            self.logger.error(f"청킹 오류 ({metadata.filename}): {e}")
            return []
    
    def _split_into_sentences(self, text: str) -> List[Tuple[str, int, int]]:
        """텍스트를 문장으로 분할 (위치 정보 포함)"""
        sentences = []
        last_end = 0
        
        for match in self.sentence_pattern.finditer(text):
            sentence_end = match.start()
            
            if sentence_end > last_end:
                sentence_text = text[last_end:sentence_end].strip()
                if sentence_text:
                    sentences.append((sentence_text, last_end, sentence_end))
            
            last_end = match.end()
        
        # 마지막 문장 처리
        if last_end < len(text):
            sentence_text = text[last_end:].strip()
            if sentence_text:
                sentences.append((sentence_text, last_end, len(text)))
        
        return sentences
    
    def _create_chunks(self, sentences: List[Tuple[str, int, int]], original_text: str) -> List[Tuple[str, int, int]]:
        """문장들을 청크로 조합"""
        chunks = []
        current_chunk_sentences = []
        current_length = 0
        
        i = 0
        while i < len(sentences):
            sentence_text, sentence_start, sentence_end = sentences[i]
            sentence_length = len(sentence_text)
            
            # 현재 청크에 문장을 추가할 수 있는지 확인
            if current_length + sentence_length <= self.chunk_size:
                current_chunk_sentences.append((sentence_text, sentence_start, sentence_end))
                current_length += sentence_length + 1  # 공백 포함
                i += 1
            else:
                # 현재 청크가 비어있지 않으면 저장
                if current_chunk_sentences:
                    chunk = self._build_chunk(current_chunk_sentences, original_text)
                    chunks.append(chunk)
                    
                    # 오버랩을 위한 문장들 계산
                    overlap_sentences = self._get_overlap_sentences(
                        current_chunk_sentences, self.overlap_size
                    )
                    
                    # 다음 청크를 오버랩 문장들로 시작
                    current_chunk_sentences = overlap_sentences
                    current_length = sum(len(s[0]) for s in overlap_sentences) + len(overlap_sentences)
                else:
                    # 단일 문장이 청크 크기를 초과하는 경우
                    # 문장을 강제로 분할
                    chunk = self._split_long_sentence(sentence_text, sentence_start, sentence_end)
                    chunks.append(chunk)
                    i += 1
        
        # 마지막 청크 처리
        if current_chunk_sentences:
            chunk = self._build_chunk(current_chunk_sentences, original_text)
            chunks.append(chunk)
        
        return chunks
    
    def _build_chunk(self, sentences: List[Tuple[str, int, int]], original_text: str) -> Tuple[str, int, int]:
        """문장들로부터 청크 구성"""
        if not sentences:
            return "", 0, 0
        
        start_pos = sentences[0][1]
        end_pos = sentences[-1][2]
        
        # 원본 텍스트에서 해당 범위 추출 (공백 보존)
        chunk_text = original_text[start_pos:end_pos].strip()
        
        return chunk_text, start_pos, end_pos
    
    def _get_overlap_sentences(self, sentences: List[Tuple[str, int, int]], 
                              overlap_size: int) -> List[Tuple[str, int, int]]:
        """오버랩할 문장들 선택"""
        if not sentences:
            return []
        
        overlap_sentences = []
        current_length = 0
        
        # 뒤에서부터 오버랩 크기만큼 선택
        for sentence_text, sentence_start, sentence_end in reversed(sentences):
            sentence_length = len(sentence_text)
            
            if current_length + sentence_length <= overlap_size:
                overlap_sentences.insert(0, (sentence_text, sentence_start, sentence_end))
                current_length += sentence_length + 1
            else:
                break
        
        return overlap_sentences
    
    def _split_long_sentence(self, sentence: str, start_pos: int, end_pos: int) -> Tuple[str, int, int]:
        """긴 문장을 강제로 분할"""
        if len(sentence) <= self.chunk_size:
            return sentence, start_pos, end_pos
        
        # 단어 경계에서 분할 시도
        words = sentence.split()
        truncated_words = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 <= self.chunk_size:
                truncated_words.append(word)
                current_length += len(word) + 1
            else:
                break
        
        if truncated_words:
            truncated_text = " ".join(truncated_words)
            return truncated_text, start_pos, start_pos + len(truncated_text)
        else:
            # 단어도 너무 긴 경우 문자 단위로 자르기
            truncated_text = sentence[:self.chunk_size]
            return truncated_text, start_pos, start_pos + len(truncated_text)
    
    def get_chunk_stats(self, chunks: List[ChunkResult]) -> dict:
        """청킹 통계 정보"""
        if not chunks:
            return {}
        
        chunk_sizes = [len(chunk.text) for chunk in chunks]
        
        return {
            "total_chunks": len(chunks),
            "avg_chunk_size": sum(chunk_sizes) / len(chunk_sizes),
            "min_chunk_size": min(chunk_sizes),
            "max_chunk_size": max(chunk_sizes),
            "total_characters": sum(chunk_sizes)
        }