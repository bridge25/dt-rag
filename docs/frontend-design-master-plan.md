# DT-RAG 프론트엔드 마스터 플랜 v2.0

> **작성일**: 2025-10-30
> **버전**: v2.0.0
> **프로젝트**: Dynamic Taxonomy RAG System
> **목적**: 사용자 중심 SaaS 플랫폼 프론트엔드 설계

---

## 📋 목차

1. [프로젝트 개요](#1-프로젝트-개요)
2. [핵심 컨셉](#2-핵심-컨셉)
3. [주요 기능 흐름](#3-주요-기능-흐름)
4. [UI/UX 디자인 가이드](#4-uiux-디자인-가이드)
5. [에이전트 시스템](#5-에이전트-시스템)
6. [TAXONOMY 시각화](#6-taxonomy-시각화)
7. [경험치 & 게이미피케이션](#7-경험치--게이미피케이션)
8. [페이지 구조](#8-페이지-구조)
9. [기술 스택](#9-기술-스택)
10. [API 연동 계획](#10-api-연동-계획)
11. [구현 우선순위](#11-구현-우선순위)

---

## 1. 프로젝트 개요

### 1.1 서비스 정의

**DT-RAG**는 단순한 RAG 검색 도구가 아닌, **"지식 베이스 빌딩 + 전문 에이전트 육성 플랫폼"**입니다.

사용자는:
- 자신만의 **지식 베이스(TAXONOMY)**를 구축하고
- 특정 지식 영역을 담당하는 **전문 에이전트**를 생성/육성하며
- 에이전트와 대화하며 **실시간 피드백**으로 성능을 향상시킵니다

### 1.2 핵심 가치 제안

| 기존 RAG 서비스 | DT-RAG |
|----------------|--------|
| 단순 문서 업로드 → 검색 | 지식 자동 수집 + 체계적 분류 |
| 일반 챗봇 | 전문 에이전트 육성 (레벨/경험치) |
| 관리자 도구 중심 | 사용자 경험 중심 (게이미피케이션) |
| 고정된 지식 베이스 | 성장하는 TAXONOMY (버전 관리) |

### 1.3 타겟 사용자

- **개인 연구자**: 특정 분야 전문 지식 축적 및 활용
- **콘텐츠 크리에이터**: 주제별 리서치 자동화
- **기업 팀**: 부서별/프로젝트별 지식 관리
- **교육자/학생**: 학습 자료 체계화 및 맞춤형 튜터 생성

---

## 2. 핵심 컨셉

### 2.1 세 가지 핵심 축

```
┌─────────────────────────────────────────────────┐
│                                                  │
│  1️⃣ 지식 수집 (데이터 주입)                      │
│  ↓                                               │
│  2️⃣ 지식 구조화 (TAXONOMY)                       │
│  ↓                                               │
│  3️⃣ 지식 활용 (에이전트)                         │
│                                                  │
└─────────────────────────────────────────────────┘
```

### 2.2 차별화 포인트

#### ✨ **리서치 에이전트 (자동 지식 수집)**
- 사용자: "암 전문 의학박사 에이전트 만들고 싶어"
- 시스템:
  1. 필요한 지식 유형 정의 (종양학, 치료법, 최신 연구...)
  2. 웹에서 관련 논문/자료 자동 수집
  3. TAXONOMY에 자동 분류
  4. HITL 검증 후 최종 반영

#### 🗂️ **시각적 TAXONOMY 탐색**
- 다단계 카테고리를 **줌 인/아웃 가능한 트리**로 표시
- 드래그로 영역 선택 → 에이전트 지식 범위 설정
- 버전 관리 (v1.0 → v2.0) 및 비교 기능

#### 🎮 **게임형 에이전트 육성**
- NFT 카드 스타일의 에이전트 디스플레이
- 경험치/레벨/레어리티 시스템
- 실제 성능(RAGAS 점수) 기반 성장

---

## 3. 주요 기능 흐름

### 3.1 사용자 여정 (User Journey)

```
로그인
  ↓
[메인 화면] 에이전트 카드 확인
  ↓
┌──────────────┬──────────────┬──────────────┐
│              │              │              │
│ 🔹 시나리오 1 │ 🔹 시나리오 2 │ 🔹 시나리오 3 │
│ 데이터 추가   │ 에이전트 생성│ 에이전트 사용│
│              │              │              │
└──────────────┴──────────────┴──────────────┘
```

---

### 3.2 시나리오 1: 데이터 수집 & 주입

#### **방법 A: 직접 업로드**
```
[📤 데이터 업로드] 페이지
  ↓
드래그 앤 드롭 (PDF, DOCX, TXT, JPG...)
  ↓
백그라운드 처리:
  1. 텍스트 추출 (OCR 포함)
  2. PII 필터링
  3. 청킹 (Chunking)
  4. 임베딩 생성
  5. 자동 분류 (ML Classifier)
  ↓
HITL 큐 (신뢰도 < 0.7인 경우)
  ↓
TAXONOMY에 반영
```

#### **방법 B: 리서치 에이전트 활용**
```
[📤 데이터 업로드] 페이지 → 대화창
  ↓
사용자: "암 전문 의학박사 에이전트 만들고 싶어"
  ↓
리서치 에이전트 (백엔드 구현 예정):
  1. LLM으로 필요 지식 유형 정의
     - 종양학 기초
     - 항암 치료법
     - 임상 연구 동향
     - 환자 상담 가이드
  ↓
  2. 각 유형별 웹 서치 (Brave Search, SerpAPI 등)
     - 논문 (PubMed, arXiv)
     - 의료 가이드라인
     - 최신 뉴스
  ↓
  3. 수집 진행 상황 UI 표시
     [████████░░] 80% - 임상 연구 수집 중...
  ↓
  4. 사용자 확인 (중간 승인)
     "이런 자료들을 찾았어요. 수집할까요?"
     [✓ 승인] [✗ 거부] [⚙️ 조정]
  ↓
  5. TAXONOMY에 자동 분류 및 저장
```

**UI 컴포넌트**:
- `FileUploadDropzone` - 드래그 앤 드롭 영역
- `IngestionProgressCard` - 처리 진행 상황 (단계별 표시)
- `ResearchAgentChatPanel` - 리서치 에이전트 대화창
- `HITLQueueModal` - HITL 검증 모달

---

### 3.3 시나리오 2: 에이전트 생성

```
[🗂️ TAXONOMY] 페이지
  ↓
줌/패닝으로 트리 탐색
  ↓
드래그로 지식 영역 선택
  예: "의학 > 암학 > 폐암" + "암학 > 위암" (다중 선택)
  ↓
미니맵에 선택 영역 하이라이트 표시
  └─ 선택된 문서 수: 1,234개
  └─ 총 용량: 45 MB
  ↓
[+ 에이전트 생성] 버튼 클릭
  ↓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
에이전트 생성 폼 (모달 또는 별도 페이지)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 기본 정보
  - 이름: [암학 전문 상담가]
  - 이모티콘: [😎] (선택)
  - 역할: [의학 전문가]
  - 전문성 레벨: [전문가 ▼]

💬 말투 & 스타일
  - 말투: [존댓말 ▼]
  - 톤: [따뜻함 ▼]
  - 응답 길이: [상세히 ▼]
  - 이모지 사용: [✓]

🔧 작업 범위
  - 답변 소스 정책: [소스 근거 필수 ▼]
  - 불확실성 처리: [모름 선언 ▼]
  - 재확인 규칙: [모호한 질문 시 ▼]

🛠️ 도구 사용
  - [✓] 웹 검색
  - [✓] 계산기
  - [✗] 코드 실행
  - [✗] 이메일 전송

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[취소] [생성하기]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ↓
백엔드 API 호출:
  POST /api/v1/agents/from-category
  {
    "name": "암학 전문 상담가",
    "taxonomy_categories": ["의학/암학/폐암", "의학/암학/위암"],
    "persona": { ... },
    "tools": ["web_search", "calculator"]
  }
  ↓
에이전트 카드 생성 (Lv.1, Common)
  ↓
메인 화면에 표시
```

**제약 조건**:
- 무료 사용자: 최대 3개 에이전트
- 유료 사용자: 무제한
- TAXONOMY가 비어있으면 생성 버튼 비활성화 + 안내 메시지

---

### 3.4 시나리오 3: 에이전트 사용 & 피드백

```
[🏠 홈] 에이전트 카드 클릭
  ↓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
대화 창 열림 (모달 또는 전체 화면)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌────────────────────────────────────────────┐
│ 암학 전문 상담가 😎  Lv.5  [Epic]         │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                            │
│ 사용자: "폐암 초기 증상이 뭐예요?"        │
│                                            │
│ 에이전트: "폐암 초기 증상으로는..."       │
│ [출처: 대한폐암학회, 2024]                │
│                                            │
│ ┌─────────────────────────────────────┐  │
│ │ 👍 도움됐어요  👎 아쉬워요  💬 추가질문│  │
│ └─────────────────────────────────────┘  │
│                                            │
│ [피드백 후]                                │
│ 💫 에이전트가 50 XP 획득! (370/600)       │
│ 품질 점수 94% → 95% 🔥                    │
│                                            │
└────────────────────────────────────────────┘

사용자가 👍 클릭 시:
  ↓
백엔드 API 호출:
  POST /api/v1/reflection/feedback
  {
    "agent_id": "agent-001",
    "user_rating": 5,
    "success_flag": true
  }
  ↓
프론트엔드 업데이트:
  - totalXP += 50 (대화) + 50 (👍)
  - positiveFeedbacks += 1
  - qualityScore 재계산
  ↓
애니메이션 효과:
  - XP 바 증가 애니메이션
  - "+100 XP" 플로팅 텍스트
  - 레벨업 시 축하 모달
```

**대화 히스토리**:
- 옵션 A: 에이전트 카드 → [📊 기록] 버튼 → 히스토리 모달
- 옵션 B: 별도 [💬 대화 히스토리] 메뉴 → 모든 에이전트 대화 기록

---

## 4. UI/UX 디자인 가이드

### 4.1 디자인 철학

**"프로페셔널 × 아기자기한 게임 감성"**

- **Stack AI의 전문성**: 깔끔한 레이아웃, 넉넉한 여백, 명확한 타이포
- **게임 카드의 재미**: 캐릭터, 레벨, 레어리티, 성장 시스템
- **대중적 친근함**: 파스텔 액센트, 부드러운 효과

### 4.2 색상 팔레트

#### **라이트 모드 (기본)**

```css
/* 메인 색상 */
--primary: #0099FF;        /* 밝은 블루 (버튼, 링크) */
--primary-light: #E6F5FF;  /* 연한 블루 (배경 강조) */
--primary-dark: #0066CC;   /* 진한 블루 (호버) */

/* 배경 */
--background: #FFFFFF;     /* 순백 */
--surface: #F9FAFB;        /* 연한 회색 (카드 배경) */
--surface-hover: #F3F4F6;  /* 호버 시 */

/* 아기자기한 액센트 */
--accent-purple: #A78BFA;  /* 보라 (Epic) */
--accent-pink: #FB7185;    /* 핑크 (알림, 하이라이트) */
--accent-green: #34D399;   /* 민트 (성공) */
--accent-yellow: #FCD34D;  /* 노랑 (경고, 레벨업) */
--accent-orange: #FB923C;  /* 오렌지 (Rare) */
--accent-gold: #F59E0B;    /* 금색 (Legendary) */

/* 텍스트 */
--text-primary: #1F2937;   /* 진한 회색 (제목, 본문) */
--text-secondary: #6B7280; /* 중간 회색 (부가 정보) */
--text-tertiary: #9CA3AF;  /* 연한 회색 (캡션) */

/* 보더 */
--border: #E5E7EB;         /* 얇은 보더 (1px) */
--border-strong: #D1D5DB;  /* 진한 보더 */

/* 피드백 */
--success: #10B981;        /* 녹색 */
--error: #EF4444;          /* 빨강 */
--warning: #F59E0B;        /* 주황 */
--info: #3B82F6;           /* 파랑 */
```

#### **다크 모드 (옵션)**

```css
--background: #1A1A1F;     /* 약간 밝은 남색 (완전 검정 X) */
--surface: #2A2A35;        /* 카드 배경 */
--text-primary: #F9FAFB;   /* 연한 회색 */
--text-secondary: #9CA3AF; /* 중간 회색 */
--border: #374151;         /* 다크 보더 */

/* 액센트는 밝게 조정 */
--primary: #60A5FA;        /* 연한 블루 */
```

---

### 4.3 타이포그래피

```css
/* 폰트 패밀리 */
font-family: 'Pretendard', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;

/* 폰트 계층 */
H1: 32px / Bold / letter-spacing: -0.02em    /* 페이지 제목 */
H2: 24px / SemiBold / letter-spacing: -0.01em /* 섹션 제목 */
H3: 18px / Medium                             /* 카드 제목 */
Body: 16px / Regular / line-height: 1.6       /* 본문 */
Caption: 14px / Regular                       /* 부가 정보 */
Small: 12px / Regular                         /* 작은 텍스트 */
```

**폰트 선택 이유**:
- **Pretendard**: 한글 최적화, 가변 폰트, 무료, 다양한 굵기
- **Inter**: 영문/숫자 가독성 우수 (Stack AI 참고)

---

### 4.4 간격 시스템 (Spacing)

```css
/* 8px 기반 간격 시스템 */
--space-1: 4px;    /* 매우 좁음 */
--space-2: 8px;    /* 좁음 */
--space-3: 12px;   /* 보통-좁음 */
--space-4: 16px;   /* 보통 */
--space-5: 20px;   /* 보통-넓음 */
--space-6: 24px;   /* 넓음 */
--space-8: 32px;   /* 매우 넓음 */
--space-10: 40px;  /* 섹션 간 */
--space-12: 48px;  /* 큰 섹션 간 */
--space-16: 64px;  /* 페이지 섹션 */
--space-20: 80px;  /* 메인 섹션 (Stack AI 스타일) */
--space-24: 96px;
--space-30: 120px;

/* 레이아웃 */
--max-width: 1200px;   /* 메인 콘텐츠 최대 폭 */
--max-width-wide: 1440px; /* 와이드 레이아웃 */
--header-height: 60px; /* 헤더 높이 */
```

---

### 4.5 컴포넌트 스타일

#### **카드 (Card)**

```css
.card {
  background: var(--background);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: var(--space-4);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: all 0.2s ease;
}

.card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}
```

#### **버튼 (Button)**

```css
/* Primary Button */
.btn-primary {
  background: var(--primary);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 12px 24px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease;
}

.btn-primary:hover {
  background: var(--primary-dark);
}

/* Secondary Button */
.btn-secondary {
  background: transparent;
  color: var(--primary);
  border: 1px solid var(--primary);
  border-radius: 8px;
  padding: 12px 24px;
  font-weight: 600;
  cursor: pointer;
}
```

#### **경험치 바 (Progress Bar)**

```css
.progress-bar {
  width: 100%;
  height: 8px;
  background: var(--surface);
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--primary), var(--primary-light));
  border-radius: 4px;
  transition: width 0.5s ease;
}

/* 레어리티별 그라데이션 */
.progress-fill.rare {
  background: linear-gradient(90deg, #60A5FA, #3B82F6);
}

.progress-fill.epic {
  background: linear-gradient(90deg, #A78BFA, #8B5CF6);
}

.progress-fill.legendary {
  background: linear-gradient(90deg, #FCD34D, #F59E0B);
}
```

---

### 4.6 레이아웃 구조

```
┌─────────────────────────────────────────────────────────┐
│ Header (Sticky, 60px)                                   │
│ [로고 DT-RAG]  [🏠홈] [🗂️분류] [📤업로드]  [👤프로필]  │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│                                                          │
│  Main Content (max-width: 1200px, 중앙 정렬)            │
│  padding: 80px 20px                                     │
│                                                          │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│                                                          │
│  [섹션 1] margin-bottom: 80px                           │
│  [섹션 2] margin-bottom: 80px                           │
│  [섹션 3]                                               │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**특징**:
- Sticky 헤더 (스크롤 시 항상 표시)
- 최대 폭 제한 (너무 넓지 않게)
- 섹션 간 넉넉한 여백 (80px, Stack AI 스타일)

---

## 5. 에이전트 시스템

### 5.1 에이전트 카드 디자인

```
┌─────────────────────┐
│                     │
│      😎 (대형)       │ ← 캐릭터 (상단 중앙)
│                     │
│  암학 전문 상담가     │ ← 이름 (18px Bold)
│  Lv.5  [Epic]       │ ← 레벨 & 레어리티 (이름 밑)
├─────────────────────┤
│ ━━━━━○ 67%          │ ← 경험치 바 (그라데이션)
│ 420/600 XP          │
├─────────────────────┤
│ ⭐ 품질 94% 🔥      │ ← 품질 점수
│ 👍 85 · 👎 5       │ ← 피드백 내역
├─────────────────────┤
│ 📚 지식 1,234개     │ ← 스탯
│ 💬 대화 89회        │
├─────────────────────┤
│ [💬 대화] [📊 기록] │ ← 액션 버튼
└─────────────────────┘
```

**스타일링**:
```css
.agent-card {
  width: 280px;
  background: white;
  border: 1px solid var(--border);
  border-radius: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  transition: all 0.2s ease;
}

/* 레어리티별 상단 테두리 */
.agent-card.common {
  border-top: 3px solid #9CA3AF;
}

.agent-card.rare {
  border-top: 3px solid;
  border-image: linear-gradient(90deg, #60A5FA, #3B82F6) 1;
}

.agent-card.epic {
  border-top: 3px solid;
  border-image: linear-gradient(90deg, #A78BFA, #8B5CF6) 1;
}

.agent-card.legendary {
  border-top: 3px solid;
  border-image: linear-gradient(90deg, #FCD34D, #F59E0B) 1;
  /* 미세한 글로우 효과 */
  box-shadow: 0 0 20px rgba(251, 191, 36, 0.3);
}

.agent-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

/* 캐릭터 영역 */
.agent-character {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 120px;
  font-size: 64px;
  background: linear-gradient(135deg, #F9FAFB, #E5E7EB);
}
```

---

### 5.2 레벨 & 레어리티 시스템

#### **레벨 시스템**

| 레벨 | 필요 XP | 레어리티 |
|------|---------|---------|
| 1    | 0       | Common  |
| 2    | 100     | Common  |
| 3    | 300     | Rare    |
| 4    | 600     | Rare    |
| 5    | 1,000   | Epic    |
| 6    | 1,500   | Epic    |
| 7    | 2,100   | Epic    |
| 8    | 2,800   | Legendary |
| 9    | 3,600   | Legendary |
| 10   | 4,500   | Legendary |

**레벨업 공식**:
```typescript
function getLevelFromXP(totalXP: number): number {
  const levels = [0, 100, 300, 600, 1000, 1500, 2100, 2800, 3600, 4500];
  for (let i = levels.length - 1; i >= 0; i--) {
    if (totalXP >= levels[i]) {
      return i + 1;
    }
  }
  return 1;
}

function getXPRequired(level: number): number {
  const levels = [0, 100, 300, 600, 1000, 1500, 2100, 2800, 3600, 4500];
  return levels[level] || levels[levels.length - 1];
}
```

#### **레어리티 등급**

```typescript
enum Rarity {
  COMMON = "Common",      // 회색, Lv. 1-2
  RARE = "Rare",          // 파란색, Lv. 3-4
  EPIC = "Epic",          // 보라색, Lv. 5-7
  LEGENDARY = "Legendary" // 금색, Lv. 8+
}

function getRarity(level: number): Rarity {
  if (level >= 8) return Rarity.LEGENDARY;
  if (level >= 5) return Rarity.EPIC;
  if (level >= 3) return Rarity.RARE;
  return Rarity.COMMON;
}
```

---

### 5.3 에이전트 페르소나 설정

#### **A. 페르소나 & 정체성 (필수)**

```typescript
interface AgentPersona {
  // 기본 정보
  name: string;                    // 에이전트 이름
  role: string;                    // 역할 (예: "의학 전문가", "법률 상담가")
  expertiseLevel: "beginner" | "intermediate" | "expert"; // 전문성 레벨
  description: string;             // 한줄 설명
  goals: string[];                 // 핵심 목표 (Top 3)
  limitations: string[];           // 금칙 주제/한계

  // B. 말투 & 커뮤니케이션 스타일
  speechStyle: "formal" | "casual" | "friendly" | "business"; // 말투
  tone: "warm" | "neutral" | "direct" | "challenging" | "calm"; // 톤
  responseLength: "brief" | "moderate" | "detailed"; // 응답 길이
  useEmojis: boolean;              // 이모지 사용 여부
  language: "ko-KR" | "en-US";     // 언어

  // C. 작업 범위 & 정책
  sourcePolicy: "strict" | "preferred" | "flexible"; // 소스 정책
  uncertaintyHandling: "admit" | "estimate" | "clarify"; // 불확실성 처리
  clarifyThreshold: number;        // 재확인 임계값 (0.0~1.0)

  // D. 도구/액션 사용
  enabledTools: string[];          // 사용 가능 도구 ["web_search", "calculator", ...]
  actionPolicy: "auto" | "confirm" | "disabled"; // 액션 정책
}
```

#### **생성 폼 예시**

```typescript
// 기본값 (사용자 선택 안 할 경우)
const defaultPersona: AgentPersona = {
  name: "새 에이전트",
  role: "일반 어시스턴트",
  expertiseLevel: "intermediate",
  description: "다양한 주제에 대해 도움을 드립니다",
  goals: ["정확한 정보 제공", "친절한 응대", "빠른 응답"],
  limitations: ["의료 진단 금지", "법률 자문 금지", "투자 조언 금지"],

  speechStyle: "friendly",
  tone: "warm",
  responseLength: "moderate",
  useEmojis: true,
  language: "ko-KR",

  sourcePolicy: "preferred",
  uncertaintyHandling: "admit",
  clarifyThreshold: 0.3,

  enabledTools: ["web_search"],
  actionPolicy: "confirm"
};
```

---

## 6. TAXONOMY 시각화

### 6.1 기술 스택 후보

| 라이브러리 | 장점 | 단점 | 추천도 |
|-----------|------|------|--------|
| **React Flow** | 드래그 앤 드롭, 커스터마이징 쉬움 | 트리 구조에 약간 과함 | ⭐⭐⭐⭐ |
| **D3.js** | 완전한 제어 가능 | 학습 곡선 높음 | ⭐⭐⭐ |
| **Cytoscape.js** | 네트워크 그래프 특화 | 트리에는 오버스펙 | ⭐⭐ |
| **react-arborist** | 트리 전용, 가상 스크롤 | 시각적 효과 제한적 | ⭐⭐⭐⭐ |

**최종 권장**: **React Flow** (유연성 + 커뮤니티 지원)

---

### 6.2 TAXONOMY 페이지 레이아웃

```
┌─────────────────────────────────────────────────────────┐
│ 🗂️ TAXONOMY v2.1.0 [버전 선택 ▼] [비교] [설정]       │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ ┌────────────────┬───────────────────────────────────┐ │
│ │                │                                   │ │
│ │  Mini Map      │  Main Tree View                   │ │
│ │  (전체 구조)    │  (줌/패닝 가능)                   │ │
│ │                │                                   │ │
│ │  ┌──────────┐  │   ┌─────────────┐                │ │
│ │  │●  의학    │  │   │   의학       │ ← 루트 노드  │ │
│ │  │ ├●암학    │  │   ├─ 암학       │                │ │
│ │  │ │└●폐암   │  │   │  ├─ 폐암 ✓  │ ← 선택됨     │ │
│ │  │ │ ●위암   │  │   │  ├─ 위암 ✓  │ ← 선택됨     │ │
│ │  │ └●심장학  │  │   │  └─ 혈액암   │                │ │
│ │  │●  기술    │  │   └─ 심장학      │                │ │
│ │  └──────────┘  │                                   │ │
│ │                │   [+ 노드 추가] [수정] [삭제]     │ │
│ │  [선택 초기화] │                                   │ │
│ │                │                                   │ │
│ └────────────────┴───────────────────────────────────┘ │
│                                                          │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│                                                          │
│ 📊 선택 정보                                             │
│ ┌─────────────────────────────────────────────────────┐│
│ │ 선택된 노드: 2개 (폐암, 위암)                        ││
│ │ 총 문서: 1,234개                                     ││
│ │ 총 용량: 45 MB                                       ││
│ │ 평균 품질 점수: 0.89                                 ││
│ │                                                      ││
│ │ [에이전트 생성하기]                                  ││
│ └─────────────────────────────────────────────────────┘│
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

### 6.3 노드 선택 인터랙션

#### **방법 1: 단일 클릭 (노드 선택)**
```typescript
function handleNodeClick(nodeId: string) {
  // 토글 방식
  if (selectedNodes.includes(nodeId)) {
    setSelectedNodes(selectedNodes.filter(id => id !== nodeId));
  } else {
    setSelectedNodes([...selectedNodes, nodeId]);
  }

  // 하위 노드 자동 포함
  const childNodes = getChildNodes(nodeId);
  setSelectedNodes([...selectedNodes, nodeId, ...childNodes]);
}
```

#### **방법 2: 드래그 (영역 선택)**
```typescript
function handleDragSelection(startNode: string, endNode: string) {
  // 드래그 범위 내 모든 노드 선택
  const nodesInRange = getNodesInRange(startNode, endNode);
  setSelectedNodes(nodesInRange);
}
```

#### **방법 3: 우클릭 메뉴 (컨텍스트 메뉴)**
```typescript
const contextMenuOptions = [
  { label: "선택", action: () => selectNode(nodeId) },
  { label: "하위 전체 선택", action: () => selectNodeWithChildren(nodeId) },
  { label: "제외", action: () => deselectNode(nodeId) },
  { label: "노드 수정", action: () => openEditModal(nodeId) },
  { label: "노드 삭제", action: () => deleteNode(nodeId) },
];
```

---

### 6.4 버전 관리

```typescript
interface TaxonomyVersion {
  version: string;          // "v2.1.0"
  createdAt: Date;
  createdBy: string;
  status: "draft" | "published" | "archived";
  changeLog: string;        // "폐암 하위 분류 3개 추가"
  totalNodes: number;
  totalDocuments: number;
}

// 버전 비교 UI
function TaxonomyVersionCompare({ baseVersion, targetVersion }) {
  return (
    <div>
      <h3>v{baseVersion} → v{targetVersion} 변경 사항</h3>
      <ul>
        <li className="added">+ 추가: 폐암 > 소세포암 (3개 노드)</li>
        <li className="modified">◎ 수정: 위암 > 조기 위암 (설명 변경)</li>
        <li className="deleted">- 삭제: 혈액암 > 백혈병 (1개 노드)</li>
      </ul>
    </div>
  );
}
```

---

## 7. 경험치 & 게이미피케이션

### 7.1 경험치 시스템 (조작 방지)

#### **핵심 원칙**
- **XP는 절대 감소하지 않음** (사용자 동기 부여 유지)
- **품질 점수는 별도 관리** (실제 성능 반영)
- **투명한 지표 공개** (👍/👎 개수 모두 표시)

#### **데이터 구조**

```typescript
interface Agent {
  id: string;
  name: string;
  level: number;              // 경험치 기반 (1~10+)
  totalXP: number;            // 누적 경험치 (절대 감소 X)
  qualityScore: number;       // 품질 점수 (0.0~1.0, 증감 가능)

  // 통계
  totalChats: number;         // 총 대화 수
  totalFeedbacks: number;     // 총 피드백 수
  positiveFeedbacks: number;  // 👍 개수
  negativeFeedbacks: number;  // 👎 개수
  avgRagasScore: number;      // 평균 RAGAS 점수 (0.0~1.0)

  // 메타데이터
  createdAt: Date;
  lastUsedAt: Date;
  taxonomyCategories: string[];
  persona: AgentPersona;
}
```

---

### 7.2 XP 획득 규칙

```typescript
function gainXP(agent: Agent, action: ActionType): number {
  const xpTable = {
    CHAT: 10,                 // 대화 1회
    POSITIVE_FEEDBACK: 50,    // 👍
    // NEGATIVE_FEEDBACK: 0   // 👎 (XP 획득 없음, 감소도 없음)
    RAGAS_BONUS: 100,         // RAGAS > 0.9 시 보너스
  };

  let xp = xpTable[action] || 0;

  // RAGAS 보너스 (높은 품질 응답)
  if (action === "CHAT" && agent.lastRagasScore > 0.9) {
    xp += xpTable.RAGAS_BONUS;
  }

  return xp;
}
```

---

### 7.3 품질 점수 계산

```typescript
function calculateQualityScore(agent: Agent): number {
  // 피드백이 없으면 중립 (0.5)
  if (agent.totalFeedbacks === 0) {
    return 0.5;
  }

  // 긍정 피드백 비율 (70% 가중치)
  const feedbackRatio = agent.positiveFeedbacks / agent.totalFeedbacks;

  // RAGAS 점수 (30% 가중치)
  const ragasScore = agent.avgRagasScore || 0.5;

  // 최종 품질 점수
  const qualityScore = feedbackRatio * 0.7 + ragasScore * 0.3;

  return Math.round(qualityScore * 100) / 100; // 소수점 2자리
}
```

**예시**:
```
에이전트 A:
- 👍 85개, 👎 5개 (총 90개)
- feedbackRatio = 85/90 = 0.944
- avgRagasScore = 0.89
- qualityScore = 0.944 * 0.7 + 0.89 * 0.3 = 0.661 + 0.267 = 0.928 = 93%

에이전트 B:
- 👍 100개, 👎 0개 (총 100개)
- feedbackRatio = 100/100 = 1.0
- avgRagasScore = 0.65 (낮은 RAGAS)
- qualityScore = 1.0 * 0.7 + 0.65 * 0.3 = 0.7 + 0.195 = 0.895 = 90%
```

→ **조작 방지**: 무작정 👍만 눌러도 RAGAS가 낮으면 품질 점수는 낮아짐

---

### 7.4 피드백 UI

```typescript
function FeedbackButtons({ agentId, chatId }) {
  const [feedbackGiven, setFeedbackGiven] = useState(false);

  const handleFeedback = async (isPositive: boolean) => {
    // 백엔드 API 호출
    await fetch("/api/v1/reflection/feedback", {
      method: "POST",
      body: JSON.stringify({
        agent_id: agentId,
        chat_id: chatId,
        user_rating: isPositive ? 5 : 1,
        success_flag: isPositive,
      }),
    });

    // XP 획득 애니메이션
    if (isPositive) {
      showXPAnimation("+50 XP");
    }

    setFeedbackGiven(true);
  };

  return (
    <div className="feedback-buttons">
      <button onClick={() => handleFeedback(true)} disabled={feedbackGiven}>
        👍 도움됐어요
      </button>
      <button onClick={() => handleFeedback(false)} disabled={feedbackGiven}>
        👎 아쉬워요
      </button>
    </div>
  );
}
```

---

### 7.5 레벨업 애니메이션

```typescript
function LevelUpModal({ agent, onClose }) {
  return (
    <div className="level-up-modal">
      <h2>🎉 레벨업!</h2>
      <div className="agent-icon">{agent.icon}</div>
      <p>{agent.name}이(가)</p>
      <p className="level-text">
        Lv.{agent.level - 1} → <strong>Lv.{agent.level}</strong>
      </p>

      {/* 레어리티 변경 시 */}
      {getRarity(agent.level) !== getRarity(agent.level - 1) && (
        <div className="rarity-upgrade">
          <p>등급 상승! {getRarity(agent.level - 1)} → {getRarity(agent.level)}</p>
        </div>
      )}

      <button onClick={onClose}>확인</button>
    </div>
  );
}
```

---

## 8. 페이지 구조

### 8.1 전체 메뉴 구조

```
┌─────────────────────────────────────────────────────────┐
│ Header (Sticky)                                          │
│ [로고 DT-RAG]                                            │
│                                                          │
│ 메뉴:                                                    │
│ - 🏠 홈                                                  │
│ - 🗂️ TAXONOMY                                           │
│ - 📤 데이터 업로드                                       │
│ - 🤖 에이전트 관리                                       │
│ - 💬 대화 히스토리                                       │
│                                                          │
│ 오른쪽:                                                  │
│ - 🔔 알림 (레벨업, HITL 작업 등)                        │
│ - 👤 프로필 드롭다운                                     │
│   ├─ 내 정보                                            │
│   ├─ 설정                                               │
│   ├─ 📊 관리자 (권한 있을 때만)                         │
│   └─ 로그아웃                                           │
└─────────────────────────────────────────────────────────┘
```

---

### 8.2 페이지별 상세 설계

#### **1. 홈 (🏠 Home)**

**URL**: `/`

**목적**: 에이전트 중심의 메인 대시보드

```
┌─────────────────────────────────────────────────────────┐
│ 📊 내 통계                                               │
│ ┌───────────┬───────────┬───────────┬───────────┐      │
│ │ 에이전트   │ 총 지식    │ 이번 주    │ TAXONOMY  │      │
│ │ 5개        │ 3,421개   │ 대화 127회 │ v2.1.0    │      │
│ └───────────┴───────────┴───────────┴───────────┘      │
├─────────────────────────────────────────────────────────┤
│ 🤖 내 에이전트들                 [+ 새 에이전트 생성]   │
│ 정렬: [최근 사용순 ▼]  필터: [전체 레벨 ▼]             │
│                                                          │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│ │ Agent 1  │ │ Agent 2  │ │ Agent 3  │ │ Agent 4  │  │
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
├─────────────────────────────────────────────────────────┤
│ 💡 추천 액션                                             │
│ • 리서치 에이전트로 "양자컴퓨팅" 지식 수집하기          │
│ • 암학 전문 에이전트 레벨업까지 180 XP! (3번 대화)     │
└─────────────────────────────────────────────────────────┘
```

**컴포넌트**:
- `StatCard` (통계 카드)
- `AgentCard` (에이전트 카드)
- `RecommendationPanel` (추천 패널)

---

#### **2. TAXONOMY (🗂️ Taxonomy)**

**URL**: `/taxonomy`

**목적**: 시각적 지식 구조 탐색 및 에이전트 생성

```
┌─────────────────────────────────────────────────────────┐
│ 🗂️ TAXONOMY v2.1.0                                      │
│ [버전: v2.1.0 ▼] [비교] [내보내기] [설정]              │
├─────────────────────────────────────────────────────────┤
│ ┌────────────────┬───────────────────────────────────┐ │
│ │ Mini Map       │ Main Tree View                    │ │
│ │ (전체 구조)     │ (줌/패닝, 드래그 선택)             │ │
│ │                │                                   │ │
│ │ [선택 초기화]   │ [+ 노드 추가] [수정] [삭제]       │ │
│ └────────────────┴───────────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│ 📊 선택 정보                                             │
│ 선택된 노드: 2개 | 문서: 1,234개 | 용량: 45 MB         │
│ [에이전트 생성하기]                                      │
└─────────────────────────────────────────────────────────┘
```

**기능**:
- 줌 인/아웃 (마우스 휠, 핀치)
- 드래그로 영역 선택
- 노드 클릭으로 선택/해제
- 우클릭 컨텍스트 메뉴
- 버전 비교 모달

**컴포넌트**:
- `TaxonomyTreeView` (React Flow 기반)
- `TaxonomyMiniMap`
- `NodeDetailsPanel`
- `VersionSelector`

---

#### **3. 데이터 업로드 (📤 Upload)**

**URL**: `/upload`

**목적**: 직접 업로드 + 리서치 에이전트

```
┌─────────────────────────────────────────────────────────┐
│ 📤 데이터 업로드                                         │
├─────────────────────────────────────────────────────────┤
│ ┌──────────────────┐ ┌──────────────────┐             │
│ │ 📁 파일 업로드    │ │ 🤖 리서치 에이전트│             │
│ │                  │ │                  │             │
│ │ [드래그 & 드롭]   │ │ "암 전문 의학박사 │             │
│ │ 또는 클릭         │ │  에이전트 만들고  │             │
│ │                  │ │  싶어"           │             │
│ │ [파일 선택]       │ │                  │             │
│ │                  │ │ [대화 시작]       │             │
│ └──────────────────┘ └──────────────────┘             │
├─────────────────────────────────────────────────────────┤
│ 🔄 처리 중인 작업 (3개)                                 │
│ ┌─────────────────────────────────────────────────────┐│
│ │ Job #123: whitepaper.pdf                            ││
│ │ [████████████────] 60% - 텍스트 추출 중...          ││
│ │ [취소] [상세]                                       ││
│ └─────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

**컴포넌트**:
- `FileUploadDropzone`
- `ResearchAgentChatPanel`
- `IngestionJobCard`
- `HITLQueueModal`

---

#### **4. 에이전트 관리 (🤖 Agents)**

**URL**: `/agents`

**목적**: 전체 에이전트 리스트 + 상세 관리

```
┌─────────────────────────────────────────────────────────┐
│ 🤖 에이전트 관리                                         │
│ [+ 새 에이전트] [정렬: 레벨순 ▼] [필터: 전체 ▼]        │
├─────────────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────────────────┐│
│ │ ┌──────┐ 암학 전문 상담가  Lv.5 [Epic]             ││
│ │ │  😎  │ ━━━━━○ 67% (420/600 XP)                   ││
│ │ └──────┘ 📚 1,234 · 💬 89 · ⭐ 94%                  ││
│ │          [대화] [수정] [삭제] [히스토리]            ││
│ ├──────────────────────────────────────────────────────┤│
│ │ ┌──────┐ AI 리서처  Lv.3 [Rare]                    ││
│ │ │  🤓  │ ━━━○ 34% (102/300 XP)                     ││
│ │ └──────┘ 📚 567 · 💬 34 · ⭐ 87%                    ││
│ │          [대화] [수정] [삭제] [히스토리]            ││
│ └──────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

**기능**:
- 에이전트 리스트 (카드 또는 리스트 뷰)
- 정렬/필터 (레벨, 최근 사용, 이름)
- 상세 페이지로 이동
- 수정/삭제

---

#### **5. 대화 히스토리 (💬 History)**

**URL**: `/history`

**목적**: 모든 에이전트와의 대화 기록

```
┌─────────────────────────────────────────────────────────┐
│ 💬 대화 히스토리                                         │
│ [전체 에이전트 ▼] [최근 7일 ▼] [검색...]               │
├─────────────────────────────────────────────────────────┤
│ 📅 오늘                                                  │
│ ┌─────────────────────────────────────────────────────┐│
│ │ 😎 암학 전문 상담가 · 2시간 전                      ││
│ │ "폐암 초기 증상이 뭐예요?" → 15개 메시지             ││
│ │ 👍 도움됨 · [다시 보기]                             ││
│ └─────────────────────────────────────────────────────┘│
│ ┌─────────────────────────────────────────────────────┐│
│ │ 🤓 AI 리서처 · 5시간 전                             ││
│ │ "LangChain 최신 동향 알려줘" → 8개 메시지           ││
│ │ 👎 아쉬움 · [다시 보기]                             ││
│ └─────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────┤
│ 📅 어제                                                  │
│ ...                                                      │
└─────────────────────────────────────────────────────────┘
```

**기능**:
- 날짜별 그룹핑
- 에이전트별 필터
- 검색 (메시지 내용)
- 대화 다시 보기 (모달 또는 별도 페이지)

---

#### **6. 관리자 (📊 Admin) - 권한 필요**

**URL**: `/admin`

**목적**: 시스템 모니터링 및 관리

```
┌─────────────────────────────────────────────────────────┐
│ 📊 관리자 대시보드                                       │
├─────────────────────────────────────────────────────────┤
│ 시스템 상태                                              │
│ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐          │
│ │ API    │ │Database│ │ Redis  │ │Embedding│          │
│ │🟢Healthy│ │🟢Online│ │🟢Online│ │🟢Online │          │
│ └────────┘ └────────┘ └────────┘ └────────┘          │
├─────────────────────────────────────────────────────────┤
│ RAGAS 품질 메트릭스 (Last 24h)                          │
│ Faithfulness:     0.89 ━━━━━━━━━○                      │
│ Answer Relevancy: 0.91 ━━━━━━━━━━○                     │
│ Context Precision:0.87 ━━━━━━━━○○                      │
│ Context Recall:   0.85 ━━━━━━━━○○                      │
├─────────────────────────────────────────────────────────┤
│ HITL 큐 (23개 대기)                                     │
│ [큐 보기] [일괄 처리]                                   │
└─────────────────────────────────────────────────────────┘
```

---

## 9. 기술 스택

### 9.1 프론트엔드

```yaml
Framework: React 18 + TypeScript 5
Build Tool: Vite 5
Styling: Tailwind CSS 3 + CSS Modules (부분)
State Management: Zustand 4 (경량, 간단)
Data Fetching: TanStack Query 5 (React Query)
Routing: React Router 6
Charts: Recharts 2 (경험치 바, 통계 차트)
Tree Visualization: React Flow (TAXONOMY)
Icons: Lucide React (일관된 아이콘 세트)
Forms: React Hook Form + Zod (유효성 검증)
Animations: Framer Motion (레벨업 등)
```

### 9.2 개발 도구

```yaml
Package Manager: pnpm (빠른 설치, 디스크 절약)
Code Quality: ESLint + Prettier + TypeScript strict
Git Hooks: Husky + lint-staged (커밋 전 검사)
Testing: Vitest + Testing Library (단위 테스트)
E2E Testing: Playwright (주요 플로우)
Documentation: Storybook (컴포넌트 문서화)
```

### 9.3 배포

```yaml
Hosting: Vercel (자동 배포, 최적화)
CDN: Cloudflare (글로벌 배포)
Monitoring: Sentry (프론트엔드 에러 추적)
Analytics: PostHog (제품 분석, 사용자 행동)
```

---

## 10. API 연동 계획

### 10.1 주요 API 엔드포인트

#### **에이전트 관리**

```typescript
// 에이전트 생성
POST /api/v1/agents/from-category
{
  "name": "암학 전문 상담가",
  "taxonomy_categories": ["의학/암학/폐암", "의학/암학/위암"],
  "persona": { ... },
  "tools": ["web_search"]
}

// 에이전트 목록
GET /api/v1/agents/
Response: Agent[]

// 에이전트 상세
GET /api/v1/agents/{agent_id}
Response: Agent

// 에이전트 수정
PUT /api/v1/agents/{agent_id}
Body: Partial<Agent>

// 에이전트 삭제
DELETE /api/v1/agents/{agent_id}

// 에이전트 메트릭스
GET /api/v1/agents/{agent_id}/metrics
Response: {
  totalChats: number,
  avgResponseTime: number,
  qualityScore: number,
  ...
}
```

---

#### **TAXONOMY 관리**

```typescript
// 트리 조회
GET /api/v1/taxonomy/{version}/tree
Response: TaxonomyNode[]

// 노드 생성
POST /api/v1/taxonomy/{version}/node
Body: {
  name: string,
  parent_id: string | null,
  metadata: object
}

// 노드 수정
PUT /api/v1/taxonomy/{version}/node/{node_id}

// 노드 삭제
DELETE /api/v1/taxonomy/{version}/node/{node_id}

// 버전 비교
GET /api/v1/taxonomy/compare/{base}/{target}
Response: {
  added: TaxonomyNode[],
  modified: TaxonomyNode[],
  deleted: TaxonomyNode[]
}
```

---

#### **데이터 수집**

```typescript
// 파일 업로드
POST /ingestion/upload
FormData: { file: File }
Response: { job_id: string }

// URL 수집
POST /ingestion/urls
Body: { urls: string[] }
Response: { job_id: string }

// 작업 상태
GET /ingestion/status/{job_id}
Response: {
  status: "pending" | "processing" | "completed" | "failed",
  progress: number,
  stage: string,
  error?: string
}

// 작업 취소
POST /ingestion/cancel/{job_id}
```

---

#### **피드백 & Reflection**

```typescript
// 피드백 제출
POST /api/v1/reflection/feedback
Body: {
  agent_id: string,
  chat_id: string,
  user_rating: 1 | 2 | 3 | 4 | 5,
  success_flag: boolean,
  feedback_text?: string
}

// 성능 분석
POST /api/v1/reflection/analyze
Body: { case_id: string }
Response: {
  success_rate: number,
  avg_execution_time_ms: number,
  common_errors: ErrorPattern[]
}

// 개선 제안
POST /api/v1/reflection/suggestions
Body: { case_id: string }
Response: { suggestions: string[] }
```

---

#### **검색**

```typescript
// 하이브리드 검색
POST /api/v1/search
Body: {
  query: string,
  top_k: number,
  taxonomy_filter?: string[],
  rerank?: boolean
}
Response: {
  results: SearchResult[],
  total: number,
  query_time_ms: number
}

// 배치 검색
POST /api/v1/search/batch
Body: { queries: string[] }
Response: { results: SearchResult[][] }
```

---

### 10.2 TanStack Query 설정

```typescript
// queries/agents.ts
export const useAgents = () => {
  return useQuery({
    queryKey: ["agents"],
    queryFn: async () => {
      const res = await fetch("/api/v1/agents/");
      return res.json();
    },
    staleTime: 5 * 60 * 1000, // 5분
  });
};

export const useAgent = (agentId: string) => {
  return useQuery({
    queryKey: ["agents", agentId],
    queryFn: async () => {
      const res = await fetch(`/api/v1/agents/${agentId}`);
      return res.json();
    },
  });
};

export const useCreateAgent = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: CreateAgentRequest) => {
      const res = await fetch("/api/v1/agents/from-category", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      return res.json();
    },
    onSuccess: () => {
      // 에이전트 목록 새로고침
      queryClient.invalidateQueries({ queryKey: ["agents"] });
    },
  });
};
```

---

## 11. 구현 우선순위

### Phase 1: MVP (Week 1-3) - 핵심 기능

**목표**: 동작하는 프로토타입

| 우선순위 | 기능 | 예상 기간 |
|---------|------|-----------|
| 🔴 P0 | 홈 화면 (에이전트 카드 표시) | 3일 |
| 🔴 P0 | 에이전트 생성 (기본 폼) | 2일 |
| 🔴 P0 | 대화 창 (기본 채팅) | 3일 |
| 🔴 P0 | 피드백 버튼 (👍/👎) | 1일 |
| 🔴 P0 | 경험치 바 표시 | 2일 |
| 🟡 P1 | TAXONOMY 트리 (React Flow) | 5일 |
| 🟡 P1 | 파일 업로드 (드래그 앤 드롭) | 2일 |

---

### Phase 2: Enhanced (Week 4-6) - 고급 기능

**목표**: 완성도 향상

| 우선순위 | 기능 | 예상 기간 |
|---------|------|-----------|
| 🟡 P1 | 레벨업 애니메이션 | 2일 |
| 🟡 P1 | TAXONOMY 영역 선택 (드래그) | 3일 |
| 🟡 P1 | 대화 히스토리 페이지 | 2일 |
| 🟢 P2 | 리서치 에이전트 UI | 3일 |
| 🟢 P2 | HITL 큐 모달 | 2일 |
| 🟢 P2 | 에이전트 상세 페이지 | 2일 |

---

### Phase 3: Polish (Week 7-8) - 완성도

**목표**: 프로덕션 준비

| 우선순위 | 기능 | 예상 기간 |
|---------|------|-----------|
| 🟢 P2 | 다크 모드 | 2일 |
| 🟢 P2 | 모바일 반응형 | 3일 |
| ⚪ P3 | 관리자 대시보드 | 3일 |
| ⚪ P3 | 통계 차트 (Recharts) | 2일 |
| ⚪ P3 | 에이전트 마켓플레이스 | 5일 |

---

### Phase 4: Future (Week 9+) - 확장

**목표**: 차별화 기능

| 우선순위 | 기능 | 예상 기간 |
|---------|------|-----------|
| ⚪ P3 | 에이전트 공유 | 3일 |
| ⚪ P3 | 에이전트 템플릿 | 2일 |
| ⚪ P3 | 고급 통계 (대시보드) | 5일 |
| ⚪ P3 | 알림 시스템 (WebSocket) | 3일 |
| ⚪ P3 | 에이전트 협업 (멀티 에이전트) | 7일 |

---

## 12. 결론 & 다음 단계

### 12.1 핵심 차별화 포인트

1. **리서치 에이전트 자동 수집** - 사용자 편의성 극대화
2. **시각적 TAXONOMY** - 직관적 지식 구조 파악
3. **게임형 에이전트 육성** - 재미 + 실제 성능 향상
4. **투명한 품질 관리** - XP와 품질 점수 분리

### 12.2 즉시 시작 가능한 작업

#### **개발 환경 설정 (Day 1)**
```bash
# 프로젝트 생성
pnpm create vite dt-rag-frontend --template react-ts
cd dt-rag-frontend
pnpm install

# 패키지 추가
pnpm add \
  react-router-dom \
  @tanstack/react-query \
  zustand \
  tailwindcss \
  reactflow \
  lucide-react \
  framer-motion \
  react-hook-form \
  zod

# Tailwind CSS 설정
pnpm add -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

#### **기본 구조 생성 (Day 2)**
```
src/
├── components/
│   ├── AgentCard.tsx
│   ├── StatCard.tsx
│   ├── ProgressBar.tsx
│   └── Header.tsx
├── pages/
│   ├── HomePage.tsx
│   ├── TaxonomyPage.tsx
│   ├── UploadPage.tsx
│   └── AgentsPage.tsx
├── hooks/
│   └── useAgents.ts
├── types/
│   └── agent.ts
└── utils/
    └── xpCalculator.ts
```

#### **첫 번째 컴포넌트 (Day 3)**
- `AgentCard` 구현
- 더미 데이터로 테스트
- Storybook에 추가

### 12.3 다음 논의 주제

1. **리서치 에이전트 백엔드 구현** (웹 서치 통합)
2. **TAXONOMY 초기 데이터 구조** (샘플 데이터)
3. **과금 체계** (무료/유료 플랜)
4. **사용자 온보딩 플로우** (첫 방문자 가이드)

---

**작성자**: Claude (Anthropic AI) & User
**최종 수정**: 2025-10-30
**버전**: v2.0.0

---

## 📚 참고 자료

- [Stack AI 디자인](https://www.stack-ai.com/)
- [React Flow 문서](https://reactflow.dev/)
- [Pretendard 폰트](https://github.com/orioncactus/pretendard)
- [TanStack Query](https://tanstack.com/query/latest)
- [Zustand 상태관리](https://github.com/pmndrs/zustand)
