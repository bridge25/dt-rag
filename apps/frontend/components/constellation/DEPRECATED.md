# ⚠️ DEPRECATED - 사용하지 마세요

**상태**: DEPRECATED (2025-11-28)
**대체 위치**: `/components/taxonomy/`

---

## 이 폴더의 컴포넌트들은 더 이상 사용되지 않습니다.

### 대체 컴포넌트 매핑

| 구버전 (constellation/) | 신버전 (taxonomy/) |
|------------------------|-------------------|
| ConstellationNode.tsx | TaxonomyGraphNode.tsx |
| ConstellationGraph.tsx | taxonomy/page.tsx (내장) |
| ConstellationControlPanel.tsx | taxonomy/page.tsx (TaxonomyControlPanel) |
| ConstellationEdge.tsx | (React Flow 기본 사용) |
| TaxonomyExplorer.tsx | taxonomy/page.tsx |

### 왜 deprecated 되었나요?

1. **중복 코드**: taxonomy/page.tsx에서 React Flow 직접 사용
2. **디자인 불일치**: 구버전은 뉴디자인2 스펙 미적용
3. **유지보수 문제**: 두 곳에서 비슷한 코드 관리 불필요

### 마이그레이션 완료 여부

- [x] taxonomy/page.tsx로 기능 통합
- [x] TaxonomyGraphNode.tsx에 3D 구체 스타일 적용
- [x] 우주 배경 효과 적용
- [x] 호버 효과 (HOVERED 배지, NODE DETAILS 툴팁) 적용

### 삭제 예정

다음 major 버전에서 이 폴더를 완전히 삭제할 예정입니다.
삭제 전까지 이 컴포넌트들을 import하지 마세요.

---

**최신 디자인 가이드**: `/apps/frontend/DESIGN-SYSTEM.md`
