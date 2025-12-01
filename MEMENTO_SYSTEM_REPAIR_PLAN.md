# 🛠️ 메멘토 메모리 시스템 완전 연결 수정 계획서

**작성일**: 2025-12-01
**버전**: 1.0
**상태**: 계획 완료, 구현 준비 완료
**담당**: Mr.Alfred (MoAI-ADK Super Agent Orchestrator)

---

## 📋 개요

본 문서는 dt-rag 프로젝트의 메멘토 메모리 시스템이 실제로 작동하도록 연결하기 위한 완전한 수정 계획서입니다.

### 🎯 문제 진단 요약

**결론**: 메멘토 시스템의 설계도는 완벽하지만, 전선 연결이 안 되어서 전기가 안 흐르는 상태입니다.

| 플로우 | 기대 동작 | 실제 상태 | 문제점 |
|--------|-----------|-----------|---------|
| **1. 쿼리→메모리** | 질문하면 CaseBank에 저장 | ❌ 끊김 | `add_to_casebank()`가 빈 stub |
| **2. 메모리→응답개선** | 과거 성공 케이스로 응답 향상 | ❌ 불가 | CaseBank가 항상 비어있음 |
| **3. 학습→UI반영** | growth% 실시간 업데이트 | ❌ 가짜 | Mock 데이터 (23%, 31% 고정) |
| **4. 피드백→진화** | 👍👎로 학습 | ❌ 없음 | UI도 API도 없음 |

---

## 🎯 최종 목표

### ✅ 수정 후 기대 효과

| 수정 전 | 수정 후 |
|--------|--------|
| 같은 질문 100번 → 품질 변화 없음 | 같은 질문 10번 → 품질 향상 체감 |
| growth% = 고정된 Mock 데이터 | growth% = 실제 학습 기반 업데이트 |
| "학습" 효과 = 0% | "학습" 효과 = 실시간 반영 |
| 피드백 방법 = 없음 | 피드백 = 👍👎 버튼으로 가능 |

---

## 📊 수정 상세 계획

### 🔴 PHASE 1: P0 긴급 수정사항 (핵심 연결)
**예상 소요 시간**: 1-2일
**목표**: 메멘토 시스템의 기본적인 작동 시작

#### 수정 1: Search Router에 CaseBank 저장 연동
- **파일**: `apps/api/routers/search_router.py`
- **위치**: 584-610라인 (검색 성공 직후)
- **현재 문제**:
  ```python
  # Line 584: 검색은 하지만 CaseBank에 저장 안 함
  result = await handler.search(search_request, correlation_id=correlation_id)
  # 결과만 반환하고 메모리 저장 X
  ```
- **수정 내용**:
  - 성공적인 검색 후 `add_to_casebank()` 호출 추가
  - ExecutionLog 기록 추가
  - 에러 핸들링 강화

#### 수정 2: Search Repository Stub 구현
- **파일**: `apps/api/data/repositories/search_repository_impl.py`
- **위치**: 259-269라인
- **현재 문제**:
  ```python
  # 빈 stub - UUID만 반환
  def add_to_casebank(self, case_data: CaseBankCreateSchema) -> str:
      return str(uuid4())  # 실제 저장 안 함
  ```
- **수정 내용**:
  - 실제 CaseBank 모델 사용한 DB 저장 로직 구현
  - ExecutionLog 동시 생성
  - 벡터 데이터 처리

---

### 🟡 PHASE 2: P1 2차 수정 (학습 루프 활성화)
**예상 소요 시간**: 2-3일
**목표**: 자동 학습 및 피드백 루프 구축

#### 수정 3: ReflectionEngine 배치 작업
- **파일**: `apps/api/services/search_service.py`
- **위치**: 387라인 `add_to_casebank()` 메소드
- **수정 내용**:
  - 성공/실패 로깅 강화
  - CaseBank 저장 후 ReflectionEngine 배치 호출
  - 백그라운드 작업 스케줄링

