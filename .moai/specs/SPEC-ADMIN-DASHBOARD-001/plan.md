# SPEC-ADMIN-DASHBOARD-001 구현 계획

## @PLAN:ADMIN-DASHBOARD-001

---

## 우선순위별 마일스톤

### Primary Goals
1. **시스템 통계 API 연동** - GET /api/admin/stats
2. **통계 카드 UI** - Agent 수, 문서 수, 사용자 수
3. **Recharts 차트** - Agent 성능 라인 차트
4. **테이블 컴포넌트** - 문서 상태 테이블
5. **테스트** - 통계 로드, 차트 렌더링

### Secondary Goals
1. **실시간 업데이트** - 30초 폴링
2. **에러 알림** - 성능 저하 감지

---

## 기술 접근

### 디렉토리 구조
```
frontend/src/
├─ pages/
│  └─ AdminDashboard.tsx
├─ components/
│  └─ Admin/
│     ├─ SystemStats.tsx
│     ├─ AgentPerformanceChart.tsx
│     ├─ DocumentStatusTable.tsx
│     └─ UserActivityLog.tsx
└─ hooks/
   ├─ useAdminStats.ts
   └─ useAgentPerformance.ts
```

### 구현 순서
1. Phase 1: Admin API 연동
2. Phase 2: 통계 카드 UI
3. Phase 3: Recharts 차트
4. Phase 4: 테이블 컴포넌트
5. Phase 5: 테스트

---

## 테스트 전략
- 통계 API Mock
- 차트 렌더링 검증
- 테이블 데이터 표시

---

**작성자**: @spec-builder
**작성일**: 2025-10-31
