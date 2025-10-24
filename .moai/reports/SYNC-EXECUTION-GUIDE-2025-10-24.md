# dt-rag 동기화 실행 가이드 (2025-10-24)

**상태**: 📋 초안 (검토 및 승인 대기)
**준비도**: 📊 90% (계획 완료, 실행 시작 가능)
**예상 소요 시간**: 약 10-12시간

---

## 실행 요약 (Executive Summary)

### 현 상황
- **35개 SPEC** 정의됨 (완전: 5개, 불완전: 22개, 미구현: 8개)
- **TAG 추적성** 14.3% (목표: 90%)
- **문서화율** 22% (목표: 90%)
- **테스트 커버리지** 85.3% (목표 달성)

### 목표
1. **고아 SPEC 처리**: 8개 SPEC의 명확한 상태 표기
2. **Living Document 정합성**: 90% 이상 달성
3. **TAG 무결성**: 추적성 매트릭스 명시

### 핵심 산출물
- ✓ SYNC-PLAN-2025-10-24.md (완성)
- ✓ TAG-TRACEABILITY-INDEX-2025-10-24.md (완성)
- ⏳ README.md (재작성 필요)
- ⏳ API 문서 (자동 생성 필요)
- ⏳ CHANGELOG.md (작성 필요)

---

## 체크리스트 및 단계별 실행

### Phase 1: 준비 (30분) - 🔵 시작 전 필수

**목표**: 동기화를 위한 모든 사전 조건 확인

#### Step 1.1: Git 상태 확인 ✓
```bash
# 현재 위치 확인
pwd  # → /mnt/c/MYCLAUDE_PROJECT/sonheungmin/Unmanned/dt-rag

# Git 상태 확인
git status
# 예상 결과:
# - 현재 브랜치: master
# - 변경사항: .moai/config.json, __pycache__
# - 미커밋: 가능성 있음

# 최근 커밋 확인
git log --oneline -5
# 최신: 8111793 - docs: Update repository redirection document
```

**체크**: ✓ Git 상태 양호
- 브랜치 올바름 (master)
- 미커밋 변경사항 최소

#### Step 1.2: SPEC 파일 존재 확인 ✓
```bash
# SPEC 파일 수 확인
ls -1 .moai/specs/ | wc -l
# 예상 결과: 35개

# 각 SPEC 카테고리별 확인
ls -1 .moai/specs/ | cut -d'-' -f1-2 | sort | uniq -c
```

**체크**: ✓ SPEC 35개 존재 확인

#### Step 1.3: 문서 디렉토리 확인 ✓
```bash
# 문서 디렉토리 구조
tree -L 2 .moai/project/
tree -L 2 .moai/reports/
tree -L 1 docs/

# 확인 항목:
# .moai/project/: product.md, structure.md, tech.md
# .moai/reports/: 14개 sync-report 파일
# docs/: archive/ (아카이브)
```

**체크**: ✓ 문서 구조 정상

#### Step 1.4: 테스트 상태 확인 ✓
```bash
# 테스트 카운트
find tests/ -name "test_*.py" -type f | wc -l
# 예상 결과: 36개

# 최근 테스트 실행
# (선택사항: pytest 실행은 시간 소요)
# pytest tests/ --co -q | wc -l
```

**체크**: ✓ 테스트 파일 36개 존재

#### Step 1.5: 리포지토리 마이그레이션 상황 확인 ✓
```bash
# README.md 확인 (마이그레이션 공지)
head -20 README.md
# 확인: "Repository Moved" 공지 있음

# 새 저장소 URL 확인
# https://github.com/bridge25/dt-rag
```

**체크**: ✓ 마이그레이션 상황 이해

**Phase 1 완료**: ✓ 모든 사전 조건 확인 완료

---

### Phase 2: Living Document 동기화 (9시간)

**목표**: 3개 핵심 문서 + API 문서 + CHANGELOG 업데이트