#### 수정 4: 프론트엔드 피드백 시스템
- **API 스키마**: `apps/frontend/lib/api/types.ts`
  - 위치: ~60라인 (SearchResponseSchema 후)
  - 내용: FeedbackRequestSchema, FeedbackResponseSchema 추가
- **API 함수**: `apps/frontend/lib/api/index.ts`
  - 위치: ~60라인 (search() 함수 후)
  - 내용: submitFeedback() 함수 구현
- **UI 컴포넌트**: `apps/frontend/app/(dashboard)/chat/page.tsx`
  - 위치: 261-316라인 (결과 표시 영역)
  - 내용: 각 결과卡片에 👍👎 피드백 버튼 추가

---

### 🟢 PHASE 3: P2 최종화 (UI 데이터 연결)
**예상 소요 시간**: 1일
**목표**: 사용자에게 실제 데이터 기반 UI 제공

#### 수정 5: useAgents Mock 데이터 최적화
- **파일**: `apps/frontend/hooks/useAgents.ts`
- **현재 상태**: ✅ 올바르게 구현됨 (API 실패 시 Mock fallback)
- **수정 필요**: 없음, 현재 구현 유지

---

## 📝 구현 체크리스트

### 🔴 PHASE 1: P0 긴급 수정사항 체크리스트

#### [ ] 수정 1: Search Router CaseBank 연동
- [ ] `apps/api/routers/search_router.py` 파일 확인
- [ ] 584라인 `result = await handler.search()` 확인
- [ ] 성공적인 검색 후 CaseBank 저장 로직 추가
  - [ ] `add_to_casebank()` 호출 코드 추가
  - [ ] ExecutionLog 생성 코드 추가
  - [ ] 에러 핸들링 및 로깅 강화
- [ ] API 응답 헤더에 메모리 저장 상태 추가
- [ ] 테스트: 검색 후 CaseBank에 데이터 저장되는지 확인

#### [ ] 수정 2: Search Repository 실제 구현
- [ ] `apps/api/data/repositories/search_repository_impl.py` 파일 확인
- [ ] 259-269라인 `add_to_casebank()` 메소드 확인
- [ ] 현재 stub 코드 제거
- [ ] 실제 CaseBank 모델 사용한 DB 저장 로직 구현
  - [ ] CaseBankCreateSchema → CaseBank 모델 변환
  - [ ] 벡터 데이터 처리 및 저장
  - [ ] ExecutionLog 동시 생성
- [ ] DB 세션 관리 및 트랜잭션 처리
- [ ] 테스트: UUID 반환 대신 실제 DB ID 반환 확인

#### [ ] PHASE 1 통합 테스트
- [ ] 검색 API 호출 테스트
- [ ] CaseBank 데이터 저장 확인 (DB 조회)
- [ ] ExecutionLog 생성 확인
- [ ] 에러 발생 시 롤백 확인
- [ ] 성능 테스트 (저장 지연 < 100ms 목표)

---

### 🟡 PHASE 2: P1 2차 수정 체크리스트

#### [ ] 수정 3: ReflectionEngine 배치 작업
- [ ] `apps/api/services/search_service.py` 파일 확인
- [ ] 387라인 `add_to_casebank()` 메소드 확인
- [ ] 성공/실패 로깅 강화
  - [ ] 성공 케이스 상세 기록
  - [ ] 실패 케이스 에러 타입 분류
  - [ ] 실행 시간 측정
- [ ] ReflectionEngine 배치 호출 추가
  - [ ] `run_reflection_batch()` 주기적 실행
  - [ ] 백그라운드 태스크 스케줄링
- [ ] 테스트: 배치 실행 후 CaseBank 성공률 업데이트 확인

#### [ ] 수정 4-1: 프론트엔드 피드백 API
- [ ] `apps/frontend/lib/api/types.ts` 파일 확인
- [ ] FeedbackRequestSchema 타입 정의
  - [ ] rating: number (1-5)
  - [ ] comment: string (선택)
  - [ ] search_result_id: string
