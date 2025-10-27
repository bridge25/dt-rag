# @CODE:AGENT-GROWTH-001:DOMAIN
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class CoverageMetrics:
    total_nodes: int
    total_documents: int
    total_chunks: int
    coverage_percent: float
    node_coverage: Dict[str, int]


@dataclass
class CoverageResult:
    agent_id: str
    overall_coverage: float
    node_coverage: Dict[str, float]
    document_counts: Dict[str, int]
    target_counts: Dict[str, int]
    version: str


@dataclass
class Gap:
    node_id: str
    current_coverage: float
    target_coverage: float
    missing_docs: int
    recommendation: str
