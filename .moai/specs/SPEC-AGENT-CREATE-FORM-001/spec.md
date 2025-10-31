---
id: AGENT-CREATE-FORM-001
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
  - agent
  - form
---

# SPEC-AGENT-CREATE-FORM-001: Agent 생성 폼 워크플로우

## HISTORY

### v0.0.1 (2025-10-31)
- **INITIAL**: SPEC 초안 작성
- **AUTHOR**: @sonheungmin
- **SECTIONS**: Agent 생성 다단계 폼 EARS 요구사항 정의

---

## @SPEC:AGENT-CREATE-FORM-001 개요

### 목적
사용자가 Research Agent를 생성할 때 필요한 설정을 단계별 폼으로 입력받고, 실시간 검증 및 미리보기 기능을 제공하여 직관적인 Agent 생성 경험을 제공한다.

### 범위
- 다단계 폼 워크플로우 (스텝 네비게이션)
- Agent 기본 정보 입력 (이름, 설명, 목적)
- Taxonomy 선택 (드롭다운 또는 트리 선택)
- 프롬프트 템플릿 선택 및 커스터마이징
- 실시간 폼 검증 (Zod)
- Agent 생성 API 호출 및 결과 처리

### 제외 사항
- Agent 실행 UI (별도 SPEC-RESEARCH-AGENT-UI-001)
- Agent 수정/삭제 기능 (향후 SPEC)
- Taxonomy 시각화 (SPEC-TAXONOMY-VIZ-001 참조)

---

## Environment (환경)

### 기술 스택
- **프론트엔드**: React 19.1.1, TypeScript 5.9.3
- **폼 관리**: React Hook Form (최신 stable 버전)
- **검증**: Zod 4.1.12
- **상태 관리**: Zustand 5.0.8
- **HTTP**: Axios 1.13.1, TanStack Query 5.90.5
- **스타일링**: Tailwind CSS 4.1.16

### 백엔드 API
- `POST /api/agents` - Agent 생성
- `GET /api/taxonomies` - Taxonomy 목록 조회
- `GET /api/prompt-templates` - 프롬프트 템플릿 목록

---

## Assumptions (가정)

1. 백엔드 API가 Agent CRUD를 지원한다
2. Taxonomy 데이터가 이미 존재한다
3. 사용자는 인증된 상태이다
4. 프롬프트 템플릿은 미리 정의되어 있다

---

## Requirements (요구사항)

### Ubiquitous Requirements
- **REQ-ACF-U001**: 시스템은 3단계 폼 워크플로우를 제공해야 한다 (기본 정보 → Taxonomy 선택 → 프롬프트 설정)
- **REQ-ACF-U002**: 각 필드는 실시간 검증을 제공해야 한다
- **REQ-ACF-U003**: 사용자는 이전 단계로 돌아가 수정할 수 있어야 한다
- **REQ-ACF-U004**: 최종 단계에서 전체 설정을 미리보기할 수 있어야 한다

### Event-driven Requirements
- **REQ-ACF-E001**: WHEN 사용자가 "다음" 버튼을 클릭하면, 현재 단계의 폼을 검증하고 통과 시 다음 단계로 이동해야 한다
- **REQ-ACF-E002**: WHEN Agent 생성에 성공하면, 성공 메시지와 함께 Agent 상세 페이지로 리디렉션해야 한다
- **REQ-ACF-E003**: WHEN Agent 생성에 실패하면, 에러 메시지를 표시하고 폼을 유지해야 한다

### State-driven Requirements
- **REQ-ACF-S001**: WHILE 폼이 제출 중이면, 버튼을 비활성화하고 로딩 스피너를 표시해야 한다
- **REQ-ACF-S002**: WHILE 필드가 invalid이면, 에러 메시지를 빨간색으로 표시해야 한다

### Optional Features
- **REQ-ACF-O001**: WHERE 폼 데이터가 변경되면, 로컬 스토리지에 자동 저장할 수 있다 (임시 저장)

### Constraints
- **REQ-ACF-C001**: Agent 이름은 3~50자여야 한다
- **REQ-ACF-C002**: 설명은 최대 500자여야 한다
- **REQ-ACF-C003**: 최소 1개 이상의 Taxonomy를 선택해야 한다

---

## Specifications (상세 설계)

### 폼 단계
1. **Step 1: 기본 정보**
   - Agent 이름 (필수, 3-50자)
   - 설명 (선택, 최대 500자)
   - 목적/역할 (필수, 드롭다운: "Research", "Analysis", "Summarization")

2. **Step 2: Taxonomy 선택**
   - Taxonomy 목록 (체크박스 또는 드롭다운)
   - 선택된 Taxonomy 미리보기

3. **Step 3: 프롬프트 설정**
   - 템플릿 선택 (라디오 버튼)
   - 커스텀 프롬프트 입력 (텍스트 에리어)
   - 전체 설정 미리보기

### 데이터 모델
```typescript
interface AgentFormData {
  name: string;
  description?: string;
  purpose: 'research' | 'analysis' | 'summarization';
  taxonomyIds: string[];
  promptTemplate: string;
  customPrompt?: string;
}

const agentFormSchema = z.object({
  name: z.string().min(3).max(50),
  description: z.string().max(500).optional(),
  purpose: z.enum(['research', 'analysis', 'summarization']),
  taxonomyIds: z.array(z.string()).min(1),
  promptTemplate: z.string(),
  customPrompt: z.string().optional(),
});
```

---

## Traceability (추적성)

### TAG 체인
- **@SPEC:AGENT-CREATE-FORM-001** → Agent 생성 폼 요구사항
- **@TEST:AGENT-CREATE-FORM-001** → 폼 검증 테스트, 제출 테스트
- **@CODE:AGENT-CREATE-FORM-001** → React Hook Form, Zod 검증
- **@DOC:AGENT-CREATE-FORM-001** → 사용자 가이드

### 의존성
- **depends_on**: SPEC-FRONTEND-INIT-001, SPEC-TAXONOMY-VIZ-001 (선택)
- **blocks**: SPEC-RESEARCH-AGENT-UI-001

---

## 품질 기준
- 테스트 커버리지 ≥ 85%
- 폼 제출 시간 < 1초
- 모든 필드 검증 통과

---

**작성자**: @spec-builder
