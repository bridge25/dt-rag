"""
Ingestion Pipeline Component Tests

Tests the document ingestion pipeline components:
- Parser factory and format support
- Intelligent chunking
- PII detection

@TEST:INGESTION-001
"""

import pytest
import time
from apps.ingestion.parsers import ParserFactory, ParserError
from apps.ingestion.chunking import IntelligentChunker, ChunkingError
from apps.ingestion.pii import PIIDetector, PIIType


class TestIngestionPipelineStandalone:

    def test_parser_factory_txt(self):
        parser = ParserFactory.get_parser("txt")
        assert parser is not None
        assert parser.supports_format("txt")

    def test_txt_parser_basic(self):
        parser = ParserFactory.get_parser("txt")

        sample_text = "This is a test document. It has multiple sentences. Testing parsing functionality."
        file_content = sample_text.encode("utf-8")

        parsed_text = parser.parse(file_content, "test.txt")

        assert parsed_text == sample_text
        assert len(parsed_text) > 0

    def test_txt_parser_empty_content(self):
        parser = ParserFactory.get_parser("txt")

        empty_content = b""

        with pytest.raises(ParserError, match="empty content"):
            parser.parse(empty_content, "empty.txt")

    def test_intelligent_chunker_basic(self):
        chunker = IntelligentChunker(chunk_size=500, overlap_size=128)

        text = "This is the first sentence. This is the second sentence. This is the third sentence."

        chunks = chunker.chunk_text(text)

        assert len(chunks) > 0
        for chunk in chunks:
            assert chunk.token_count <= 500
            assert len(chunk.text) > 0

    def test_intelligent_chunker_sentence_boundary(self):
        chunker = IntelligentChunker(chunk_size=500, overlap_size=128)

        text = "First sentence. Second sentence. Third sentence. Fourth sentence. Fifth sentence."

        chunks = chunker.chunk_text(text)

        preserved_rate = chunker.calculate_sentence_boundary_preservation_rate(chunks)

        assert preserved_rate >= 0.0
        assert preserved_rate <= 1.0

    def test_intelligent_chunker_empty_text(self):
        chunker = IntelligentChunker()

        with pytest.raises(ChunkingError, match="empty"):
            chunker.chunk_text("")

    def test_pii_detector_phone_number(self):
        detector = PIIDetector()

        text = "My phone number is 010-1234-5678 for contact."

        matches = detector.detect_pii(text)

        assert len(matches) >= 1
        pii_types = [match.pii_type for match in matches]
        assert PIIType.PHONE_NUMBER in pii_types
        assert any("010-1234-5678" in match.original_text for match in matches)

    def test_pii_detector_email(self):
        detector = PIIDetector()

        text = "Contact me at test@example.com for more info."

        matches = detector.detect_pii(text)

        assert len(matches) == 1
        assert matches[0].pii_type == PIIType.EMAIL
        assert matches[0].original_text == "test@example.com"

    def test_pii_detector_multiple_types(self):
        detector = PIIDetector()

        text = "Call 010-1234-5678 or email test@example.com"

        matches = detector.detect_pii(text)

        assert len(matches) >= 2
        pii_types = [match.pii_type for match in matches]
        assert PIIType.PHONE_NUMBER in pii_types
        assert PIIType.EMAIL in pii_types

    def test_pii_masking(self):
        detector = PIIDetector()

        text = "My phone is 010-1234-5678"

        masked_text, matches = detector.detect_and_mask(text)

        assert "010-1234-5678" not in masked_text
        assert len(matches) >= 1
        mask_present = "[전화번호]" in masked_text or "[계좌번호]" in masked_text
        assert mask_present

    def test_pii_has_pii(self):
        detector = PIIDetector()

        text_with_pii = "Contact: 010-1234-5678"
        text_without_pii = "This is clean text"

        assert detector.has_pii(text_with_pii) is True
        assert detector.has_pii(text_without_pii) is False

    def test_pii_get_types(self):
        detector = PIIDetector()

        text = "Phone: 010-1234-5678, Email: test@example.com"

        pii_types = detector.get_pii_types(text)

        assert "phone_number" in pii_types
        assert "email" in pii_types
        assert len(pii_types) >= 2

    def test_end_to_end_pipeline(self):
        start_time = time.time()

        parser = ParserFactory.get_parser("txt")
        chunker = IntelligentChunker(chunk_size=500, overlap_size=128)
        pii_detector = PIIDetector()

        sample_text = """This is a comprehensive test document.
It contains multiple sentences to test chunking.
The document also includes PII data for testing.
Contact information: 010-1234-5678
Email address: user@example.com
This should be properly detected and masked.
The chunking should preserve sentence boundaries.
Each chunk should not exceed 500 tokens.
Overlap should be approximately 128 tokens."""

        file_content = sample_text.encode("utf-8")

        parsed_text = parser.parse(file_content, "test.txt")
        assert len(parsed_text) > 0

        chunks = chunker.chunk_text(parsed_text)
        assert len(chunks) > 0

        for chunk in chunks:
            assert chunk.token_count <= 500

        boundary_rate = chunker.calculate_sentence_boundary_preservation_rate(chunks)
        assert boundary_rate >= 0.0

        pii_matches = pii_detector.detect_pii(parsed_text)
        assert len(pii_matches) >= 2

        pii_types_found = [match.pii_type for match in pii_matches]
        assert PIIType.PHONE_NUMBER in pii_types_found
        assert PIIType.EMAIL in pii_types_found

        masked_text, _ = pii_detector.detect_and_mask(parsed_text)
        assert "010-1234-5678" not in masked_text
        assert "user@example.com" not in masked_text

        processing_time = (time.time() - start_time) * 1000

        assert processing_time < 1000

    def test_chunking_with_pii_content(self):
        chunker = IntelligentChunker(chunk_size=500, overlap_size=128)
        pii_detector = PIIDetector()

        text = "First paragraph with phone 010-1111-2222. Second paragraph with email test@test.com. Third paragraph clean."

        chunks = chunker.chunk_text(text)

        for chunk in chunks:
            if pii_detector.has_pii(chunk.text):
                pii_types = pii_detector.get_pii_types(chunk.text)
                assert len(pii_types) > 0

    def test_parser_unsupported_format(self):
        with pytest.raises(ParserError, match="Unsupported file format"):
            ParserFactory.get_parser("xyz")

    def test_parser_supports_format(self):
        assert ParserFactory.supports_format("txt") is True
        assert ParserFactory.supports_format("TXT") is True
        assert ParserFactory.supports_format("xyz") is False

    def test_parser_get_supported_formats(self):
        formats = ParserFactory.get_supported_formats()

        assert "txt" in formats
        assert "pdf" in formats
        assert "docx" in formats
        assert "html" in formats
        assert "csv" in formats

    def test_chunker_token_count_accuracy(self):
        chunker = IntelligentChunker()

        text = "Hello world!"
        token_count = chunker.count_tokens(text)

        assert token_count > 0
        assert isinstance(token_count, int)

    def test_chunker_overlap_functionality(self):
        chunker = IntelligentChunker(chunk_size=50, overlap_size=10)

        long_text = ". ".join([f"Sentence number {i}" for i in range(20)])

        chunks = chunker.chunk_text(long_text)

        if len(chunks) > 1:
            for i in range(len(chunks) - 1):
                assert chunks[i].token_count <= 50