- [ ] FeedbackResponseSchema 타입 정의
- [ ] `apps/frontend/lib/api/index.ts` 파일 확인
- [ ] submitFeedback() 함수 구현
  - [ ] POST /api/v1/feedback 엔드포인트
  - [ ] 에러 핸들링
  - [ ] 타입 변환

#### [ ] 수정 4-2: 프론트엔드 피드백 UI
- [ ] `apps/frontend/app/(dashboard)/chat/page.tsx` 파일 확인
- [ ] 261-316라인 결과 표시 영역 확인
- [ ] 각 결과卡片에 피드백 컴포넌트 추가
  - [ ] 👍👎 버튼 구현
  - [ ] 평점 별 스타일링
  - [ ] 클릭 이벤트 핸들러
  - [ ] 피드백 제출 API 호출
- [ ] 피드백 상태 관리 (React state)
- [ ] UI 애니메이션 및 사용자 피드백
- [ ] 테스트: 피드백 제출 후 API 확인

#### [ ] PHASE 2 통합 테스트
- [ ] ReflectionEngine 자동 실행 확인
- [ ] CaseBank 성공률 업데이트 확인
- [ ] 프론트엔드 피드백 제출 확인
- [ ] 피드백 데이터 DB 저장 확인
- [ ] 에이전트 growth% 업데이트 확인

---

### 🟢 PHASE 3: P2 최종화 체크리스트

#### [ ] 수정 5: 최종 검증
- [ ] `apps/frontend/hooks/useAgents.ts` Mock 동작 확인
- [ ] API 데이터 우선 사용 확인
- [ ] Mock fallback 정상 동작 확인

#### [ ] PHASE 3 통합 테스트
- [ ] End-to-End 플로우 테스트
  - [ ] 사용자 질문 → 검색 → CaseBank 저장 → 성공률 분석 → UI 반영
  - [ ] 피드백 제출 → 학습 루프 → 에이전트 성장
- [ ] 성능 테스트
  - [ ] 검색 응답 시간 < 500ms
  - [ ] CaseBank 저장 지연 < 100ms
  - [ ] 피드백 제출 지연 < 200ms
- [ ] 안정성 테스트
  - [ ] 동시 요청 처리
  - [ ] DB 커넥션 풀 관리
  - [ ] 에러 복구 메커니즘

---

## 🔍 진행 상태 추적

### 현재 진행 상태
- **PHASE 1**: ⏳ 준비 완료, 구현 시작 대기
- **PHASE 2**: ⏳ 준비 완료
- **PHASE 3**: ⏳ 준비 완료

### 최종 성공 지표
1. **기술적**: ✅ 검색 결과가 CaseBank에 실제로 저장
2. **성능**: ✅ ReflectionEngine이 ExecutionLog 분석으로 개선 제안 생성
3. **사용자 경험**: ✅ Agent growth%가 실제 데이터 기반으로 변동
4. **피드백 루프**: ✅ 사용자가 👍👎로 응답 품질 피드백 가능

---

## 🚀 작업 완료 체크 프롬프트

**작업 완료 시 아래 명령어를 실행하여 체크리스트를 업데이트하세요:**

```bash
# 체크리스트 항목 완료 표시
/moai:9-feedback "작업 완료: [PHASE X - 수정 Y - 세부 항목] 완료됨. 다음 항목 진행 준비 완료."

# 전체 PHASE 완료 보고
/moai:9-feedback "PHASE X 완료: 모든 체크리스트 항목 완료. 다음 PHASE 진행 준비 완료."

# 전체 프로젝트 완료 보고
/moai:9-feedback "메멘토 시스템 연결 프로젝트 완료: 모든 PHASE 완료. 시스템 정상 작동 확인됨."
```

---

## 📞 연락처 및 지원

- **프로젝트 관리자**: Mr.Alfred (MoAI-ADK Super Agent Orchestrator)
- **기술 지원**: MoAI-ADK 전문 에이전트 팀
- **문서 버전 관리**: 본 문서는 작업 진행에 따라 실시간 업데이트됩니다

---

**문서 마지막 업데이트**: 2025-12-01 13:45 KST
**다음 검토 예정**: PHASE 1 구현 완료 후