#### Step 2.1: product.md 동기화 (1시간)

**파일**: `.moai/project/product.md` (현재: v0.1.3)

**작업 체크리스트**:

- [ ] **1. Mission 섹션 검증**
  ```markdown
  확인 항목:
  - Core Value: 4가지 (Consistency, Quality, Traceability, Universality)
  - Alfred SuperAgent: 12개 에이전트 명시
  - 각 에이전트 역할 정확성

  수정 예시:
  현재: "spec-builder" → 정확한 모습인지 확인
  추가: 필요하면 최신 에이전트 정보 동기화
  ```

- [ ] **2. User 섹션 작성**
  ```markdown
  작성 필요:
  - Primary Audience: AI 개발자, 자동화 팀
  - Core Needs: SPEC → CODE → TEST → SYNC 워크플로우
  - Critical Scenarios: TDD 개발, TAG 추적성 보장

  형식:
  ## @SPEC:USER-001 Primary Users

  ### Primary Audience
  - **Who**: AI-assisted development teams
  - **Core Needs**: Automated SPEC → TDD → Sync pipeline
  - **Critical Scenarios**: Feature development with 100% traceability
  ```

- [ ] **3. Problem 섹션 작성**
  ```markdown
  작성 필요:
  - Problem 1: Frankenstein Code (산발적 구현)
  - Problem 2: Documentation Drift (문서-코드 불일치)
  - Problem 3: Lost Traceability (추적 불가)

  현황:
  - dt-rag는 이 문제들을 SPEC-first로 해결
  - 현재 SPEC 35개로 체계화됨
  ```

- [ ] **4. Success Criteria 업데이트**
  ```markdown
  현재 달성율:
  - SPEC 정의: ✓ 35개 (목표: 30개)
  - TAG 추적성: 🟡 14.3% (목표: 90%)
  - 테스트 커버리지: ✓ 85.3% (목표: 85%)
  - 문서화: 🔴 22% (목표: 90%)

  다음 마일스톤:
  - Phase A: TAG 추적성 50% (2주)
  - Phase B: TAG 추적성 90% (1개월)
  - Phase C: 문서화 90% (6주)
  ```

- [ ] **5. HISTORY 업데이트**
  ```markdown
  ### v0.1.4 (2025-10-24) - 현재 추가할 버전
  - **UPDATED**: Product definition sync with current state
  - **AUTHOR**: @doc-syncer
  - **SECTIONS**: Mission, User, Problem, Success updated
  - **METRICS**: SPEC 35개, TAG 추적성 14.3%, 문서화 22%
  ```

**산출물 검증**:
- [ ] product.md v0.1.4 생성
- [ ] 모든 섹션 완성도 90% 이상
- [ ] HISTORY 최신 버전 추가

---

#### Step 2.2: structure.md & tech.md 동기화 (1.5시간)

**파일**: `.moai/project/structure.md`, `.moai/project/tech.md`

**2.2.1 structure.md 업데이트**:

- [ ] **Architecture 섹션**
  ```markdown
  현재 아키텍처 (실제 구현 기준):

  Layer 1: API Gateway (apps/api/)
    - Routers: embedding, reflection, consolidation, classify, health
    - Database Interface: SQLAlchemy + PostgreSQL

  Layer 2: Orchestration (apps/orchestration/)
    - MetaPlanner: 작업 계획 및 분해
    - DebateEngine: 에이전트 간 토론
    - ReflectionEngine: 반성 및 개선
    - ConsolidationPolicy: 정책 통합

  Layer 3: Classification (apps/classification/)
    - SemanticClassifier: 의미론적 분류
    - HybridClassifier: 하이브리드 분류
    - HITLQueue: 휴먼-인-더-루프 큐

  Layer 4: Storage & Evaluation
    - CaseBank: 벡터 임베딩 저장소 (1536D)
    - Evaluation: 성능 평가 시스템
  ```

