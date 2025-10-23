# SPEC-INGESTION-001: Document Ingestion Pipeline System

**상태**: completed
**우선순위**: critical
**담당자**: @claude
**작성일**: 2025-10-09
**최종 수정일**: 2025-10-09

## 1. 개요

### 1.1 목적

다양한 형식의 문서를 파싱하고, 지능형 청킹, PII 탐지/마스킹, 임베딩 생성을 거쳐 데이터베이스에 저장하는 엔터프라이즈급 문서 처리 파이프라인을 제공한다.

### 1.2 범위

**포함 사항**:
- 7가지 파일 형식 파싱 (PDF, DOCX, HTML, CSV, TXT, Markdown)
- 토큰 기반 지능형 청킹 (tiktoken, 500 tokens/chunk)
- PII 탐지 및 마스킹 (주민번호, 전화번호, 이메일, 카드번호, 계좌번호)
- 배치 임베딩 생성 (OpenAI API)
- Redis 기반 Job Queue (priority queues)
- 100 worker JobOrchestrator
- 문서/청크/임베딩 데이터베이스 저장
- Taxonomy path 자동 할당

**제외 사항**:
- OCR 기반 이미지 텍스트 추출
- 스캔 문서 처리
- 실시간 스트리밍 처리

### 1.3 이해관계자

- **개발팀**: Parser, Chunker, PII Detector, JobOrchestrator 구현
- **QA팀**: 파싱 정확도 검증, PII 탐지율 테스트, 처리량 측정
- **운영팀**: Job Queue 모니터링, Worker pool 관리
- **보안팀**: PII 마스킹 검증, 데이터 유출 방지
- **컴플라이언스팀**: PII 처리 규정 준수 확인

---

## 2. 요구사항 (EARS)

### 2.1 기능 요구사항

#### FR-ING-001: 다중 형식 파일 파싱
**WHERE** 사용자가 문서를 업로드할 때,
**WHEN** file_format이 지원 형식인 경우,
**THEN** 시스템은 다음 파서를 사용하여 텍스트를 추출해야 한다:

**지원 형식** (7가지):
1. **PDF**: pymupdf + pymupdf4llm (Markdown 출력)
2. **DOCX**: python-docx (단락 추출)
3. **HTML**: BeautifulSoup + lxml (script/style 제거)
4. **CSV**: pandas (Markdown 테이블 출력)
5. **TXT**: UTF-8 디코딩
6. **Markdown**: Regex 기반 파싱 (헤더, 링크, 이미지 제거)

**품질 요구사항**:
- 빈 콘텐츠 감지 및 ParserError 발생
- UTF-8 인코딩 오류 무시 (`errors="ignore"`)

#### FR-ING-002: 지능형 토큰 기반 청킹
**WHERE** 파싱된 텍스트가 제공될 때,
**WHEN** 청킹 요청이 발생하는 경우,
**THEN** 시스템은 다음 알고리즘으로 청크를 생성해야 한다:

**청킹 설정**:
- `chunk_size`: 500 tokens (기본값)
- `overlap_size`: 128 tokens (기본값)
- `encoding`: `cl100k_base` (tiktoken)

**청킹 로직**:
1. 문장 단위로 텍스트 분리 (정규식: `[.!?。！？]\s+`)
2. 문장 토큰 수 계산
3. 문장이 chunk_size 초과 시 단어 단위로 분할
4. chunk_size 도달 시 청크 생성 및 overlap 적용
5. 문장 경계 보존 여부 플래그 설정

**출력**:
- `Chunk` dataclass:
  - `text`: 청크 텍스트
  - `token_count`: 토큰 수
  - `start_position`, `end_position`: 위치
  - `sentence_boundary_preserved`: 문장 경계 보존 여부 (bool)

**품질 메트릭**:
- 문장 경계 보존율 계산 (`calculate_sentence_boundary_preservation_rate`)

#### FR-ING-003: PII 탐지 및 마스킹
**WHERE** 청크 텍스트가 생성될 때,
**WHEN** PII 탐지가 요청되는 경우,
**THEN** 시스템은 다음 PII 유형을 탐지하고 마스킹해야 한다:

**PII 유형** (5가지):
1. **주민등록번호**: `\d{6}[-\s]?[1-4]\d{6}` + Checksum 검증
2. **전화번호**: `0\d{1,2}[-\s]?\d{3,4}[-\s]?\d{4}` (국내), `+82` (국제)
3. **이메일**: `[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}`
4. **카드번호**: Visa/Mastercard/Amex/JCB + Luhn 알고리즘 검증
5. **계좌번호**: `\d{3,4}[-\s]?\d{2,6}[-\s]?\d{4,8}`

