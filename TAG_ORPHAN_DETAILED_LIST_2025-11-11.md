# TAG 시스템 - 상세 고아 TAG 목록

**생성일**: 2025-11-11  
**프로젝트**: dt-rag-standalone  
**검증 범위**: 전체 프로젝트 소스 코드

---

## 목차
1. [CODE 없는 SPEC (구현 미완료)](#1-code-없는-spec-구현-미완료)
2. [SPEC 없는 CODE (고아 TAG)](#2-spec-없는-code-고아-tag)
3. [SPEC 없는 TEST (고아 TAG)](#3-spec-없는-test-고아-tag)
4. [해결 방안](#4-해결-방안)

---

## 1. CODE 없는 SPEC (구현 미완료)

약 **36개 SPEC**이 CODE 태그 없이 존재합니다. 활성/비활성 여부 확인 필요:

### 1.1 적극적으로 진행 중인 SPEC (우선순위 높음)

```
🟡 CASEBANK-UNIFY-001
   - SPEC 위치: .moai/specs/SPEC-CASEBANK-UNIFY-001/
   - 구현 추정 위치: apps/api/database.py, services/, migrations/
   - 상태: CODE 태그 누락 (구현은 있으나 태그 없음)
   - 조치: 구현 파일에 @CODE:CASEBANK-UNIFY-001 추가

🟡 POKEMON-IMAGE-001
   - 유사 SPEC 존재: POKEMON-IMAGE-COMPLETE-001 (완전)
   - 상태: 참고용/레거시 추정
   - 조치: POKEMON-IMAGE-COMPLETE-001 사용 권장

🟡 ROUTER-CONFLICT-001
   - SPEC 위치: .moai/specs/SPEC-ROUTER-CONFLICT-001/
   - 구현 파일: apps/api/routers/agent_factory_router.py (라인 43)
   - 상태: 코드에 태그 없음
   - 조치: # @CODE:ROUTER-CONFLICT-001 추가
```

### 1.2 향후 구현 대기 SPEC (우선순위 낮음)

```
ADMIN-DASHBOARD-001        - 대시보드 기능 (검토 필요)
AGENT-CREATE-FORM-001      - 에이전트 생성 폼 (검토 필요)
API-001                    - API 게이트웨이 (검토 필요)
AUTH-002                   - 인증 시스템 (검토 필요)
BTN-001                    - 버튼 컴포넌트 (검토 필요)
CICD-001                   - CI/CD 파이프라인 (검토 필요)
CLASS-001                  - 분류 시스템 (검토 필요)
DARK-MODE-001              - 다크 모드 (검토 필요)
DATA-UPLOAD-001            - 데이터 업로드 (검토 필요)
ENV-VALIDATE-001           - 환경 검증 (검토 필요)
EVAL-001                   - 평가 시스템 (검토 필요)
FRONTEND-INIT-001          - 프론트엔드 초기화 (검토 필요)
FRONTEND-INTEGRATION-001   - 프론트엔드 통합 (검토 필요)
HOOKS-REFACTOR-001         - 훅 리팩토링 (검토 필요)
IMPORT-ASYNC-FIX-001       - 비동기 임포트 (검토 필요)
INGESTION-001              - 데이터 수집 (검토 필요)
JOB-OPTIMIZE-001           - 작업 최적화 (검토 필요)
MOBILE-RESPONSIVE-001      - 모바일 반응형 (검토 필요)
OCR-CASCADE-001            - OCR 캐스케이드 (검토 필요)
REPLAY-001                 - 재생 기능 (검토 필요)
RESEARCH-AGENT-UI-001      - 연구 에이전트 UI (검토 필요)
ROUTER-IMPORT-FIX-001      - 라우터 임포트 수정 (검토 필요)
SECURITY-001               - 보안 시스템 (검토 필요)
SOFTQ-001                  - SOFTQ 구현 (검토 필요)
TAG-CLEANUP-001            - TAG 정리 (검토 필요)
TAXONOMY-KEYNAV-002        - 택소노미 키 네비게이션 (검토 필요)
(+ 10개 추가)
```

---

## 2. SPEC 없는 CODE (고아 TAG)

### 2.1 긴급 해결 필요 (우선순위 1)

```
🔴 ROUTER-CONFLICT-001
   - 파일: apps/api/routers/agent_factory_router.py (라인 43)
   - 내용: 라우터 엔드포인트 충돌 해결
   - SPEC: 존재하지만 CODE 라인에 태그 없음
   - 조치: 코드에 # @CODE:ROUTER-CONFLICT-001 추가

🔴 PAYMENT-001
   - 참조 위치: 문서 및 보고서 (실제 코드 구현 불명확)
   - 상태: SPEC 없음
   - 조치: 
     A) SPEC 문서 생성 (.moai/specs/SPEC-PAYMENT-001/)
     B) 또는 모든 참조 제거

🟡 AVATAR-SERVICE-001
   - 파일: apps/api/services/avatar_service.py
   - 관련 SPEC: POKEMON-IMAGE-COMPLETE-001 (확인 필요)
   - 조치: 
     A) POKEMON-IMAGE-COMPLETE-001과 연결
     B) 또는 독립적인 SPEC 생성

🟡 AGENT-DAO-AVATAR-002
   - 파일: apps/api/agent_dao.py (라인 8, 48, 74)
   - 관련 기능: Pokemon 아바타 시스템
   - 관련 SPEC: POKEMON-IMAGE-COMPLETE-001 추정
   - 조치:
     A) POKEMON-IMAGE-COMPLETE-001과 연결
     B) 또는 AGENT-DAO-AVATAR-002 SPEC 생성
```

### 2.2 부분적 문제 (우선순위 2)

```
🟡 AGENT-ROUTER-BUGFIX-001-C01 through C04
   - 파일: 
     * apps/api/routers/agent_router.py (C01, C03, C04)
     * apps/api/agent_dao.py (C04)
     * apps/api/schemas/agent_schemas.py (C02)
   - 문제: 부모 SPEC(AGENT-ROUTER-BUGFIX-001)은 C01-C04 정의하지만 
           @SPEC:AGENT-ROUTER-BUGFIX-001-C01 등이 없음
   - 조치:
     A) 부모 SPEC 문서에 C01-C04 명확히 정의
     B) 또는 각각 독립적인 SPEC 문서 생성

🟡 AGENT-CARD-001 서브 컴포넌트들
   - AGENT-CARD-001-ANIM-001
   - AGENT-CARD-001-ERROR-001
   - AGENT-CARD-001-PAGE-001
   - AGENT-CARD-001-UI-001 through UI-005
   - AGENT-CARD-001-UTILS-001 through UTILS-004
   - 상태: 부모 SPEC은 있으나 서브 SPEC 없음
   - 설계 검토: 의도적 서브 컴포넌트인지 확인 필요

🟡 AGENT-GROWTH-004 서브 모듈들
   - AGENT-GROWTH-004:BACKGROUND
   - AGENT-GROWTH-004:WORKER
   - AGENT-GROWTH-004:QUEUE
   - AGENT-GROWTH-004:DAO
   - AGENT-GROWTH-004:SERVICE
   - AGENT-GROWTH-004:MODEL
   - 상태: 부모 SPEC은 있으나 서브 TAG 미정의
   - 설계 검토: 아키텍처 검토 필요
```

---

## 3. SPEC 없는 TEST (고아 TAG)

약 **51개 TEST TAG**가 SPEC 없이 존재합니다:

```
🟡 AGENT-CARD-001-HOOK-001
   - 파일: tests/
   - 관련 기능: 훅 테스트
   - 부모 SPEC: AGENT-CARD-001 (부모는 있음)
   - 조치: 부모 SPEC 참조로 처리하거나 서브 SPEC 생성

🟡 CASEBANK-UNIFY-INTEGRATION-001
   - 파일: tests/integration/
   - 상태: 통합 테스트 (부모 SPEC 필요)
   - 조치: SPEC:CASEBANK-UNIFY-001 생성 후 링크

🟡 CASEBANK-UNIFY-UNIT-001
   - 파일: tests/unit/
   - 상태: 단위 테스트 (부모 SPEC 필요)
   - 조치: SPEC:CASEBANK-UNIFY-001 생성 후 링크

🟡 AGENT-GROWTH-002-PHASE2
   - 파일: tests/
   - 관련 SPEC: AGENT-GROWTH-002
   - 상태: 페이즈별 테스트 (부모 SPEC 명확화 필요)
   - 조치: 부모 SPEC 검토 및 명확화

(+ 47개 추가 TEST TAG들...)
```

---

## 4. 해결 방안

### 4.1 즉시 조치 (우선순위 1 - 이번 세션)

#### Step 1: CASEBANK-UNIFY-001 완성 (1-2시간)
```bash
# 1. 구현 파일 확인
grep -r "casebank_unify\|CaseBank.*unify" apps/api/

# 2. 각 파일의 시작에 주석 추가
# @CODE:CASEBANK-UNIFY-001

# 3. Git 커밋
git add apps/api/database.py ...
git commit -m "feat: tag CASEBANK-UNIFY-001 implementation @CODE:CASEBANK-UNIFY-001"
```

#### Step 2: AGENT-ROUTER-BUGFIX-001 명확화 (1시간)
```bash
# 파일: .moai/specs/SPEC-AGENT-ROUTER-BUGFIX-001/spec.md
# 수정: C01-C04 각 버그 명확히 정의

# 또는 별도 SPEC 생성
mkdir -p .moai/specs/SPEC-AGENT-ROUTER-BUGFIX-001-C01
mkdir -p .moai/specs/SPEC-AGENT-ROUTER-BUGFIX-001-C02
# ...
```

#### Step 3: ROUTER-CONFLICT-001 태그 추가 (30분)
```bash
# 파일: apps/api/routers/agent_factory_router.py
# 라인 43 근처에 주석 추가:
# @CODE:ROUTER-CONFLICT-001
```

#### Step 4: 고아 TAG 정리 (1시간)
```bash
# PAYMENT-001 처리: SPEC 생성 또는 제거
# AVATAR-* 처리: 부모 SPEC 확인 및 연결
# POKEMON-IMAGE: 체인 확인
```

### 4.2 단기 조치 (우선순위 2-3 - 이번 주)

1. **부모 SPEC 정의 정확화**
   - 모든 C01-C04, UI-001-005 등 서브 TAG의 정의 명확화
   - 각 부모 SPEC 문서에서 서브 TAG 목록 추가

2. **미구현 SPEC 분류**
   - 36개 미구현 SPEC을 활성/비활성으로 분류
   - 활성 항목은 우선순위 정렬
   - 비활성 항목은 보관 처리

3. **TEST TAG 체계화**
   - 51개 TEST TAG의 부모 SPEC 확인
   - 필요시 서브 SPEC 생성 또는 부모 SPEC 참조로 표준화

### 4.3 장기 개선 (2주)

1. **Pre-commit Hook 도입**
   ```bash
   # TAG 형식 자동 검증
   # - @SPEC:DOMAIN-NNN 형식 확인
   # - @CODE:DOMAIN-NNN 형식 확인
   # - SPEC과 CODE 연결 검증
   ```

2. **TAG 가이드라인 수립**
   - 서브 컴포넌트 TAG 명명 규칙 통일
   - 부모-자식 관계 정의 명확화

3. **자동화 스크립트**
   - TAG 체인 무결성 자동 검사 스크립트
   - 주간 TAG 리포트 자동 생성

---

## 5. 추적 체크리스트

### 이번 세션 (우선순위 1)
- [ ] CASEBANK-UNIFY-001 CODE 태그 추가
- [ ] AGENT-ROUTER-BUGFIX-001 C01-C04 정의 명확화
- [ ] ROUTER-CONFLICT-001 코드 태그 추가
- [ ] PAYMENT-001 처리 (SPEC 생성 또는 제거)
- [ ] AVATAR-SERVICE-001, AGENT-DAO-AVATAR-002 정리

### 이번 주
- [ ] 고아 TEST TAG 36개 검토
- [ ] 미구현 SPEC 활성/비활성 분류 완료
- [ ] 서브 TAG 네이밍 규칙 통일
- [ ] 전체 체인 무결성 75% 이상 달성

### 2주 내
- [ ] 체인 무결성 90% 달성
- [ ] Pre-commit hook 도입
- [ ] TAG 자동화 스크립트 구현

---

**보고서 작성**: TAG 시스템 검증 에이전트  
**검증 완료**: 2025-11-11  
**다음 검증**: 즉시 조치 완료 후  

