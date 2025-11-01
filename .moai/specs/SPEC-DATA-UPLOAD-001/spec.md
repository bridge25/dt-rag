---
id: DATA-UPLOAD-001
version: 0.0.1
status: draft
created: 2025-10-31
updated: 2025-10-31
author: @sonheungmin
priority: high
category: feature
labels:
  - frontend
  - react
  - typescript
  - data-ingestion
  - file-upload
---

# SPEC-DATA-UPLOAD-001: 데이터 업로드 및 Ingestion UI

## HISTORY

### v0.0.1 (2025-10-31)
- **INITIAL**: SPEC 초안 작성
- **AUTHOR**: @sonheungmin
- **SECTIONS**: 데이터 업로드 및 Ingestion EARS 요구사항 정의

---

## @SPEC:DATA-UPLOAD-001 개요

### 목적
사용자가 문서 파일 (PDF, TXT, DOCX)을 업로드하고, 백엔드 RAG Ingestion 파이프라인과 연동하여 Taxonomy 자동 분류 및 벡터 저장을 수행하는 UI를 제공한다.

### 범위
- 파일 드래그 앤 드롭 업로드
- 멀티파일 업로드 지원
- 업로드 진행률 표시
- Ingestion 상태 모니터링 (Processing, Completed, Failed)
- 업로드된 파일 목록 및 메타데이터 표시

### 제외 사항
- 파일 내용 편집 기능
- Taxonomy 수동 할당 (자동 분류만 지원)
- Admin 권한 관리 (SPEC-ADMIN-DASHBOARD-001)

---

## Environment (환경)

### 기술 스택
- **프론트엔드**: React 19.1.1, TypeScript 5.9.3
- **파일 업로드**: React Dropzone (최신 stable)
- **HTTP**: Axios 1.13.1 (multipart/form-data)
- **상태 관리**: Zustand 5.0.8, TanStack Query 5.90.5
- **스타일링**: Tailwind CSS 4.1.16

### 백엔드 API
- `POST /api/documents/upload` - 파일 업로드
- `GET /api/documents/:id/status` - Ingestion 상태 조회
- `GET /api/documents` - 업로드된 문서 목록

---

## Assumptions (가정)

1. 백엔드에 Ingestion 파이프라인이 구현되어 있다
2. 지원 파일 형식: PDF, TXT, DOCX, MD
3. 최대 파일 크기: 10MB
4. 동시 업로드 최대 5개

---

## Requirements (요구사항)

### Ubiquitous Requirements
- **REQ-DU-U001**: 시스템은 드래그 앤 드롭으로 파일 업로드를 지원해야 한다
- **REQ-DU-U002**: 업로드 진행률을 실시간으로 표시해야 한다
- **REQ-DU-U003**: Ingestion 상태 (Processing, Completed, Failed)를 표시해야 한다

### Event-driven Requirements
- **REQ-DU-E001**: WHEN 파일 업로드가 완료되면, Ingestion 상태 폴링을 시작해야 한다
- **REQ-DU-E002**: WHEN Ingestion이 실패하면, 에러 메시지를 표시하고 재시도 버튼을 제공해야 한다

### State-driven Requirements
- **REQ-DU-S001**: WHILE 파일 업로드 중이면, 진행률 바를 표시해야 한다
- **REQ-DU-S002**: WHILE Ingestion 중이면, 스피너와 "처리 중..." 메시지를 표시해야 한다

### Optional Features
- **REQ-DU-O001**: WHERE 파일이 PDF이면, 첫 페이지 썸네일을 생성할 수 있다

### Constraints
- **REQ-DU-C001**: 파일 크기는 10MB를 초과할 수 없다
- **REQ-DU-C002**: 지원 파일 형식: PDF, TXT, DOCX, MD만 허용해야 한다
- **REQ-DU-C003**: 동시 업로드는 최대 5개까지 허용해야 한다

---

## Specifications (상세 설계)

### 컴포넌트 구조
```typescript
<DataUploadPage>
  ├─ <FileDropzone>           // 드래그 앤 드롭 영역
  ├─ <UploadProgress>         // 진행률 표시
  ├─ <IngestionStatus>        // Ingestion 상태 모니터링
  └─ <DocumentList>           // 업로드된 문서 목록
```

### 데이터 모델
```typescript
interface UploadedDocument {
  id: string;
  filename: string;
  size: number;
  uploadedAt: string;
  status: 'uploading' | 'processing' | 'completed' | 'failed';
  progress: number; // 0-100
  errorMessage?: string;
}
```

---

## Traceability (추적성)

### TAG 체인
- **@SPEC:DATA-UPLOAD-001** → 데이터 업로드 요구사항
- **@TEST:DATA-UPLOAD-001** → 업로드 테스트, 상태 폴링 테스트
- **@CODE:DATA-UPLOAD-001** → React Dropzone, Axios upload
- **@DOC:DATA-UPLOAD-001** → 사용자 가이드

### 의존성
- **depends_on**: SPEC-FRONTEND-INIT-001
- **blocks**: SPEC-RESEARCH-AGENT-UI-001 (업로드된 데이터로 Agent 실행)

---

## 품질 기준
- 테스트 커버리지 ≥ 85%
- 업로드 속도: 1MB당 1초 이하
- Ingestion 상태 폴링 간격: 2초

---

**작성자**: @spec-builder