**검증 로직**:
- **주민번호**: 생년월일 유효성 (월 1-12, 일 1-31), 성별코드 (1-4)
- **카드번호**: Luhn checksum 검증

**마스킹 레이블**:
- 주민번호 → `[주민번호]`
- 전화번호 → `[전화번호]`
- 이메일 → `[이메일]`
- 카드번호 → `[카드번호]`
- 계좌번호 → `[계좌번호]`

**출력**:
- `PIIMatch` dataclass:
  - `pii_type`: PII 유형
  - `original_text`: 원본 텍스트
  - `start_position`, `end_position`: 위치
  - `confidence`: 신뢰도 (1.0)

**우선순위 처리**:
주민번호 > 카드번호 > 전화번호 > 이메일 > 계좌번호 (겹침 방지)

#### FR-ING-004: 배치 임베딩 생성
**WHERE** 모든 청크가 생성되고 PII 마스킹이 완료된 후,
**WHEN** 임베딩 생성이 요청되는 경우,
**THEN** 시스템은 다음을 수행해야 한다:

1. `batch_generate_embeddings` 호출 (batch_size=50)
2. 청크 텍스트 배열 전달
3. OpenAI API를 통해 임베딩 벡터 생성
4. 진행률 표시 (show_progress=True)

**성능 요구사항**:
- 배치 크기: 50 chunks/batch
- API 호출 재시도: 최대 3회
- 타임아웃: 30s/batch

#### FR-ING-005: Job Queue 관리
**WHERE** 문서 처리 작업이 제출될 때,
**WHEN** JobQueue에 작업을 추가하는 경우,
**THEN** 시스템은 다음을 수행해야 한다:

**Queue 구조** (Redis):
- `ingestion:queue:high`: Priority 1-3
- `ingestion:queue:medium`: Priority 4-7
- `ingestion:queue:low`: Priority 8-10

**Job Payload**:
```json
{
  "job_id": "uuid",
  "command_id": "uuid",
  "data": {
    "file_name": "doc.pdf",
    "file_content_hex": "hex_string",
    "file_format": "pdf",
    "taxonomy_path": ["category", "subcategory"],
    "source_url": "https://...",
    "metadata": {}
  },
  "priority": 5,
  "enqueued_at": "2025-10-09T12:00:00Z"
}
```

**Idempotency Key 처리**:
- 중복 요청 탐지 (idempotency key 확인)
- 기존 job_id 반환 시 ValueError 발생
- TTL: 3600s (1시간)

#### FR-ING-006: JobOrchestrator 작업 처리
**WHERE** JobOrchestrator가 시작된 후,
**WHEN** Worker가 작업을 처리할 때,
**THEN** 시스템은 다음 파이프라인을 실행해야 한다:

**처리 단계**:
1. **Parse**: ParserFactory로 파일 파싱
2. **Chunk**: IntelligentChunker로 청킹
3. **PII Detection**: PIIDetector로 PII 탐지/마스킹
4. **Embedding**: EmbeddingService로 임베딩 생성 (배치)
5. **Database**: Document, Chunk, Embedding, DocTaxonomy 저장

**Worker Pool**:
- 최대 Worker 수: 100 (configurable)
- Dequeue timeout: 5s
- Priority 순서: high → medium → low

**재시도 로직**:
- 최대 재시도 횟수: 3회
- 재시도 불가 오류: ParserError, ValidationError, AuthenticationError
- 재시도 지연: 지수 백오프 (2^retry_count seconds)
- `_should_retry` 메서드로 재시도 여부 판단

#### FR-ING-007: Job 상태 관리
**WHERE** Job이 처리되는 동안,
**WHEN** 상태 업데이트가 필요할 때,
**THEN** 시스템은 다음 상태를 Redis에 저장해야 한다:

**Job 상태**:
- `pending`: 대기 중
- `processing`: 처리 중
- `completed`: 완료
- `failed`: 실패
- `retrying`: 재시도 중

