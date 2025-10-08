# 다음 세션 시작 프롬프트

아래 내용을 새 세션에 붙여넣어 시작하세요.

---

## 📋 세션 시작 지시문

안녕. 이전 세션에서 Phase 2 & 3 구현을 완료했지만, TaxonomyDAO 데이터 조회 이슈로 통합 테스트를 완료하지 못했어.

**지금부터 할 일:**
1. `PHASE2_3_NEXT_SESSION_CONTEXT.md` 파일을 **전체** 읽어서 상황 파악
2. TaxonomyDAO 이슈 디버깅 및 해결
3. Phase 2/3 통합 테스트 완료

**반드시 지켜야 할 원칙 (바이브코딩):**
- **추측 금지**: 모든 정보를 코드를 직접 읽어서 확인
- **전체 읽기**: 관련 파일은 양이 많아도 전부 읽기 (건너뛰지 않음)
- **에러 즉시 해결**: 나중으로 미루지 않고 지금 해결
- **정석 구현**: 임시방편/우회 절대 금지
- **Code as SOT**: 문서나 주석보다 실제 코드 우선

**첫 번째 작업:**
```
C:\MYCLAUDE_PROJECT\sonheungmin\Unmanned\dt-rag\PHASE2_3_NEXT_SESSION_CONTEXT.md 파일을 읽어서 전체 상황을 파악해.
```

읽은 후에 나에게 요약해서 보고하고, 디버깅 계획을 제시해.

---

## 🎯 구체적 작업 지시

### Step 1: 컨텍스트 파악 (필수)
1. `PHASE2_3_NEXT_SESSION_CONTEXT.md` **전체** 읽기
2. 완료된 작업과 현재 이슈를 나에게 요약 보고
3. 이슈 원인 가설 3가지 제시

### Step 2: 근본 원인 특정
컨텍스트 문서의 "디버깅 체크리스트" 섹션을 따라:
1. DATABASE_URL 환경 변수 실제 값 확인
2. `apps/core/db_session.py` **전체** 읽고 연결 설정 분석
3. `apps/api/database.py`의 TaxonomyDAO **전체** 읽고 쿼리 로직 분석
4. 로그 추가하여 실제 쿼리 실행 여부 확인

### Step 3: 해결책 적용
1. 특정된 원인에 따라 해결책 구현
2. API 서버 재시작
3. 통합 테스트 실행

### Step 4: DoD 확인
- [ ] `GET /api/v1/taxonomy/versions` → 실제 DB 버전 목록 반환
- [ ] `GET /api/v1/taxonomy/1.0.0/tree` → 9개 노드 포함된 트리 반환
- [ ] 모든 수정 사항 commit (린트/타입 통과 확인)

---

## ⚠️ 중요 제약사항

1. **절대 하지 말 것:**
   - 문서나 주석만 보고 추측
   - 파일 일부만 읽고 건너뛰기
   - 임시 Mock 데이터로 우회
   - 에러를 "나중에 해결"로 미루기

2. **반드시 할 것:**
   - 모든 파일을 Read tool로 직접 읽기
   - 에러 발생 시 즉시 해결
   - 변경사항 적용 후 반드시 테스트
   - 작업 완료 시 DoD 체크리스트 확인

3. **TodoWrite 사용:**
   - 작업 시작 시 todo 리스트 생성
   - 각 단계 완료 시 즉시 상태 업데이트
   - 절대 여러 작업을 한 번에 완료 처리하지 않기

---

## 📂 핵심 파일 (컨텍스트 문서에 상세 정보 있음)

**즉시 읽어야 할 파일:**
1. `C:\MYCLAUDE_PROJECT\sonheungmin\Unmanned\dt-rag\PHASE2_3_NEXT_SESSION_CONTEXT.md` (컨텍스트)
2. `C:\MYCLAUDE_PROJECT\sonheungmin\Unmanned\dt-rag\apps\core\db_session.py` (DB 연결)
3. `C:\MYCLAUDE_PROJECT\sonheungmin\Unmanned\dt-rag\apps\api\database.py` (TaxonomyDAO)

**테스트 대상 파일:**
- `apps/api/services/taxonomy_service.py`
- `apps/api/routers/taxonomy_router.py`
- `apps/classification/hybrid_classifier.py`
- `apps/classification/hitl_queue.py`

---

## 🚀 빠른 시작

1. **컨텍스트 읽기:**
   ```
   PHASE2_3_NEXT_SESSION_CONTEXT.md 파일을 전체 읽어줘
   ```

2. **상황 파악 보고:**
   ```
   읽은 내용을 바탕으로:
   - 완료된 작업 요약
   - 현재 이슈 설명
   - 디버깅 계획 3단계 제시
   ```

3. **작업 시작:**
   ```
   디버깅을 시작하자. 먼저 DATABASE_URL 환경 변수부터 확인해.
   ```

---

## 📝 보고 형식

작업 진행 중 다음 형식으로 보고:

```
✅ [완료] 작업명
- 수행 내용
- 결과

⚠️ [이슈] 문제 발견
- 증상
- 원인 분석
- 해결 방법

🔍 [분석] 코드 분석
- 파일명:라인번호
- 발견 사항
- 다음 단계
```

---

지금 시작할까?
