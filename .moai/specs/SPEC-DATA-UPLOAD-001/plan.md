# SPEC-DATA-UPLOAD-001 구현 계획

## @PLAN:DATA-UPLOAD-001

---

## 우선순위별 마일스톤

### Primary Goals
1. **React Dropzone 통합** - 드래그 앤 드롭 UI
2. **파일 업로드 API 연동** - Axios multipart/form-data
3. **진행률 표시** - ProgressBar 컴포넌트
4. **Ingestion 상태 폴링** - TanStack Query 폴링
5. **테스트** - 업로드 시나리오, 에러 처리

### Secondary Goals
1. **파일 검증** - 크기, 형식 검증
2. **재시도 로직** - 실패 시 재업로드

---

## 기술 접근

### 디렉토리 구조
```
frontend/src/
├─ components/
│  └─ DataUpload/
│     ├─ DataUploadPage.tsx
│     ├─ FileDropzone.tsx
│     ├─ UploadProgress.tsx
│     ├─ IngestionStatus.tsx
│     └─ DocumentList.tsx
├─ hooks/
│  ├─ useFileUpload.ts
│  └─ useIngestionStatus.ts
└─ types/
   └─ document.ts
```

### 필수 라이브러리
```bash
npm install react-dropzone
```

### 구현 순서
1. Phase 1: React Dropzone 설정
2. Phase 2: Axios 업로드 로직
3. Phase 3: 진행률 UI
4. Phase 4: Ingestion 폴링
5. Phase 5: 테스트

---

## 테스트 전략
- 파일 업로드 Mock
- 진행률 업데이트 검증
- Ingestion 상태 폴링
- 에러 시나리오 (파일 크기 초과)

---

**작성자**: @spec-builder
**작성일**: 2025-10-31