**Status Data**:
```json
{
  "job_id": "uuid",
  "command_id": "uuid",
  "status": "processing",
  "progress_percentage": 50.0,
  "current_stage": "PII Detection",
  "chunks_processed": 5,
  "total_chunks": 10,
  "error_message": null,
  "started_at": "2025-10-09T12:00:00Z",
  "completed_at": null,
  "retry_count": 0,
  "max_retries": 3,
  "updated_at": "2025-10-09T12:01:00Z"
}
```

**TTL**: 86400s (24시간)

#### FR-ING-008: 데이터베이스 저장
**WHERE** 모든 처리 단계가 완료된 후,
**WHEN** 데이터베이스 저장이 요청되는 경우,
**THEN** 시스템은 트랜잭션으로 다음을 저장해야 한다:

**저장 순서**:
1. **Document** 테이블:
   - `doc_id`, `source_url`, `title`, `content_type`
   - `doc_metadata`, `processed_at`

2. **DocTaxonomy** 테이블 (taxonomy_path가 있는 경우):
   - `mapping_id`, `doc_id`, `path`
   - `confidence` (1.0), `source` ('ingestion')
   - `assigned_at`

3. **Chunk** 테이블 (각 청크별):
   - `chunk_id`, `doc_id`, `text`, `span`
   - `chunk_index`, `chunk_metadata`
   - `token_count`, `has_pii`, `pii_types`
   - `created_at`

4. **Embedding** 테이블 (각 청크별):
   - `embedding_id`, `chunk_id`, `vec`
   - `model_name`, `created_at`

**트랜잭션 보장**:
- 전체 commit 또는 전체 rollback
- 저장 실패 시 에러 로그 및 rollback

#### FR-ING-009: Event 발행
**WHERE** 문서 처리가 완료된 후,
**WHEN** Event 발행이 요청되는 경우,
**THEN** 시스템은 `DocumentProcessedEventV1`을 생성해야 한다:

```python
DocumentProcessedEventV1(
    correlationId=correlation_id,
    command_id=command_id,
    status=ProcessingStatusV1.COMPLETED,
    document_id=str(doc_id),
    chunks=[ChunkV1(...)],
    total_chunks=len(chunks),
    total_tokens=sum(chunk.token_count),
    processing_duration_ms=duration_ms
)
```

---

### 2.2 비기능 요구사항

#### NFR-ING-001: 성능 요구사항
**WHERE** 프로덕션 환경에서,
**WHEN** 정상 부하 조건일 때,
**THEN** 시스템은 다음 성능을 보장해야 한다:

**처리 처리량**:
- 단일 문서: < 5s (파싱 + 청킹 + PII + 임베딩 + 저장)
- 배치 처리 (100 workers): > 20 docs/min

**파서 성능**:
- PDF (10 pages): < 2s
- DOCX (20 pages): < 1s
- HTML (100KB): < 0.5s

**청킹 성능**:
- 1,000 sentences: < 1s
- 문장 경계 보존율: > 80%

**PII 탐지 성능**:
- 10,000 characters: < 100ms
- False positive rate: < 5%

**임베딩 생성 성능**:
- 50 chunks/batch: < 3s (OpenAI API 포함)

#### NFR-ING-002: 확장성 요구사항
**WHERE** 시스템 부하가 증가할 때,
**WHEN** 동시 처리 작업 수가 증가하는 경우,
**THEN** 시스템은 다음을 지원해야 한다:

- Worker 수 조정 (기본 100, 최대 500)
- Redis Queue 수평 확장 (Cluster mode)
- 데이터베이스 연결 풀링 (async_session)

#### NFR-ING-003: 안정성 요구사항
**WHERE** 프로덕션 환경에서,
**WHEN** 시스템 운영 중,
**THEN** 시스템은 다음 안정성을 제공해야 한다:

**재시도 메커니즘**:
- 최대 3회 재시도 (지수 백오프)
- 재시도 불가 오류 감지 (ParserError, ValidationError)

**Graceful Degradation**:
- Parser 실패 시 ParserError 반환
- Embedding 실패 시 재시도 후 실패 표시

**트랜잭션 보장**:
- 데이터베이스 저장 실패 시 rollback
- 부분 저장 방지

#### NFR-ING-004: 보안 요구사항
**WHERE** 민감 정보를 처리할 때,
**WHEN** PII가 탐지되는 경우,
**THEN** 시스템은 다음을 수행해야 한다:

**PII 마스킹**:
- 원본 PII는 저장하지 않음
- 마스킹된 텍스트만 저장
- PII 유형 메타데이터 기록 (`pii_types`)

