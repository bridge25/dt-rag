# Document Ingestion Pipeline

Dynamic Taxonomy RAG v1.8.1을 위한 강력하고 확장 가능한 문서 처리 파이프라인입니다.

## 🚀 주요 기능

### 📄 다중 포맷 문서 파싱
- **텍스트 파일**: `.txt`, `.text`
- **PDF 문서**: `.pdf` (PyPDF2 + pdfplumber)
- **HTML 문서**: `.html`, `.htm` (BeautifulSoup + html2text)
- **Markdown**: `.md`, `.markdown`
- **JSON 데이터**: `.json`
- **CSV 파일**: `.csv`
- **URL 스크래핑**: `http://`, `https://`

### 🔧 지능형 청킹 전략
- **Token-based**: 정확한 토큰 단위 분할 (tiktoken 사용)
- **Semantic**: 문장/단락 기반 의미 보존 청킹
- **Sliding Window**: 오버랩 기반 연속성 보장
- **Adaptive**: 문서 구조 기반 적응형 청킹

### 🔒 PII 필터링 및 보안
- **이메일 주소**: 탐지 및 마스킹
- **전화번호**: 한국/국제 번호 지원
- **주민등록번호**: 한국 SSN 탐지
- **신용카드 번호**: Luhn 알고리즘 검증
- **규정 준수**: GDPR, CCPA, PIPA 지원

### ⚡ 성능 최적화
- **배치 처리**: 대용량 문서 일괄 처리
- **비동기 처리**: asyncio 기반 고성능
- **진행률 추적**: 실시간 처리 상태 모니터링
- **오류 복구**: 강력한 에러 핸들링

## 📦 설치

```bash
# 기본 의존성 설치
pip install -r requirements.txt

# 선택적 의존성 (고급 기능)
pip install PyPDF2 pdfplumber    # PDF 처리
pip install nltk kiwipiepy       # 고급 텍스트 처리
```

## 🔧 사용법

### 1. 기본 사용법

```python
from apps.ingestion import IngestionPipeline

# 파이프라인 초기화
pipeline = IngestionPipeline(
    chunking_strategy="token_based",
    chunking_params={"chunk_size": 500, "chunk_overlap": 128},
    enable_embeddings=True
)

# 단일 문서 처리
result = await pipeline.process_document("document.pdf")
print(f"처리 결과: {result.chunks_created}개 청크 생성")

# 배치 처리
sources = ["doc1.txt", "doc2.pdf", "https://example.com"]
batch_result = await pipeline.process_batch(sources)
print(f"배치 처리: {batch_result.successful}/{batch_result.total_documents} 성공")
```

### 2. 커스텀 설정

```python
from apps.ingestion.pii_filter import PIIFilter, MaskingStrategy, PIIType

# PII 필터 커스터마이징
pii_filter = PIIFilter(compliance_mode="strict")
custom_strategies = {
    PIIType.EMAIL: MaskingStrategy.REDACT,
    PIIType.PHONE: MaskingStrategy.HASH
}

pipeline = IngestionPipeline(
    chunking_strategy="semantic",
    pii_filter=pii_filter,
    quality_threshold=0.9
)
```

### 3. API 사용법

```bash
# 파일 업로드
curl -X POST "http://localhost:8000/ingestion/upload" \
     -F "files=@document.pdf" \
     -F "config={\"chunking\":{\"strategy\":\"token_based\",\"chunk_size\":500}}"

# URL 처리
curl -X POST "http://localhost:8000/ingestion/urls" \
     -H "Content-Type: application/json" \
     -d '{
       "urls": ["https://example.com/article"],
       "config": {
         "pii_filtering": {"compliance_mode": "strict"},
         "enable_embeddings": true
       }
     }'

# 처리 상태 확인
curl "http://localhost:8000/ingestion/status/{job_id}"
```

## 🏗️ 아키텍처

### 파이프라인 구조

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Document      │───▶│    Chunking     │───▶│  PII Filtering  │
│   Parsing       │    │   Strategy      │    │   & Masking     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Metadata      │    │  Token Count    │    │   Compliance    │
│   Extraction    │    │   & Validation  │    │   Validation    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 ▼
                    ┌─────────────────┐    ┌─────────────────┐
                    │   Embedding     │───▶│   Database      │
                    │   Generation    │    │   Storage       │
                    └─────────────────┘    └─────────────────┘
