"""
Unit tests for database module (apps.api.database)

This test module provides comprehensive coverage for database-related functionality
including connection management, data access objects, and search operations.
"""
# @TEST:EMBED-001 | SPEC: .moai/specs/SPEC-EMBED-001/spec.md

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from datetime import datetime
import uuid
from typing import Dict, Any, List

# Import the modules under test
from apps.api.database import (
    DatabaseManager,
    TaxonomyDAO,
    SearchDAO,
    ClassifyDAO,
    EmbeddingService,
    BM25Scorer,
    CrossEncoderReranker,
    SearchMetrics,
    init_database,
    test_database_connection,
    setup_search_system
)


class TestDatabaseManager:
    """Test cases for DatabaseManager class"""

    @pytest.fixture
    def db_manager(self):
        """Create DatabaseManager instance for testing"""
        return DatabaseManager()

    @pytest.mark.unit
    async def test_init_database_success(self, db_manager):
        """Test successful database initialization"""
        with patch.object(db_manager.engine, 'begin') as mock_begin:
            mock_conn = AsyncMock()
            mock_begin.return_value.__aenter__.return_value = mock_conn

            result = await db_manager.init_database()

            assert result is True
            mock_begin.assert_called_once()

    @pytest.mark.unit
    async def test_init_database_failure(self, db_manager):
        """Test database initialization failure"""
        with patch.object(db_manager.engine, 'begin') as mock_begin:
            mock_begin.side_effect = Exception("Connection failed")

            result = await db_manager.init_database()

            assert result is False

    @pytest.mark.unit
    async def test_get_session(self, db_manager):
        """Test database session creation"""
        session = db_manager.get_session()

        # Should return a session factory
        assert callable(session)

    @pytest.mark.unit
    async def test_test_connection_success(self, db_manager):
        """Test successful database connection test"""
        with patch.object(db_manager, 'async_session') as mock_session_factory:
            mock_session = AsyncMock()
            mock_session_factory.return_value.__aenter__.return_value = mock_session
            mock_session.execute.return_value = Mock()

            result = await db_manager.test_connection()

            assert result is True
            mock_session.execute.assert_called_once()

    @pytest.mark.unit
    async def test_test_connection_failure(self, db_manager):
        """Test database connection test failure"""
        with patch.object(db_manager, 'async_session') as mock_session_factory:
            mock_session_factory.side_effect = Exception("Connection failed")

            result = await db_manager.test_connection()

            assert result is False


class TestTaxonomyDAO:
    """Test cases for TaxonomyDAO class"""

    @pytest.mark.unit
    async def test_get_tree_with_existing_data(self, mock_async_session):
        """Test getting taxonomy tree with existing data"""
        # Mock the database session and query result
        mock_session = mock_async_session.return_value
        mock_result = Mock()
        mock_result.fetchall.return_value = [
            (1, "AI", ["AI"], 1),
            (2, "RAG", ["AI", "RAG"], 1),
            (3, "ML", ["AI", "ML"], 1)
        ]
        mock_session.execute.return_value = mock_result

        with patch('apps.api.database.db_manager.async_session', return_value=mock_async_session):
            tree = await TaxonomyDAO.get_tree("1")

            assert len(tree) == 3
            assert tree[0]["label"] == "AI"
            assert tree[0]["version"] == 1
            assert tree[0]["node_id"] == 1

    @pytest.mark.unit
    async def test_get_tree_with_empty_data(self, mock_async_session):
        """Test getting taxonomy tree with no existing data (triggers default insertion)"""
        mock_session = mock_async_session.return_value

        # First query returns empty, second query returns default data
        mock_result_empty = Mock()
        mock_result_empty.fetchall.return_value = []

        mock_result_with_data = Mock()
        mock_result_with_data.fetchall.return_value = [
            (1, "AI", ["AI"], 1),
            (2, "RAG", ["AI", "RAG"], 1)
        ]

        mock_session.execute.side_effect = [
            mock_result_empty,  # First query (empty)
            None,  # Insert operations
            None,
            None,
            None,
            None,
            mock_result_with_data  # Second query (with data)
        ]

        with patch('apps.api.database.db_manager.async_session', return_value=mock_async_session):
            tree = await TaxonomyDAO.get_tree("1")

            assert len(tree) >= 1
            assert tree[0]["label"] in ["AI", "RAG"]

    @pytest.mark.unit
    async def test_get_tree_with_database_error(self, mock_async_session):
        """Test getting taxonomy tree with database error (fallback)"""
        mock_session = mock_async_session.return_value
        mock_session.execute.side_effect = Exception("Database error")

        with patch('apps.api.database.db_manager.async_session', return_value=mock_async_session):
            tree = await TaxonomyDAO.get_tree("1")

            # Should return fallback tree
            assert len(tree) >= 1
            assert tree[0]["label"] == "AI"
            assert "children" in tree[0]