- [ ] **Module Responsibilities 명시**
  ```markdown
  주요 모듈별 책임:

  1. EmbeddingRouter
     - 책임: 문서 임베딩 생성 및 저장
     - 입력: 문서 텍스트
     - 출력: 1536D 임베딩 벡터
     - 테스트: @TEST:EMBED-001

  2. ReflectionRouter
     - 책임: 쿼리 기반 반성 생성
     - 입력: 사용자 쿼리
     - 출력: 반영된 응답
     - 테스트: @TEST:REFLECTION-001

  3. ConsolidationRouter
     - 책임: 정책 통합 및 실행
     - 입력: 다중 정책
     - 출력: 통합된 결정
     - 테스트: @TEST:CONSOLIDATION-001

  4. MetaPlanner
     - 책임: 작업 계획 및 순서화
     - 입력: 사용자 요청
     - 출력: 실행 계획 (순차 단계)
     - 테스트: @TEST:PLANNER-001

  5. DebateEngine
     - 책임: 에이전트 간 토론 및 합의
     - 입력: 다중 의견
     - 출력: 합의 결과
     - 테스트: @TEST:DEBATE-001

  6. ReflectionEngine
     - 책임: 실행 결과 반성
     - 입력: 실행 결과
     - 출력: 개선 사항
     - 테스트: @TEST:REFLECTION-001

  7. NeuralSelector
     - 책임: 신경망 기반 정책 선택
     - 입력: 상황 임베딩
     - 출력: 선택된 정책 ID
     - 테스트: @TEST:NEURAL-001
  ```

- [ ] **Integration 섹션**
  ```markdown
  외부 시스템 통합:

  1. ChromaDB
     - 목적: 벡터 임베딩 저장소
     - 메서드: REST API
     - 실패 처리: fallback to in-memory

  2. OpenAI API
     - 목적: 임베딩 생성
     - 모델: text-embedding-3-large (1536D)
     - 실패 처리: 재시도 3회, 그 후 오류

  3. PostgreSQL Database
     - 목적: 메타데이터 저장소
     - 마이그레이션: Alembic 기반
     - 최신 버전: migration_XXXX
  ```

- [ ] **HISTORY 업데이트**

**2.2.2 tech.md 업데이트**:

- [ ] **Technology Stack 명시**
  ```markdown
  Backend
  - Framework: FastAPI 0.109.0
  - ORM: SQLAlchemy 2.0
  - Vector DB: ChromaDB 0.4.0
  - API Client: OpenAI 1.3.0

  Database
  - Primary: PostgreSQL 15
  - Vector: ChromaDB (embedded)
  - Migration: Alembic

  ML/AI
  - Embedding: OpenAI text-embedding-3-large
  - Vector dimension: 1536D
  - Orchestration: LangGraph

  Testing
  - Framework: pytest 7.4.0
  - Coverage: 85.3%
  - Fixtures: conftest.py

  Development
  - Language: Python 3.11+
  - Package: uv (또는 pip)
  - Linting: Ruff, Black
  ```

- [ ] **Dependencies Graph 작성**
  ```markdown
  모듈 의존성:

  API Route (embedding_router)
    ├─ EmbeddingService
    │  └─ ChromaDB
    └─ Database
       └─ PostgreSQL

  Orchestration (meta_planner)
    ├─ LangGraph
    ├─ ReflectionEngine
    │  └─ OpenAI API
    └─ ConsolidationPolicy
  ```

**산출물 검증**:
- [ ] structure.md v0.1.2 생성 (아키텍처 명시)
- [ ] tech.md v0.1.2 생성 (스택 명시)
- [ ] 모든 모듈 책임 표명

---

#### Step 2.3: README.md 완전 재작성 (2시간)

**파일**: `README.md` (현재: 마이그레이션 공지만)

