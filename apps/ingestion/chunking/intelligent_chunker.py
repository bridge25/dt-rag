import re
from dataclasses import dataclass
from typing import List

try:
    import tiktoken

    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False


@dataclass
class Chunk:
    text: str
    token_count: int
    start_position: int
    end_position: int
    sentence_boundary_preserved: bool


class ChunkingError(Exception):
    pass


class IntelligentChunker:
    def __init__(
        self,
        chunk_size: int = 500,
        overlap_size: int = 128,
        encoding_name: str = "cl100k_base",
    ):
        if not TIKTOKEN_AVAILABLE:
            raise ChunkingError("tiktoken not installed")

        self.chunk_size = chunk_size
        self.overlap_size = overlap_size
        self.encoding = tiktoken.get_encoding(encoding_name)

    def count_tokens(self, text: str) -> int:
        return len(self.encoding.encode(text))

    def split_into_sentences(self, text: str) -> List[str]:
        sentence_endings = r"[.!?。！？]\s+"
        sentences = re.split(sentence_endings, text)

        sentences = [s.strip() for s in sentences if s.strip()]

        return sentences

    def chunk_text(self, text: str) -> List[Chunk]:
        if not text or not text.strip():
            raise ChunkingError("Input text is empty")

        sentences = self.split_into_sentences(text)

        if not sentences:
            raise ChunkingError("No sentences found in text")

        chunks = []
        current_chunk_sentences = []
        current_tokens = 0
        position = 0

        for sentence in sentences:
            sentence_tokens = self.count_tokens(sentence)

            if sentence_tokens > self.chunk_size:
                if current_chunk_sentences:
                    chunk_text = " ".join(current_chunk_sentences)
                    chunks.append(
                        Chunk(
                            text=chunk_text,
                            token_count=current_tokens,
                            start_position=position - current_tokens,
                            end_position=position,
                            sentence_boundary_preserved=True,
                        )
                    )
                    current_chunk_sentences = []
                    current_tokens = 0

                words = sentence.split()
                word_chunk = []
                word_tokens = 0

                for word in words:
                    word_token_count = self.count_tokens(word)

                    if word_tokens + word_token_count > self.chunk_size:
                        if word_chunk:
                            chunk_text = " ".join(word_chunk)
                            chunks.append(
                                Chunk(
                                    text=chunk_text,
                                    token_count=word_tokens,
                                    start_position=position,
                                    end_position=position + word_tokens,
                                    sentence_boundary_preserved=False,
                                )
                            )
                            position += word_tokens
                            word_chunk = []
                            word_tokens = 0

                    word_chunk.append(word)
                    word_tokens += word_token_count

                if word_chunk:
                    chunk_text = " ".join(word_chunk)
                    chunks.append(
                        Chunk(
                            text=chunk_text,
                            token_count=word_tokens,
                            start_position=position,
                            end_position=position + word_tokens,
                            sentence_boundary_preserved=False,
                        )
                    )
                    position += word_tokens

                continue

            if current_tokens + sentence_tokens > self.chunk_size:
                chunk_text = " ".join(current_chunk_sentences)
                chunks.append(
                    Chunk(
                        text=chunk_text,
                        token_count=current_tokens,
                        start_position=position - current_tokens,
                        end_position=position,
                        sentence_boundary_preserved=True,
                    )
                )

                overlap_sentences = []
                overlap_tokens = 0
                for sent in reversed(current_chunk_sentences):
                    sent_tokens = self.count_tokens(sent)
                    if overlap_tokens + sent_tokens > self.overlap_size:
                        break
                    overlap_sentences.insert(0, sent)
                    overlap_tokens += sent_tokens

                current_chunk_sentences = overlap_sentences
                current_tokens = overlap_tokens

            current_chunk_sentences.append(sentence)
            current_tokens += sentence_tokens
            position += sentence_tokens

        if current_chunk_sentences:
            chunk_text = " ".join(current_chunk_sentences)
            chunks.append(
                Chunk(
                    text=chunk_text,
                    token_count=current_tokens,
                    start_position=position - current_tokens,
                    end_position=position,
                    sentence_boundary_preserved=True,
                )
            )

        return chunks

    def calculate_sentence_boundary_preservation_rate(
        self, chunks: List[Chunk]
    ) -> float:
        if not chunks:
            return 0.0

        preserved_count = sum(
            1 for chunk in chunks if chunk.sentence_boundary_preserved
        )
        return preserved_count / len(chunks)
