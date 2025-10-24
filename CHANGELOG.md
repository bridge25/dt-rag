# CHANGELOG

모든 주요 변경사항은 이 파일에 기록됩니다.
형식: [Semantic Versioning](https://semver.org/) 준수

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