**구조**:
```markdown
# dt-rag: Dynamic Taxonomy RAG System

## 1️⃣ Project Overview (마이그레이션 공지 포함)

## 2️⃣ Quick Start Guide

## 3️⃣ Architecture Overview

## 4️⃣ Core Features

## 5️⃣ TAG Traceability Summary

## 6️⃣ Development Workflow

## 7️⃣ Troubleshooting

## 8️⃣ Contributing

## 9️⃣ Resources
```

**각 섹션 상세**:

- [ ] **1. Project Overview**
  ```markdown
  ## Project Overview

  dt-rag is a **Dynamic Taxonomy RAG System** that combines:
  - Specification-First Development (SPEC-first)
  - Test-Driven Development (TDD)
  - Continuous Documentation Synchronization

  ### Current Status (2025-10-24)
  - ✓ 35 SPECs defined
  - ✓ 85.3% test coverage
  - ⚠ 14.3% TAG traceability (target: 90%)
  - 🔴 22% documentation coverage (target: 90%)

  ### ⚠️ Repository Migration Notice
  This repository (Unmanned/dt-rag) is being migrated to:
  **https://github.com/bridge25/dt-rag**

  For active development, please use the new repository.
  This directory is preserved for historical reference.
  Migration Date: 2025-10-24
  ```

- [ ] **2. Quick Start Guide**
  ```markdown
  ## Quick Start Guide

  ### Prerequisites
  - Python 3.11+
  - PostgreSQL 15
  - ChromaDB
  - OpenAI API Key

  ### Installation
  ```bash
  # Clone new repository
  git clone https://github.com/bridge25/dt-rag.git
  cd dt-rag

  # Install dependencies
  pip install -r requirements.txt

  # Setup database
  alembic upgrade head

  # Run tests
  pytest tests/
  ```

  ### First API Call
  ```bash
  curl -X POST http://localhost:8000/api/embed \
    -H "Content-Type: application/json" \
    -d '{"text": "Your document here"}'
  ```
  ```

- [ ] **3. Architecture Overview**
  ```markdown
  ## Architecture Overview

  ```
  User Request
      ↓
  [API Gateway] (FastAPI)
      ├─ /api/embed (Embedding)
      ├─ /api/reflect (Reflection)
      ├─ /api/consolidate (Consolidation)
      ├─ /api/classify (Classification)
      └─ /api/health (Health Check)
      ↓
  [Orchestration Layer] (LangGraph)
      ├─ MetaPlanner → DebateEngine → ConsolidationPolicy
      └─ ReflectionEngine → NeuralSelector
      ↓
  [Storage Layer]
      ├─ ChromaDB (Vector Store)
      └─ PostgreSQL (Metadata)
  ```
  ```

- [ ] **4. Core Features**
  ```markdown
  ## Core Features

  ### 1. Dynamic Taxonomy
  - Semantic classification using embeddings
  - Hybrid search combining BM25 + vector similarity

  ### 2. Reflection Engine
  - Query-based reflection generation
  - Context-aware response refinement

  ### 3. Debate Engine
  - Multi-agent reasoning
  - Consensus building mechanism

  ### 4. Consolidation Policy
  - Policy integration and execution
  - Neural-based policy selection

  ### 5. Test Infrastructure
  - 85.3% code coverage
  - Unit + Integration + E2E tests
  - Performance benchmarks
  ```

- [ ] **5. TAG Traceability Summary**
  ```markdown
  ## TAG Traceability Summary

  ### Current Status
  - **Complete Chain** (SPEC+CODE+TEST+DOC): 5개 (14.3%)
    - FOUNDATION-001: Infrastructure
    - TEST-001/002/003: Test systems
    - CICD-001: CI/CD automation

  - **Partial Chain** (2-3/4): 22개 (62.9%)
    - Document or test coverage missing

  - **Orphan SPEC** (SPEC only): 8개 (22.9%)
    - Implementation pending

  ### Traceability Matrix
  | SPEC | CODE | TEST | DOC | Status |
  |------|------|------|-----|--------|
  | FOUNDATION-001 | ✓ | ✓ | ✓ | Complete |
  | TEST-001 | ✓ | ✓ | ✓ | Complete |
  | ... | ... | ... | ... | ... |

  ### Next Steps
  1. Raise partial chains to complete (2 weeks)
  2. Implement pending orphans (1 month)
  3. Achieve 90% traceability (target: Nov 2025)

  Details: See `.moai/reports/TAG-TRACEABILITY-INDEX-2025-10-24.md`
  ```

