---
id: BTN-001
title: 재사용 가능한 버튼 컴포넌트
domain: ui-component
version: 1.0.0
status: completed
created: 2025-10-24
author: spec-builder
---

# SPEC-BTN-001: 재사용 가능한 버튼 컴포넌트

## HISTORY

### v1.0.0 (2025-10-24)
- **RETROACTIVE DOCUMENTATION**: 기존 구현 완료된 공통 버튼 컴포넌트를 문서화
- 다양한 variant 지원 (primary, secondary, danger)
- 크기 옵션 지원 (sm, md, lg)
- 로딩 상태 및 비활성화 상태 관리

---

## Environment

**WHEN** 애플리케이션 전반에서 일관된 스타일과 동작을 가진 버튼이 필요한 경우

---

## Assumptions

- Next.js 15 App Router 환경에서 실행
- React 19.0.0 사용
- Tailwind CSS 기반 스타일링
- 버튼은 폼 제출, 액션 트리거, 네비게이션 등 다양한 용도로 사용됨

---

## Requirements

**R1**: 시스템은 3가지 시각적 변형(variant)을 제공해야 한다 (primary, secondary, danger)
**R2**: 시스템은 3가지 크기 옵션을 제공해야 한다 (sm, md, lg)
**R3**: 버튼은 로딩 상태를 표시할 수 있어야 한다
**R4**: 버튼은 비활성화 상태를 지원해야 한다
**R5**: 모든 HTML button 속성을 지원해야 한다 (onClick, type, disabled 등)

---

## Specifications

### Button 컴포넌트 (`app/components/ui/Button.tsx`)

**Props Interface**:
```typescript
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  isLoading?: boolean
  children: React.ReactNode
}
```

**Variant 스타일**:
- **primary**: 파란색 배경 (`bg-blue-600`, hover: `bg-blue-700`)
- **secondary**: 회색 배경 (`bg-gray-600`, hover: `bg-gray-700`)
- **danger**: 빨간색 배경 (`bg-red-600`, hover: `bg-red-700`)

**Size 스타일**:
- **sm**: `px-3 py-1.5 text-sm`
- **md**: `px-4 py-2 text-base` (기본값)
- **lg**: `px-6 py-3 text-lg`

**상태별 동작**:
- **isLoading=true**: Spinner 표시, 클릭 비활성화, 투명도 감소
- **disabled=true**: 클릭 비활성화, 회색 배경, 커서 변경 (`cursor-not-allowed`)

**접근성**:
- 키보드 포커스 링 표시 (`focus:ring-2`)
- disabled 상태에서 적절한 시각적 피드백

### 파일 구조

```
app/
└── components/
    └── ui/
        └── Button.tsx              # @CODE:BTN-001:UI
```

---

## Traceability

- **@SPEC:BTN-001**: 본 문서
- **@CODE:BTN-001:UI**: `app/components/ui/Button.tsx`
- **@TEST:BTN-001**: (미구현 - 테스트 누락 상태)

---

## Acceptance Criteria

### AC1: Variant 렌더링

**Given** Button 컴포넌트가 존재하고
**When** `variant="primary"`로 렌더링하면
**Then**
- 파란색 배경이 적용되어야 함
- 호버 시 더 진한 파란색으로 변경되어야 함

**When** `variant="danger"`로 렌더링하면
**Then**
- 빨간색 배경이 적용되어야 함

### AC2: 크기 옵션

**Given** Button 컴포넌트가 존재하고
**When** `size="sm"`로 렌더링하면
**Then**
- 작은 패딩과 폰트 크기가 적용되어야 함

**When** `size="lg"`로 렌더링하면
**Then**
- 큰 패딩과 폰트 크기가 적용되어야 함

### AC3: 로딩 상태

**Given** Button 컴포넌트가 존재하고
**When** `isLoading=true`로 렌더링하면
**Then**
- Spinner가 표시되어야 함
- 버튼이 비활성화되어야 함
- 투명도가 감소되어야 함

### AC4: 비활성화 상태

**Given** Button 컴포넌트가 존재하고
**When** `disabled=true`로 렌더링하면
**Then**
- 클릭 이벤트가 발생하지 않아야 함
- 회색 배경이 적용되어야 함
- 커서가 `not-allowed`로 변경되어야 함

---

## Notes

- 본 SPEC은 이미 구현 완료된 코드를 소급 문서화한 것임
- 실제 구현은 2025-10-24 이전에 완료되었으며, TAG는 누락된 상태
- **테스트 누락**: `Button.tsx`에 대한 단위 테스트 없음
- **개선 권장사항**: Storybook 또는 Chromatic을 통한 시각적 회귀 테스트 추가 고려
- 다음 단계: `/alfred:3-sync`를 통해 TAG 추가 및 테스트 보완 필요