class TestEmbeddingService:
    """Test cases for EmbeddingService class"""

    @pytest.mark.unit
    async def test_generate_embedding_dummy_mode(self):
        """Test embedding generation in dummy mode"""
        embedding = await EmbeddingService.generate_embedding("test text", "dummy")

        assert isinstance(embedding, list)
        assert len(embedding) == 1536  # EMBEDDING_DIMENSIONS
        assert all(isinstance(x, float) for x in embedding)

    @pytest.mark.unit
    async def test_generate_embedding_no_api_key(self):
        """Test embedding generation without API key (falls back to dummy)"""
        with patch('apps.api.database.OPENAI_API_KEY', None):
            embedding = await EmbeddingService.generate_embedding("test text")

            assert isinstance(embedding, list)
            assert len(embedding) == 1536

    @pytest.mark.unit
    async def test_generate_embedding_api_success(self):
        """Test successful embedding generation via API"""
        mock_embedding = [0.1] * 1536

        with patch('apps.api.database.OPENAI_API_KEY', 'test-key'):
            with patch('httpx.AsyncClient') as mock_client:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "data": [{"embedding": mock_embedding}]
                }
                mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

                embedding = await EmbeddingService.generate_embedding("test text")

                assert embedding == mock_embedding

    @pytest.mark.unit
    async def test_generate_embedding_api_failure(self):
        """Test embedding generation API failure (falls back to dummy)"""
        with patch('apps.api.database.OPENAI_API_KEY', 'test-key'):
            with patch('httpx.AsyncClient') as mock_client:
                mock_response = Mock()
                mock_response.status_code = 500
                mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

                embedding = await EmbeddingService.generate_embedding("test text")

                assert isinstance(embedding, list)
                assert len(embedding) == 1536

    @pytest.mark.unit
    async def test_generate_batch_embeddings(self):
        """Test batch embedding generation"""
        texts = ["text 1", "text 2", "text 3"]

        with patch.object(EmbeddingService, 'generate_embedding') as mock_generate:
            mock_generate.side_effect = [
                [0.1] * 1536,
                [0.2] * 1536,
                [0.3] * 1536
            ]

            embeddings = await EmbeddingService.generate_batch_embeddings(texts, batch_size=2)

            assert len(embeddings) == 3
            assert mock_generate.call_count == 3

    @pytest.mark.unit
    def test_get_dummy_embedding_consistency(self):
        """Test dummy embedding consistency for same text"""
        text = "consistent test text"

        embedding1 = EmbeddingService._get_dummy_embedding(text)
        embedding2 = EmbeddingService._get_dummy_embedding(text)

        assert embedding1 == embedding2
        assert len(embedding1) == 1536


