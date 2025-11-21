# SPEC-TAG-IMPL-001: 구현 계획

## 개요

| 항목 | 값 |
|------|-----|
| **SPEC ID** | TAG-IMPL-001 |
| **버전** | 0.0.1 |
| **작성일** | 2025-11-21 |
| **상태** | draft |
| **우선순위** | Critical |

---

## 1. 구현 전략

### 1.1 접근 방식

**점진적 TAG 추가 전략**:
1. 핵심 모듈부터 시작하여 외곽으로 확장
2. 각 Phase 완료 시 검증 후 다음 Phase 진행
3. 코드 기능 변경 없이 주석만 추가

### 1.2 의존성 그래프

```
Phase 1 (Backend 핵심)
    ↓
Phase 2 (Backend 전체) ←── 병렬 가능 ──→ Phase 3 (Frontend)
    ↓                                      ↓
    └────────────→ Phase 4 (테스트) ←──────┘
                        ↓
                  Phase 5 (자동화)
```

---

## 2. Phase별 상세 계획

### Phase 1: 핵심 Backend 모듈 TAG 추가

**범위**: ~50개 파일
**우선순위**: P0 (Critical)

#### 대상 디렉토리
```
apps/api/routers/          # API 라우터 (~15개)
apps/api/services/         # 서비스 레이어 (~10개)
apps/search/               # 검색 엔진 (~8개)
apps/orchestration/src/    # LangGraph 파이프라인 (~10개)
apps/core/                 # 핵심 유틸리티 (~7개)
```

#### 작업 단계
1. **파일-SPEC 매핑 테이블 작성**
   - 각 파일이 어떤 SPEC에 해당하는지 결정
   - 다중 SPEC 관련 파일 식별

2. **TAG 형식 템플릿 준비**
   ```python
   # -*- coding: utf-8 -*-
   """
   {모듈 설명}

   @CODE:{DOMAIN}-{NNN}
   """
   ```

3. **파일별 TAG 추가**
   - 기존 docstring 유지
   - @CODE 태그만 추가
   - 코드 기능 변경 없음

4. **검증**
   - TAG 형식 검증
   - 테스트 실행 (기존 테스트 통과 확인)

#### 예상 커밋
- `tag(phase1): Add @CODE tags to apps/api/routers/`
- `tag(phase1): Add @CODE tags to apps/search/`
- `tag(phase1): Add @CODE tags to apps/orchestration/`
- `tag(phase1): Phase 1 completion - 50 files tagged`

---

### Phase 2: 나머지 Backend 파일 TAG 추가

**범위**: ~88개 파일
**우선순위**: P1 (High)

#### 대상 디렉토리
```
apps/api/                  # 나머지 API 파일
apps/classification/       # 분류 모듈
apps/ingestion/            # 문서 수집
apps/evaluation/           # 평가 시스템
apps/knowledge_builder/    # 지식 빌더
apps/security/             # 보안 모듈
apps/monitoring/           # 모니터링
apps/agent_system/         # 에이전트 시스템
```

#### 작업 단계
1. Phase 1과 동일한 프로세스
2. 도메인별 SPEC 매핑 확정
3. TAG 추가 및 검증

---

### Phase 3: Frontend 컴포넌트 TAG 추가

**범위**: ~122개 파일
**우선순위**: P2 (Medium)

#### 대상 디렉토리
```
frontend/src/components/   # React 컴포넌트
frontend/src/pages/        # 페이지 컴포넌트
frontend/src/hooks/        # 커스텀 훅
frontend/src/utils/        # 유틸리티
apps/frontend/             # Next.js 앱 (중복 정리 후)
```

#### TAG 형식 (TypeScript)
```typescript
/**
 * {컴포넌트 설명}
 *
 * @CODE:{DOMAIN}-{NNN}
 */
```

#### 특별 고려사항
- `frontend/` vs `apps/frontend/` 중복 해결 필요
- 컴포넌트 계층 구조에 따른 TAG 설계

---

### Phase 4: 테스트 파일 TAG 추가

**범위**: ~108개 파일
**우선순위**: P1 (High)

#### 대상 디렉토리
```
tests/unit/                # 단위 테스트
tests/integration/         # 통합 테스트
tests/e2e/                 # E2E 테스트
tests/performance/         # 성능 테스트
tests/security/            # 보안 테스트
```

