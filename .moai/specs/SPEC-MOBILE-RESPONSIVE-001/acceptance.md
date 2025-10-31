# SPEC-MOBILE-RESPONSIVE-001 인수 기준

## @TEST:MOBILE-RESPONSIVE-001

---

## 기능 인수 기준

### 1. 반응형 레이아웃

#### 시나리오 1.1: 모바일 화면 (< 768px)
**Given**: Viewport 너비가 375px이고,
**When**: 페이지를 렌더링하면,
**Then**:
- 햄버거 메뉴가 표시되어야 한다
- 그리드가 1열로 표시되어야 한다

**검증**:
```typescript
test('should show mobile layout on small screen', async () => {
  global.innerWidth = 375;
  render(<App />);

  expect(screen.getByTestId('hamburger-menu')).toBeInTheDocument();
  expect(screen.getByTestId('grid')).toHaveClass('grid-cols-1');
});
```

#### 시나리오 1.2: 데스크톱 화면 (≥ 1024px)
**Given**: Viewport 너비가 1440px이고,
**When**: 페이지를 렌더링하면,
**Then**:
- 데스크톱 네비게이션이 표시되어야 한다
- 그리드가 3열로 표시되어야 한다

---

### 2. 터치 최적화

#### 시나리오 2.1: 터치 타겟 크기
**Given**: 모바일 화면이고,
**When**: 버튼을 렌더링하면,
**Then**:
- 버튼 크기가 최소 44x44px이어야 한다

---

## Definition of Done
- ✅ 3가지 브레이크포인트 동작
- ✅ 모바일 Lighthouse ≥ 85
- ✅ 터치 타겟 ≥ 44px

---

**작성자**: @spec-builder
**작성일**: 2025-10-31