class TestBM25Scorer:
    """Test cases for BM25Scorer class"""

    @pytest.mark.unit
    def test_preprocess_text_basic(self):
        """Test basic text preprocessing"""
        text = "This is a TEST document with Special characters! 123"
        tokens = BM25Scorer.preprocess_text(text)

        assert "this" not in tokens  # Removed stopword
        assert "test" in tokens
        assert "document" in tokens
        assert "special" in tokens
        assert "characters" in tokens
        assert "123" in tokens

    @pytest.mark.unit
    def test_preprocess_text_korean(self):
        """Test Korean text preprocessing"""
        text = "이것은 테스트 문서입니다. RAG 시스템을 테스트합니다."
        tokens = BM25Scorer.preprocess_text(text)

        assert "이것" not in tokens  # Removed stopword
        assert "테스트" in tokens
        assert "문서입니다" in tokens
        assert "rag" in tokens
        assert "시스템" not in tokens  # Should be "시스템을"

    @pytest.mark.unit
    def test_calculate_bm25_score_basic(self):
        """Test basic BM25 score calculation"""
        query_tokens = ["test", "document"]
        doc_tokens = ["this", "is", "a", "test", "document", "for", "testing"]
        corpus_stats = {
            "avg_doc_length": 10,
            "total_docs": 100,
            "term_doc_freq": {"test": 20, "document": 30}
        }

        score = BM25Scorer.calculate_bm25_score(query_tokens, doc_tokens, corpus_stats)

        assert isinstance(score, float)
        assert score >= 0.0

    @pytest.mark.unit
    def test_calculate_bm25_score_no_match(self):
        """Test BM25 score calculation with no matching terms"""
        query_tokens = ["nonexistent", "terms"]
        doc_tokens = ["completely", "different", "words"]
        corpus_stats = {
            "avg_doc_length": 10,
            "total_docs": 100,
            "term_doc_freq": {}
        }

        score = BM25Scorer.calculate_bm25_score(query_tokens, doc_tokens, corpus_stats)

        assert score == 0.0

    @pytest.mark.unit
    def test_calculate_bm25_score_empty_input(self):
        """Test BM25 score calculation with empty input"""
        score = BM25Scorer.calculate_bm25_score([], [], {})
        assert score == 0.0

        score = BM25Scorer.calculate_bm25_score(["test"], [], {})
        assert score == 0.0

        score = BM25Scorer.calculate_bm25_score([], ["test"], {})
        assert score == 0.0


class TestCrossEncoderReranker:
    """Test cases for CrossEncoderReranker class"""

    @pytest.mark.unit
    def test_rerank_results_basic(self):
        """Test basic result reranking"""
        query = "test query"
        search_results = [
            {
                "text": "This is a test document about queries",
                "metadata": {"bm25_score": 0.8, "vector_score": 0.6}
            },
            {
                "text": "Another document",
                "metadata": {"bm25_score": 0.3, "vector_score": 0.9}
            },
            {
                "text": "Test query document with matching terms",
                "metadata": {"bm25_score": 0.5, "vector_score": 0.7}
            }
        ]

        reranked = CrossEncoderReranker.rerank_results(query, search_results, top_k=2)

        assert len(reranked) == 2
        assert all("score" in result for result in reranked)
        # Results should be sorted by score in descending order
        assert reranked[0]["score"] >= reranked[1]["score"]

    @pytest.mark.unit
    def test_rerank_results_empty_list(self):
        """Test reranking with empty results list"""
        reranked = CrossEncoderReranker.rerank_results("query", [], top_k=5)

        assert reranked == []

    @pytest.mark.unit
    def test_calculate_query_overlap(self):
        """Test query overlap calculation"""
        query = "test machine learning"
        text = "This is a test of machine learning algorithms"

        overlap = CrossEncoderReranker._calculate_query_overlap(query, text)

        assert isinstance(overlap, float)
        assert 0.0 <= overlap <= 1.0
        assert overlap > 0.5  # Should have good overlap

    @pytest.mark.unit
    def test_calculate_query_overlap_no_match(self):
        """Test query overlap with no matching words"""
        overlap = CrossEncoderReranker._calculate_query_overlap(
            "completely different", "no matching words here"
        )

        assert overlap == 0.0

    @pytest.mark.unit
    def test_calculate_query_overlap_empty_query(self):
        """Test query overlap with empty query"""
        overlap = CrossEncoderReranker._calculate_query_overlap("", "some text")

        assert overlap == 0.0


