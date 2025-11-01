# SPEC-DARK-MODE-001 인수 기준

## @TEST:DARK-MODE-001

---

## 기능 인수 기준

### 1. 테마 전환

#### 시나리오 1.1: Light → Dark 전환
**Given**: 현재 테마가 Light이고,
**When**: Dark Mode 토글을 클릭하면,
**Then**:
- 배경색이 어두워져야 한다
- 텍스트 색상이 밝아져야 한다
- 로컬 스토리지에 'dark'가 저장되어야 한다

**검증**:
```typescript
test('should switch to dark mode', async () => {
  render(<App />);

  const toggle = screen.getByRole('button', { name: 'Dark Mode' });
  fireEvent.click(toggle);

  await waitFor(() => {
    expect(document.documentElement).toHaveClass('dark');
    expect(localStorage.getItem('theme')).toBe('dark');
  });
});
```

---

### 2. 시스템 테마 감지

#### 시나리오 2.1: 시스템 다크모드 적용
**Given**: 시스템 설정이 Dark Mode이고,
**When**: 페이지를 처음 로드하면,
**Then**:
- Dark Mode가 자동으로 적용되어야 한다

---

## Definition of Done
- ✅ 테마 전환 동작
- ✅ 로컬 스토리지 저장
- ✅ WCAG AA 색상 대비

---

**작성자**: @spec-builder
**작성일**: 2025-10-31
