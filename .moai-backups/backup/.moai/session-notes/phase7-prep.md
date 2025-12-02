# Phase 7 준비: no-redef 에러 10개 해결

**생성일**: 2025-10-29
**이전 세션 종료 상태**: Phase 5, 6 완료 (264→222 에러)

---

## 현재 상태

### 완료된 Phase
✅ **Phase 5** (커밋: 535a9f92)
- unused-ignore 78개 → 0개 (100% 해결)
- 방법: 자동화 regex + 수동 주석 제거

✅ **Phase 6** (커밋: 26753cef)
- var-annotated 26개 → 0개 (100% 해결)
- 방법: 명시적 타입 어노테이션 추가
  - `변수: 타입 = 초기값` 패턴 적용
  - dict[str, int], list[str], Any 사용

### 현재 mypy 에러 분포 (222개)

```
85 misc
49 union-attr
26 arg-type
10 no-redef          ← Phase 7 타겟
 9 unreachable
 9 return-value
 7 dict-item
 6 call-overload
 5 index
 5 func-returns-value
```

---

## Phase 7: no-redef 에러 해결

### 타겟
- **에러 개수**: 10개
- **복잡도**: 낮음 (변수 리네이밍)
- **예상 소요 시간**: 15-20분

### no-redef 에러란?
변수나 함수가 같은 스코프 내에서 재정의되는 경우 발생하는 에러입니다.

```python
# 잘못된 예
value = 10
value = "hello"  # error: Name "value" already defined [no-redef]

# 올바른 예
value = 10
value_str = "hello"  # 다른 이름 사용
```

### 해결 전략

1. **변수 리네이밍**: 재정의되는 변수에 명확한 이름 부여
2. **스코프 분리**: 필요 시 함수나 블록으로 분리
3. **타입 가드**: Union 타입의 경우 타입 가드 사용

### 에러 위치 (10개)

**파일별 분포**:
1. **apps/monitoring/core/ragas_metrics_extension.py** (3개)
   - Line 20: Counter 재정의
   - Line 30: Gauge 재정의
   - Line 40: Histogram 재정의
   - 패턴: 중복 import 또는 변수명 충돌

2. **apps/api/deps.py** (1개)
   - Line 355: key_info 재정의 (line 313에 이미 정의됨)
   - 패턴: 함수 내 변수 재사용

3. **apps/api/routers/search_router.py** (1개)
   - Line 998: clear_search_cache 재정의
   - 패턴: import와 함수 정의 충돌

4. **apps/orchestration/src/main.py** (5개)
   - Line 57: SearchHit 재정의
   - Line 131: get_pipeline 재정의 (1차)
   - Line 152: get_pipeline 재정의 (2차)
   - Line 259: PipelineRequest 재정의 (1차)
   - Line 274: PipelineRequest 재정의 (2차)
   - 패턴: 동적 import 시도 중 중복 정의

**에러 확인 명령어**:
```bash
mypy apps/ --config-file=pyproject.toml 2>&1 | grep "no-redef"
```

---

## 새 세션 시작 가이드

### 1. 프로젝트 상태 확인
```bash
cd /mnt/c/MYCLAUDE_PROJECT/sonheungmin/dt-rag-standalone
git status
git log --oneline -5
```

### 2. Phase 7 에러 목록 확인
```bash
# 전체 no-redef 에러 목록
mypy apps/ --config-file=pyproject.toml 2>&1 | grep "no-redef"

# 파일별 에러 개수
mypy apps/ --config-file=pyproject.toml 2>&1 | grep "no-redef" | cut -d':' -f1 | sort | uniq -c
```

### 3. TodoList 업데이트
```json
[
  {"content": "Phase 5: unused-ignore 에러 78개 해결", "status": "completed", "activeForm": "완료"},
  {"content": "Phase 6: var-annotated 에러 26개 해결", "status": "completed", "activeForm": "완료"},
  {"content": "Phase 7: no-redef 에러 10개 해결 (변수 재정의 방지)", "status": "in_progress", "activeForm": "진행 중"}
]
```

### 4. 작업 시작 명령어
```bash
# 에러 분석
mypy apps/ --config-file=pyproject.toml 2>&1 | grep "no-redef" | head -5

# 첫 번째 파일 읽기 (예시)
# Read 도구로 에러가 발생한 파일의 해당 라인 읽기
```

### 5. 작업 완료 후 커밋
```bash
git add -A && git commit -m "🟢 GREEN: SPEC-MYPY-CONSOLIDATION-002 Phase 7 완료 - no-redef 에러 10개 해결 (100%)

변수 재정의 방지 및 명확한 변수명 사용

**진행률**:
- no-redef: 10→0 (100% 해결)
- 전체 mypy 에러: 222→212 (10개 감소)

**변경 파일**: [파일 목록]
**리네이밍 패턴**: [패턴 설명]

@CODE:MYPY-CONSOLIDATION-002 | SPEC: .moai/specs/SPEC-MYPY-CONSOLIDATION-002/spec.md

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 다음 Phase 후보 (우선순위)

Phase 7 완료 후 다음 타겟:

1. **Phase 8: unreachable** (9개) - 도달 불가능 코드 제거
2. **Phase 9: func-returns-value** (5개) - 반환값 타입 일치
3. **Phase 10: return-value** (9개) - 반환값 검증
4. **Phase 11: dict-item** (7개) - 딕셔너리 키 타입

**중복잡도 작업**:
- arg-type (26개)
- union-attr (49개)
- misc (85개) - 분석 필요

---

## 참고 자료

- **SPEC 문서**: `.moai/specs/SPEC-MYPY-CONSOLIDATION-002/spec.md`
- **이전 세션 커밋**:
  - Phase 5: `535a9f92`
  - Phase 6: `26753cef`
- **현재 브랜치**: `master`
- **mypy 설정**: `pyproject.toml`

---

## 예상 작업 흐름

```
1. no-redef 에러 10개 분석 (파일별 위치 파악)
   ↓
2. 배치 처리 (파일별 또는 패턴별 그룹화)
   ↓
3. 변수 리네이밍 (명확한 이름 사용)
   ↓
4. mypy 검증 (no-redef: 10→0 확인)
   ↓
5. 커밋 & 다음 Phase 계획
```

---

**작성자**: Claude (Alfred)
**마지막 업데이트**: 2025-10-29