**파일 크기 제한**:
- 최대 파일 크기: 50MB
- 초과 시 ValidationError 발생

**입력 검증**:
- file_name: 1-255자
- file_extension: file_format과 일치 여부 검증
- taxonomy_path: 1-10개 요소

#### NFR-ING-005: 관측성 요구사항
**WHERE** 시스템 운영 중,
**WHEN** 모니터링 및 디버깅이 필요할 때,
**THEN** 시스템은 다음을 제공해야 한다:

**처리 메트릭**:
- `processing_duration_ms` (파싱, 청킹, PII, 임베딩, 저장 각 단계별)
- `total_chunks`, `total_tokens`
- `pii_detection_count` (PII 유형별)

**Job Queue 메트릭**:
- Queue 크기 (high, medium, low 각각)
- 대기 시간 (enqueued_at → started_at)
- 처리 시간 (started_at → completed_at)

**Worker 메트릭**:
- Active workers
- Completed jobs, Failed jobs
- Retry count

**로그**:
- 파싱 완료: `"Parsed {len} characters from {file_name}"`
- 청킹 완료: `"Created {len} chunks from {file_name}"`
- PII 탐지 완료: `"PII detection completed for {file_name}"`
- 임베딩 생성 완료: `"Generating embeddings for {len} chunks"`
- 저장 완료: `"Stored document {doc_id} with {len} chunks"`

---

## 3. 아키텍처 설계

### 3.1 시스템 구성도

```
┌──────────────────────────────────────────────────────────┐
│               Document Ingestion Pipeline                │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │   Parser Factory (7 Parsers)                    │   │
│  │   ┌────────┐  ┌──────┐  ┌──────┐  ┌──────┐     │   │
│  │   │  PDF   │  │ DOCX │  │ HTML │  │ CSV  │     │   │
│  │   │pymupdf │  │python│  │ BS4  │  │pandas│     │   │
│  │   └────────┘  │-docx │  │+lxml │  └──────┘     │   │
│  │               └──────┘  └──────┘               │   │
│  │   ┌────────┐  ┌──────┐  ┌──────┐               │   │
│  │   │  TXT   │  │  MD  │  │ Base │               │   │
│  │   │UTF-8   │  │Regex │  │Parser│               │   │
│  │   └────────┘  └──────┘  └──────┘               │   │
│  └─────────────────────────────────────────────────┘   │
│                         ▼                                │
│  ┌─────────────────────────────────────────────────┐   │
│  │   Intelligent Chunker (tiktoken)                │   │
│  │   - chunk_size: 500 tokens                      │   │
│  │   - overlap: 128 tokens                         │   │
│  │   - sentence boundary preservation              │   │
│  └─────────────────────────────────────────────────┘   │
│                         ▼                                │
│  ┌─────────────────────────────────────────────────┐   │
│  │   PII Detector (5 Types)                        │   │
│  │   - 주민번호, 전화번호, 이메일                    │   │
│  │   - 카드번호, 계좌번호                            │   │
│  │   - Validation: Checksum, Luhn                  │   │
│  └─────────────────────────────────────────────────┘   │
│                         ▼                                │
│  ┌─────────────────────────────────────────────────┐   │
│  │   Embedding Service (OpenAI)                    │   │
│  │   - batch_generate_embeddings (50 chunks)       │   │
│  │   - text-embedding-3-large (1536 dims)          │   │
│  └─────────────────────────────────────────────────┘   │
│                         ▼                                │
│  ┌─────────────────────────────────────────────────┐   │
│  │   Database Storage (Transactional)              │   │
│  │   - Document                                    │   │
│  │   - DocTaxonomy                                 │   │
│  │   - Chunk (with PII metadata)                   │   │
│  │   - Embedding                                   │   │
│  └─────────────────────────────────────────────────┘   │
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │   Job Queue (Redis)                             │   │
│  │   ┌──────────┐  ┌──────────┐  ┌──────────┐     │   │
│  │   │  High    │  │ Medium   │  │   Low    │     │   │
│  │   │Priority  │  │Priority  │  │Priority  │     │   │
│  │   │  1-3     │  │  4-7     │  │  8-10    │     │   │
│  │   └──────────┘  └──────────┘  └──────────┘     │   │
│  └─────────────────────────────────────────────────┘   │
│                         ▼                                │
│  ┌─────────────────────────────────────────────────┐   │
│  │   JobOrchestrator (100 Workers)                 │   │
│  │   - Worker pool management                      │   │
│  │   - Retry logic (exponential backoff)           │   │
│  │   - Status tracking (Redis)                     │   │
│  └─────────────────────────────────────────────────┘   │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### 3.2 데이터 모델

#### DocumentUploadCommandV1 (Pydantic)
```python
class DocumentUploadCommandV1(BaseModel):
    kind: Literal["Command"] = "Command"
    name: Literal["DocumentUpload"] = "DocumentUpload"
    version: Literal["v1"] = "v1"
    correlationId: str
    idempotencyKey: Optional[str]

    command_id: str
    file_name: str  # 1-255자
    file_content: bytes  # ≤ 50MB
    file_format: DocumentFormatV1  # PDF, DOCX, HTML, CSV, TXT
    taxonomy_path: List[str]  # 1-10개
    source_url: Optional[str]
    author: Optional[str]
    language: str = "ko"  # 2자 코드
    metadata: Dict[str, Any] = {}
    priority: int = 5  # 1-10
    requested_at: datetime
