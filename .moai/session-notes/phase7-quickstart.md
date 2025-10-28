# Phase 7 빠른 시작 가이드

> **다음 세션에서 바로 작업 시작하기**

---

## 🚀 즉시 시작 (3분)

### 1. 프로젝트로 이동
```bash
cd /mnt/c/MYCLAUDE_PROJECT/sonheungmin/dt-rag-standalone
```

### 2. 현재 상태 확인
```bash
# 마지막 커밋 확인
git log --oneline -3

# 출력 예상:
# 26753cef Phase 6 완료 - var-annotated 26개
# 535a9f92 Phase 5 완료 - unused-ignore 78개
# 222bbf0a Phase 4-4 완료 - no-any-return 11개
```

### 3. Phase 7 에러 목록 확인
```bash
mypy apps/ --config-file=pyproject.toml 2>&1 | grep "no-redef"
```

**예상 출력**: 10개 에러

---

## 📋 Phase 7 작업 계획

### 타겟
- **에러 타입**: no-redef (Name already defined)
- **개수**: 10개 (3파일)
- **복잡도**: ⭐ (낮음)

### 작업 순서

#### Batch 1: ragas_metrics_extension.py (3개)
**문제**: Counter, Gauge, Histogram 중복 정의

**해결책**:
- import 구문 정리
- 중복 정의 제거
- 필요시 조건부 import 사용

#### Batch 2: deps.py (1개)
**문제**: key_info 변수 재사용 (line 313, 355)

**해결책**:
- 두 번째 사용 시 다른 변수명 사용
- 예: `key_info` → `updated_key_info` 또는 `new_key_info`

#### Batch 3: search_router.py (1개)
**문제**: clear_search_cache 함수 재정의

**해결책**:
- import와 함수 정의 충돌 해결
- 필요시 함수명 변경 또는 import 제거

#### Batch 4: orchestration/main.py (5개)
**문제**: 동적 import 시 SearchHit, get_pipeline, PipelineRequest 중복 정의

**해결책**:
- 조건부 import 구조 개선
- 이미 정의된 경우 재정의 방지
- try-except 블록 내 변수명 충돌 해결

---

## 🔧 작업 템플릿

### 1. 파일 읽기
```bash
# Read 도구 사용 예시
Read 파일경로, offset=라인-5, limit=10
```

### 2. 변수 리네이밍 패턴
```python
# Before (에러 발생)
value = calculate_initial()
# ... 중간 코드 ...
value = calculate_updated()  # error: Name "value" already defined

# After (해결)
initial_value = calculate_initial()
# ... 중간 코드 ...
updated_value = calculate_updated()  # OK
```

### 3. 조건부 정의 패턴
```python
# Before (에러 발생)
from module import MyClass
# ...
try:
    from other import MyClass  # error: Name "MyClass" already defined
except ImportError:
    pass

# After (해결)
from module import MyClass
# ...
try:
    from other import MyClass as OtherMyClass  # OK: 별칭 사용
except ImportError:
    OtherMyClass = MyClass
```

---

## ✅ 작업 완료 체크리스트

- [ ] Batch 1: ragas_metrics_extension.py 수정 (3개 해결)
- [ ] Batch 2: deps.py 수정 (1개 해결)
- [ ] Batch 3: search_router.py 수정 (1개 해결)
- [ ] Batch 4: orchestration/main.py 수정 (5개 해결)
- [ ] mypy 검증: `mypy apps/ --config-file=pyproject.toml 2>&1 | grep "no-redef" | wc -l` → 0
- [ ] 전체 에러 확인: `mypy apps/ --config-file=pyproject.toml 2>&1 | tail -3` → 212 errors
- [ ] 커밋 생성 (템플릿은 phase7-prep.md 참조)

---

## 📊 진행률 추적

```
시작: 222 errors (no-redef: 10)
목표: 212 errors (no-redef: 0)
감소: 10 errors (4.5%)
```

---

## 🎯 다음 단계

Phase 7 완료 후:
1. **Phase 8**: unreachable (9개) - 도달 불가능 코드 제거
2. **Phase 9**: func-returns-value (5개) - 반환값 타입 일치

---

**생성일**: 2025-10-29
**예상 소요 시간**: 15-20분
