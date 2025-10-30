# @TEST:AGENT-CARD-001 Acceptance Criteria

## 개요

Pokemon-Style Agent Card System의 상세 인수 조건 및 테스트 시나리오입니다. Given-When-Then 형식으로 모든 요구사항의 검증 기준을 정의합니다.

## 테스트 시나리오

### 시나리오 1: AgentCard 렌더링

#### AC-001: 기본 카드 렌더링
**Given** 에이전트 데이터가 다음과 같이 주어졌을 때:
```typescript
{
  agent_id: "123e4567-e89b-12d3-a456-426614174000",
  name: "Breast Cancer Specialist",
  level: 5,
  current_xp: 1200,
  total_documents: 150,
  total_queries: 300,
  avg_faithfulness: 0.85,
  coverage_percent: 75.5,
  created_at: "2025-01-01T00:00:00Z",
  updated_at: "2025-01-02T00:00:00Z"
}
```

**When** AgentCard 컴포넌트가 렌더링되면

**Then** 다음이 표시되어야 한다:
- ✅ 에이전트 이름: "Breast Cancer Specialist"
- ✅ 레벨 배지: "Lv.5 EPIC" (보라색)
- ✅ XP 진행 바: 200/500 XP (40%)
- ✅ 스탯:
  - 지식: "지식 150개"
  - 대화: "대화 300회"
  - 품질: "품질 85%" (황색)
- ✅ 액션 버튼: "대화", "기록"
- ✅ 보라색 테두리 + 8px blur 글로우

#### AC-002: 긴 이름 처리
**Given** 에이전트 이름이 "Very Long Agent Name That Should Be Truncated With Ellipsis"일 때

**When** AgentCard가 렌더링되면

**Then** 다음이 적용되어야 한다:
- ✅ 최대 2줄 표시
- ✅ 2줄 초과 시 말줄임표(...)
- ✅ 전체 이름은 title 속성으로 표시 (hover 시 툴팁)

#### AC-003: null/undefined 데이터 처리
**Given** avg_faithfulness가 null일 때

**When** AgentCard가 렌더링되면

**Then** 다음이 표시되어야 한다:
- ✅ 품질 점수: "품질 0%" (적색)
- ✅ 에러 없이 정상 렌더링

---

### 시나리오 2: 희귀도 시스템

#### AC-004: Common 희귀도 (Lv.1-2)
**Given** 에이전트 레벨이 1일 때

**When** RarityBadge와 카드 테두리가 렌더링되면

**Then** 다음이 적용되어야 한다:
- ✅ 배지: "Lv.1 COMMON" (⭐ 아이콘)
- ✅ 테두리: 2px solid #9CA3AF (회색)
- ✅ 그림자: shadow-sm (작은 그림자)
- ✅ 글로우 없음

#### AC-005: Rare 희귀도 (Lv.3-4)
**Given** 에이전트 레벨이 3일 때

**When** 카드가 렌더링되면

**Then** 다음이 적용되어야 한다:
- ✅ 배지: "Lv.3 RARE" (🔹 아이콘)
- ✅ 테두리: 2px solid #3B82F6 (청색)
- ✅ 그림자: shadow-md shadow-blue-500/50
- ✅ 글로우 없음

#### AC-006: Epic 희귀도 (Lv.5-7)
**Given** 에이전트 레벨이 6일 때

**When** 카드가 렌더링되면

**Then** 다음이 적용되어야 한다:
- ✅ 배지: "Lv.6 EPIC" (💎 아이콘)
- ✅ 테두리: 2px solid #8B5CF6 (보라색)
- ✅ 그림자: shadow-lg shadow-purple-500/50
- ✅ 8px blur 글로우 효과

#### AC-007: Legendary 희귀도 (Lv.8+)
**Given** 에이전트 레벨이 10일 때

**When** 카드가 렌더링되면

**Then** 다음이 적용되어야 한다:
- ✅ 배지: "Lv.10 LEGENDARY" (👑 아이콘)
- ✅ 테두리: 4px, 무지개 그라디언트 (yellow → pink → purple)
- ✅ 그림자: shadow-xl shadow-yellow-500/50
- ✅ 12px blur 글로우 + pulse 애니메이션
- ✅ 반짝임 효과 (CSS animation)

