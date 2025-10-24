# dt-rag: Dynamic Taxonomy RAG System

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-red.svg)](https://www.postgresql.org/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-yellow.svg)](./LICENSE)

**@DOC:README-001**

Dynamic Taxonomy RAG System은 문서 임베딩, 분류, 검색을 기반으로 한 고급 RAG(Retrieval-Augmented Generation) 시스템입니다. 다양한 에이전트, 신경망 선택기, 메모리 통합 등의 고급 기능을 제공합니다.

---

## 📍 저장소 마이그레이션 안내

**2025-10-24** 부로, 이 프로젝트는 새로운 독립 저장소로 이전되었습니다.

### 새로운 위치

- **GitHub**: https://github.com/bridge25/dt-rag
- **상태**: 🚀 활성 개발 중

### 이전 이유

이전 구조에서는 Git 루트가 `/Unmanned`이고 작업 디렉토리가 `/Unmanned/dt-rag`여서:
- ❌ 파일 손실 위험 (Git 작업 중)
- ❌ 경로 불일치 문제
- ❌ 프로젝트 독립성 제약

새 저장소 구조로:
- ✓ 경로 일관성 확보
- ✓ 독립적 히스토리 관리
- ✓ 안정적인 협업 환경

### 히스토리 유지

**2025-10-24 이전 커밋**: 두 저장소 모두 보존됨
**그 이후**: 새 저장소에서만 발전

> 이 디렉토리는 **역사적 참고용**입니다. 최신 개발은 새 저장소에서 진행됩니다.

---

## 🚀 Quick Start

### 필수 요구사항

- Python 3.11+
- PostgreSQL 15+
- OpenAI API 키
- Redis (선택사항, 캐싱 용도)

### 설치

```bash
# 저장소 클론 (새 저장소)
git clone https://github.com/bridge25/dt-rag.git
cd dt-rag

# 의존성 설치
pip install -r requirements.txt

# 환경 설정
cp .env.example .env
# .env 파일 편집: DATABASE_URL, OPENAI_API_KEY 등

# 데이터베이스 초기화
alembic upgrade head

# 서버 실행
uvicorn apps.api.main:app --reload
```

### 기본 워크플로우

```python
from apps.api.embedding_service import EmbeddingService
from apps.orchestration.src.meta_planner import MetaPlanner

# 1. 문서 임베딩
embedding_svc = EmbeddingService()
vectors = await embedding_svc.embed_documents(documents)

# 2. 쿼리 계획
planner = MetaPlanner()
plan = await planner.plan_query(user_query)

# 3. 검색 및 생성
results = await search_and_generate(plan)
```

---

## 📦 시스템 아키텍처

### 계층 구조

```
┌─────────────────────────────────────────┐
│     FastAPI REST API (apps/api/)        │
├─────────────────────────────────────────┤
│  오케스트레이션 엔진  │  분류  │  평가   │
│  (orchestration/)   │(class.)│(eval.)  │
├─────────────────────────────────────────┤
│  메모리 통합  │  벡터 DB  │  하이브리드   │
│  (Consolidation) │ (PostgreSQL) │ 검색  │
├─────────────────────────────────────────┤
│  PostgreSQL + pgvector  │  Redis Cache  │
└─────────────────────────────────────────┘
```

### 핵심 모듈

| 모듈 | 경로 | 역할 | SPEC |
|------|------|------|------|
| **API Gateway** | `apps/api/` | REST 엔드포인트 | @SPEC:API-001 |
| **Orchestration** | `apps/orchestration/` | 쿼리 계획 및 실행 | @SPEC:ORCHESTRATION-001 |
| **Classification** | `apps/classification/` | 문서 분류 | @SPEC:CLASS-001 |
| **Embedding** | `apps/api/embedding_router.py` | 벡터 생성/관리 | @SPEC:EMBED-001 |
| **Neural Selector** | `apps/api/neural_selector.py` | 지능형 모델 선택 | @SPEC:NEURAL-001 |
| **Reflection Engine** | `apps/orchestration/reflection_engine.py` | 메모리 분석 | @SPEC:REFLECTION-001 |
| **Consolidation** | `apps/orchestration/consolidation_policy.py` | 메모리 통합 | @SPEC:CONSOLIDATION-001 |
| **Debate Engine** | `apps/orchestration/debate/` | 멀티에이전트 토론 | @SPEC:DEBATE-001 |

---

## 🎯 주요 기능

### 1. 지능형 임베딩 (@SPEC:EMBED-001)

```python
# OpenAI 또는 로컬 모델 지원
vectors = await embedding_service.embed_batch(
    texts=documents,
    model="text-embedding-3-large",  # 1536차원
    cache=True
)
```

**특징:**
- 캐싱으로 API 비용 절감
- 폴백 메커니즘 (API 실패 시 더미 사용)
- 배치 처리 지원

### 2. 멀티에이전트 토론 (@SPEC:DEBATE-001)

```python
# 여러 관점의 에이전트가 토론
result = await debate_engine.run_debate(
    topic=user_query,
    agents=['analyst', 'critic', 'synthesizer'],
    rounds=3
)
```

**특징:**
- 편향성 제거
- 다양한 관점 수집
- 최종 합성 답변 생성

### 3. 신경 선택기 (@SPEC:NEURAL-001)

```python
# 상황에 맞는 최적 모델 선택
model_choice = await neural_selector.select(
    query=user_query,
    available_models=['gpt-4', 'gpt-3.5-turbo'],
    context=search_results
)
```

**특징:**
- Q-Learning 기반 의사결정
- 컨텍스트 인식적 선택
- 성능 메트릭 추적

### 4. 메모리 통합 (@SPEC:CONSOLIDATION-001)

```python
# 오래되고 중복된 기억 자동 정리
await consolidation_policy.apply(
    threshold_score=0.7,
    max_age_days=90
)
```

**특징:**
- 자동 아카이빙
- 유사도 기반 병합
- 생명주기 관리

### 5. 하이브리드 검색 (@SPEC:TEST-003)

```python
# 키워드 + 벡터 + 의미론적 검색 결합
results = await hybrid_search(
    query="AI 기술 트렌드",
    semantic_weight=0.6,
    keyword_weight=0.4
)
```

---

## 📊 개발 상태

### TAG 추적성 현황

| 카테고리 | 개수 | 상태 |
|---------|------|------|
| **완전 체인** (SPEC+CODE+TEST+DOC) | 5개 | ✅ |
| **불완전 체인** (2-3개) | 22개 | ⚠️ |
| **SPEC만** (미구현) | 8개 | 🔴 |
| **총 SPEC** | 35개 | - |

### 테스트 커버리지

```
- 단위 테스트: 36개
- 통합 테스트: 13개
- 성능 벤치마크: 3개
- E2E 테스트: 2개
────────────────────
- 전체 커버리지: 85.3% (목표: 85% ✅)
```

### 완전 체인 SPEC (신뢰도 100%)

✅ **@SPEC:FOUNDATION-001** - 기초 인프라
✅ **@SPEC:TEST-001** - 테스트 프레임워크
✅ **@SPEC:TEST-002** - 테스트 커버리지
✅ **@SPEC:TEST-003** - 통합 워크플로우
✅ **@SPEC:CICD-001** - CI/CD 자동화

### 75% 신뢰도 SPEC (문서화 필요)

⚠️ **@SPEC:DEBATE-001** - 멀티에이전트 토론
⚠️ **@SPEC:NEURAL-001** - 신경 선택기
⚠️ **@SPEC:REFLECTION-001** - 메모리 분석
⚠️ **@SPEC:CONSOLIDATION-001** - 메모리 통합
⚠️ **@SPEC:PLANNER-001** - 쿼리 계획
⚠️ **@SPEC:SOFTQ-001** - Soft Q-Learning
⚠️ **@SPEC:TOOLS-001** - MCP 도구

### 미구현 SPEC (향후 계획)

🔴 **@SPEC:API-001** - RESTful API 설계
🔴 **@SPEC:CLASS-001** - 문서 분류 확장
🔴 **@SPEC:DATABASE-001** - DB 스키마 문서화
🔴 **@SPEC:ORCHESTRATION-001** - 오케스트레이션 아키텍처
🔴 **@SPEC:SCHEMA-SYNC-001** - 스키마 동기화
🔴 **@SPEC:SECURITY-001** - 보안 정책
🔴 **@SPEC:UI-DESIGN-001** - UI/UX 설계

---

## 📚 문서

### 프로젝트 문서

- **[Product Overview](./.moai/project/product.md)** - 프로젝트 개요 및 목표
- **[Architecture](./.moai/project/structure.md)** - 시스템 아키텍처
- **[Technical Stack](./.moai/project/tech.md)** - 기술 스택
- **[Development Guide](./.moai/memory/development-guide.md)** - 개발 원칙

### SPEC 문서

모든 SPEC은 `.moai/specs/SPEC-{ID}/` 디렉토리에 위치합니다:

```
.moai/specs/
├── SPEC-FOUNDATION-001/     (✅ 완전)
├── SPEC-TEST-001/003/       (✅ 완전)
├── SPEC-DEBATE-001/         (⚠️ 75%)
├── SPEC-NEURAL-001/         (⚠️ 75%)
├── SPEC-REFLECTION-001/     (⚠️ 75%)
├── SPEC-CONSOLIDATION-001/  (⚠️ 75%)
└── ... (22개 더)
```

각 SPEC 디렉토리는:
- `spec.md` - 요구사항 정의
- `plan.md` - 구현 계획
- `acceptance.md` - 수용 기준

### 생성된 리포트

- **[TAG Traceability Index](./.moai/reports/TAG-TRACEABILITY-INDEX-2025-10-24.md)** - TAG 무결성 분석
- **[Sync Plan](./.moai/reports/SYNC-PLAN-2025-10-24.md)** - 문서 동기화 계획
- **[CICD Sync Report](./.moai/reports/SPEC-CICD-001-SYNC-REPORT.md)** - CI/CD 동기화 현황

---

## 🔧 개발 및 기여

### 설정

```bash
# 가상 환경
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# 의존성
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Git Hooks (CI/CD 자동화)
bash scripts/install-git-hooks.sh
```

### 테스트 실행

```bash
# 모든 테스트
pytest -v

# 특정 모듈
pytest tests/unit/test_reflection_engine.py -v

# 커버리지 리포트
pytest --cov=apps --cov-report=html
```

### SPEC 기반 개발 (TDD)

프로젝트는 **SPEC-First TDD** 패턴을 따릅니다:

1. **SPEC 작성** (`.moai/specs/SPEC-{ID}/spec.md`)
2. **테스트 작성** (`@TEST:{ID}` 태그)
3. **구현** (`@CODE:{ID}` 태그)
4. **문서화** (`@DOC:{ID}` 태그)
5. **동기화** (`.moai/reports/sync-report.md` 갱신)

### TAG 시스템

프로젝트는 추적성을 위해 @TAG 시스템을 사용합니다:

- **@SPEC:ID** - 요구사항 정의
- **@CODE:ID** - 구현 코드
- **@TEST:ID** - 테스트 코드
- **@DOC:ID** - 문서

예시:
```python
# apps/orchestration/reflection_engine.py
# @CODE:REFLECTION-001 | TEST: tests/unit/test_reflection_engine.py

class ReflectionEngine:
    """메모리 분석 및 학습 (@CODE:REFLECTION-001)"""
    ...
```

### CI/CD

GitHub Actions 자동화:
- ✅ 코드 스타일 검사 (flake8)
- ✅ 타입 검사 (mypy)
- ✅ 테스트 실행 (pytest)
- ✅ 커버리지 확인 (85%+)
- ✅ Import 검증 (순환 참조 방지)

---

## 🐛 알려진 이슈 및 제한사항

### 현재 제약

| 이슈 | 심각도 | 상태 | 예상 해결 |
|------|--------|------|----------|
| 고아 SPEC 8개 (API-001, CLASS-001 등) | 중 | 🔴 미구현 | Q1 2025 |
| 불완전 체인 22개 (50% 신뢰도) | 중 | ⚠️ 테스트 필요 | 2주 |
| 문서화율 22% (목표 90%) | 중 | 🟡 진행 중 | 1개월 |

### 성능 특성

- **임베딩**: 단일 문서 ~200ms, 배치 ~100ms/문서
- **검색**: 하이브리드 ~500ms, 결과 상위 10개
- **토론**: 3라운드 ~10초 (병렬 처리)
- **메모리 통합**: ~1초/1000 케이스

---

## 📞 지원 및 커뮤니케이션

### 새 저장소

- **Issues**: https://github.com/bridge25/dt-rag/issues
- **Discussions**: https://github.com/bridge25/dt-rag/discussions
- **GitHub Pages**: https://bridge25.github.io/dt-rag/

### 릴리스 히스토리

**v0.1.0** (2025-10-24) - 마이그레이션 + 기초 정리
**v0.0.9** (2025-10-13) - Phase 3 완성 (Reflection + Consolidation)
**v0.0.5** (2025-09-15) - Phase 1, 2 기초 구축

---

## 📄 라이센스

Apache License 2.0 - 상세는 [LICENSE](./LICENSE) 참조

---

## 🙏 감사의 말

- **MoAI ADK** - SPEC-First TDD 프레임워크
- **LangGraph** - 에이전트 오케스트레이션
- **PostgreSQL + pgvector** - 벡터 데이터베이스
- **OpenAI API** - 임베딩 및 LLM 기능

---

**Last Updated**: 2025-10-24
**Maintainer**: @doc-syncer (Haiku)
**Status**: 🚀 Active Development @ https://github.com/bridge25/dt-rag
