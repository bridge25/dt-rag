# SPEC-AGENT-CREATE-FORM-001 구현 계획

## @PLAN:AGENT-CREATE-FORM-001

---

## 개요
React Hook Form과 Zod를 활용한 3단계 Agent 생성 폼 워크플로우를 구현합니다.

---

## 우선순위별 마일스톤

### Primary Goals
1. **React Hook Form + Zod 통합**
   - React Hook Form 설치 및 설정
   - Zod 스키마 정의 (agentFormSchema)
   - useForm 훅 초기화

2. **3단계 폼 UI**
   - Step 1: 기본 정보 폼 (이름, 설명, 목적)
   - Step 2: Taxonomy 선택 UI
   - Step 3: 프롬프트 설정 및 미리보기
   - 스텝 네비게이션 컴포넌트

3. **실시간 검증**
   - 필드별 Zod 검증
   - 에러 메시지 표시
   - 다음 버튼 활성화/비활성화

4. **API 연동**
   - POST /api/agents 호출
   - 성공/실패 처리
   - 리디렉션 (Agent 상세 페이지)

5. **테스트**
   - 폼 검증 테스트
   - 제출 플로우 테스트

### Secondary Goals
1. **로컬 스토리지 임시 저장**
   - 폼 데이터 자동 저장
   - 페이지 재방문 시 복원

2. **접근성 개선**
   - ARIA 레이블
   - 키보드 네비게이션

---

## 기술 접근

### 디렉토리 구조
```
frontend/src/
├─ components/
│  └─ AgentCreationForm/
│     ├─ AgentCreationForm.tsx
│     ├─ StepBasicInfo.tsx
│     ├─ StepTaxonomySelect.tsx
│     ├─ StepPromptConfig.tsx
│     ├─ StepNavigation.tsx
│     └─ FormPreview.tsx
├─ hooks/
│  ├─ useAgentCreation.ts
│  └─ useTaxonomies.ts
├─ schemas/
│  └─ agentFormSchema.ts
└─ types/
   └─ agent.ts
```

### 필수 라이브러리
```bash
npm install react-hook-form @hookform/resolvers
```

### 구현 순서
1. Phase 1: Zod 스키마 + React Hook Form 설정
2. Phase 2: Step 1-3 컴포넌트 구현
3. Phase 3: 스텝 네비게이션 로직
4. Phase 4: API 연동 및 제출
5. Phase 5: 테스트 작성

---

## 파일 구조
- 컴포넌트: 6개
- 훅: 2개
- 스키마: 1개
- 타입: 1개
- 테스트: 4개

---

## 테스트 전략
- 폼 검증 (Zod 스키마)
- 단계별 네비게이션
- API 호출 모킹
- E2E 시나리오 (전체 폼 제출)

---

**작성자**: @spec-builder
**작성일**: 2025-10-31
