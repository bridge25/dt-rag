---
id: MYPY-001
version: 0.0.1
status: draft
priority: critical
created: 2025-01-25
domain: Type Safety
title: MyPy Strict Mode 완전 준수 - 1,008개 타입 오류 제로화
tags: [mypy, type-safety, quality-gate, ci-cd, python]
related_specs: [CICD-001]
---

# @SPEC:MYPY-001 - MyPy Strict Mode 완전 준수

## HISTORY

### v0.0.1 (2025-01-25)
- **INITIAL**: MyPy strict mode 1,008개 타입 오류 제로화 SPEC 작성
- **Context**: CI/CD Quality Gate 통합을 위한 타입 안전성 확보
- **Scope**: 92개 Python 파일, 6가지 오류 유형, 3-Phase 접근법
- **Strategy**: 자동화 우선 → 수동 수정 → 검증 단계

---

## 1. Environment (환경)

### 1.1 System Context
- **Codebase**: dt-rag-standalone Python 코드베이스 (92개 파일)
- **MyPy Version**: 1.13.0 (strict mode)
- **Python Version**: 3.9+
- **Total Errors**: 1,008개 타입 오류
- **CI/CD Pipeline**: `.github/workflows/ci.yml` (현재 `continue-on-error: true`)

### 1.2 Error Classification
| Category | Count | Automation | Priority |
|----------|-------|------------|----------|
| `no-untyped-def` | ~300 | ✅ Auto | P0 |
| `var-annotated` | ~200 | ✅ Auto | P0 |
| `assignment` | ~150 | ❌ Manual | P1 |
| `arg-type` | ~120 | ❌ Manual | P1 |
| `call-arg` | ~100 | ❌ Manual | P2 |
| `attr-defined`, `no-redef`, `return-value` | ~138 | ❌ Manual | P2 |

### 1.3 Technical Constraints
- **Zero Regression**: 기존 기능 동작 100% 보존
- **Coverage Maintenance**: 현재 pytest coverage 수준 유지 또는 향상
- **CI/CD Integration**: Quality Gate 통과 (`mypy --strict` exit code 0)
- **No Type Ignore**: `# type: ignore` 주석 사용 금지 (정당한 사유 있을 경우 승인 필요)

---

## 2. Assumptions (전제 조건)

### 2.1 Technical Assumptions
- **A1**: 모든 Python 파일은 타입 힌트 추가 가능한 구조
- **A2**: 자동화 스크립트는 단순 패턴 오류만 처리 (복잡한 로직은 수동)
- **A3**: MyPy strict mode 설정은 변경하지 않음 (`.mypy.ini` 또는 `pyproject.toml`)
- **A4**: 타입 스텁이 필요한 외부 라이브러리는 `types-*` 패키지 설치

### 2.2 Process Assumptions
- **A5**: Phase 1 자동화로 ~60% 오류 해결 가능
- **A6**: Phase 2 수동 수정 시 파일당 평균 10분 소요
- **A7**: Phase 3 검증 단계에서 새로운 오류 발생 시 즉시 수정
- **A8**: 각 Phase 완료 후 commit 및 CI 검증 수행

---

## 3. Requirements (요구사항)

### 3.1 Ubiquitous (항상 충족)
- **REQ-1**: 모든 Python 함수와 메서드는 명시적 타입 힌트 보유
- **REQ-2**: 모든 클래스 속성과 인스턴스 변수는 타입 어노테이션 보유
- **REQ-3**: `mypy --strict` 실행 시 오류 개수 0개 (exit code 0)
- **REQ-4**: CI/CD Quality Gate에서 MyPy 검증 통과 필수

### 3.2 Event-driven (특정 조건 발생 시)
- **REQ-5**: WHEN 자동화 스크립트 실행 시 → 패턴 기반 오류만 수정, 로직 변경 금지
- **REQ-6**: WHEN 수동 수정 시 → 변경 전 해당 파일의 테스트 실행 및 통과 확인
- **REQ-7**: WHEN 타입 오류 수정 시 → 동일 파일의 모든 관련 오류 함께 처리
- **REQ-8**: WHEN 외부 라이브러리 타입 누락 시 → `types-*` 패키지 설치 또는 stub 파일 생성

### 3.3 State-driven (상태 기반)
- **REQ-9**: IF Phase 1 완료 → ~600개 자동화 가능 오류 제로화 완료
- **REQ-10**: IF Phase 2 완료 → 모든 수동 수정 대상 오류 제로화 완료
- **REQ-11**: IF Phase 3 완료 → CI/CD에서 `continue-on-error: false` 적용 및 통과

### 3.4 Constraints (제약사항)
- **CON-1**: `# type: ignore` 사용 금지 (예외: 명확한 문서화된 사유)
- **CON-2**: 기존 함수 시그니처 변경 시 모든 호출부 동시 수정
- **CON-3**: 타입 변경으로 인한 runtime 동작 변경 금지
- **CON-4**: MyPy 설정 완화 금지 (strict mode 유지)

---

## 4. Specifications (상세 사양)

### 4.1 Phase 1: Automation Strategy (자동화 전략)

#### 4.1.1 자동화 대상 오류
1. **no-untyped-def** (~300개)
   - Pattern: 함수 정의에 타입 힌트 누락
   - Solution: 기본 타입 추가 (`-> None`, `-> Any`)
   ```python
   # Before
   def process_data(data):
       return data

   # After
   def process_data(data: Any) -> Any:
       return data
   ```

2. **var-annotated** (~200개)
   - Pattern: 변수 선언 시 타입 어노테이션 누락
   - Solution: 타입 추론 또는 명시적 어노테이션
   ```python
   # Before
   cache = {}

   # After
   cache: Dict[str, Any] = {}
   ```