#### AC-008: 희귀도 전환 애니메이션
**Given** 에이전트가 Lv.4 (Rare)에서 Lv.5 (Epic)으로 레벨업했을 때

**When** 카드가 업데이트되면

**Then** 다음 애니메이션이 실행되어야 한다:
- ✅ 테두리 색상 전환 (blue → purple, 0.5초 ease-in-out)
- ✅ 그림자 전환 (blue → purple, 0.5초)
- ✅ 배지 아이콘 전환 (🔹 → 💎)

---

### 시나리오 3: XP 진행 바

#### AC-009: XP 진행도 계산
**Given** 에이전트가 다음 상태일 때:
- current_xp: 450
- level: 4

**When** ProgressBar가 렌더링되면

**Then** 다음이 계산되어야 한다:
- ✅ 레벨 4 시작 XP: 300
- ✅ 레벨 5 시작 XP: 600
- ✅ 현재 진행도: 450 - 300 = 150 XP
- ✅ 최대 XP: 600 - 300 = 300 XP
- ✅ 백분율: (150 / 300) * 100 = 50%
- ✅ 텍스트: "150 / 300 XP"
- ✅ 진행 바 너비: 50%

#### AC-010: 희귀도별 그라디언트
**Given** 에이전트 희귀도가 Epic일 때

**When** ProgressBar가 렌더링되면

**Then** 다음이 적용되어야 한다:
- ✅ 배경색: #E5E7EB (gray-200)
- ✅ 진행 바 그라디언트: `bg-gradient-to-r from-purple-500 to-pink-500`
- ✅ 진행 바 높이: 8px
- ✅ border-radius: rounded-full

#### AC-011: XP 증가 애니메이션
**Given** 에이전트 XP가 100에서 150으로 증가했을 때

**When** ProgressBar가 업데이트되면

**Then** 다음 애니메이션이 실행되어야 한다:
- ✅ framer-motion animate: width 0% → 50% (0.3초 ease-out)
- ✅ 부드러운 전환 (no jank)
- ✅ 텍스트 변경: "100 / 300 XP" → "150 / 300 XP"

#### AC-012: 레벨업 임계값 도달
**Given** 에이전트 XP가 595에서 605로 증가했을 때 (레벨업 임계값 600)

**When** ProgressBar가 업데이트되면

**Then** 다음이 발생해야 한다:
- ✅ 레벨 변경: 4 → 5
- ✅ XP 진행도 리셋: 605 - 600 = 5 XP
- ✅ 새 최대 XP: 1000 - 600 = 400 XP
- ✅ 진행 바 너비: (5 / 400) * 100 = 1.25%
- ✅ useLevelUpNotification 트리거

---

### 시나리오 4: 스탯 표시

#### AC-013: 기본 스탯 렌더링
**Given** 에이전트 데이터가 다음과 같을 때:
```typescript
{
  total_documents: 1250,
  total_queries: 3420,
  avg_faithfulness: 0.92
}
```

**When** StatDisplay가 렌더링되면

**Then** 다음이 표시되어야 한다:
- ✅ "지식 1,250개" (쉼표 구분)
- ✅ "대화 3,420회" (쉼표 구분)
- ✅ "품질 92%" (녹색)

#### AC-014: 품질 점수 색상 로직
**Given** 다양한 avg_faithfulness 값이 주어졌을 때

**When** StatDisplay가 렌더링되면

**Then** 다음 색상이 적용되어야 한다:

| avg_faithfulness | 품질 점수 | 색상 (Tailwind) |
|------------------|----------|----------------|
| 0.95            | 95%      | text-green-600 |
| 0.85            | 85%      | text-yellow-600 |
| 0.65            | 65%      | text-red-600 |
| null            | 0%       | text-red-600 |

#### AC-015: 큰 숫자 포맷팅
**Given** total_queries가 1234567일 때

**When** StatDisplay가 렌더링되면

**Then** 다음이 표시되어야 한다:
- ✅ "대화 1,234,567회" (천 단위 쉼표)
- ⚠️ 또는 "대화 1.2M회" (K/M 단위 축약) - 선택 사항

---

