# 🔄 새로운 세션 컨텍스트 가이드

> **프로젝트**: Dynamic Taxonomy RAG v1.8.1
> **목표**: feature/complete-rag-system-v1.8.1 → master 브랜치 안전 통합
> **현재 상태**: Phase 1 완료, Phase 2 준비 완료

---

## 📋 즉시 실행 가이드 (새 세션용)

### 1️⃣ 프로젝트 상태 파악
```bash
# 현재 브랜치 확인
git status
git log --oneline -5

# 통합 계획서 읽기
cat MASTER_INTEGRATION_PLAN.md

# Phase 1 완료 상태 확인
cat PHASE_1_COMPLETION_CHECKLIST.md
```

### 2️⃣ 다음 작업 선택

#### 옵션 A: Phase 2 계속 진행 (권장)
```markdown
**작업 범위**: 포괄적 테스트 검증 (Day 2-3)
**담당 서브에이전트**: rag-evaluation-specialist, database-architect, hybrid-search-specialist
**예상 소요**: 2-3일

다음 명령으로 시작:
"Phase 2 포괄적 테스트 검증을 시작합니다. MASTER_INTEGRATION_PLAN.md의 Phase 2 섹션을 참조하여 단위 테스트부터 시작해주세요."
```

#### 옵션 B: 즉시 master 통합 (빠른 경로)
```markdown
**작업 범위**: 최소한의 검증 후 즉시 PR 생성
**리스크**: 중간 정도 (Phase 1에서 기본 검증 완료)
**예상 소요**: 1일

다음 명령으로 시작:
"Phase 1이 완료되었으니 최소한의 추가 검증 후 master 브랜치 통합을 진행해주세요."
```

#### 옵션 C: 특정 이슈 해결 (선택적)
```markdown
**작업 범위**: 코드 스타일 개선, 특정 컴포넌트 테스트
**리스크**: 낮음 (선택적 개선)

예시 명령:
"Flake8에서 발견된 코드 스타일 이슈를 해결해주세요."
"하이브리드 검색 시스템의 성능 테스트만 수행해주세요."
```

---

## 📊 현재 프로젝트 상태 (2025-09-18)

### ✅ 완료된 작업 (Phase 1)
- **브랜치 정리**: test_github_actions.py 제거, 커밋 스쿼시 완료
- **충돌 검증**: master 브랜치와 자동 병합 가능 확인
- **보안 검증**: 하드코딩 시크릿 없음, 환경변수 안전 사용
- **GitHub Actions**: API 의존성 제거, CI 호환성 완료

### 📈 주요 메트릭
- **변경 파일**: 186개
- **코드 변경량**: 71,780+ lines 추가
- **보안 등급**: ✅ SECURE (critical 0개)
- **충돌 위험**: ✅ LOW
- **테스트 파일**: 17개 준비됨

### 🎯 핵심 기능 (Dynamic Taxonomy RAG v1.8.1)
1. **하이브리드 검색**: BM25 + Vector + Cross-encoder reranking
2. **분류 파이프라인**: Rule-based + LLM with confidence scoring
3. **7단계 LangGraph**: State management + error recovery
4. **DAG 기반 Taxonomy**: 동적 버전 관리 + 마이그레이션
5. **포괄적 평가**: RAGAS + golden dataset
6. **보안 강화**: CORS 수정 + 감사 로깅

---

## 🔧 서브에이전트 전문 분야

### 📊 rag-evaluation-specialist
- **전문 분야**: 단위 테스트, 커버리지, RAGAS 평가
- **Phase 2 역할**: 80%+ 커버리지 달성, 품질 메트릭 측정
- **호출 방법**: "rag-evaluation-specialist를 통해 단위 테스트 커버리지를 검증해주세요"

### 🗄️ database-architect
- **전문 분야**: PostgreSQL, pgvector, 마이그레이션, 성능
- **Phase 2 역할**: 데이터베이스 통합 테스트, 성능 벤치마크
- **호출 방법**: "database-architect로 데이터베이스 마이그레이션과 성능을 검증해주세요"

### 🔍 hybrid-search-specialist
- **전문 분야**: BM25, Vector search, 크로스 엔코더 리랭킹
- **Phase 2 역할**: 검색 성능 벤치마크, 부하 테스트
- **호출 방법**: "hybrid-search-specialist로 검색 시스템 성능을 측정해주세요"

