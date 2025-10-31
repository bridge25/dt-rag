# SPEC-RESEARCH-AGENT-UI-001 인수 기준

## @TEST:RESEARCH-AGENT-UI-001

---

## 기능 인수 기준

### 1. 메시지 전송 및 응답

#### 시나리오 1.1: 메시지 전송
**Given**: Agent가 선택되어 있고,
**When**: "What is machine learning?" 메시지를 전송하면,
**Then**:
- 메시지가 채팅창에 표시되어야 한다
- Agent 응답 스트리밍이 시작되어야 한다

**검증**:
```typescript
test('should send message and receive response', async () => {
  render(<ResearchAgentUI />);

  const input = screen.getByPlaceholderText('메시지를 입력하세요');
  fireEvent.change(input, { target: { value: 'What is ML?' } });
  fireEvent.submit(input);

  await waitFor(() => {
    expect(screen.getByText('What is ML?')).toBeInTheDocument();
    expect(screen.getByText(/Machine learning is.../)).toBeInTheDocument();
  });
});
```

---

### 2. 스트리밍 응답

#### 시나리오 2.1: 실시간 스트리밍
**Given**: 메시지를 전송했고,
**When**: SSE 응답이 청크 단위로 도착하면,
**Then**:
- 각 청크가 실시간으로 표시되어야 한다

---

## Definition of Done
- ✅ 모든 인수 기준 통과
- ✅ SSE 스트리밍 동작
- ✅ 대화 이력 저장

---

**작성자**: @spec-builder
**작성일**: 2025-10-31