```

#### ChunkV1 (Pydantic)
```python
class ChunkV1(BaseModel):
    chunk_id: str
    text: str  # 1-10,000자
    token_count: int  # ≥ 1
    position: int  # ≥ 0
    has_pii: bool = False
    pii_types: List[str] = []  # ["email", "phone_number", ...]
```

#### DocumentProcessedEventV1 (Pydantic)
```python
class DocumentProcessedEventV1(BaseModel):
    kind: Literal["Event"] = "Event"
    name: Literal["DocumentProcessed"] = "DocumentProcessed"
    version: Literal["v1"] = "v1"
    correlationId: str

    event_id: str
    command_id: str
    status: ProcessingStatusV1  # PENDING, PROCESSING, COMPLETED, FAILED
    document_id: Optional[str]
    chunks: List[ChunkV1]
    total_chunks: int
    total_tokens: int
    processing_duration_ms: float
    error_message: Optional[str]
    error_code: Optional[str]
    processed_at: datetime
```

#### Chunk (IntelligentChunker)
```python
@dataclass
class Chunk:
    text: str
    token_count: int
    start_position: int
    end_position: int
    sentence_boundary_preserved: bool
```

#### PIIMatch (PIIDetector)
```python
@dataclass
class PIIMatch:
    pii_type: PIIType  # RESIDENT_REGISTRATION_NUMBER, PHONE_NUMBER, ...
    original_text: str
    start_position: int
    end_position: int
    confidence: float  # 1.0