class TestSearchDAO:
    """Test cases for SearchDAO class"""

    @pytest.mark.unit
    async def test_hybrid_search_optimization_available(self):
        """Test hybrid search with optimization modules available"""
        query = "test search query"
        filters = {"canonical_in": [["AI", "RAG"]]}

        # Mock the optimization modules
        mock_optimizer = AsyncMock()
        mock_optimizer.execute_parallel_search.return_value = (
            [{"chunk_id": "1", "text": "bm25 result"}],  # bm25_results
            [{"chunk_id": "2", "text": "vector result"}],  # vector_results
            Mock(total_time=0.1, parallel_time=0.05, memory_usage=100)  # metrics
        )
        mock_optimizer.execute_fusion_with_concurrency_control.return_value = [
            {"chunk_id": "1", "text": "combined result", "score": 0.8}
        ]
        mock_optimizer.execute_cpu_intensive_task.return_value = [
            {"chunk_id": "1", "text": "final result", "score": 0.9, "metadata": {}}
        ]

        with patch('apps.api.database.get_async_optimizer', return_value=mock_optimizer):
            with patch('apps.api.database.get_gc_optimizer') as mock_gc:
                with patch('apps.api.database.get_concurrency_controller') as mock_cc:
                    mock_gc.return_value.optimized_gc_context.return_value.__aenter__ = AsyncMock()
                    mock_gc.return_value.optimized_gc_context.return_value.__aexit__ = AsyncMock()
                    mock_cc.return_value.controlled_execution.return_value.__aenter__ = AsyncMock()
                    mock_cc.return_value.controlled_execution.return_value.__aexit__ = AsyncMock()

                    with patch('apps.api.database.db_manager.async_session') as mock_session_factory:
                        mock_session = AsyncMock()
                        mock_session_factory.return_value.__aenter__.return_value = mock_session

                        results = await SearchDAO.hybrid_search(query, filters)

                        assert len(results) >= 0
                        if results:
                            assert "metadata" in results[0]
                            assert results[0]["metadata"]["optimization_enabled"] is True

    @pytest.mark.unit
    async def test_hybrid_search_fallback_to_legacy(self):
        """Test hybrid search fallback to legacy mode"""
        query = "test search query"

        with patch('apps.api.database.get_async_optimizer', side_effect=ImportError()):
            with patch.object(SearchDAO, '_execute_legacy_hybrid_search') as mock_legacy:
                mock_legacy.return_value = [{"chunk_id": "1", "text": "legacy result"}]

                results = await SearchDAO.hybrid_search(query)

                mock_legacy.assert_called_once()
                assert results == [{"chunk_id": "1", "text": "legacy result"}]

    @pytest.mark.unit
    def test_build_filter_clause_empty_filters(self):
        """Test filter clause building with no filters"""
        clause = SearchDAO._build_filter_clause(None)
        assert clause == ""

        clause = SearchDAO._build_filter_clause({})
        assert clause == ""

    @pytest.mark.unit
    def test_build_filter_clause_canonical_in_filter(self):
        """Test filter clause building with canonical_in filter"""
        filters = {"canonical_in": [["AI", "RAG"], ["AI", "ML"]]}

        clause = SearchDAO._build_filter_clause(filters)

        assert "AND" in clause
        assert "dt.path" in clause

    @pytest.mark.unit
    def test_build_filter_clause_doc_type_filter(self):
        """Test filter clause building with doc_type filter"""
        filters = {"doc_type": ["text/plain", "application/pdf"]}

        clause = SearchDAO._build_filter_clause(filters)

        assert "AND" in clause
        assert "d.content_type" in clause

    @pytest.mark.unit
    def test_combine_search_results_basic(self):
        """Test combining BM25 and vector search results"""
        bm25_results = [
            {
                "chunk_id": "1",
                "text": "bm25 result",
                "metadata": {"bm25_score": 0.8, "vector_score": 0.0}
            }
        ]
        vector_results = [
            {
                "chunk_id": "1",
                "text": "same result",
                "metadata": {"bm25_score": 0.0, "vector_score": 0.7}
            },
            {
                "chunk_id": "2",
                "text": "vector only",
                "metadata": {"bm25_score": 0.0, "vector_score": 0.6}
            }
        ]

        combined = SearchDAO._combine_search_results(bm25_results, vector_results, 10)

        assert len(combined) == 2
        # First result should be hybrid (contains both scores)
        hybrid_result = next(r for r in combined if r["chunk_id"] == "1")
        assert hybrid_result["metadata"]["bm25_score"] == 0.8
        assert hybrid_result["metadata"]["vector_score"] == 0.7
        assert hybrid_result["metadata"]["source"] == "hybrid"

    @pytest.mark.unit
    def test_combine_search_results_no_overlap(self):
        """Test combining results with no overlap"""
        bm25_results = [{"chunk_id": "1", "metadata": {"bm25_score": 0.8, "vector_score": 0.0}}]
        vector_results = [{"chunk_id": "2", "metadata": {"bm25_score": 0.0, "vector_score": 0.7}}]

        combined = SearchDAO._combine_search_results(bm25_results, vector_results, 10)

        assert len(combined) == 2
        chunk_ids = {r["chunk_id"] for r in combined}
        assert chunk_ids == {"1", "2"}


