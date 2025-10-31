# SPEC-DATA-UPLOAD-001 인수 기준

## @TEST:DATA-UPLOAD-001

---

## 기능 인수 기준

### 1. 파일 업로드

#### 시나리오 1.1: 드래그 앤 드롭 업로드
**Given**: Dropzone이 렌더링되어 있고,
**When**: PDF 파일을 드롭하면,
**Then**:
- 파일 업로드가 시작되어야 한다
- 진행률 바가 표시되어야 한다

**검증**:
```typescript
test('should upload file via drag and drop', async () => {
  render(<DataUploadPage />);

  const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });
  const dropzone = screen.getByTestId('dropzone');

  fireEvent.drop(dropzone, { dataTransfer: { files: [file] } });

  await waitFor(() => {
    expect(screen.getByText(/업로드 중.../)).toBeInTheDocument();
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });
});
```

#### 시나리오 1.2: 파일 크기 초과 에러
**Given**: 15MB 파일을 업로드하려고 하면,
**Then**:
- "파일 크기는 10MB를 초과할 수 없습니다" 에러가 표시되어야 한다

---

### 2. Ingestion 상태 모니터링

#### 시나리오 2.1: Ingestion 완료
**Given**: 파일 업로드가 완료되고,
**When**: Ingestion이 성공하면,
**Then**:
- 상태가 "Completed"로 표시되어야 한다
- 성공 아이콘이 표시되어야 한다

**검증**:
```typescript
test('should show completed status', async () => {
  render(<DataUploadPage />);

  // Upload file
  await uploadFile('test.pdf');

  // Mock ingestion completion
  server.use(
    http.get('/api/documents/:id/status', () => {
      return HttpResponse.json({ status: 'completed' });
    })
  );

  await waitFor(() => {
    expect(screen.getByText('Completed')).toBeInTheDocument();
  });
});
```

---

## 비기능 인수 기준

### 성능

#### 시나리오 P1: 업로드 속도
**Given**: 5MB 파일을 업로드하면,
**Then**:
- 5초 이내에 업로드가 완료되어야 한다 (1MB/s 기준)

---

## Definition of Done
- ✅ 모든 인수 기준 통과
- ✅ 테스트 커버리지 ≥ 85%
- ✅ 파일 검증 로직 구현

---

**작성자**: @spec-builder
**작성일**: 2025-10-31
