# SPEC-RESEARCH-AGENT-UI-001 구현 계획

## @PLAN:RESEARCH-AGENT-UI-001

---

## 우선순위별 마일스톤

### Primary Goals
1. **채팅 UI 기본 구조** - 메시지 입력, 응답 표시
2. **SSE 스트리밍** - EventSource 연동
3. **Agent 선택** - 드롭다운 UI
4. **대화 이력** - Zustand 저장
5. **테스트** - 메시지 전송, 스트리밍 수신

### Secondary Goals
1. **소스 인용** - RAG 참조 문서 표시
2. **코드 하이라이팅** - Syntax highlighting

---

## 기술 접근

### 디렉토리 구조
```
frontend/src/
├─ components/
│  └─ ResearchAgentUI/
│     ├─ ResearchAgentUI.tsx
│     ├─ AgentSelector.tsx
│     ├─ ChatWindow.tsx
│     ├─ MessageInput.tsx
│     └─ SourceCitations.tsx
├─ hooks/
│  ├─ useAgentChat.ts
│  └─ useStreamingResponse.ts
└─ store/
   └─ chatStore.ts
```

### 구현 순서
1. Phase 1: 채팅 UI 컴포넌트
2. Phase 2: EventSource SSE 연동
3. Phase 3: Zustand 대화 이력
4. Phase 4: 소스 인용
5. Phase 5: 테스트

---

## 테스트 전략
- 메시지 전송 Mock
- SSE 스트리밍 Mock
- 대화 이력 저장 검증

---

**작성자**: @spec-builder
**작성일**: 2025-10-31
