"""
고성능 BM25 검색 엔진
Okapi BM25 알고리즘의 최적화된 구현
"""

import math
import re
from collections import defaultdict, Counter
from typing import List, Dict, Any, Optional, Tuple
import asyncio
import asyncpg
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

class BM25Engine:
    """고성능 BM25 검색 엔진"""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        Args:
            k1: Term frequency 조정 파라미터 (1.2-2.0 권장)
            b: Document length normalization (0.0-1.0)
        """
        self.k1 = k1
        self.b = b
        self.doc_freqs = {}  # term -> document frequency
        self.doc_lengths = {}  # doc_id -> length
        self.avg_doc_length = 0
        self.total_docs = 0
        self.corpus_stats_computed = False

    async def initialize_corpus_stats(self, session: AsyncSession):
        """코퍼스 통계 정보 초기화 (한 번만 실행)"""
        if self.corpus_stats_computed:
            return

        try:
            # 문서 길이 통계 계산
            length_query = text("""
                SELECT chunk_id, LENGTH(text) as doc_length
                FROM chunks
                WHERE text IS NOT NULL AND LENGTH(text) > 0
            """)

            result = await session.execute(length_query)
            rows = result.fetchall()

            total_length = 0
            for row in rows:
                doc_length = row.doc_length
                self.doc_lengths[row.chunk_id] = doc_length
                total_length += doc_length

            self.total_docs = len(rows)
            self.avg_doc_length = total_length / self.total_docs if self.total_docs > 0 else 0

            # 문서 빈도 계산 (Term frequency across documents)
            await self._compute_document_frequencies(session)

            self.corpus_stats_computed = True
            logger.info(f"BM25 corpus stats initialized: {self.total_docs} docs, avg_length: {self.avg_doc_length:.1f}")

        except Exception as e:
            logger.error(f"Failed to initialize corpus stats: {e}")

    async def _compute_document_frequencies(self, session: AsyncSession):
        """문서별 단어 빈도 계산"""
        try:
            # 모든 문서의 텍스트를 가져와서 단어 빈도 계산
            text_query = text("""
                SELECT chunk_id, text
                FROM chunks
                WHERE text IS NOT NULL AND LENGTH(text) > 10
                LIMIT 10000  -- 대용량 처리를 위한 제한
            """)

            result = await session.execute(text_query)
            rows = result.fetchall()

            doc_word_sets = {}
            for row in rows:
                words = self._tokenize(row.text)
                doc_word_sets[row.chunk_id] = set(words)

            # 각 단어가 나타나는 문서 수 계산
            word_doc_counts = defaultdict(int)
            for word_set in doc_word_sets.values():
                for word in word_set:
                    word_doc_counts[word] += 1

            self.doc_freqs = dict(word_doc_counts)
            logger.info(f"Computed document frequencies for {len(self.doc_freqs)} unique terms")

        except Exception as e:
            logger.error(f"Failed to compute document frequencies: {e}")

    def _tokenize(self, text: str) -> List[str]:
        """향상된 토크나이저"""
        # 소문자 변환 및 특수문자 제거
        text = text.lower()
        # 영어 단어와 한글 추출
        tokens = re.findall(r'\b[a-z]+\b|[가-힣]+', text)
        # 짧은 토큰 제거
        return [token for token in tokens if len(token) >= 2]

    async def search(
        self,
        session: AsyncSession,
        query: str,
        topk: int = 20,
        filters: Dict = None
    ) -> List[Dict[str, Any]]:
        """BM25 검색 수행"""
        # 코퍼스 통계 초기화
        await self.initialize_corpus_stats(session)

        # 쿼리 토크나이즈
        query_terms = self._tokenize(query)
        if not query_terms:
            return []

        # 후보 문서 필터링
        candidate_docs = await self._get_candidate_documents(session, query_terms, filters)

        # BM25 점수 계산
        scored_docs = []
        for doc in candidate_docs:
            score = self._calculate_bm25_score(doc, query_terms)
            if score > 0:
                doc['bm25_score'] = score
                doc['source'] = 'bm25'
                scored_docs.append(doc)

        # 점수순 정렬
        scored_docs.sort(key=lambda x: x['bm25_score'], reverse=True)
        return scored_docs[:topk]

    async def _get_candidate_documents(
        self,
        session: AsyncSession,
        query_terms: List[str],
        filters: Dict = None
    ) -> List[Dict[str, Any]]:
        """후보 문서 검색 (term matching 기반)"""
        try:
            # OR 조건으로 쿼리 생성
            where_conditions = []
            params = {}

            for i, term in enumerate(query_terms[:10]):  # 최대 10개 단어
                where_conditions.append(f"LOWER(c.text) LIKE :term_{i}")
                params[f"term_{i}"] = f'%{term}%'

            filter_clause = self._build_filter_clause(filters)

            query_sql = f"""
                SELECT
                    c.chunk_id,
                    c.text,
                    d.title,
                    d.source_url,
                    dt.path as taxonomy_path,
                    JSON_EXTRACT(d.doc_metadata, '$.type') as doc_type
                FROM chunks c
                JOIN documents d ON c.doc_id = d.doc_id
                LEFT JOIN doc_taxonomy dt ON d.doc_id = dt.doc_id
                WHERE ({' OR '.join(where_conditions)})
                {filter_clause}
                ORDER BY LENGTH(c.text) DESC
                LIMIT 1000
            """

            result = await session.execute(text(query_sql), params)
            rows = result.fetchall()

            return [dict(row._mapping) for row in rows]

        except Exception as e:
            logger.error(f"Error getting candidate documents: {e}")
            return []

    def _build_filter_clause(self, filters: Dict) -> str:
        """필터 조건 생성"""
        if not filters:
            return ""

        clauses = []
        # taxonomy 필터
        if 'canonical_in' in filters:
            # 간단한 path 매칭
            clauses.append("dt.path IS NOT NULL")

        return f" AND {' AND '.join(clauses)}" if clauses else ""

    def _calculate_bm25_score(self, doc: Dict, query_terms: List[str]) -> float:
        """BM25 점수 계산"""
        if not doc.get('text'):
            return 0.0

        doc_text = doc['text']
        doc_tokens = self._tokenize(doc_text)
        doc_length = len(doc_tokens)

        # 토큰 빈도 계산
        token_counts = Counter(doc_tokens)

        score = 0.0
        for term in query_terms:
            if term not in token_counts:
                continue

            # Term frequency in document
            tf = token_counts[term]

            # Document frequency (전체 문서에서 이 단어가 나타나는 문서 수)
            df = self.doc_freqs.get(term, 1)

            # IDF 계산
            idf = math.log((self.total_docs - df + 0.5) / (df + 0.5))

            # Document length normalization
            doc_length_norm = self.doc_lengths.get(doc['chunk_id'], doc_length)
            length_factor = (1 - self.b) + self.b * (doc_length_norm / self.avg_doc_length)

            # BM25 공식
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * length_factor

            term_score = idf * (numerator / denominator)
            score += term_score

        return score


class OptimizedBM25:
    """메모리 최적화된 BM25 (대용량 코퍼스용)"""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b

    async def search_with_preprocessing(
        self,
        session: AsyncSession,
        query: str,
        topk: int = 20,
        filters: Dict = None
    ) -> List[Dict[str, Any]]:
        """전처리된 인덱스 사용 BM25 검색"""
        try:
            # PostgreSQL의 full-text search 활용
            if "postgresql" in str(session.bind.url):
                return await self._postgresql_bm25_search(session, query, topk, filters)
            else:
                # SQLite 폴백
                return await self._sqlite_bm25_search(session, query, topk, filters)

        except Exception as e:
            logger.error(f"Optimized BM25 search failed: {e}")
            return []

    async def _postgresql_bm25_search(
        self,
        session: AsyncSession,
        query: str,
        topk: int,
        filters: Dict
    ) -> List[Dict[str, Any]]:
        """PostgreSQL full-text search 기반 BM25"""
        filter_clause = self._build_filter_clause(filters)

        query_sql = text(f"""
            SELECT
                c.chunk_id,
                c.text,
                d.title,
                d.source_url,
                dt.path as taxonomy_path,
                ts_rank_cd(
                    setweight(to_tsvector('english', COALESCE(d.title, '')), 'A') ||
                    setweight(to_tsvector('english', c.text), 'B'),
                    websearch_to_tsquery('english', :query),
                    32 | 1  -- normalization + log(doc_length)
                ) as bm25_score
            FROM chunks c
            JOIN documents d ON c.doc_id = d.doc_id
            LEFT JOIN doc_taxonomy dt ON d.doc_id = dt.doc_id
            WHERE (
                to_tsvector('english', d.title) @@ websearch_to_tsquery('english', :query)
                OR to_tsvector('english', c.text) @@ websearch_to_tsquery('english', :query)
            )
            {filter_clause}
            ORDER BY bm25_score DESC
            LIMIT :topk
        """)

        result = await session.execute(query_sql, {
            "query": query,
            "topk": topk
        })

        rows = result.fetchall()
        return [dict(row._mapping) for row in rows]

    async def _sqlite_bm25_search(
        self,
        session: AsyncSession,
        query: str,
        topk: int,
        filters: Dict
    ) -> List[Dict[str, Any]]:
        """SQLite FTS5 기반 BM25 최적화"""
        try:
            # 1단계: FTS5 가상 테이블 존재 확인 및 생성
            await self._ensure_fts5_table(session)

            # 2단계: FTS5 검색 시도
            fts5_results = await self._fts5_search(session, query, topk, filters)
            if fts5_results:
                logger.info(f"FTS5 search returned {len(fts5_results)} results")
                return fts5_results

            # 3단계: 폴백 - 향상된 LIKE 검색
            return await self._enhanced_like_search(session, query, topk, filters)

        except Exception as e:
            logger.error(f"SQLite BM25 search failed: {e}")
            return await self._basic_fallback_search(session, query, topk, filters)

    async def _ensure_fts5_table(self, session: AsyncSession):
        """FTS5 가상 테이블 생성 (없는 경우)"""
        try:
            # FTS5 테이블 존재 확인
            check_query = text("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='chunks_fts'
            """)
            result = await session.execute(check_query)
            table_exists = result.fetchone() is not None

            if not table_exists:
                # FTS5 가상 테이블 생성
                create_fts_query = text("""
                    CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
                        chunk_id UNINDEXED,
                        title,
                        text,
                        content='chunks_with_docs',
                        content_rowid='rowid',
                        tokenize='porter unicode61'
                    )
                """)
                await session.execute(create_fts_query)

                # 뷰 생성 (chunks + documents join)
                create_view_query = text("""
                    CREATE VIEW IF NOT EXISTS chunks_with_docs AS
                    SELECT
                        c.rowid,
                        c.chunk_id,
                        COALESCE(d.title, '') as title,
                        c.text
                    FROM chunks c
                    LEFT JOIN documents d ON c.doc_id = d.doc_id
                """)
                await session.execute(create_view_query)

                # FTS5 인덱스 채우기
                populate_query = text("INSERT INTO chunks_fts(chunks_fts) VALUES('rebuild')")
                await session.execute(populate_query)

                await session.commit()
                logger.info("FTS5 table created and populated")

        except Exception as e:
            logger.warning(f"FTS5 table creation failed: {e}")

    async def _fts5_search(
        self,
        session: AsyncSession,
        query: str,
        topk: int,
        filters: Dict
    ) -> List[Dict[str, Any]]:
        """FTS5 전문 검색"""
        try:
            # 쿼리 정규화 (FTS5 문법)
            fts_query = self._normalize_fts_query(query)
            filter_clause = self._build_filter_clause(filters)

            search_query = text(f"""
                SELECT
                    c.chunk_id,
                    c.text,
                    d.title,
                    d.source_url,
                    dt.path as taxonomy_path,
                    chunks_fts.rank as bm25_score
                FROM chunks_fts
                JOIN chunks c ON chunks_fts.chunk_id = c.chunk_id
                JOIN documents d ON c.doc_id = d.doc_id
                LEFT JOIN doc_taxonomy dt ON d.doc_id = dt.doc_id
                WHERE chunks_fts MATCH :fts_query
                {filter_clause}
                ORDER BY chunks_fts.rank
                LIMIT :topk
            """)

            result = await session.execute(search_query, {
                "fts_query": fts_query,
                "topk": topk
            })

            rows = result.fetchall()
            return [dict(row._mapping) for row in rows]

        except Exception as e:
            logger.warning(f"FTS5 search failed: {e}")
            return []

    def _normalize_fts_query(self, query: str) -> str:
        """FTS5 쿼리 정규화"""
        # 특수문자 제거 및 단어 분리
        import re
        words = re.findall(r'\b\w+\b', query.lower())

        # 불용어 제거
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        words = [w for w in words if w not in stopwords and len(w) > 1]

        if not words:
            return query  # 폴백

        # FTS5 OR 연산자로 연결
        return ' OR '.join(words[:10])  # 최대 10개 단어

    async def _enhanced_like_search(
        self,
        session: AsyncSession,
        query: str,
        topk: int,
        filters: Dict
    ) -> List[Dict[str, Any]]:
        """향상된 LIKE 기반 검색"""
        filter_clause = self._build_filter_clause(filters)

        # 쿼리 토큰화
        tokens = re.findall(r'\b\w+\b', query.lower())
        tokens = [t for t in tokens if len(t) > 1][:5]  # 최대 5개 토큰

        # 동적 LIKE 조건 생성
        like_conditions = []
        params = {"topk": topk}

        for i, token in enumerate(tokens):
            param_name = f"token_{i}"
            like_conditions.extend([
                f"LOWER(d.title) LIKE :{param_name}",
                f"LOWER(c.text) LIKE :{param_name}"
            ])
            params[param_name] = f'%{token}%'

        if not like_conditions:
            return []

        # 점수 계산식 개선
        score_formula = []
        for i, token in enumerate(tokens):
            param_name = f"token_{i}"
            score_formula.extend([
                f"CASE WHEN LOWER(d.title) LIKE :{param_name} THEN 3.0 ELSE 0.0 END",
                f"CASE WHEN LOWER(c.text) LIKE :{param_name} THEN 1.0 ELSE 0.0 END"
            ])

        query_sql = text(f"""
            SELECT
                c.chunk_id,
                c.text,
                d.title,
                d.source_url,
                dt.path as taxonomy_path,
                ({' + '.join(score_formula)}) as bm25_score
            FROM chunks c
            JOIN documents d ON c.doc_id = d.doc_id
            LEFT JOIN doc_taxonomy dt ON d.doc_id = dt.doc_id
            WHERE ({' OR '.join(like_conditions)})
            {filter_clause}
            ORDER BY bm25_score DESC,
                     CASE WHEN LENGTH(c.text) BETWEEN 100 AND 1000 THEN 1 ELSE 0 END DESC,
                     LENGTH(c.text) ASC
            LIMIT :topk
        """)

        result = await session.execute(query_sql, params)
        rows = result.fetchall()
        return [dict(row._mapping) for row in rows]

    async def _basic_fallback_search(
        self,
        session: AsyncSession,
        query: str,
        topk: int,
        filters: Dict
    ) -> List[Dict[str, Any]]:
        """기본 폴백 검색"""
        try:
            query_lower = query.lower()
            query_like = f'%{query_lower}%'

            basic_query = text("""
                SELECT
                    c.chunk_id,
                    c.text,
                    d.title,
                    d.source_url,
                    dt.path as taxonomy_path,
                    1.0 as bm25_score
                FROM chunks c
                JOIN documents d ON c.doc_id = d.doc_id
                LEFT JOIN doc_taxonomy dt ON d.doc_id = dt.doc_id
                WHERE LOWER(c.text) LIKE :query_like
                ORDER BY LENGTH(c.text) ASC
                LIMIT :topk
            """)

            result = await session.execute(basic_query, {
                "query_like": query_like,
                "topk": topk
            })

            rows = result.fetchall()
            return [dict(row._mapping) for row in rows]

        except Exception as e:
            logger.error(f"Basic fallback search failed: {e}")
            return []

    def _build_filter_clause(self, filters: Dict) -> str:
        """필터 조건 생성"""
        if not filters:
            return ""

        clauses = []
        if 'canonical_in' in filters:
            clauses.append("dt.path IS NOT NULL")

        return f" AND {' AND '.join(clauses)}" if clauses else ""