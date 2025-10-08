import time
import json
from apps.ingestion.parsers import ParserFactory
from apps.ingestion.chunking import IntelligentChunker
from apps.ingestion.pii import PIIDetector, PIIType


def test_ingestion_pipeline_metrics():

    parser = ParserFactory.get_parser("txt")
    chunker = IntelligentChunker(chunk_size=500, overlap_size=128)
    pii_detector = PIIDetector()

    sample_text = """This is a comprehensive test document for ingestion pipeline.
It contains multiple sentences to test chunking functionality.
The document also includes PII data for testing detection accuracy.
Contact information: 010-1234-5678 for urgent matters.
Email address: user@example.com for general inquiries.
Additional phone: 010-9876-5432 for technical support.
This should be properly detected and masked by the PII detector.
The chunking should preserve sentence boundaries whenever possible.
Each chunk should not exceed 500 tokens as configured.
Overlap should be approximately 128 tokens for context preservation.
Testing with a longer document to trigger multiple chunks.
This is sentence number twelve in the test document.
This is sentence number thirteen to add more content.
Final sentence number fourteen for completion."""

    start_time = time.time()

    file_content = sample_text.encode("utf-8")

    parsed_text = parser.parse(file_content, "metrics_test.txt")

    chunks = chunker.chunk_text(parsed_text)

    boundary_rate = chunker.calculate_sentence_boundary_preservation_rate(chunks)

    pii_matches = pii_detector.detect_pii(parsed_text)

    masked_text, _ = pii_detector.detect_and_mask(parsed_text)

    processing_time = (time.time() - start_time) * 1000

    metrics = {
        "parsing": {
            "input_size_bytes": len(file_content),
            "output_size_chars": len(parsed_text),
            "success": len(parsed_text) > 0
        },
        "chunking": {
            "total_chunks": len(chunks),
            "avg_tokens_per_chunk": sum(c.token_count for c in chunks) / len(chunks),
            "max_tokens_in_chunk": max(c.token_count for c in chunks),
            "min_tokens_in_chunk": min(c.token_count for c in chunks),
            "sentence_boundary_preservation_rate": boundary_rate,
            "chunks_preserving_boundaries": sum(1 for c in chunks if c.sentence_boundary_preserved),
            "configured_chunk_size": chunker.chunk_size,
            "configured_overlap": chunker.overlap_size
        },
        "pii_detection": {
            "total_pii_found": len(pii_matches),
            "unique_pii_types": len(set(m.pii_type for m in pii_matches)),
            "pii_types_detected": [m.pii_type.value for m in pii_matches],
            "phone_numbers_detected": sum(1 for m in pii_matches if m.pii_type == PIIType.PHONE_NUMBER),
            "emails_detected": sum(1 for m in pii_matches if m.pii_type == PIIType.EMAIL),
            "masking_successful": "010-1234-5678" not in masked_text and "user@example.com" not in masked_text
        },
        "performance": {
            "total_processing_time_ms": processing_time,
            "throughput_bytes_per_sec": (len(file_content) / processing_time) * 1000 if processing_time > 0 else 0
        }
    }

    print("\n" + "="*80)
    print("INGESTION PIPELINE METRICS REPORT")
    print("="*80)
    print(json.dumps(metrics, indent=2))
    print("="*80)

    assert metrics["parsing"]["success"]
    assert metrics["chunking"]["total_chunks"] > 0
    assert metrics["chunking"]["max_tokens_in_chunk"] <= 500
    assert 0.0 <= metrics["chunking"]["sentence_boundary_preservation_rate"] <= 1.0
    assert metrics["pii_detection"]["total_pii_found"] >= 2
    assert metrics["pii_detection"]["masking_successful"]
    assert metrics["performance"]["total_processing_time_ms"] < 1000


def test_chunking_boundary_preservation_detailed():

    chunker = IntelligentChunker(chunk_size=500, overlap_size=128)

    test_cases = [
        {
            "name": "Short text (single chunk)",
            "text": "This is a short text. It has only two sentences.",
            "expected_chunks": 1
        },
        {
            "name": "Medium text (multiple chunks)",
            "text": ". ".join([f"Sentence number {i} with some content" for i in range(20)]),
            "expected_chunks": ">=1"
        },
        {
            "name": "Text with long sentence",
            "text": "Short sentence. " + " ".join(["word"] * 200) + ". Another short sentence.",
            "expected_chunks": ">=1"
        }
    ]

    results = []

    for test_case in test_cases:
        chunks = chunker.chunk_text(test_case["text"])
        boundary_rate = chunker.calculate_sentence_boundary_preservation_rate(chunks)

        result = {
            "test_case": test_case["name"],
            "total_chunks": len(chunks),
            "boundary_preservation_rate": boundary_rate,
            "max_tokens": max(c.token_count for c in chunks),
            "chunks_detail": [
                {
                    "tokens": c.token_count,
                    "boundary_preserved": c.sentence_boundary_preserved,
                    "text_preview": c.text[:50] + "..." if len(c.text) > 50 else c.text
                }
                for c in chunks
            ]
        }

        results.append(result)

        assert len(chunks) > 0
        assert all(c.token_count <= 500 for c in chunks)

    print("\n" + "="*80)
    print("CHUNKING BOUNDARY PRESERVATION DETAILED REPORT")
    print("="*80)
    print(json.dumps(results, indent=2))
    print("="*80)


def test_pii_detection_accuracy():

    detector = PIIDetector()

    test_cases = [
        {
            "name": "Phone number (Korean format)",
            "text": "Contact: 010-1234-5678",
            "expected_pii_types": [PIIType.PHONE_NUMBER],
            "should_mask": "010-1234-5678"
        },
        {
            "name": "Email address",
            "text": "Send to: test@example.com",
            "expected_pii_types": [PIIType.EMAIL],
            "should_mask": "test@example.com"
        },
        {
            "name": "Multiple PII types",
            "text": "Contact 010-1111-2222 or test@test.com",
            "expected_pii_types": [PIIType.PHONE_NUMBER, PIIType.EMAIL],
            "should_mask": "010-1111-2222"
        },
        {
            "name": "No PII",
            "text": "This is clean text without any personal information",
            "expected_pii_types": [],
            "should_mask": None
        }
    ]

    results = []

    for test_case in test_cases:
        matches = detector.detect_pii(test_case["text"])
        masked_text, _ = detector.detect_and_mask(test_case["text"])

        detected_types = [m.pii_type for m in matches]

        result = {
            "test_case": test_case["name"],
            "original_text": test_case["text"],
            "pii_found": len(matches),
            "detected_types": [t.value for t in detected_types],
            "masked_text": masked_text,
            "masking_successful": test_case["should_mask"] not in masked_text if test_case["should_mask"] else True
        }

        results.append(result)

        for expected_type in test_case["expected_pii_types"]:
            assert expected_type in detected_types, f"Expected {expected_type} not found in {detected_types}"

        if test_case["should_mask"]:
            assert test_case["should_mask"] not in masked_text

    print("\n" + "="*80)
    print("PII DETECTION ACCURACY REPORT")
    print("="*80)
    print(json.dumps(results, indent=2))
    print("="*80)


if __name__ == "__main__":
    test_ingestion_pipeline_metrics()
    test_chunking_boundary_preservation_detailed()
    test_pii_detection_accuracy()
