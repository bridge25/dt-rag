# Common Schemas

OpenAPI v1.8.1 compliant Pydantic models for the Dynamic Taxonomy RAG system.

## Installation

```bash
pip install -e .
```

## Usage

```python
from common_schemas.models import ClassifyRequest, ClassifyResponse

# Create a classification request
request = ClassifyRequest(
    chunk_id="chunk_001",
    text="머신러닝 모델을 사용한 RAG 시스템 구축"
)
```

## Testing

```bash
pytest tests/contract_test.py
```