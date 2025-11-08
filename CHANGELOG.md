# CHANGELOG

모든 주요 변경사항은 이 파일에 기록됩니다.
형식: [Semantic Versioning](https://semver.org/) 준수

---

<!-- @DOC:TAILWIND-V4-COMPLETE-001-CHANGELOG -->
## [2.2.1] - 2025-11-08

### Fixed

#### Frontend - Tailwind CSS v4 Complete Migration
- **SPEC-TAILWIND-V4-COMPLETE-001**: Tailwind CSS v4 마이그레이션 완전 검증 및 완료
  - **Configuration Audit (SPEC-1)**: ✅ 완료
    - `tailwind.config.ts` v4 호환성 검증
    - PostCSS 설정 확인
    - Content paths 최적화
  - **Component Code Audit (SPEC-2)**: ✅ 완료
    - JIT 호환 패턴 검증 (AgentCard, RarityBadge)
    - 동적 클래스 패턴 제거 완료
    - Case-insensitive rarity 비교 구현
  - **API Integration Verification (SPEC-3)**: ✅ 완료
    - 백엔드 연동 환경에서 스타일 렌더링 확인
    - Loading/Error/Success 상태별 스타일 검증
    - 4단계 희귀도 색상 정확성 확인 (Common/Rare/Epic/Legendary)
  - **Cross-Browser Testing (SPEC-4)**: ✅ 완료
    - Chrome 111+, Firefox 113+, Safari 15.4+ OKLCH 색상 검증
    - 반응형 그리드 breakpoint 동작 확인 (mobile/tablet/desktop)
  - **Production Build Validation (SPEC-5)**: ✅ 완료
    - CSS bundle size 최적화 확인 (< 50KB gzipped)
    - Tree-shaking 동작 검증
    - FOUC (Flash of Unstyled Content) 없음 확인
  - **Documentation Update (SPEC-6)**: ✅ 완료
    - README.md Known Issues 섹션 업데이트 (RESOLVED)
    - CHANGELOG.md 항목 추가
    - SPEC status: draft → in-review 전환

  **기술적 개선**:
  - OKLCH 색상 시스템 안정화 (numbered scale: `-500`, `-600`, etc.)
  - JIT 컴파일러 호환 패턴 100% 적용
  - `@import "tailwindcss"` 문법 완전 전환 (v3 `@tailwind` directives 제거)
  - CSS-in-JS 동적 클래스 패턴 제거 (explicit conditionals 사용)

  **검증 결과**:
  | 메트릭 | 목표 | 결과 |
  |--------|------|------|
  | JIT 호환성 | 100% | ✅ 100% |
  | CSS Bundle Size | < 50KB (gzipped) | ✅ 달성 |
  | Cross-browser 렌더링 | 3+ browsers | ✅ 통과 |
  | API 연동 스타일 | 100% | ✅ 검증 완료 |
  | Production Build | 오류 없음 | ✅ Clean |

  **TAG 체인**:
  - @SPEC:TAILWIND-V4-COMPLETE-001 (v0.0.2)
  - @CODE:TAILWIND-V4-COMPLETE-001 (frontend/src/components/*)
  - @DOC:TAILWIND-V4-COMPLETE-001 (README.md, CHANGELOG.md)

  **이전 이슈**: [TAILWIND_V4_MIGRATION_ISSUE.md](.moai/issues/TAILWIND_V4_MIGRATION_ISSUE.md)

### Changed

#### Documentation
- **README.md**: Known Issues 섹션에서 Tailwind v4 이슈 RESOLVED로 업데이트
- **SPEC-TAILWIND-V4-COMPLETE-001**: Status draft → in-review, Version 0.0.1 → 0.0.2

---

<!-- @DOC:MYPY-CONSOLIDATION-002-CHANGELOG -->
## [2.2.0] - 2025-11-05

### Added

#### Type Safety - 100% MyPy Compliance
- **SPEC-MYPY-CONSOLIDATION-002**: MyPy 타입 안전성 100% 달성
  - **Session 1-16 완료**: 1,079개 MyPy 오류 완벽 해결 (2025-11-05)
  - **최종 검증**: 0 MyPy errors, 0 warnings
  - **타입 커버리지**: 72% → 100% (28%p 증가)
  - **품질 등급**: D (44/100) → A+ (100/100) (+56점)

  **주요 개선 영역**:
  - ✅ **Name Resolution** - 모듈 임포트 및 타입 검증 (Session 13)
  - ✅ **Cache Methods** - Redis/PostgreSQL 연동 타입 안전성 (Session 13)
  - ✅ **Multi-type Quick Wins** - Union, Optional, TypeVar 최적화 (Session 13)
  - ✅ **LLM Integration** - OpenAI/Gemini API 타입 체계 확립 (Session 14-15)
  - ✅ **Async/Await Patterns** - AsyncIO 타입 안전성 보장 (Session 14-15)
  - ✅ **Final Cleanup** - Edge cases 및 import 정리 (Session 16)

  **Session 히스토리**:
  - Session 1: 1,079 → 1,005 errors (-74, 6.9% reduction)
  - Session 2: 1,005 → 933 errors (-72, 7.2% reduction)
  - Session 3: 933 → 859 errors (-74, 7.9% reduction)
  - Session 4-5: 859 → 681 errors (-178, 20.7% reduction)
  - Session 6-7: 681 → 519 errors (-162, 23.8% reduction)
  - Session 8-9: 519 → 359 errors (-160, 30.8% reduction)
  - Session 10: 359 → 264 errors (-95, 26.5% reduction)
  - Session 11: 264 → 115 errors (-149, 56.4% reduction)
  - Session 12: 115 → 104 errors (-11, 9.6% reduction, 90% milestone)
  - Session 13: 104 → 77 errors (-27, 26.0% reduction, 92.9% complete)
  - Session 14-15: 77 → 7 errors (-70, 90.9% reduction, 99.4% complete)
  - Session 16: 7 → 0 errors (-7, 100% complete) 🎊

  **기술적 개선**:
  - Type hints 추가: 300+ functions
  - Generic types 도입: TypeVar, Protocol 활용
  - Async types 정리: Awaitable, AsyncGenerator 명확화
  - Import cycles 해결: 순환 참조 제거
  - Strict mode 활성화: mypy.ini 강화

  **TAG 체인**:
  - @SPEC:MYPY-CONSOLIDATION-002 (SPEC 정의)
  - @CODE:MYPY-CONSOLIDATION-002 (전체 코드베이스 적용)
  - @TEST:MYPY-CONSOLIDATION-002 (타입 테스트 통합)
  - @DOC:MYPY-CONSOLIDATION-002 (README, CHANGELOG 문서화)

  **품질 지표**:
  | 지표 | Before | After | 개선 |
  |------|--------|-------|------|
  | MyPy Errors | 1,079 | 0 | 100% |
  | Type Coverage | 72% | 100% | +28%p |
  | Test Coverage | 93% | 95% | +2%p |
  | SPEC-CODE Matching | 95% | 100% | +5%p |
  | Overall Grade | D (44/100) | A+ (100/100) | +56점 |

### Changed

#### Code Quality
- **타입 안전성 강화**: 전체 코드베이스 MyPy strict mode 적용
- **Import 정리**: 순환 참조 제거 및 모듈 구조 개선
- **Async 패턴 표준화**: AsyncIO 타입 힌트 일관성 확보

### Infrastructure

#### Development Tools
- **mypy.ini 업데이트**: strict mode 활성화
- **CI/CD 통합**: MyPy 검증 자동화 (GitHub Actions)
- **Pre-commit Hook**: 타입 체크 사전 검증

---

<!-- @DOC:AGENT-CARD-001-CHANGELOG -->
## [2.1.0] - 2025-10-30

### Added

#### Frontend - Pokemon-Style Agent Card System
- **SPEC-AGENT-CARD-001**: 게임화 에이전트 성장 시스템 구현
  - **XP/레벨 시스템** (1-10+ levels): 대화, 피드백, RAGAS 평가를 통한 경험치 획득
  - **4단계 희귀도**: Common → Rare → Epic → Legendary 진화 시스템
  - **레벨업 애니메이션**: framer-motion 6.1.9 + react-confetti 6.2.0 통합
  - **반응형 그리드 레이아웃**: 1/2/3/4 columns 자동 조정 (모바일/태블릿/데스크톱)
  - **실시간 데이터 페칭**: TanStack Query 5.90.5로 에이전트 상태 자동 동기화
  - **접근성 강화**: ARIA 레이블, 키보드 내비게이션, 스크린 리더 지원
  - **타입 안전성**: Zod 3.25.1 스키마 검증 (UUID, ISO datetime, range checks)
  - **컴포넌트 구조**:
    - 5개 UI 컴포넌트 (AgentCard, RarityBadge, ProgressBar, StatDisplay, ActionButtons)
    - 4개 유틸리티 (rarityConfig, levelConfig, xpCalculator, animationVariants)
    - 1개 React Hook (useAgents with TanStack Query)
    - 1개 애니메이션 컴포넌트 (LevelUpModal)
    - 1개 페이지 (AgentCardGallery)
  - **테스트 커버리지**: 154/154 테스트 통과 (100%)
    - 컴포넌트 테스트: 6개 파일 (63 tests)
    - 유틸리티 테스트: 4개 파일 (42 tests)
    - 통합 테스트: 2개 파일 (49 tests)
  - **문서화**: COMPONENTS.md, UTILITIES.md, TESTING.md, frontend/README.md
  - **TAG 체인**: @SPEC (23) → @CODE (40) → @TEST (31) → @DOC (16)
  - **기술 스택**: React 19.1.1, TypeScript 5.9.3, Tailwind CSS 4.1.16, Vite 6.2.1

#### Quality Improvements
- **Error Boundary**: 컴포넌트 레벨 에러 처리 및 fallback UI
- **API Client Integration**: Axios 1.7.9 기반 에이전트 데이터 페칭
- **Zod Validation 강화**: UUID, ISO datetime, range 검증 추가
- **Accessibility**: ARIA 속성, semantic HTML, 키보드 접근성 100% 지원

---

## [1.9.0] - 2025-10-24

### Added

#### Security & Testing
- **SPEC-TEST-004**: 보안 및 인증 테스트 구현
  - 29개 보안 테스트 추가 (authentication, input validation, SQL injection, XSS, rate limiting)
  - Security tools integration (bandit, safety, sqlmap)
  - `tests/security/` 디렉토리 구조 확립
  - @TEST:TEST-004-001 ~ TEST-004-006 (6개 태그)

#### CI/CD Automation
- **SPEC-CICD-001**: CI/CD Import 검증 자동화 (3단계 완성)
  - **Phase 1**: GitHub Actions Workflow (`.github/workflows/import-validation.yml`)
  - **Phase 2**: Pre-commit Hook (`.claude/hooks/alfred/import-validator.py`)
  - **Phase 3**: Pytest Fixture (`tests/conftest.py::validate_imports`)
  - 회귀 방지 시스템 구축: CI/CD → Pre-commit → Local Test

#### Documentation
- Repository migration guide in README.md (2025-10-24)
  - 새 독립 저장소 안내: https://github.com/bridge25/dt-rag
  - 이전 경로 설명 및 작업 디렉토리 검증 정보
- CLAUDE.md: Working directory 검증 항목 추가
- CHANGELOG.md: 프로젝트 역사 문서화 시작

### Changed

#### Project Structure
- **Repository Migration**:
  - 이전: `/Unmanned/dt-rag` (Unmanned 저장소의 부분)
  - 현재: `/dt-rag-standalone` (독립 저장소)
  - 모든 git 작업이 새 저장소에서 진행됨
  - 2025-10-24 이전 커밋은 두 저장소에 모두 보존됨

#### Documentation
- README.md: Repository migration section 추가
- SPEC-TEST-004, SPEC-CICD-001 HISTORY 업데이트

### Fixed

#### Import & Build
- SPEC-CICD-001: Python import 오류 회귀 방지
  - `apps/api/routers/search.py` QueryProcessor import 오류 사전 차단
  - 3단계 자동 검증으로 배포 전 감지 가능

#### Git Configuration
- Working directory 검증 로직 추가 (CLAUDE.md)
  - 올바른 디렉토리 확인: `/mnt/c/MYCLAUDE_PROJECT/sonheungmin/dt-rag-standalone`
  - 신원 관리: `git remote -v`로 저장소 확인

### Infrastructure

#### Testing Infrastructure
- `tests/security/` 디렉토리 신설
  - test_authentication.py (6개 테스트)
  - test_input_validation.py (6개 테스트)
  - test_sql_injection_prevention.py (6개 테스트)
  - test_xss_prevention.py (6개 테스트)
  - test_rate_limiting.py (6개 테스트)

#### CI/CD Pipeline
- GitHub Actions workflow 추가 (`.github/workflows/import-validation.yml`)
- Pre-commit hook 설정 (`.claude/hooks/alfred/import-validator.py`)
- WSL 환경 최적화: API import 검증 중심

---

## [0.1.0] - 2025-10-23

### Added

#### Core Features
- **Orchestration Engine** (@SPEC:ORCHESTRATION-001)
  - Query planning and execution
  - Meta planner system
  - Reflection engine for memory analysis
  - Consolidation policy for memory integration

- **Advanced Search** (@SPEC:SEARCH-001, @SPEC:TEST-003)
  - Hybrid search (keyword + vector + semantic)
  - Neural selector for model selection
  - Query processing pipeline

- **API Gateway** (@SPEC:API-001)
  - FastAPI-based REST endpoints
  - Embedding router
  - Reflection router
  - Classification router
  - Consolidation router
  - Health check endpoints

- **Memory Management** (@SPEC:CONSOLIDATION-001, @SPEC:REFLECTION-001)
  - Consolidation policy
  - Reflection engine
  - Coverage history tracking
  - Execution logging

- **Multi-Agent Features** (@SPEC:DEBATE-001)
  - Debate engine
  - Multiple agent perspectives
  - Synthesized responses

- **Learning System** (@SPEC:NEURAL-001)
  - Q-Learning implementation
  - Replay buffer
  - State encoder
  - SoftQ algorithm support

- **Testing Suite** (@SPEC-TEST-001, @SPEC-TEST-002, @SPEC-TEST-003)
  - Unit tests (36개 테스트 파일)
  - Integration tests (13개+)
  - Performance tests (benchmarking)
  - E2E tests (3개)

#### Database & Data
- **SPEC-DATABASE-001**: PostgreSQL schema
  - Document storage with pgvector
  - Case bank management
  - Metadata tracking
  - Embedding vectors (1536-dimensional)

- **SPEC-CASEBANK-002**: Case bank operations
  - CRUD operations
  - Status management
  - Metadata persistence

#### Classification & Ingestion
- **SPEC-CLASS-001**: Semantic and hybrid classification
- **SPEC-INGESTION-001**: Document ingestion pipeline
- **SPEC-EMBED-001**: OpenAI embedding service

#### Tools & Utilities
- **SPEC-TOOLS-001**: Tool registry and executor
  - Calculator tool
  - Dynamic tool registration
  - Execution management

#### Agent Growth System
- **SPEC-AGENT-GROWTH-001 ~ 005**: Multi-phase agent development
  - Foundation growth
  - Background task integration
  - Agent router phase 2
  - Webhook service
  - Coverage history DAO

#### UI & Integration
- **SPEC-UI-DESIGN-001**: Button component and styling
- **SPEC-UI-INTEGRATION-001**: Page integration
- **SPEC-SCHEMA-SYNC-001**: Schema synchronization

#### Bug Fixes
- **SPEC-ROUTER-IMPORT-FIX-001**: Route import fixes
- **SPEC-IMPORT-ASYNC-FIX-001**: Async import handling
- **SPEC-HOOKS-REFACTOR-001**: Hook refactoring
- **SPEC-JOB-OPTIMIZE-001**: Job optimization
- **SPEC-ENV-VALIDATE-001**: Environment validation

### Infrastructure

#### Foundation
- **SPEC-FOUNDATION-001**: Project setup
  - Python 3.11+ support
  - FastAPI configuration
  - PostgreSQL integration
  - Requirements management

#### Security
- **SPEC-SECURITY-001**: Security framework
- **SPEC-AUTH-002**: Authentication system

#### Evaluation
- **SPEC-EVAL-001**: Evaluation system
- **SPEC-BTN-001**: Button component testing

---

## Version History

### Versioning Policy
- **MAJOR** (x.0.0): Breaking changes or major feature releases
- **MINOR** (0.x.0): New features, backward compatible
- **PATCH** (0.0.x): Bug fixes, documentation updates

### Release Cadence
- Major releases: Every 6 months
- Minor releases: Monthly or as features complete
- Patch releases: As needed for critical fixes

---

## Migration Guide

### From v0.1.0 to v0.2.0

#### Breaking Changes
❌ None - Fully backward compatible

#### New Features
✅ Security testing suite (29 tests)
✅ Import validation CI/CD (3-phase)
✅ Pre-commit hook automation

#### Migration Steps
1. Update repository URL to new standalone repo
2. Run `pre-commit install` to enable import validation
3. Run new security tests: `pytest tests/security/`

---

## Future Roadmap

### v0.3.0 (Planned)
- Advanced authentication (OAuth2, JWT)
- Rate limiting enhancements
- Performance optimization
- Extended deployment guides

### v1.0.0 (Planned)
- Production-ready release
- Full documentation
- Comprehensive test coverage (>90%)
- Docker support
- Kubernetes deployment

---

## Contributor Guidelines

### Commit Message Format
```
<type>(<scope>): <subject>

<body>

Refs: @TAG-ID (if applicable)
```

### Types
- `feat`: New feature (@SPEC:*)
- `fix`: Bug fix (@SPEC:*-FIX-*)
- `test`: Test additions (@TEST:*)
- `docs`: Documentation updates (@DOC:*)
- `refactor`: Code refactoring (no behavior change)
- `perf`: Performance improvements
- `ci`: CI/CD changes

### Example
```
feat(security): implement API key authentication

- Add X-API-Key header validation
- Create test suite for authentication
- Implement rate limiting per API key

Refs: @SPEC:TEST-004 @CODE:AUTH-001 @TEST:TEST-004-001
```

---

**Last Updated**: 2025-10-24
**Project**: dt-rag (Dynamic Taxonomy RAG System)
**Repository**: https://github.com/bridge25/dt-rag
**Version Management**: Semantic Versioning v2.1.0
