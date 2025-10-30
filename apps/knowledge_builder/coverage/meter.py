# @CODE:AGENT-GROWTH-001:DOMAIN
from typing import List, Optional, Dict, Any
from .models import CoverageMetrics, CoverageResult, Gap


class CoverageMeterService:
    def __init__(self, session_factory: Optional[Any] = None) -> None:
        self._session_factory = session_factory

    # @IMPL:AGENT-GROWTH-001:0.2.1
    async def calculate_coverage(
        self,
        taxonomy_version: str,
        node_ids: Optional[List[str]] = None
    ) -> CoverageMetrics:
        if node_ids is None or len(node_ids) == 0:
            return CoverageMetrics(
                total_nodes=0,
                total_documents=0,
                total_chunks=0,
                coverage_percent=0.0,
                node_coverage={}
            )

        if self._session_factory is None:
            from apps.core.db_session import async_session
            self._session_factory = async_session

        from sqlalchemy import select, func
        from apps.api.database import DocTaxonomy, TaxonomyNode, DocumentChunk
        import uuid

        async with self._session_factory() as session:
            total_nodes_result = await session.execute(
                select(func.count(TaxonomyNode.node_id))
                .where(TaxonomyNode.version == taxonomy_version)
            )
            total_nodes = total_nodes_result.scalar() or 0

            doc_count_result = await session.execute(
                select(func.count(DocTaxonomy.doc_id.distinct()))
                .where(DocTaxonomy.version == taxonomy_version)
            )
            total_documents = doc_count_result.scalar() or 0

            chunk_count_result = await session.execute(
                select(func.count(DocumentChunk.chunk_id))
                .join(DocTaxonomy, DocumentChunk.doc_id == DocTaxonomy.doc_id)
                .where(DocTaxonomy.version == taxonomy_version)
            )
            total_chunks = chunk_count_result.scalar() or 0

            node_coverage = {}
            for node_id_str in node_ids:
                try:
                    node_uuid = uuid.UUID(node_id_str)
                except ValueError:
                    continue

                node_doc_count_result = await session.execute(
                    select(func.count(DocTaxonomy.doc_id.distinct()))
                    .where(DocTaxonomy.node_id == node_uuid)
                    .where(DocTaxonomy.version == taxonomy_version)
                )
                node_doc_count = node_doc_count_result.scalar() or 0

                node_chunk_count_result = await session.execute(
                    select(func.count(DocumentChunk.chunk_id))
                    .join(DocTaxonomy, DocumentChunk.doc_id == DocTaxonomy.doc_id)
                    .where(DocTaxonomy.node_id == node_uuid)
                    .where(DocTaxonomy.version == taxonomy_version)
                )
                node_chunk_count = node_chunk_count_result.scalar() or 0

                # @CODE:MYPY-CONSOLIDATION-002 | Phase 13: arg-type resolution (Fix 24 - store only int, not dict)
                node_coverage[node_id_str] = node_doc_count

            coverage_percent = 0.0
            if total_nodes > 0:
                # @CODE:MYPY-CONSOLIDATION-002 | Phase 13: arg-type resolution (Fix 24 - cov is now int, not dict)
                covered_nodes = sum(1 for cov in node_coverage.values() if cov > 0)
                coverage_percent = (covered_nodes / total_nodes) * 100.0

            return CoverageMetrics(
                total_nodes=total_nodes,
                total_documents=total_documents,
                total_chunks=total_chunks,
                coverage_percent=coverage_percent,
                node_coverage=node_coverage
            )

    async def _get_descendant_nodes(
        self,
        session: Any,
        root_node_ids: List[str],
        version: str
    ) -> List[str]:
        from apps.api.taxonomy_dag import taxonomy_dag_manager
        import networkx as nx

        # @CODE:MYPY-CONSOLIDATION-002 | Phase 13: arg-type resolution (Fix 25 - convert str to int)
        graph = await taxonomy_dag_manager._build_networkx_graph(int(version))

        descendants = set(root_node_ids)
        for root_id in root_node_ids:
            try:
                descendants.update(nx.descendants(graph, root_id))
            except nx.NetworkXError:
                continue

        return list(descendants)

    async def detect_gaps(
        self,
        coverage_result: CoverageMetrics,
        threshold: float = 0.5
    ) -> List[Gap]:
        gaps = []

        # @CODE:MYPY-CONSOLIDATION-002 | Phase 2: Fix attr-defined (int has no get method)
        for node_id, doc_count in coverage_result.node_coverage.items():
            # node_coverage is Dict[str, int], so value is int, not dict
            target_count = max(doc_count, 10)

            current_coverage = (doc_count / target_count * 100) if target_count > 0 else 0.0
            target_coverage = threshold * 100

            if current_coverage < target_coverage:
                missing_docs = int(target_count * threshold - doc_count)
                gaps.append(Gap(
                    node_id=node_id,
                    current_coverage=current_coverage,
                    target_coverage=target_coverage,
                    missing_docs=missing_docs,
                    recommendation=f"Collect {missing_docs} more documents for this topic"
                ))

        gaps.sort(key=lambda g: g.missing_docs, reverse=True)
        return gaps
