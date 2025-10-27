# BATCH6 Checkpoint #5 작업 가이드

---

## 📖 프로젝트 배경과 전체 맥락

### SPEC-MYPY-001: MyPy Strict Mode 적용

**목표**: dt-rag-standalone 프로젝트의 모든 Python 코드에 MyPy strict mode를 적용하여 타입 안정성 확보

**Phase 2 시작**: 108 errors in 38 files (2025-10-26 기준)
- Phase 1에서 기본 에러 정리 완료
- Phase 2는 남은 108개 에러를 0으로 만드는 것이 목표

### BATCH1-6 전체 여정

#### BATCH1-5 (이전 세션들)
- **방법론**: 동일한 체크포인트 기반 접근
- **전략**: Fixable errors 집중, import-not-found 스킵
- **패턴**: 에러 타입별 수정 패턴 학습 및 반복 적용

#### BATCH6 (현재 진행 중)
- **시작**: 108 errors (CP#1 이전)
- **CP#1**: 타겟 파일 3개 처리
- **CP#2**: 10개 파일 배치 처리 (BATCH2 완료 후)
- **CP#3**: 3개 파일 추가 처리 → **100 errors 달성**
- **CP#4**: embedding_service.py 완전 클린 → **85 errors 달성** ✅ (현재)
- **CP#5**: **다음 목표 - 75 errors 이하**

### 방법론 일관성 확인 (중요!)

**이전 세션에서 확인한 내용**:
- BATCH1-6 모두 **동일한 체크포인트 기반 방식** 사용 확인됨
- 직접 파일 수정 (Edit tool) + 즉시 검증 패턴 일관성 유지
- 한 파일을 완전히 클린하게 만든 후 다음 파일로 이동하는 원칙 준수

---

## 🎓 CP#1-4 작업 요약과 교훈

### CP#1-3: 초기 단계 (108 → 100 errors)
**주요 작업**:
- router 파일들 (classify.py, health.py 등) 타입 수정
- batch_search.py 대규모 수정
- evaluation_router.py 클린

**배운 점**:
- ✅ 작은 파일부터 시작하면 빠른 성과
- ✅ router 파일들은 대부분 간단한 타입 선언 추가로 해결
- ⚠️ 큰 파일(100+ lines)은 여러 체크포인트로 나누기

### CP#4: embedding_service.py 완전 클린 (100 → 85 errors) ✅

**처리한 에러들** (8개 수정 적용):
1. **var-annotated**: 변수 타입 선언 추가
2. **no-any-return**: `cast(List[float], array.tolist())` 패턴
3. **Optional 처리**: None 체크 명시적 추가
4. **NumPy 배열**: `cast(np.ndarray, ...)` 타입 캐스팅

**핵심 패턴 발견**:
```python
# Pattern 1: NumPy array → List[float]
return cast(List[float], vector.tolist())

# Pattern 2: Optional None check
if self.model_config is None:
    raise ValueError("...")

# Pattern 3: Any → 명시적 타입
batch_embeddings_raw: Any = await loop.run_in_executor(...)
for arr in batch_embeddings_raw:
    result = self.process(cast(np.ndarray, arr))
```

**결과**:
- ✅ 15 errors → 0 errors (100% 성공)
- ✅ 570+ 라인 파일 완전 클린
- ✅ 모든 에러 타입 체계적 해결

---

## 🏗️ MoAI 워크플로우 핵심 원칙

### 1. 체크포인트 기반 접근 (Checkpoint-driven)
```
목표 설정 → 파일 선택 → 수정 → 검증 → 리포트 → 다음 CP
```
- 각 CP는 **독립적이고 검증 가능한** 작업 단위
- CP 완료 시 반드시 **에러 카운트 감소** 확인

### 2. 완전성 원칙 (Completeness)
```
한 파일을 시작하면 → 0 errors까지 완전히 처리
```
- ❌ 부분 수정 후 다른 파일로 이동 금지
- ✅ 파일당 0 errors 달성 후 다음 파일
- 예외: import-not-found 같은 unfixable errors는 스킵

### 3. 즉시 검증 원칙 (Immediate Verification)
```
수정 후 즉시 → mypy <파일명> → 에러 확인
```
- 모든 수정 후 바로 MyPy 실행
- 에러가 남아있으면 즉시 추가 수정
- 파일 완료 시 `Success: no issues found` 확인

### 4. 전략적 선택 (Strategic Selection)
```
Fixable errors 우선 → import-not-found 스킵
작은 파일 우선 → 빠른 성과 달성
```
- **Fixable errors**: attr-defined, no-any-return, call-arg, assignment
- **Unfixable errors**: import-not-found, import-untyped (외부 라이브러리)

### 5. 패턴 학습과 재사용 (Pattern Reuse)
```
에러 해결 → 패턴 정리 → 유사 에러에 재적용
```
- 같은 에러 타입은 같은 패턴으로 해결
- CP#4에서 학습한 패턴을 CP#5에서 활용

---

## ⚠️ 피해야 할 실수와 함정

### 1. import-not-found 에러와 싸우지 마세요
```python
# ❌ 이런 에러는 수정 불가
error: Cannot find implementation or library stub for module named "langfuse"
error: Cannot find implementation or library stub for module named "sentry_sdk"
```
**이유**: 외부 라이브러리에 stub 파일(`.pyi`)이 없어서 발생
**해결**: 스킵하고 다음 에러로 (프로젝트 범위 밖)

### 2. Python 3.9 호환성 주의
```python
# ❌ Python 3.10+ 문법
def func() -> str | None:
    pass

# ✅ Python 3.9 호환
from typing import Optional
def func() -> Optional[str]:
    pass
```

### 3. 부분 수정 금지
```python
# ❌ 나쁜 예: 5개 에러 중 3개만 수정하고 다음 파일로
# ✅ 좋은 예: 5개 에러 모두 해결 (또는 unfixable 확인) 후 다음 파일
```

### 4. 검증 없이 진행 금지
```python
# ❌ 나쁜 예: 3개 파일 수정 → 한 번에 검증
# ✅ 좋은 예: 파일 하나 수정 → 즉시 mypy 검증 → 다음 파일
```

### 5. cast import 깜빡하지 마세요
```python
# ❌ 자주 하는 실수
return cast(List[float], arr.tolist())  # NameError: cast not defined

# ✅ 파일 상단에 import 필수
from typing import cast, List, Dict, Any, Optional
```

---

## 📊 현재 상태 (CP#4 완료 후)

- **총 에러**: 85 errors in 37 files
- **이전 상태**: 100 errors (CP#3 완료 후)
- **감소량**: 15 errors eliminated ✅
- **완료 파일**: apps/api/embedding_service.py (15 → 0 errors)
- **진척률**: 21.3% (108 → 85 = 23 errors eliminated)

---

## 🎯 CP#5 목표

**전략**: Fixable errors 위주로 처리, import-not-found는 스킵

### 타겟 파일 우선순위

#### 1순위: agent_task_worker.py (4 errors) - 빠른 처리 가능 ⚡
```bash
# 에러 확인
mypy apps/api/background/agent_task_worker.py --config-file=pyproject.toml 2>&1 | head -20
```
**선택 이유**: 작은 파일, 빠른 성과, CP#4 패턴 적용 가능

#### 2순위: security_manager.py (5 errors) - attr-defined 집중
```bash
# 에러 확인
mypy apps/security/core/security_manager.py --config-file=pyproject.toml 2>&1
```
**선택 이유**: attr-defined 에러 위주, 학습한 패턴 적용

#### 3순위: langfuse_client.py (8 errors) - fixable만 선택
```bash
# 에러 타입 분석 먼저
mypy apps/api/monitoring/langfuse_client.py --config-file=pyproject.toml 2>&1
```
**주의**: import-not-found 에러 많을 수 있음 → fixable만 처리

#### 스킵: config.py (9 errors) - import-not-found 대부분 ❌
```
# 이 파일은 나중에 처리 (대부분 unfixable)
```

---

## 📝 작업 시작 명령

### 1. 현재 상태 확인
```bash
cd /mnt/c/MYCLAUDE_PROJECT/sonheungmin/dt-rag-standalone
mypy apps/ --config-file=pyproject.toml 2>&1 | tail -3
```

### 2. CP#5 타겟 파일별 에러 확인
```bash
# agent_task_worker.py (4 errors) - 우선 타겟
mypy apps/api/background/agent_task_worker.py --config-file=pyproject.toml 2>&1
```

### 3. 파일 읽기
```bash
# 에러 확인 후 파일 전체 읽기
cat apps/api/background/agent_task_worker.py
```

---

## 🔧 수정 패턴 가이드 (CP#4 검증됨)

### Pattern 1: no-any-return 에러
```python
# BEFORE
return some_array.tolist()

# AFTER
from typing import cast, List
return cast(List[float], some_array.tolist())
```
**적용 횟수**: CP#4에서 5회 사용 ✅

### Pattern 2: var-annotated 에러
```python
# BEFORE
self.cache = {}

# AFTER
self.cache: Dict[str, Any] = {}
```
**적용 횟수**: CP#4에서 2회 사용 ✅

### Pattern 3: Optional 타입 None 체크
```python
# BEFORE
value = optional_dict['key']

# AFTER
if optional_dict is None:
    raise ValueError("Required config missing")
value = optional_dict['key']
```
**적용 횟수**: CP#4에서 1회 사용 ✅

### Pattern 4: NumPy ndarray 캐스팅
```python
# BEFORE
for embedding in batch_embeddings:
    result = self.process(embedding)

# AFTER
batch_embeddings_raw: Any = await executor(...)
for embedding_array in batch_embeddings_raw:
    result = self.process(cast(np.ndarray, embedding_array))
```
**적용 횟수**: CP#4에서 1회 사용 ✅

### Pattern 5: attr-defined 에러 (예상)
```python
# BEFORE
result.some_attr  # attr not defined in type

# AFTER (Option 1: 타입 확인 후 cast)
if hasattr(result, 'some_attr'):
    value = result.some_attr

# AFTER (Option 2: 타입 선언)
result: SpecificType = get_result()
value = result.some_attr
```
**예상 사용**: CP#5에서 security_manager.py

---

## 📈 에러 타입 분포 (CP#5 기준)

```
28 import-not-found  ❌ unfixable (외부 라이브러리 stub 없음)
11 attr-defined      ✅ fixable
 8 no-any-return     ✅ fixable (cast 패턴)
 6 call-arg          ✅ fixable
 5 import-untyped    ❌ unfixable
 5 assignment        ✅ fixable
 4 var-annotated     ✅ fixable
 3 return-value      ✅ fixable
 3 arg-type          ✅ fixable
```

**Fixable errors**: ~57개 (85 - 28 import-not-found)

---

## ✅ CP#5 성공 기준

- [ ] agent_task_worker.py: 4 → 0 errors
- [ ] security_manager.py: 5 → 0 or <3 errors
- [ ] langfuse_client.py: fixable errors만 처리 (목표 8 → 3-4 errors)
- [ ] 전체 에러: 85 → 75 이하 (10+ errors 감소)

---

## 🚀 세션 시작 스크립트

```bash
# 1. 디렉토리 이동
cd /mnt/c/MYCLAUDE_PROJECT/sonheungmin/dt-rag-standalone

# 2. 현재 상태 확인
echo "=== Current MyPy Status ==="
mypy apps/ --config-file=pyproject.toml 2>&1 | tail -1

# 3. CP#5 타겟 #1 에러 확인
echo "=== agent_task_worker.py errors ==="
mypy apps/api/background/agent_task_worker.py --config-file=pyproject.toml 2>&1

# 4. 준비 완료
echo "Ready to start CP#5!"
```

---

## 📚 참고 파일

- `error_files_cp5.txt` - 파일별 에러 개수
- `error_types_cp5.txt` - 에러 타입별 분포
- `NEXT_SESSION_CP5.md` (이 파일) - 전체 가이드

---

## ⚠️ 체크리스트 (작업 시작 전 확인)

- [ ] **디렉토리 확인**: `/mnt/c/MYCLAUDE_PROJECT/sonheungmin/dt-rag-standalone`
- [ ] **Python 버전**: 3.9 호환 문법 사용 (`Optional[X]` not `X | None`)
- [ ] **Import 준비**: `from typing import cast, List, Dict, Any, Optional`
- [ ] **목표 이해**: Fixable errors만 처리, unfixable은 스킵
- [ ] **완전성 원칙**: 한 파일을 0 errors까지 완전히 처리
- [ ] **즉시 검증**: 수정 후 바로 `mypy <파일명>` 실행

---

## 🎯 최종 목표

**BATCH6 완료**: 108 errors → 0 errors
- CP#1-CP#4: 23 errors eliminated (108 → 85) ✅
- CP#5 목표: 10+ errors (85 → 75 이하)
- 전체 진척률: 21.3% → 30%+

**Phase 2 완료 시**: MyPy strict mode 100% 적용 완료

---

## 💡 Quick Start (복사해서 실행)

```bash
# 새 세션 시작 시 이 명령만 실행
cd /mnt/c/MYCLAUDE_PROJECT/sonheungmin/dt-rag-standalone && \
mypy apps/ --config-file=pyproject.toml 2>&1 | tail -3 && \
echo "=== Target: agent_task_worker.py ===" && \
mypy apps/api/background/agent_task_worker.py --config-file=pyproject.toml 2>&1
```

**작업 시작**: 위 명령 실행 후 agent_task_worker.py 파일 읽고 수정 시작!

---

## 🤝 작업 철학

> "한 번에 한 파일씩, 완벽하게. 검증하고 다음으로."

- **체계적**: 체크포인트 기반으로 진행
- **완전**: 시작한 파일은 끝까지
- **검증**: 모든 수정 후 즉시 확인
- **학습**: 패턴을 찾고 재사용

이 원칙들이 BATCH1-6을 관통하는 핵심입니다. 🎯