class TestClassifyDAO:
    """Test cases for ClassifyDAO class"""

    @pytest.mark.unit
    async def test_classify_text_rag_domain(self):
        """Test text classification for RAG domain"""
        text = "This document discusses retrieval augmented generation and vector embeddings for RAG systems."

        result = await ClassifyDAO.classify_text(text)

        assert result["canonical"] == ["AI", "RAG"]
        assert result["label"] == "RAG Systems"
        assert isinstance(result["confidence"], float)
        assert 0.0 <= result["confidence"] <= 1.0
        assert isinstance(result["reasoning"], list)
        assert len(result["reasoning"]) > 0
        assert isinstance(result["node_id"], int)
        assert result["version"] == 1

    @pytest.mark.unit
    async def test_classify_text_ml_domain(self):
        """Test text classification for ML domain"""
        text = "Machine learning model training with neural networks and algorithms for classification tasks."

        result = await ClassifyDAO.classify_text(text)

        assert result["canonical"] == ["AI", "ML"]
        assert result["label"] == "Machine Learning"
        assert isinstance(result["confidence"], float)
        assert 0.0 <= result["confidence"] <= 1.0

    @pytest.mark.unit
    async def test_classify_text_taxonomy_domain(self):
        """Test text classification for Taxonomy domain"""
        text = "Classification hierarchy and taxonomy ontology for category organization systems."

        result = await ClassifyDAO.classify_text(text)

        assert result["canonical"] == ["AI", "Taxonomy"]
        assert result["label"] == "Taxonomy Systems"
        assert isinstance(result["confidence"], float)

    @pytest.mark.unit
    async def test_classify_text_general_domain(self):
        """Test text classification for general/unknown domain"""
        text = "This is some random text without specific domain indicators."

        result = await ClassifyDAO.classify_text(text)

        assert result["canonical"] == ["AI", "General"]
        assert result["label"] == "General AI"
        assert result["confidence"] == 0.6

    @pytest.mark.unit
    async def test_classify_text_with_hint_paths(self):
        """Test text classification with hint paths"""
        text = "RAG system implementation"
        hint_paths = [["AI", "RAG"], ["AI", "ML"]]

        result = await ClassifyDAO.classify_text(text, hint_paths)

        # Should match RAG and get confidence boost
        assert result["canonical"] == ["AI", "RAG"]
        assert result["confidence"] > 0.6  # Should be boosted
        assert any("Hint path match" in reason for reason in result["reasoning"])

    @pytest.mark.unit
    async def test_classify_text_error_handling(self):
        """Test classification error handling"""
        # Simulate an error in classification
        with patch('apps.api.database.logger') as mock_logger:
            # Force an error by patching a method that will be called
            with patch.object(str, 'lower', side_effect=Exception("Test error")):
                result = await ClassifyDAO.classify_text("test text")

                # Should return fallback classification
                assert result["canonical"] == ["AI", "General"]
                assert result["label"] == "General AI"
                assert result["confidence"] == 0.5
                assert any("분류 오류로 인한 기본 분류" in reason for reason in result["reasoning"])
                mock_logger.error.assert_called_once()


