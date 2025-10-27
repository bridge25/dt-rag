import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from apps.search.hybrid_search_engine import HybridSearchEngine


class TestSQLInjectionPrevention:

    def test_build_filter_clause_taxonomy_injection(self):
        engine = HybridSearchEngine(enable_caching=False, enable_reranking=False)

        malicious_filters = {"taxonomy_paths": [["; DROP TABLE chunks; --"]]}

        filter_clause, params = engine._build_filter_clause(malicious_filters)

        assert "DROP" not in filter_clause
        assert "--" not in filter_clause
        assert len(params) == 0

    def test_build_filter_clause_content_type_injection(self):
        engine = HybridSearchEngine(enable_caching=False, enable_reranking=False)

        malicious_filters = {"content_types": ["text' OR '1'='1"]}

        filter_clause, params = engine._build_filter_clause(malicious_filters)

        assert "OR" not in filter_clause or len(params) == 0
        assert "'" not in str(params)

    def test_build_filter_clause_date_injection(self):
        engine = HybridSearchEngine(enable_caching=False, enable_reranking=False)

        malicious_filters = {"date_range": {"start": "2024-01-01' OR 1=1; --"}}

        filter_clause, params = engine._build_filter_clause(malicious_filters)

        assert "OR" not in filter_clause or "date_start" not in params
        assert "--" not in filter_clause

    def test_build_filter_clause_multiple_injections(self):
        engine = HybridSearchEngine(enable_caching=False, enable_reranking=False)

        malicious_filters = {
            "taxonomy_paths": [["'; DELETE FROM documents; --"]],
            "content_types": ["text' UNION SELECT * FROM users--"],
            "date_range": {
                "start": "2024-01-01' OR '1'='1",
                "end": "2024-12-31'; DROP TABLE embeddings; --",
            },
        }

        filter_clause, params = engine._build_filter_clause(malicious_filters)

        assert "DELETE" not in filter_clause
        assert "UNION" not in filter_clause
        assert "DROP" not in filter_clause
        assert (
            len([p for p in params.values() if "DROP" in str(p) or "DELETE" in str(p)])
            == 0
        )

    def test_build_filter_clause_valid_filters(self):
        engine = HybridSearchEngine(enable_caching=False, enable_reranking=False)

        valid_filters = {
            "taxonomy_paths": [["AI", "Machine_Learning"]],
            "content_types": ["article"],
            "date_range": {"start": "2024-01-01T00:00:00"},
        }

        filter_clause, params = engine._build_filter_clause(valid_filters)

        assert filter_clause != ""
        assert "taxonomy_path_0" in params
        assert "content_type_0" in params
        assert "date_start" in params

    def test_content_type_whitelist_validation(self):
        engine = HybridSearchEngine(enable_caching=False, enable_reranking=False)

        invalid_filters = {
            "content_types": [
                "application/x-executable",
                "text/plain; DROP TABLE",
                "../../etc/passwd",
            ]
        }

        filter_clause, params = engine._build_filter_clause(invalid_filters)

        assert len([k for k in params.keys() if k.startswith("content_type_")]) == 0
        assert "DROP" not in filter_clause

    def test_taxonomy_path_alphanumeric_validation(self):
        engine = HybridSearchEngine(enable_caching=False, enable_reranking=False)

        invalid_filters = {
            "taxonomy_paths": [
                ["../../../etc/passwd"],
                ["'; DROP TABLE chunks--"],
                ["'; DELETE FROM documents WHERE '1'='1"],
            ]
        }

        filter_clause, params = engine._build_filter_clause(invalid_filters)

        assert len([k for k in params.keys() if k.startswith("taxonomy_path_")]) == 0
        assert "DROP" not in filter_clause
        assert "DELETE" not in filter_clause

    def test_taxonomy_path_with_valid_segments(self):
        engine = HybridSearchEngine(enable_caching=False, enable_reranking=False)

        mixed_filters = {
            "taxonomy_paths": [
                ["valid_path", "'; DROP TABLE--"],
                ["AI", "Machine_Learning"],
            ]
        }

        filter_clause, params = engine._build_filter_clause(mixed_filters)

        assert "DROP" not in filter_clause
        assert len([k for k in params.keys() if k.startswith("taxonomy_path_")]) == 2
        param_values = [str(v) for v in params.values()]
        assert all("DROP" not in val for val in param_values)

    def test_date_format_validation(self):
        engine = HybridSearchEngine(enable_caching=False, enable_reranking=False)

        invalid_dates = [
            "not-a-date",
            "2024-13-45",
            "'; DROP TABLE--",
            "2024-01-01' OR '1'='1",
            "../../../etc/passwd",
        ]

        for invalid_date in invalid_dates:
            filters = {"date_range": {"start": invalid_date}}

            filter_clause, params = engine._build_filter_clause(filters)

            assert "DROP" not in filter_clause
            assert "date_start" not in params or params["date_start"] == invalid_date

    def test_parameterized_query_return_format(self):
        engine = HybridSearchEngine(enable_caching=False, enable_reranking=False)

        filters = {
            "taxonomy_paths": [["AI", "ML"]],
            "content_types": ["article"],
            "date_range": {"start": "2024-01-01T00:00:00"},
        }

        filter_clause, params = engine._build_filter_clause(filters)

        assert isinstance(filter_clause, str)
        assert isinstance(params, dict)
        assert filter_clause.startswith(" AND ")

    def test_empty_filters(self):
        engine = HybridSearchEngine(enable_caching=False, enable_reranking=False)

        filter_clause, params = engine._build_filter_clause({})

        assert filter_clause == ""
        assert params == {}