```

### 모듈 구조

```
apps/ingestion/
├── __init__.py                 # 패키지 초기화
├── document_parser.py          # 문서 파서 팩토리
├── chunking_strategy.py        # 청킹 전략들
├── pii_filter.py              # PII 탐지 및 필터링
├── ingestion_pipeline.py       # 메인 파이프라인
└── requirements.txt           # 의존성 목록
```

## 📊 성능 지표

### 처리 성능 목표
- **처리 실패율**: < 1%
- **PII 필터링 정확도**: > 99%
- **처리 속도**: > 1MB/sec
- **청킹 일관성**: 100% 토큰 제한 준수

### 품질 보증
- **중복 탐지**: < 0.5% 중복률
- **데이터 검증**: 100% 유효성 검사
- **오류 복구**: 95% 자동 복구율

## 🔧 설정 옵션

### 청킹 전략 설정

```python
# Token-based (권장)
ChunkingConfig(
    strategy="token_based",
    chunk_size=500,           # 청크 크기 (토큰)
    chunk_overlap=128,        # 오버랩 크기
    min_chunk_size=50         # 최소 청크 크기
)

# Semantic (의미 기반)
ChunkingConfig(
    strategy="semantic",
    max_chunk_size=500,
    prefer_paragraphs=True,   # 단락 우선
    overlap_sentences=1       # 문장 오버랩
)
```

### PII 필터링 설정

```python
# 엄격 모드 (GDPR/CCPA 준수)
PIIConfig(
    compliance_mode="strict",
    confidence_threshold=0.9,
    custom_strategies={
        "email": "redact",
        "phone": "redact",
        "ssn_kr": "redact"
    }
)

# 균형 모드 (실용적)
PIIConfig(
    compliance_mode="balanced",
    confidence_threshold=0.8
)
```

## 🧪 테스트

```bash
# 기본 기능 테스트 (DB 없이)
python test_ingestion_basic.py

# 전체 통합 테스트 (DB 필요)
python test_ingestion_pipeline.py

# 특정 모듈 테스트
python -m pytest tests/ingestion/
```

## 🔍 모니터링

### 처리 상태 확인

```python
# 파이프라인 통계
stats = pipeline.get_statistics()
print(f"처리된 문서: {stats['processing_stats']['documents_processed']}")
print(f"생성된 청크: {stats['processing_stats']['chunks_created']}")
print(f"필터링된 PII: {stats['processing_stats']['pii_filtered']}")

# 실시간 진행률
class CustomProgressCallback(ProgressCallback):
    async def update(self, current, total, status, details):
        print(f"진행률: {current}/{total} ({current/total*100:.1f}%)")
        print(f"상태: {status}")
```

### 품질 메트릭

```python
# 처리 품질 확인
for result in batch_result.results:
    print(f"문서: {result.source}")
    print(f"  품질 점수: {result.metadata.get('quality_score', 'N/A')}")
    print(f"  처리 시간: {result.processing_time:.2f}초")
    print(f"  청크 수: {result.chunks_created}")
```

## 🚨 문제 해결

### 일반적인 문제들

1. **ImportError: No module named 'tiktoken'**
   ```bash
   pip install tiktoken
   ```

2. **PDF 파싱 실패**
   ```bash
   pip install PyPDF2 pdfplumber
   ```

3. **PII 탐지 부정확**
   ```python
   # 신뢰도 임계값 조정
   pii_filter = PIIFilter(confidence_threshold=0.7)
   ```

4. **메모리 부족**
   ```python
   # 배치 크기 감소
   pipeline = IngestionPipeline(batch_size=5)
   ```

### 로그 확인

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 특정 모듈 로그만
logging.getLogger('apps.ingestion').setLevel(logging.INFO)
```

## 🔗 연관 문서

- [API 문서](../api/README.md)
- [데이터베이스 스키마](../database.py)
- [프로젝트 전체 문서](../../README.md)

## 📄 라이선스

Dynamic Taxonomy RAG v1.8.1 프로젝트의 일부입니다.