### 🌐 api-designer
- **전문 분야**: FastAPI, OpenAPI, Docker, 환경 설정
- **Phase 3-4 역할**: Docker 최적화, API 문서화
- **호출 방법**: "api-designer로 API 문서화와 Docker 환경을 최적화해주세요"

### 🔐 security-compliance-auditor
- **전문 분야**: 보안 감사, 의존성 검사, 취약점 스캔
- **Phase 3 역할**: 의존성 보안, 최종 보안 감사
- **호출 방법**: "security-compliance-auditor로 전체 보안 감사를 수행해주세요"

### 🔀 langgraph-orchestrator
- **전문 분야**: LangGraph 워크플로우, 상태 관리, 에러 복구
- **Phase 2 역할**: 오케스트레이션 통합 테스트
- **호출 방법**: "langgraph-orchestrator로 7단계 워크플로우를 검증해주세요"

---

## 📁 중요 파일 위치

### 📋 계획 및 문서
- `MASTER_INTEGRATION_PLAN.md` - **메인 통합 계획서** (616 lines)
- `PHASE_1_COMPLETION_CHECKLIST.md` - Phase 1 완료 상태
- `SESSION_CONTEXT_GUIDE.md` - 이 파일 (새 세션 가이드)

### 🧪 테스트 파일 (17개)
```
test_classification_pipeline.py         # 분류 파이프라인
test_database_fixes.py                  # 데이터베이스 수정사항
test_document_ingestion_comprehensive.py # 문서 수집 종합
test_hybrid_search_comprehensive.py     # 하이브리드 검색 종합
test_taxonomy_dag.py                    # DAG 기반 분류법
# ... 총 17개 테스트 파일
```

### 🏗️ 주요 앱 구조
```
apps/
├── api/                    # FastAPI 메인 API
├── classification/         # 분류 파이프라인
├── document_ingestion/     # 문서 수집
├── evaluation/            # RAGAS 평가 프레임워크
├── orchestration/         # LangGraph 오케스트레이션
├── search/               # 하이브리드 검색
└── taxonomy/             # 동적 분류법 관리
```

### 🔧 설정 파일
- `.github/workflows/` - GitHub Actions (API 의존성 제거 완료)
- `docker-compose.yml` - Docker 환경
- `requirements.txt` - Python 의존성

---

## 🚨 주의사항 및 팁

### ⚠️ 중요 주의사항
1. **대규모 변경**: 71K+ lines 변경으로 신중한 테스트 필요
2. **API 의존성**: GitHub Actions에서 외부 API 호출 금지 (해결됨)
3. **PostgreSQL 필수**: 모든 테스트에 PostgreSQL + pgvector 필요
4. **환경변수**: 실제 API 키 없이도 더미 모드 동작 확인

### 💡 효율적인 진행 팁
1. **병렬 서브에이전트**: 여러 전문가를 동시에 활용
2. **점진적 검증**: 컴포넌트별 → 통합 → E2E 순서
3. **성능 기준**: 검색 < 100ms, API < 200ms 목표
4. **커버리지 목표**: 각 앱 80% 이상

### 🔄 진행 상황 추적
- TodoWrite 도구로 진행 상황 체계적 관리
- Phase별 체크리스트 활용
- 각 서브에이전트 작업 결과 문서화

---

## 🚀 새 세션 시작 템플릿

### 즉시 사용 가능한 명령어들

#### Phase 2 시작 (권장)
```
"MASTER_INTEGRATION_PLAN.md를 참조하여 Phase 2 포괄적 테스트 검증을 시작해주세요. 먼저 rag-evaluation-specialist로 단위 테스트 커버리지부터 확인해주세요."
```

#### 빠른 통합 경로
```
"Phase 1이 완료되었으니 GitHub Actions 워크플로우 테스트와 함께 최소한의 검증 후 master 브랜치 PR을 준비해주세요."
```

#### 특정 컴포넌트 테스트
```
"하이브리드 검색 시스템의 성능 벤치마크만 hybrid-search-specialist로 수행해주세요."
```

#### 전체 상태 확인
```
"현재 프로젝트 상태를 확인하고 다음 단계를 추천해주세요."
```

---

**📝 이 가이드를 새 세션 시작 시 참조하여 효율적인 작업 진행이 가능합니다.**

**🎯 목표**: 안전하고 체계적인 master 브랜치 통합으로 Dynamic Taxonomy RAG v1.8.1 배포 완료