```

### 3.3 데이터베이스 스키마

**documents** 테이블:
```sql
CREATE TABLE documents (
    doc_id UUID PRIMARY KEY,
    source_url TEXT,
    title TEXT,
    content_type TEXT,
    doc_metadata JSONB,
    processed_at TIMESTAMP
);
```

**chunks** 테이블:
```sql
CREATE TABLE chunks (
    chunk_id UUID PRIMARY KEY,
    doc_id UUID REFERENCES documents(doc_id),
    text TEXT,
    span TEXT,  -- "start,end"
    chunk_index INT,
    chunk_metadata JSONB,
    token_count INT,
    has_pii BOOLEAN,
    pii_types TEXT[],  -- ["email", "phone_number"]
    created_at TIMESTAMP
);
```

**embeddings** 테이블:
```sql
CREATE TABLE embeddings (
    embedding_id UUID PRIMARY KEY,
    chunk_id UUID REFERENCES chunks(chunk_id),
    vec VECTOR(1536),
    model_name TEXT,
    created_at TIMESTAMP
);
```

**doc_taxonomy** 테이블:
```sql
CREATE TABLE doc_taxonomy (
    mapping_id UUID PRIMARY KEY,
    doc_id UUID REFERENCES documents(doc_id),
    path TEXT[],  -- ["category", "subcategory"]
    confidence REAL,
    source TEXT,  -- 'ingestion', 'classification'
    assigned_at TIMESTAMP
);
```

### 3.4 Redis 데이터 구조

**Job Queue** (List):
```
ingestion:queue:high -> [job_payload_json, ...]
ingestion:queue:medium -> [job_payload_json, ...]
ingestion:queue:low -> [job_payload_json, ...]
```

**Job Status** (String + TTL):
```
ingestion:job:{job_id} -> {status_json}  (TTL: 86400s)
```

**Idempotency Key** (String + TTL):
```
ingestion:idempotency:{idempotency_key} -> job_id  (TTL: 3600s)
```

---

## 4. 제약사항

### 4.1 기술적 제약사항

1. **파일 크기 제한**: 최대 50MB
2. **지원 형식**: PDF, DOCX, HTML, CSV, TXT, Markdown (7가지)
3. **청킹 토큰 제한**: 500 tokens/chunk (tiktoken cl100k_base)
4. **PII 탐지**: 정규식 기반 (ML 모델 미사용)
5. **임베딩 모델**: OpenAI text-embedding-3-large (1536 dims)

### 4.2 운영 제약사항

1. **Worker 수**: 최대 100 workers (기본값)
2. **재시도 횟수**: 최대 3회
3. **Redis 의존성**: Job Queue 및 Status 저장에 필수
4. **데이터베이스**: PostgreSQL + pgvector 필수

### 4.3 보안 제약사항

1. **PII 저장 금지**: 원본 PII는 데이터베이스에 저장 불가
2. **마스킹 강제**: 모든 PII는 마스킹 레이블로 대체
3. **파일 검증**: file_name과 file_format 확장자 일치 필수

---

## 5. 테스트 전략

### 5.1 단위 테스트
- [ ] 각 Parser별 단위 테스트 (PDF, DOCX, HTML, CSV, TXT, Markdown)
- [ ] IntelligentChunker 테스트 (문장 경계, 오버랩, 토큰 계산)
- [ ] PIIDetector 테스트 (5가지 PII 유형, checksum, Luhn)
- [ ] JobQueue 테스트 (enqueue, dequeue, idempotency, retry)

### 5.2 통합 테스트
- [ ] 전체 Pipeline 테스트 (Parse → Chunk → PII → Embed → DB)
- [ ] JobOrchestrator 테스트 (worker pool, 재시도, 상태 관리)
- [ ] 트랜잭션 테스트 (rollback on error)

### 5.3 성능 테스트
- [ ] 처리 처리량 측정 (20 docs/min)
- [ ] 파서 성능 측정 (PDF 10 pages < 2s)
- [ ] 청킹 성능 측정 (1,000 sentences < 1s)
- [ ] PII 탐지 성능 측정 (10,000 chars < 100ms)

### 5.4 보안 테스트
- [ ] PII 마스킹 검증 (원본 PII 저장 여부 확인)
- [ ] 파일 크기 제한 테스트 (50MB 초과 시 에러)
- [ ] 입력 검증 테스트 (file_name, taxonomy_path)

---

## 6. 운영 계획

### 6.1 배포 체크리스트

**의존성**:
- tiktoken, pymupdf, pymupdf4llm
- python-docx, beautifulsoup4, lxml, pandas
- Redis (Job Queue)
- PostgreSQL + pgvector

**환경변수**:
- Redis 연결 정보
- PostgreSQL 연결 정보
- OpenAI API Key

### 6.2 모니터링 메트릭

**처리 메트릭**:
- `documents_processed_total`, `documents_failed_total`
- `processing_duration_avg`, `processing_duration_p95`
- `chunks_created_total`, `tokens_processed_total`
- `pii_detected_total` (PII 유형별)

**Queue 메트릭**:
- `queue_size_high`, `queue_size_medium`, `queue_size_low`
- `queue_wait_time_avg`, `queue_wait_time_p95`

**Worker 메트릭**:
- `active_workers`, `completed_jobs`, `failed_jobs`
- `retry_count_total`

### 6.3 Alert 조건

- **Critical**: Worker pool 100% 사용, Queue 크기 > 1,000
- **High**: 처리 실패율 > 10%, 재시도 횟수 > 100/min
- **Medium**: 처리 지연 > 10s, PII 탐지 실패
- **Low**: 문장 경계 보존율 < 70%

---

## 7. 참조 문서

- `.moai/specs/SPEC-EMBED-001/spec.md` - Embedding Service
- `apps/ingestion/parsers/` - 7개 파서 구현
- `apps/ingestion/chunking/intelligent_chunker.py` - 청킹 알고리즘
- `apps/ingestion/pii/detector.py` - PII 탐지 로직
- `apps/ingestion/batch/job_orchestrator.py` - Job 처리 로직
- `apps/ingestion/batch/job_queue.py` - Redis Queue 관리

---

## 8. 변경 이력

| 날짜 | 변경 내용 | 작성자 |
|------|----------|--------|
| 2025-10-09 | 초안 작성 (역공학 기반) | @claude |