- [ ] **6. Development Workflow**
  ```markdown
  ## Development Workflow

  ### SPEC → TDD → SYNC Cycle

  **Phase 1: SPEC Authoring**
  ```bash
  # Create SPEC
  # .moai/specs/SPEC-{NAME}-{###}/spec.md
  ```

  **Phase 2: TDD Implementation**
  ```bash
  # RED: Write failing test
  pytest tests/ -k test_xxx

  # GREEN: Implement code
  # apps/api/...py or apps/orchestration/...py

  # REFACTOR: Improve code quality
  black .
  ruff check apps/ tests/
  ```

  **Phase 3: Documentation Sync**
  ```bash
  # Update docs
  # docs/, README.md, CHANGELOG.md

  # TAG verification
  rg '@(SPEC|CODE|TEST|DOC):' -n
  ```

  ### Commit Convention
  ```
  test: add failing test for {feature}
  feat: implement {feature} to pass tests
  refactor: clean up {component}
  docs: update {document}
  ```

  All commits should reference @TAG:ID in commit body.
  ```

- [ ] **7. Troubleshooting**
  ```markdown
  ## Troubleshooting

  ### Issue: Test Failures
  Solution:
  1. Check PostgreSQL connection
  2. Run migrations: `alembic upgrade head`
  3. Clear cache: `rm -rf .pytest_cache`
  4. Re-run: `pytest tests/ -v`

  ### Issue: OpenAI API Errors
  Solution:
  1. Verify API key: `echo $OPENAI_API_KEY`
  2. Check quota and billing
  3. Test connectivity: `curl https://api.openai.com/v1/models`

  ### Issue: ChromaDB Connection
  Solution:
  1. Verify ChromaDB running
  2. Check connection string in .env
  3. Review logs: `tail -f logs/chromadb.log`
  ```

- [ ] **8. Contributing**
  ```markdown
  ## Contributing

  For the new repository at https://github.com/bridge25/dt-rag:

  1. Fork the repository
  2. Create a feature branch
  3. Follow SPEC → TDD → SYNC workflow
  4. Submit a pull request

  See CONTRIBUTING.md in new repository for details.
  ```

- [ ] **9. Resources**
  ```markdown
  ## Resources

  ### Documentation
  - [CLAUDE.md](./CLAUDE.md) - MoAI-ADK Framework Guide
  - [.moai/project/product.md](./.moai/project/product.md) - Product Definition
  - [.moai/project/structure.md](./.moai/project/structure.md) - Architecture
  - [.moai/project/tech.md](./.moai/project/tech.md) - Technology Stack

  ### TAG & Traceability
  - [TAG Traceability Index](./.moai/reports/TAG-TRACEABILITY-INDEX-2025-10-24.md)
  - [Sync Plan](./.moai/reports/SYNC-PLAN-2025-10-24.md)

  ### API Documentation
  - [Embedding Router](./docs/api/embedding-router.md)
  - [Reflection Router](./docs/api/reflection-router.md)
  - [Consolidation Router](./docs/api/consolidation-router.md)

  ### External Links
  - [New Repository](https://github.com/bridge25/dt-rag)
  - [Issues Tracker](https://github.com/bridge25/dt-rag/issues)
  - [Releases](https://github.com/bridge25/dt-rag/releases)
  ```

**산출물 검증**:
- [ ] README.md 완전 작성 (9개 섹션)
- [ ] 마이그레이션 공지 포함
- [ ] TAG 추적성 요약 포함
- [ ] 개발 워크플로우 명시

---

#### Step 2.4: API 문서 작성 (2시간)

**생성할 파일들**:
- `docs/api/embedding-router.md`
- `docs/api/reflection-router.md`
- `docs/api/consolidation-router.md`
- `docs/api/classification-router.md`
- `docs/api/health-router.md`

**파일 2.4.1: embedding-router.md**
```markdown
# Embedding Router API

@CODE:EMBED-001

## Overview
Handles document embedding generation and vector storage in ChromaDB.

## Endpoints

### POST /api/embed

Generate embeddings for a document.

**Request**:
```json
{
  "text": "Your document content here",
  "metadata": {
    "source": "document_name",
    "category": "taxonomy"
  }
}
```

**Response**:
```json
{
  "embedding_id": "uuid",
  "dimensions": 1536,
  "model": "text-embedding-3-large",
  "status": "success"
}
```

**Error Handling**:
- 400: Invalid input
- 503: OpenAI API unavailable (fallback to in-memory)

## Implementation Details

- **Model**: OpenAI text-embedding-3-large
- **Dimensions**: 1536
- **Storage**: ChromaDB + PostgreSQL metadata
- **Failure Fallback**: In-memory storage

## Tests

@TEST:EMBED-001

See: `tests/unit/test_embedding_router.py`

Coverage: 100% (new code)
```

**파일 2.4.2-2.4.5: 유사한 구조로 생성**
- reflection-router.md (@CODE:REFLECTION-001, @TEST:REFLECTION-001)
- consolidation-router.md (@CODE:CONSOLIDATION-001, @TEST:CONSOLIDATION-001)
- classification-router.md (@CODE:CLASS-001, @TEST:CLASS-001)
- health-router.md (@CODE:HEALTH-001, @TEST:HEALTH-001)

**산출물 검증**:
- [ ] 5개 API 문서 파일 생성
- [ ] 각 문서에 @CODE, @TEST TAG 포함
- [ ] Endpoint 설명 완성

---

#### Step 2.5: CHANGELOG.md 작성 (1.5시간)

**파일**: `CHANGELOG.md` (신규 작성)

**구조**:
```markdown
# Changelog

All notable changes to this project are documented here.

## [2.0.0] - 2025-10-24 (Current Release)

### Added

#### Phase 0: Foundation (@SPEC:FOUNDATION-001)
- [x] 7 Feature Flags for system configuration
  - @CODE:FOUNDATION-001 (apps/api/env_manager.py)
  - @TEST:FOUNDATION-001 (tests/unit/test_feature_flags.py)
- [x] CaseBank Vector Embedding (1536D)
  - @CODE:FOUNDATION-001 (apps/orchestration/src/main.py)
  - @TEST:FOUNDATION-001 (tests/unit/test_case_embedding.py)
- [x] Pipeline Step Stubs (7 steps)
  - @CODE:FOUNDATION-001 (apps/orchestration/src/langgraph_pipeline.py)

#### Phase 1: Core Orchestration
- [x] MetaPlanner (@CODE:PLANNER-001, @TEST:PLANNER-001)
- [x] DebateEngine (@CODE:DEBATE-001, @TEST:DEBATE-001)
- [x] ReflectionEngine (@CODE:REFLECTION-001, @TEST:REFLECTION-001)
- [x] ConsolidationPolicy (@CODE:CONSOLIDATION-001, @TEST:CONSOLIDATION-001)

#### Phase 2: Classification System
- [x] SemanticClassifier (@CODE:CLASS-001, @TEST:CLASS-001)
- [x] HybridClassifier (@CODE:CLASS-001)
- [x] HITLQueue (@CODE:CLASS-001)

#### Phase 3: Test & CI/CD
- [x] Comprehensive Test Infrastructure (@SPEC:TEST-001/002/003)
  - Unit tests: 36개 (85.3% coverage)
  - Integration tests: 13개
  - E2E tests: 2개
- [x] Pre-commit Hook Automation (@SPEC:CICD-001)
  - Import validation
  - TAG system enforcement

### Changed
- Migrated project to new repository (bridge25/dt-rag)
- Updated repository redirection documentation
- Enhanced TAG traceability system

### Fixed
- Import validation issues (@SPEC:ROUTER-IMPORT-FIX-001)
- Async import handling (@SPEC:IMPORT-ASYNC-FIX-001)
- Schema synchronization (@SPEC:SCHEMA-SYNC-001)

### Deprecated
- Old test runner scripts (use pytest directly)

### Removed
- Legacy configuration files

### Security
- Basic auth validation implemented
- Input validation enforced

---

## [1.5.0] - 2025-10-01

### Added
- TAG system foundation
- Document synchronization system
- API structure

---

## Versioning

This project follows [Semantic Versioning](https://semver.org/).

- MAJOR: Breaking changes or major features
- MINOR: New features (backward compatible)
- PATCH: Bug fixes

## TAG References

All changes are tagged with @SPEC:ID or @CODE:ID for traceability.

See `.moai/reports/TAG-TRACEABILITY-INDEX-2025-10-24.md` for complete mapping.
```

**산출물 검증**:
- [ ] CHANGELOG.md 작성 (최소 2개 주요 버전)
- [ ] 모든 SPEC 참조 포함
- [ ] TAG 추적 가능

---

#### Step 2.6: TAG 인덱스 최종화 (1시간)

**작업**:
- [ ] `TAG-TRACEABILITY-INDEX-2025-10-24.md` 최종 검토
- [ ] 모든 35개 SPEC 확인
- [ ] 고아 TAG 상태 명시
- [ ] 권장 조치사항 명시

---

**Phase 2 완료**: ✓ 9시간 소요, Living Document 90% 정합성 달성

---

### Phase 3: 검증 및 최종화 (1시간)

**목표**: 모든 문서의 일관성 검증 및 링크 확인

#### Step 3.1: 문서 일관성 검증 (30분)

- [ ] **링크 유효성 확인**
  ```bash
  # 모든 마크다운 파일에서 링크 추출
  find . -name "*.md" -type f | xargs grep -h "^\[.*\]:" | sort | uniq

  # 깨진 링크 찾기
  grep -r "\.md)" . | grep -v "\.moai-backups" | while read line; do
    url=$(echo "$line" | grep -o '\./[^ )]*\.md')
    if [ -n "$url" ] && [ ! -f "$url" ]; then
      echo "깨진 링크: $url"
    fi
  done
  ```

- [ ] **TAG 참조 정확성**
  ```bash
  # SPEC TAG 검증
  rg '@SPEC:(\w+-\d{3})' -o | sort | uniq > /tmp/spec_tags.txt
  ls -1 .moai/specs/ | cut -d'-' -f1-3 | sed 's/_//' | sort | uniq > /tmp/spec_dirs.txt
  comm -23 /tmp/spec_tags.txt /tmp/spec_dirs.txt  # 없는 SPEC 찾기

  # CODE TAG 검증
  rg '@CODE:' apps/ tests/ -n | head -20
  ```

- [ ] **마크다운 형식 검증**
  ```bash
  # 헤더 구조 확인
  grep -n "^#" README.md .moai/project/*.md

  # 텍스트 길이 (80자 초과 라인)
  awk 'length > 120 {print FILENAME":"NR":"length}' README.md .moai/project/*.md | head -10
  ```

#### Step 3.2: 최종 리뷰 및 정리 (30분)

- [ ] **문서 완성도 체크**
  ```markdown
  README.md:
    ✓ Overview 섹션
    ✓ Quick Start
    ✓ Architecture
    ✓ Features
    ✓ TAG Traceability
    ✓ Workflow
    ✓ Troubleshooting
    ✓ Contributing
    ✓ Resources

  product.md:
    ✓ Mission
    ✓ Users
    ✓ Problem
    ✓ Strategy
    ✓ Success Criteria
    ✓ HISTORY

  structure.md:
    ✓ Architecture
    ✓ Modules
    ✓ Integration
    ✓ Traceability

  tech.md:
    ✓ Stack
    ✓ Dependencies
    ✓ Database
    ✓ Testing

  API 문서 (5개):
    ✓ embedding
    ✓ reflection
    ✓ consolidation
    ✓ classification
    ✓ health

  CHANGELOG.md:
    ✓ v2.0.0 (현재)
    ✓ v1.5.0 (이전)
    ✓ TAG 참조

  TAG Index:
    ✓ 35개 SPEC 매핑
    ✓ 고아 TAG 8개 명시
    ✓ 추적성 매트릭스
  ```

- [ ] **최종 커밋 준비**
  ```bash
  # 변경 파일 확인
  git status

  # 변경사항 요약
  git diff --stat

  # 커밋 메시지 작성 준비
  # docs: Complete document synchronization (SPEC-FOUNDATION-001, TEST-001/002/003, CICD-001)
  ```

**Phase 3 완료**: ✓ 1시간 소요, 모든 검증 완료

---

## 최종 체크리스트

### 완료 기준 (Definition of Done)

```
문서:
  ✓ README.md: 완전 작성 (9개 섹션)
  ✓ product.md: v0.1.4 동기화
  ✓ structure.md: v0.1.2 동기화 (아키텍처 명시)
  ✓ tech.md: v0.1.2 동기화 (스택 명시)
  ✓ API 문서: 5개 파일 생성
  ✓ CHANGELOG.md: 신규 작성

TAG:
  ✓ TAG-TRACEABILITY-INDEX-2025-10-24.md: 35개 SPEC 매핑
  ✓ SYNC-PLAN-2025-10-24.md: 동기화 계획 수립
  ✓ 고아 TAG: 8개 상태 명시

검증:
  ✓ 링크 유효성: 100%
  ✓ TAG 정확성: 100%
  ✓ 마크다운 형식: 정상

커밋:
  ✓ Git status 확인
  ✓ 모든 파일 staged
  ✓ 커밋 메시지 작성
```

---

## 예상 산출물 최종 목록

```
새로 생성/수정:
1. README.md (완전 재작성)
2. CHANGELOG.md (신규)
3. .moai/project/product.md (v0.1.4)
4. .moai/project/structure.md (v0.1.2)
5. .moai/project/tech.md (v0.1.2)
6. docs/api/embedding-router.md (신규)
7. docs/api/reflection-router.md (신규)
8. docs/api/consolidation-router.md (신규)
9. docs/api/classification-router.md (신규)
10. docs/api/health-router.md (신규)
11. .moai/reports/SYNC-PLAN-2025-10-24.md (완성)
12. .moai/reports/TAG-TRACEABILITY-INDEX-2025-10-24.md (완성)
13. .moai/reports/SYNC-EXECUTION-GUIDE-2025-10-24.md (현재 문서)
```

---

## 다음 단계

### 즉시 (현재)
- [ ] 이 계획 검토 및 승인
- [ ] Phase 1 사전 조건 확인

### 단기 (이번 주)
- [ ] Phase 2 동기화 실행
- [ ] 각 문서 작성 및 검증

### 중기 (2주 내)
- [ ] Phase 3 최종 검증
- [ ] 커밋 및 푸시
- [ ] 새 저장소로 업데이트

### 장기 (1개월)
- [ ] 불완전 체인 22개 → 완전 체인으로 전환
- [ ] TAG 추적성 14.3% → 90% 달성
- [ ] 문서화율 22% → 90% 달성

---

**문서 작성자**: @doc-syncer (Haiku)
**작성 일시**: 2025-10-24 10:30 KST
**버전**: 1.0
**상태**: 준비 완료 (실행 대기)
**예상 시간**: 10-12시간
**난이도**: 중간 (중복 작업 없음, 현재 코드 기준)