### 시나리오 5: XP 계산 로직

#### AC-016: 채팅 완료 XP
**Given** 사용자가 에이전트와 채팅을 완료했을 때

**When** calculateXPGain('chat')이 호출되면

**Then** 다음이 반환되어야 한다:
- ✅ 반환 값: 10
- ✅ 플로팅 텍스트: "+10 XP" (1초 동안 위로 이동 + 페이드아웃)

#### AC-017: 긍정 피드백 XP
**Given** 사용자가 긍정 피드백(👍)을 남겼을 때

**When** calculateXPGain('feedback')이 호출되면

**Then** 다음이 반환되어야 한다:
- ✅ 반환 값: 50
- ✅ 플로팅 텍스트: "+50 XP" (강조 색상: 청색)

#### AC-018: RAGAS 보너스 (고품질)
**Given** 응답의 avg_faithfulness가 0.95일 때

**When** calculateXPGain('ragas', 0.95)이 호출되면

**Then** 다음이 반환되어야 한다:
- ✅ 반환 값: 100
- ✅ 플로팅 텍스트: "+100 XP 🌟" (금색 색상 + 특수 효과)

#### AC-019: RAGAS 보너스 (저품질)
**Given** 응답의 avg_faithfulness가 0.75일 때

**When** calculateXPGain('ragas', 0.75)이 호출되면

**Then** 다음이 반환되어야 한다:
- ✅ 반환 값: 0 (임계값 0.9 미달)
- ✅ XP 증가 없음

---

### 시나리오 6: 레벨 계산

#### AC-020: 레벨 1-9 매핑
**Given** 다양한 XP 값이 주어졌을 때

**When** getLevelFromXP()가 호출되면

**Then** 다음 레벨이 반환되어야 한다:

| XP  | Expected Level |
|-----|---------------|
| 0   | 1             |
| 50  | 1             |
| 100 | 2             |
| 299 | 2             |
| 300 | 3             |
| 600 | 4             |
| 1000| 5             |
| 1500| 6             |
| 2100| 7             |
| 2900| 8             |
| 3900| 9             |
| 5000| 10            |

#### AC-021: XP 진행도 계산
**Given** current_xp = 450, level = 4일 때

**When** getXPProgress(450, 4)가 호출되면

**Then** 다음이 반환되어야 한다:
```typescript
{
  current: 150,    // 450 - 300 (level 4 시작 XP)
  max: 300,        // 600 - 300 (level 5 - level 4)
  percentage: 50   // (150 / 300) * 100
}
```

---

### 시나리오 7: 레벨업 모달

#### AC-022: 레벨업 모달 표시
**Given** 에이전트가 Lv.4 → Lv.5로 레벨업했을 때

**When** LevelUpModal이 열리면

**Then** 다음이 표시되어야 한다:
- ✅ 모달 제목: "🎉 축하합니다!"
- ✅ 새 레벨: "Lv.5 달성!"
- ✅ 희귀도 변경: "RARE → EPIC 진화!" (Rare → Epic이므로 표시)
- ✅ Confetti 애니메이션 (화면 전체, 3초)
- ✅ "확인" 버튼

#### AC-023: 희귀도 미변경 레벨업
**Given** 에이전트가 Lv.5 → Lv.6로 레벨업했을 때 (둘 다 Epic)

**When** LevelUpModal이 열리면

**Then** 다음이 표시되어야 한다:
- ✅ 모달 제목: "🎉 축하합니다!"
- ✅ 새 레벨: "Lv.6 달성!"
- ❌ 희귀도 변경 메시지 없음
- ✅ Confetti 애니메이션

#### AC-024: 모달 닫기
**Given** 레벨업 모달이 열려 있을 때

**When** "확인" 버튼을 클릭하면

**Then** 다음이 발생해야 한다:
- ✅ 모달 페이드아웃 (0.3초)
- ✅ Confetti 중지
- ✅ isOpen 상태 false로 변경

#### AC-025: 모달 외부 클릭 닫기
**Given** 레벨업 모달이 열려 있을 때

**When** 모달 외부 영역을 클릭하면

**Then** 다음이 발생해야 한다:
- ✅ 모달 닫힘
- ✅ Confetti 중지

---

