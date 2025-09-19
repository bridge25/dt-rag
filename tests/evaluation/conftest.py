"""
Pytest configuration and shared fixtures for evaluation framework tests
"""
import pytest
import asyncio
import tempfile
import sys
import os
from pathlib import Path

# Add evaluation module to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'apps', 'evaluation'))


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_directory():
    """Create a temporary directory for test files"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def sample_config():
    """Sample configuration for testing"""
    return {
        "ragas_engine": {
            "use_openai": True,
            "timeout_seconds": 300,
            "metrics": {
                "faithfulness": {
                    "threshold": 0.85,
                    "weight": 0.30
                },
                "answer_relevancy": {
                    "threshold": 0.80,
                    "weight": 0.25
                },
                "context_precision": {
                    "threshold": 0.75,
                    "weight": 0.25
                },
                "context_recall": {
                    "threshold": 0.80,
                    "weight": 0.20
                }
            }
        },
        "golden_dataset": {
            "quality_thresholds": {
                "min_annotation_agreement": 0.8,
                "min_completeness": 0.95,
                "min_consistency": 0.9,
                "min_diversity": 0.7,
                "min_quality_score": 0.8
            },
            "constraints": {
                "min_query_length": 10,
                "max_query_length": 500,
                "min_answer_length": 20,
                "max_answer_length": 2000
            }
        },
        "ab_testing": {
            "default_significance_level": 0.05,
            "default_statistical_power": 0.80,
            "default_minimum_detectable_effect": 0.05
        },
        "orchestrator": {
            "max_concurrent_jobs": 3,
            "quality_gate_enforcement": True,
            "auto_retry_failed_jobs": True,
            "max_retry_attempts": 2
        }
    }


@pytest.fixture
def mock_openai_embeddings():
    """Mock OpenAI embeddings for testing"""
    import numpy as np

    def mock_embed(texts):
        # Return random embeddings for testing
        return [np.random.rand(384).tolist() for _ in texts]

    return mock_embed


@pytest.fixture
def sample_taxonomy_data():
    """Sample taxonomy data for testing"""
    return {
        "AI": {
            "Machine Learning": {
                "Supervised Learning": ["Classification", "Regression"],
                "Unsupervised Learning": ["Clustering", "Dimensionality Reduction"],
                "Deep Learning": ["Neural Networks", "CNN", "RNN"]
            },
            "Natural Language Processing": {
                "Text Processing": ["Tokenization", "Parsing"],
                "Language Understanding": ["NER", "Sentiment Analysis"],
                "Text Generation": ["RAG", "Summarization"]
            },
            "Computer Vision": {
                "Image Processing": ["Filtering", "Enhancement"],
                "Object Detection": ["YOLO", "R-CNN"],
                "Image Generation": ["GAN", "Diffusion Models"]
            }
        },
        "Data Science": {
            "Statistics": ["Descriptive", "Inferential"],
            "Data Analysis": ["EDA", "Visualization"],
            "Big Data": ["Distributed Computing", "Data Warehousing"]
        }
    }


@pytest.fixture
def mock_rag_responses():
    """Mock RAG responses for testing"""
    from core.ragas_engine import RAGResponse

    return [
        RAGResponse(
            answer="Machine learning is a subset of artificial intelligence.",
            retrieved_docs=[
                {"content": "ML is part of AI", "score": 0.9},
                {"content": "Algorithms learn from data", "score": 0.8}
            ],
            confidence=0.85,
            processing_time=1.2,
            metadata={"query_type": "definition"}
        ),
        RAGResponse(
            answer="Deep learning uses neural networks with multiple layers.",
            retrieved_docs=[
                {"content": "Deep learning architecture", "score": 0.88},
                {"content": "Neural network layers", "score": 0.82}
            ],
            confidence=0.91,
            processing_time=1.5,
            metadata={"query_type": "explanation"}
        )
    ]


@pytest.fixture
def mock_dt_rag_pipeline():
    """Mock dt-rag pipeline for integration testing"""
    from unittest.mock import Mock, AsyncMock

    pipeline = Mock()
    pipeline.execute = AsyncMock()

    async def mock_execute(request):
        response = Mock()
        response.answer = f"Mock answer for: {request.query}"
        response.sources = [
            {"content": "Mock source 1", "score": 0.85},
            {"content": "Mock source 2", "score": 0.80}
        ]
        response.confidence = 0.85
        response.processing_time = 1.0
        response.metadata = {"pipeline_version": "test"}
        return response

    pipeline.execute = mock_execute
    return pipeline


@pytest.fixture
def performance_test_data():
    """Large dataset for performance testing"""
    queries = []
    expected_answers = []
    expected_contexts = []

    domains = ["AI", "ML", "NLP", "CV", "Data Science"]
    difficulties = ["beginner", "intermediate", "advanced"]

    for i in range(100):
        domain = domains[i % len(domains)]
        difficulty = difficulties[i % len(difficulties)]

        queries.append(f"Test query {i} about {domain}")
        expected_answers.append(f"Expected answer {i} for {domain} question")
        expected_contexts.append([
            f"Context 1 for {domain}",
            f"Context 2 for {domain}"
        ])

    return {
        "queries": queries,
        "expected_answers": expected_answers,
        "expected_contexts": expected_contexts,
        "domains": domains,
        "difficulties": difficulties
    }


@pytest.fixture
def database_mock():
    """Mock database connection for testing"""
    from unittest.mock import AsyncMock, Mock

    db = Mock()
    db.execute = AsyncMock()
    db.fetch = AsyncMock()
    db.fetchone = AsyncMock()
    db.fetchall = AsyncMock()

    # Mock common query results
    db.fetchall.return_value = [
        {"id": "test_1", "content": "Test document 1", "score": 0.85},
        {"id": "test_2", "content": "Test document 2", "score": 0.80}
    ]

    return db


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to handle markers"""
    if config.getoption("--runslow"):
        # Run all tests including slow ones
        return

    skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)


def pytest_addoption(parser):
    """Add command line options"""
    parser.addoption(
        "--runslow",
        action="store_true",
        default=False,
        help="run slow tests"
    )
    parser.addoption(
        "--runintegration",
        action="store_true",
        default=False,
        help="run integration tests"
    )


@pytest.fixture(autouse=True)
def cleanup_temp_files():
    """Automatically cleanup temporary files after each test"""
    yield
    # Cleanup code runs after each test
    import gc
    import tempfile

    # Force garbage collection
    gc.collect()

    # Clean up any remaining temporary files
    try:
        temp_dir = tempfile.gettempdir()
        for file_path in Path(temp_dir).glob("pytest-*"):
            if file_path.is_file():
                file_path.unlink(missing_ok=True)
            elif file_path.is_dir():
                import shutil
                shutil.rmtree(file_path, ignore_errors=True)
    except Exception:
        # Ignore cleanup errors
        pass