#### 4.1.2 자동화 스크립트 설계
```python
# scripts/fix_mypy_auto.py
import ast
import libcst as cst

class TypeAnnotationTransformer(cst.CSTTransformer):
    # 1. 함수 시그니처 자동 타입 추가
    # 2. 변수 어노테이션 자동 추가
    # 3. AST 기반 안전한 변환
    pass
```

**실행 계획**:
1. `mypy_errors.txt` 파싱하여 자동화 대상 추출
2. 파일별로 변환 적용
3. 변환 후 pytest 실행하여 regression 확인
4. Commit: `fix(mypy): apply automated type annotations (Phase 1)`

---

### 4.2 Phase 2: Manual Correction Strategy (수동 수정 전략)

#### 4.2.1 수동 수정 대상 오류

**P1 Priority** (~270개):
- `assignment`: 타입 불일치 할당
- `arg-type`: 함수 인자 타입 불일치

**P2 Priority** (~238개):
- `call-arg`: 함수 호출 시 인자 개수/타입 불일치
- `attr-defined`: 존재하지 않는 속성 접근
- `no-redef`: 재정의 오류
- `return-value`: 반환 타입 불일치

#### 4.2.2 수동 수정 프로세스
1. **오류 그룹핑**: 동일 파일의 오류 한 번에 처리
2. **테스트 우선**: 수정 전 해당 파일 테스트 실행
3. **타입 정확도**: `Any` 사용 최소화, 구체적 타입 지정
4. **리뷰 체크포인트**: 10개 파일마다 commit 및 CI 검증

**예시**:
```python
# assignment 오류 수정
# Before
def get_config() -> Dict[str, str]:
    return {"timeout": 30}  # error: int not assignable to str

# After
def get_config() -> Dict[str, Union[str, int]]:
    return {"timeout": 30}
```

---

### 4.3 Phase 3: Verification & CI Integration (검증 및 통합)

#### 4.3.1 로컬 검증
```bash
# 1. MyPy strict 검증
mypy --strict . --exclude venv

# 2. Pytest 전체 실행
pytest tests/ -v --cov

# 3. Coverage 비교
pytest --cov --cov-report=term-missing
```

#### 4.3.2 CI/CD Quality Gate 업데이트
```yaml
# .github/workflows/ci.yml
- name: MyPy Type Check
  run: |
    mypy --strict . --exclude venv
  # continue-on-error: false  # Phase 3 완료 후 제거
```

#### 4.3.3 최종 검증 기준
- ✅ `mypy --strict` exit code 0
- ✅ 모든 pytest 테스트 통과
- ✅ Coverage 유지 또는 향상
- ✅ CI/CD Quality Gate 통과

---

## 5. Traceability (추적성)

### 5.1 TAG Chain
- **@SPEC:MYPY-001**: 이 문서
- **@TEST:MYPY-001**: `tests/type_safety/test_mypy_compliance.py` (CI 검증)
- **@CODE:MYPY-001**: 전체 Python 파일 타입 힌트 개선
- **@DOC:MYPY-001**: `.moai/specs/SPEC-MYPY-001/plan.md`, `acceptance.md`

### 5.2 Related Artifacts
- **Input**: `mypy_errors.txt` (1,008개 오류 목록)
- **Scripts**: `scripts/fix_mypy_auto.py`, `scripts/verify_types.py`
- **CI Config**: `.github/workflows/ci.yml`
- **MyPy Config**: `pyproject.toml` 또는 `.mypy.ini`

### 5.3 Dependencies
- **Upstream**: SPEC-CICD-001 (CI/CD Quality Gate 정의)
- **Downstream**: 모든 Python 모듈 (타입 안전성 의존)

---

## 6. Success Criteria (성공 기준)

### 6.1 Primary Goals
- ✅ **Goal 1**: MyPy strict mode에서 오류 0개 달성
- ✅ **Goal 2**: CI/CD Quality Gate 통과 (`continue-on-error: false`)
- ✅ **Goal 3**: 기존 모든 테스트 통과 (zero regression)

### 6.2 Secondary Goals
- ✅ **Goal 4**: 타입 힌트 정확도 향상 (`Any` 사용 최소화)
- ✅ **Goal 5**: 자동화 스크립트 재사용 가능성 확보
- ✅ **Goal 6**: 타입 안전성 문서화 (이 SPEC 및 Living Docs)

### 6.3 Quality Metrics
- **Type Coverage**: 100% (모든 함수, 변수, 클래스 속성)
- **Test Coverage**: 현재 수준 유지 또는 향상
- **CI Build Time**: 추가 시간 < 2분
- **Technical Debt**: `# type: ignore` 사용 0건 (또는 문서화된 예외만)

---

## 7. Notes & Risks

### 7.1 Known Risks
- **R1**: 자동화 스크립트가 잘못된 타입 추론 가능성 → pytest로 회귀 검증
- **R2**: 수동 수정 시 타입 변경으로 인한 API 호환성 문제 → 시그니처 변경 시 모든 호출부 확인
- **R3**: Phase 3에서 새로운 오류 발견 가능성 → 즉시 수정 및 재검증

### 7.2 Mitigation Strategies
- **M1**: Phase별 commit 및 CI 검증으로 문제 조기 발견
- **M2**: 파일별 테스트 실행으로 regression 방지
- **M3**: `Any` 사용 시 TODO 주석으로 향후 개선 표시

---

**SPEC Owner**: spec-builder agent
**Review Status**: Draft (User Approval Pending)
**Next Step**: `/alfred:2-run SPEC-MYPY-001` (TDD 구현)