class TestSearchMetrics:
    """Test cases for SearchMetrics class"""

    @pytest.fixture
    def search_metrics(self):
        """Create SearchMetrics instance for testing"""
        return SearchMetrics()

    @pytest.mark.unit
    def test_record_search_basic(self, search_metrics):
        """Test basic search recording"""
        search_metrics.record_search("hybrid", 0.15, error=False)

        assert len(search_metrics.search_latencies) == 1
        assert search_metrics.search_latencies[0] == 0.15
        assert search_metrics.search_counts["hybrid"] == 1
        assert search_metrics.error_counts == 0

    @pytest.mark.unit
    def test_record_search_with_error(self, search_metrics):
        """Test search recording with error"""
        search_metrics.record_search("bm25", 0.25, error=True)

        assert search_metrics.search_counts["bm25"] == 1
        assert search_metrics.error_counts == 1

    @pytest.mark.unit
    def test_record_search_memory_management(self, search_metrics):
        """Test search recording memory management (keeps last 1000)"""
        # Record more than 1000 searches
        for i in range(1050):
            search_metrics.record_search("vector", 0.1 + i * 0.001)

        assert len(search_metrics.search_latencies) == 1000
        assert search_metrics.search_counts["vector"] == 1050

    @pytest.mark.unit
    def test_get_metrics_with_data(self, search_metrics):
        """Test getting metrics with recorded data"""
        # Record some searches
        search_metrics.record_search("hybrid", 0.1)
        search_metrics.record_search("hybrid", 0.2)
        search_metrics.record_search("bm25", 0.15, error=True)

        metrics = search_metrics.get_metrics()

        assert "avg_latency" in metrics
        assert metrics["avg_latency"] == 0.15  # (0.1 + 0.2 + 0.15) / 3
        assert "p95_latency" in metrics
        assert "total_searches" in metrics
        assert metrics["total_searches"] == 3
        assert "search_counts" in metrics
        assert "error_rate" in metrics
        assert metrics["error_rate"] == 1/3
        assert "period_start" in metrics

    @pytest.mark.unit
    def test_get_metrics_no_data(self, search_metrics):
        """Test getting metrics with no recorded data"""
        metrics = search_metrics.get_metrics()

        assert metrics == {"no_data": True}

    @pytest.mark.unit
    def test_reset_metrics(self, search_metrics):
        """Test resetting metrics"""
        # Record some data
        search_metrics.record_search("hybrid", 0.1)
        search_metrics.record_search("bm25", 0.2, error=True)

        # Reset
        old_start_time = search_metrics.last_reset
        search_metrics.reset()

        # Check everything is cleared
        assert len(search_metrics.search_latencies) == 0
        assert search_metrics.search_counts == {"bm25": 0, "vector": 0, "hybrid": 0}
        assert search_metrics.error_counts == 0
        assert search_metrics.last_reset > old_start_time


class TestUtilityFunctions:
    """Test cases for utility functions"""

    @pytest.mark.unit
    async def test_init_database_success(self):
        """Test database initialization utility function"""
        with patch('apps.api.database.db_manager.init_database') as mock_init:
            mock_init.return_value = True

            result = await init_database()

            assert result is True
            mock_init.assert_called_once()

    @pytest.mark.unit
    async def test_test_database_connection_success(self):
        """Test database connection test utility function"""
        with patch('apps.api.database.db_manager.test_connection') as mock_test:
            mock_test.return_value = True

            result = await test_database_connection()

            assert result is True
            mock_test.assert_called_once()

    @pytest.mark.unit
    async def test_setup_search_system_success(self):
        """Test search system setup success"""
        with patch('apps.api.database.db_manager.async_session') as mock_session_factory:
            mock_session = AsyncMock()
            mock_session_factory.return_value.__aenter__.return_value = mock_session

            with patch('apps.api.database.init_database', return_value=True):
                with patch.object(SearchDAO, 'optimize_search_indices') as mock_optimize:
                    mock_optimize.return_value = {"success": True, "indices_created": ["idx1", "idx2"]}

                    with patch.object(SearchDAO, 'get_search_analytics') as mock_analytics:
                        mock_analytics.return_value = {"statistics": {"total_chunks": 10}}

                        result = await setup_search_system()

                        assert result is True
                        mock_optimize.assert_called_once()

    @pytest.mark.unit
    async def test_setup_search_system_failure(self):
        """Test search system setup failure"""
        with patch('apps.api.database.init_database', return_value=False):
            result = await setup_search_system()

            assert result is False

    @pytest.mark.unit
    @pytest.mark.skip(reason="get_search_performance_metrics removed - use monitoring.search_metrics instead")
    async def test_get_search_performance_metrics_success(self):
        """Test getting search performance metrics successfully"""
        pass

    @pytest.mark.unit
    @pytest.mark.skip(reason="get_search_performance_metrics removed - use monitoring.search_metrics instead")
    async def test_get_search_performance_metrics_failure(self):
        """Test getting search performance metrics with database error"""
        pass