#### TAG 매핑 전략
- **@TEST** 태그는 테스트 대상 코드의 **@CODE** 태그와 동일한 SPEC ID 사용
- 예: `test_hybrid_search.py` → `@TEST:SEARCH-001`

---

### Phase 5: 자동화 및 CI 통합

**범위**: 스크립트 및 CI 설정
**우선순위**: P0 (Critical)

#### 5.1 TAG 검증 스크립트

**파일**: `.moai/scripts/validate_tags.py`

```python
# -*- coding: utf-8 -*-
"""
TAG 체인 검증 스크립트

@CODE:TAG-IMPL-001
"""

def validate_tag_chain():
    """TAG 체인 완성률 및 고아 TAG 검증"""
    pass

def generate_tag_report():
    """TAG 상태 보고서 생성"""
    pass
```

#### 5.2 TAG 인덱스 생성기

**파일**: `.moai/scripts/generate_tag_index.py`

```python
# -*- coding: utf-8 -*-
"""
TAG 인덱스 자동 생성

@CODE:TAG-IMPL-001
"""

def scan_codebase_for_tags():
    """코드베이스에서 모든 TAG 스캔"""
    pass

def generate_catalog_json():
    """.moai/indexes/tag_catalog.json 생성"""
    pass
```

#### 5.3 GitHub Actions 통합

**파일**: `.github/workflows/tag-validation.yml`

```yaml
name: TAG Validation

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  validate-tags:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Validate TAG chain
        run: python .moai/scripts/validate_tags.py
      - name: Check TAG completeness
        run: |
          COMPLETENESS=$(python -c "import json; print(json.load(open('.moai/indexes/tag_catalog.json'))['stats']['chain_completeness'])")
          if (( $(echo "$COMPLETENESS < 0.90" | bc -l) )); then
            echo "::warning::TAG chain completeness below 90%: $COMPLETENESS"
          fi
```

---

## 3. 검증 기준

### 3.1 Phase별 완료 기준

| Phase | 완료 기준 |
|-------|----------|
| Phase 1 | 50개 핵심 파일 TAG 완료, 테스트 통과 |
| Phase 2 | 88개 Backend 파일 TAG 완료, Backend TAG 100% |
| Phase 3 | 122개 Frontend 파일 TAG 완료, Frontend TAG 100% |
| Phase 4 | 108개 테스트 파일 TAG 완료, @TEST-@CODE 매핑 100% |
| Phase 5 | CI 통합 완료, 자동 검증 통과 |

### 3.2 전체 완료 기준

- [ ] TAG 체인 완성률 **90%+**
- [ ] 고아 TAG **0개**
- [ ] 모든 테스트 통과
- [ ] CI 파이프라인 통합 완료
- [ ] TAG 인덱스 자동 생성 동작

---

## 4. 리스크 및 완화 전략

| 리스크 | 영향 | 완화 전략 |
|--------|------|-----------|
| SPEC 미매핑 파일 발견 | Medium | 신규 SPEC 생성 또는 MISC 카테고리 활용 |
| Frontend 중복 디렉토리 | High | Phase 3 전 프론트엔드 통합 선행 |
| 대형 파일 TAG 복잡성 | Medium | 파일 레벨 TAG만 적용, 함수 레벨은 Phase 5+ |
| CI 실행 시간 증가 | Low | 캐싱 및 병렬 실행 최적화 |

---

## 5. 일정 (상대적)

```
Phase 1 ████████░░░░░░░░ (첫 번째)
Phase 2 ░░░░████████░░░░ (Phase 1 후)
Phase 3 ░░░░████████░░░░ (Phase 1 후, Phase 2와 병렬 가능)
Phase 4 ░░░░░░░░████████ (Phase 2, 3 후)
Phase 5 ░░░░░░░░░░░░████ (Phase 4 후)
```

---

## 6. 참조 자료

- [SPEC-TAG-IMPL-001 명세서](./spec.md)
- [SPEC-TAG-IMPL-001 수락 기준](./acceptance.md)
- [MoAI-ADK TAG Guidelines](https://github.com/modu-ai/moai-adk)

---

**문서 작성**: spec-builder agent
**상태**: draft