### 시나리오 8: 애니메이션 효과

#### AC-026: 플로팅 XP 텍스트
**Given** 에이전트가 50 XP를 획득했을 때

**When** 플로팅 텍스트 애니메이션이 실행되면

**Then** 다음이 발생해야 한다:
- ✅ 텍스트: "+50 XP" (청색)
- ✅ 시작 위치: 카드 중앙
- ✅ 이동: 위로 30px 이동 (1초 동안)
- ✅ 투명도: 1.0 → 0.0 (페이드아웃)
- ✅ framer-motion initial/animate 사용

#### AC-027: Confetti 애니메이션
**Given** 레벨업이 발생했을 때

**When** ConfettiAnimation이 실행되면

**Then** 다음이 적용되어야 한다:
- ✅ react-confetti 사용
- ✅ 지속 시간: 3초
- ✅ 색상: 희귀도별 색상 (Epic → 보라색 계열)
- ✅ 중력: 0.1 (천천히 떨어짐)
- ✅ 3초 후 자동 중지

#### AC-028: 카드 스케일 애니메이션
**Given** 레벨업이 발생했을 때

**When** AgentCard에 스케일 애니메이션이 적용되면

**Then** 다음이 실행되어야 한다:
- ✅ 스케일: 1.0 → 1.05 → 1.0 (0.5초)
- ✅ ease-in-out 전환
- ✅ 3회 반복 (총 1.5초)

#### AC-029: 테두리 펄스 효과
**Given** 레벨업이 발생했을 때

**When** 카드 테두리에 펄스 효과가 적용되면

**Then** 다음이 실행되어야 한다:
- ✅ box-shadow 밝기 증가/감소 (0.5초 주기)
- ✅ 3회 반복
- ✅ CSS animation 사용

---

### 시나리오 9: 반응형 그리드

#### AC-030: Mobile 레이아웃 (< 640px)
**Given** 화면 너비가 375px일 때

**When** HomePage가 렌더링되면

**Then** 다음이 적용되어야 한다:
- ✅ 그리드 열: 1열
- ✅ 카드 간격: 16px (gap-4)
- ✅ 카드 너비: 280px 고정
- ✅ 중앙 정렬

#### AC-031: Tablet 레이아웃 (640-1024px)
**Given** 화면 너비가 768px일 때

**When** HomePage가 렌더링되면

**Then** 다음이 적용되어야 한다:
- ✅ 그리드 열: 2열
- ✅ 카드 간격: 16px
- ✅ 카드 너비: 280px 고정

#### AC-032: Desktop 레이아웃 (1024-1536px)
**Given** 화면 너비가 1280px일 때

**When** HomePage가 렌더링되면

**Then** 다음이 적용되어야 한다:
- ✅ 그리드 열: 3열
- ✅ 카드 간격: 16px
- ✅ 카드 너비: 280px 고정

#### AC-033: Large Desktop 레이아웃 (> 1536px)
**Given** 화면 너비가 1920px일 때

**When** HomePage가 렌더링되면

**Then** 다음이 적용되어야 한다:
- ✅ 그리드 열: 4열
- ✅ 카드 간격: 16px
- ✅ 카드 너비: 280px 고정

#### AC-034: 반응형 전환 애니메이션
**Given** 화면 크기가 768px → 1024px로 변경되었을 때

**When** 그리드 레이아웃이 재조정되면

**Then** 다음이 발생해야 한다:
- ✅ 부드러운 전환 (transition-all duration-300)
- ✅ 카드 재배치 애니메이션 (framer-motion layout)
- ✅ 레이아웃 시프트 없음

---

### 시나리오 10: TanStack Query 통합

#### AC-035: 데이터 로딩
**Given** HomePage가 마운트되었을 때

**When** useAgents 훅이 실행되면

**Then** 다음이 발생해야 한다:
- ✅ GET /api/v1/agents 호출
- ✅ isLoading = true
- ✅ 스켈레톤 카드 3개 표시
- ✅ 로딩 스피너 표시

#### AC-036: 데이터 로딩 성공
**Given** API가 에이전트 목록을 반환했을 때

**When** 데이터가 로드되면