# Integration-style tests that test multiple components together
class TestAgentModel:
    """Test cases for Agent ORM model"""

    @pytest.mark.unit
    async def test_agent_model_creation(self):
        """Test Agent model instance creation with default values"""
        from apps.api.database import Agent
        import uuid

        agent_id = uuid.uuid4()
        taxonomy_node_ids = [str(uuid.uuid4()), str(uuid.uuid4())]

        agent = Agent(
            agent_id=agent_id,
            name="Test Agent",
            taxonomy_node_ids=taxonomy_node_ids,
            taxonomy_version="1.0.0",
            level=1,
            current_xp=0,
            total_documents=0,
            total_chunks=0,
            coverage_percent=0.0,
            total_queries=0,
            successful_queries=0,
            avg_faithfulness=0.0,
            avg_response_time_ms=0.0
        )

        assert agent.agent_id == agent_id
        assert agent.name == "Test Agent"
        assert agent.taxonomy_node_ids == taxonomy_node_ids
        assert agent.taxonomy_version == "1.0.0"
        assert agent.level == 1
        assert agent.current_xp == 0
        assert agent.total_documents == 0
        assert agent.total_chunks == 0
        assert agent.coverage_percent == 0.0
        assert agent.total_queries == 0
        assert agent.successful_queries == 0
        assert agent.avg_faithfulness == 0.0
        assert agent.avg_response_time_ms == 0.0

    @pytest.mark.unit
    async def test_agent_model_with_custom_values(self):
        """Test Agent model with custom values"""
        from apps.api.database import Agent
        import uuid

        agent = Agent(
            agent_id=uuid.uuid4(),
            name="Custom Agent",
            taxonomy_node_ids=[str(uuid.uuid4())],
            taxonomy_version="2.0.0",
            level=3,
            current_xp=150,
            coverage_percent=75.5,
            retrieval_config={"top_k": 10, "strategy": "semantic"}
        )

        assert agent.level == 3
        assert agent.current_xp == 150
        assert agent.coverage_percent == 75.5
        assert agent.retrieval_config == {"top_k": 10, "strategy": "semantic"}


class TestDatabaseIntegration:
    """Integration tests for database components"""

    @pytest.mark.unit
    async def test_embedding_and_search_integration(self):
        """Test integration between embedding service and search"""
        # Generate an embedding
        text = "test document about machine learning"
        embedding = await EmbeddingService.generate_embedding(text, "dummy")

        # Create mock search results that would use this embedding
        mock_results = [
            {
                "text": text,
                "metadata": {"bm25_score": 0.7, "vector_score": 0.8}
            }
        ]

        # Test reranking with the results
        reranked = CrossEncoderReranker.rerank_results("machine learning", mock_results)

        assert len(reranked) == 1
        assert reranked[0]["score"] > 0
        assert isinstance(embedding, list)
        assert len(embedding) == 1536

    @pytest.mark.unit
    async def test_classification_and_taxonomy_integration(self):
        """Test integration between classification and taxonomy systems"""
        # Classify a text
        text = "This document is about retrieval augmented generation systems"
        classification = await ClassifyDAO.classify_text(text)

        # Verify classification format matches taxonomy expectations
        assert isinstance(classification["canonical"], list)
        assert len(classification["canonical"]) >= 2  # Should have at least AI + subcategory
        assert classification["canonical"][0] == "AI"  # Root should be AI

        # Test that the classification can be used as a taxonomy path
        path = classification["canonical"]
        assert isinstance(path, list)
        assert all(isinstance(p, str) for p in path)

    @pytest.mark.unit
    def test_bm25_and_cross_encoder_integration(self):
        """Test integration between BM25 scoring and cross-encoder reranking"""
        # Preprocess text with BM25
        text = "Machine learning algorithms for document classification"
        tokens = BM25Scorer.preprocess_text(text)

        # Calculate BM25 score
        corpus_stats = {"avg_doc_length": 10, "total_docs": 100, "term_doc_freq": {}}
        bm25_score = BM25Scorer.calculate_bm25_score(["machine", "learning"], tokens, corpus_stats)

        # Create search result with BM25 score
        search_result = {
            "text": text,
            "metadata": {"bm25_score": bm25_score, "vector_score": 0.8}
        }

        # Test reranking
        reranked = CrossEncoderReranker.rerank_results("machine learning", [search_result])

        assert len(reranked) == 1
        assert "score" in reranked[0]
        assert reranked[0]["score"] > 0