**Then** 다음이 발생해야 한다:
- ✅ isLoading = false
- ✅ isSuccess = true
- ✅ 스켈레톤 카드 숨김
- ✅ 실제 AgentCard 렌더링 (받은 개수만큼)

#### AC-037: 데이터 로딩 실패
**Given** API가 500 에러를 반환했을 때

**When** 에러가 발생하면

**Then** 다음이 표시되어야 한다:
- ✅ isError = true
- ✅ 에러 메시지: "에이전트 목록을 불러올 수 없습니다"
- ✅ 재시도 버튼
- ✅ 스켈레톤 카드 숨김

#### AC-038: Stale 데이터 리페치
**Given** 데이터가 로드된 지 35초가 지났을 때 (staleTime: 30초)

**When** 사용자가 윈도우에 포커스하면

**Then** 다음이 발생해야 한다:
- ✅ GET /api/v1/agents 재호출
- ✅ 백그라운드 리페치 (UI 변경 없음)
- ✅ 새 데이터로 업데이트

#### AC-039: 폴링 (선택 사항)
**Given** 폴링이 활성화되었을 때 (refetchInterval: 60000)

**When** 60초마다

**Then** 다음이 발생해야 한다:
- ✅ GET /api/v1/agents 자동 호출
- ✅ 백그라운드 업데이트
- ✅ 새 에이전트 추가 시 자동 표시

#### AC-040: 빈 데이터 처리
**Given** API가 빈 배열을 반환했을 때

**When** 데이터가 로드되면

**Then** 다음이 표시되어야 한다:
- ✅ 빈 상태 메시지: "등록된 에이전트가 없습니다"
- ✅ CTA 버튼: "새 에이전트 만들기"
- ✅ 일러스트레이션 (선택 사항)

---

### 시나리오 11: 접근성

#### AC-041: ARIA 레이블
**Given** AgentCard가 렌더링되었을 때

**When** 스크린 리더가 카드를 읽으면

**Then** 다음이 읽혀야 한다:
- ✅ role="article"
- ✅ aria-label="Agent card: {agent.name}"
- ✅ ProgressBar: aria-valuenow={current}, aria-valuemax={max}
- ✅ 버튼: aria-label="대화", aria-label="기록"

#### AC-042: 키보드 네비게이션
**Given** 사용자가 키보드를 사용할 때

**When** Tab 키를 누르면

**Then** 다음이 포커스되어야 한다:
1. ✅ 첫 번째 카드의 "대화" 버튼
2. ✅ 첫 번째 카드의 "기록" 버튼
3. ✅ 두 번째 카드의 "대화" 버튼
4. ✅ (계속)

**And** Enter 키를 누르면:
- ✅ 버튼 클릭 이벤트 트리거

#### AC-043: 포커스 표시
**Given** 버튼에 포커스가 있을 때

**When** 시각적으로 확인하면

**Then** 다음이 표시되어야 한다:
- ✅ 2px solid outline (청색)
- ✅ outline-offset: 2px
- ✅ focus-visible 사용 (마우스 클릭 시에는 outline 없음)

#### AC-044: 색상 대비
**Given** WCAG 2.1 AA 기준일 때

**When** 모든 텍스트와 배경의 대비를 확인하면

**Then** 다음을 만족해야 한다:
- ✅ 일반 텍스트: 최소 4.5:1 대비
- ✅ 큰 텍스트 (18px+): 최소 3:1 대비
- ✅ 품질 점수 색상: 녹색/황색/적색 모두 대비 충족

---

### 시나리오 12: 품질 점수 계산

#### AC-045: RAGAS 전용 점수
**Given** 피드백 데이터가 없고 avg_faithfulness = 0.85일 때

**When** calculateQualityScore()가 호출되면

**Then** 다음이 반환되어야 한다:
- ✅ 품질 점수: 85%
- ✅ 계산식: 0.85 * 100 = 85

#### AC-046: 피드백 + RAGAS 가중치
**Given** 다음 데이터가 주어졌을 때:
```typescript
{
  avg_faithfulness: 0.9,
  positive_feedbacks: 80,
  negative_feedbacks: 20
}
```

**When** calculateQualityScore()가 호출되면

**Then** 다음이 계산되어야 한다:
- ✅ feedbackScore: 80 / (80 + 20) = 0.8
- ✅ ragasScore: 0.9
- ✅ 품질 점수: (0.8 * 0.7 + 0.9 * 0.3) * 100 = 83%

#### AC-047: 피드백 없음 처리
**Given** positive_feedbacks = 0, negative_feedbacks = 0일 때

**When** calculateQualityScore()가 호출되면

**Then** 다음이 발생해야 한다:
- ✅ 피드백 무시 (분모가 0이므로)
- ✅ RAGAS 점수만 사용
- ✅ ZeroDivisionError 없음

#### AC-048: null 데이터 처리
**Given** avg_faithfulness = null, 피드백 데이터 없음일 때

**When** calculateQualityScore()가 호출되면

**Then** 다음이 반환되어야 한다:
- ✅ 품질 점수: 0%
- ✅ 에러 없음

---

## 성능 요구사항

### AC-049: 카드 렌더링 성능
**Given** 100개의 AgentCard가 렌더링되었을 때

**When** 스크롤 및 상호작용을 수행하면

**Then** 다음을 만족해야 한다:
- ✅ 초기 렌더링: < 500ms
- ✅ 스크롤 프레임 레이트: 60fps
- ✅ React DevTools Profiler: 평균 렌더 시간 < 16ms

### AC-050: 애니메이션 성능
**Given** 레벨업 모달이 열렸을 때

**When** Confetti 및 스케일 애니메이션이 실행되면

**Then** 다음을 만족해야 한다:
- ✅ 프레임 레이트: 60fps
- ✅ Lighthouse Performance: 90+
- ✅ CPU 사용률: < 50% (Chrome DevTools)

### AC-051: 번들 사이즈
**Given** 프로덕션 빌드를 생성했을 때

**When** 번들 사이즈를 확인하면

**Then** 다음을 만족해야 한다:
- ✅ 총 JS 번들: < 500KB (gzip)
- ✅ react-confetti: < 20KB
- ✅ framer-motion: < 100KB

---

## 크로스 브라우저 테스트

### AC-052: Chrome 호환성
**Given** Chrome 120+ 브라우저일 때

**When** 모든 기능을 테스트하면

**Then** 다음이 동작해야 한다:
- ✅ 모든 애니메이션
- ✅ Tailwind 그라디언트
- ✅ Confetti 렌더링

### AC-053: Firefox 호환성
**Given** Firefox 120+ 브라우저일 때

**When** 모든 기능을 테스트하면

**Then** 다음이 동작해야 한다:
- ✅ 모든 애니메이션
- ✅ Tailwind 그라디언트
- ✅ Confetti 렌더링

### AC-054: Safari 호환성
**Given** Safari 17+ 브라우저일 때

**When** 모든 기능을 테스트하면

**Then** 다음이 동작해야 한다:
- ✅ 모든 애니메이션
- ✅ Tailwind 그라디언트
- ✅ Confetti 렌더링
- ⚠️ backdrop-filter 폴백 확인

---

## Quality Gate

### 자동화 테스트 통과 조건
- ✅ 단위 테스트: 100% 통과 (50+ 테스트)
- ✅ 컴포넌트 테스트: 100% 통과 (20+ 테스트)
- ✅ 통합 테스트: 100% 통과 (10+ 테스트)
- ✅ 테스트 커버리지: 80% 이상

### 수동 테스트 체크리스트
- [ ] Chrome에서 모든 AC 시나리오 검증
- [ ] Firefox에서 모든 AC 시나리오 검증
- [ ] Safari에서 모든 AC 시나리오 검증
- [ ] Mobile 반응형 테스트 (375px, 768px)
- [ ] Tablet 반응형 테스트 (768px, 1024px)
- [ ] Desktop 반응형 테스트 (1280px, 1920px)
- [ ] 접근성 테스트 (axe DevTools)
- [ ] 성능 테스트 (Lighthouse)

### Lighthouse 기준
- ✅ Performance: 90+
- ✅ Accessibility: 100
- ✅ Best Practices: 95+
- ✅ SEO: 90+ (해당하는 경우)

---

**작성일**: 2025-10-30
**작성자**: @Alfred
**버전**: 0.0.1
