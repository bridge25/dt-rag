# @PLAN:REPLAY-001: Experience Replay Buffer 구현 계획

## 목표

Soft Q-learning Bandit에 Experience Replay Buffer를 추가하여 Sample Efficiency를 향상시키고, Off-policy Learning을 지원합니다.

## 구현 전략

### TDD (Test-Driven Development) 접근

1. **Red**: 테스트 작성 (실패)
2. **Green**: 최소 구현 (통과)
3. **Refactor**: 코드 개선

### Phase 1: Replay Buffer 기본 구현 (우선순위: High)

**목표**: In-memory Replay Buffer 클래스 구현

**구현 순서**:
1. `tests/unit/test_replay_buffer.py` 작성
   - `test_replay_buffer_add()`: 경험 추가 테스트
   - `test_replay_buffer_sample()`: 랜덤 샘플링 테스트
   - `test_replay_buffer_fifo_eviction()`: FIFO 정책 테스트
   - `test_replay_buffer_min_samples()`: 최소 샘플 수 테스트

2. `apps/orchestration/src/bandit/replay_buffer.py` 구현
   - `ReplayBuffer` 클래스
   - `add()` 메서드 (async)
   - `sample()` 메서드 (async)
   - `__len__()` 메서드
   - `deque(maxlen=max_size)` 사용 (FIFO 자동 처리)
   - `asyncio.Lock` 사용 (thread-safe)

3. 테스트 실행 및 검증
   - `pytest tests/unit/test_replay_buffer.py -v`
   - 커버리지: 100% 목표

**완료 조건**:
- 모든 단위 테스트 통과 (4/4)
- 코드 커버리지 100%
- FIFO eviction 정상 동작
- Thread-safe 보장

### Phase 2: Batch Learning 통합 (우선순위: High)

**목표**: Q-learning에 배치 업데이트 메서드 추가

**구현 순서**:
1. `tests/integration/test_replay_learning.py` 작성
   - `test_batch_learning_from_buffer()`: 배치 학습 테스트
   - `test_async_batch_learning()`: 비동기 실행 테스트

2. `apps/orchestration/src/bandit/q_learning.py` 수정
   - `batch_update()` 메서드 추가 (async)
   - 기존 `update_q_value()` 재사용
   - 로깅 추가 (배치 크기, 업데이트 수)

3. 테스트 실행 및 검증
   - `pytest tests/integration/test_replay_learning.py -v`
   - 기존 Q-learning 테스트 회귀 없음 확인

**완료 조건**:
- 배치 학습 테스트 통과 (2/2)
- 기존 Q-learning 동작 보존 (backward compatibility)
- 비동기 실행 검증 (메인 파이프라인 비차단)

### Phase 3: Feature Flag 통합 (우선순위: Medium)

**목표**: `experience_replay` Flag를 통한 Replay Buffer 활성화

**구현 순서**:
1. `apps/api/env_manager.py` 확인
   - `experience_replay` Flag 존재 확인 (FOUNDATION-001에서 추가됨)

2. `apps/orchestration/src/langgraph_pipeline.py` 수정
   - `ReplayBuffer` 인스턴스 추가
   - `step7_respond()`에서 경험 저장 추가
   - Feature Flag 확인 로직 추가
   - 에러 처리 (비차단)

3. 통합 테스트 작성
   - `test_experience_replay_flag_integration()`: Flag ON/OFF 동작 검증
   - Mock `get_feature_flags()` 사용

**완료 조건**:
- Flag OFF 시: 기존 동작 유지 (Replay Buffer 미사용)
- Flag ON 시: 경험 저장 및 배치 학습
- 에러 발생 시: 로그 기록 후 계속 진행 (비차단)

### Phase 4: 주기적 배치 학습 (선택적) (우선순위: Low)

**목표**: 백그라운드에서 주기적으로 배치 학습 수행

**구현 순서**:
1. `periodic_batch_learning()` 메서드 구현
   - `asyncio.create_task()`로 백그라운드 실행
   - 1분마다 배치 학습 트리거
   - Feature Flag 확인

2. 테스트 작성
   - 백그라운드 태스크 동작 검증
   - 메인 파이프라인 비차단 확인

**완료 조건**:
- 주기적 배치 학습 정상 동작
- 메인 파이프라인 성능 영향 없음

## 아키텍처 설계

### 컴포넌트 다이어그램

```
┌─────────────────────────────────────┐
│    LangGraph Pipeline (Step 7)     │
│  - step7_respond()                  │
│  - Feature Flag 확인                │
└─────────────┬───────────────────────┘
              │
              │ (state, action, reward, next_state)
              ▼
┌─────────────────────────────────────┐
│       Replay Buffer                 │
│  - add() - 경험 저장                │
│  - sample() - 랜덤 샘플링           │
│  - FIFO eviction                    │
└─────────────┬───────────────────────┘
              │
              │ batch (32 samples)
              ▼
┌─────────────────────────────────────┐
│       Soft Q-learning               │
│  - batch_update() - 배치 학습       │
│  - update_q_value() - Q-table 갱신  │
└─────────────────────────────────────┘
```

### 데이터 플로우

1. **경험 수집**: step7_respond → Replay Buffer.add()
2. **배치 샘플링**: Replay Buffer.sample(batch_size=32)
3. **배치 학습**: SoftQLearning.batch_update()
4. **Q-table 갱신**: SoftQLearning.update_q_value() (기존 메서드)

### 에러 처리 전략

- **비차단 설계**: 모든 Replay Buffer 작업 실패 시에도 파이프라인 계속 진행
- **Graceful Degradation**: 배치 크기 미달 시 사용 가능한 샘플만 사용
- **로깅 레벨**:
  - DEBUG: 경험 추가, 샘플링
  - INFO: 배치 학습 완료, FIFO eviction
  - WARNING: 배치 학습 실패
  - ERROR: Replay Buffer 저장 실패

## 리스크 및 대응 방안

### 리스크 1: 메모리 사용량 증가

**문제**: Replay Buffer가 10,000개 경험을 저장 → 메모리 부담

**대응**:
- Phase 1에서는 max_size=10000 유지 (약 1MB 미만)
- 향후 PostgreSQL 영구 저장으로 전환 가능 (Phase 2)
- 환경 변수로 max_size 조정 가능

### 리스크 2: 배치 학습 성능 저하

**문제**: 배치 학습이 메인 파이프라인을 차단할 가능성

**대응**:
- 비동기 메서드 (async/await) 사용
- 주기적 배치 학습은 백그라운드 태스크로 실행
- 배치 크기 제한 (batch_size=32, 약 10ms 예상)

### 리스크 3: 샘플 편향 (Sample Bias)

**문제**: 랜덤 샘플링이 특정 state에 편향될 가능성

**대응**:
- Python `random.sample()` 사용 (균등 분포)
- 향후 Prioritized Experience Replay로 확장 가능

## 마일스톤

### 1차 목표: Replay Buffer 기본 동작

- Replay Buffer 클래스 구현 완료
- 단위 테스트 4개 통과
- FIFO eviction 검증

**의존성**: 없음

### 2차 목표: Batch Learning 통합

- Q-learning에 batch_update() 메서드 추가
- 통합 테스트 2개 통과
- 비동기 실행 검증

**의존성**: 1차 목표 완료 필요

### 3차 목표: Feature Flag 통합

- step7_respond()에서 경험 저장
- Flag ON/OFF 동작 검증
- 에러 처리 검증

**의존성**: 2차 목표 완료 필요

### 최종 목표: Production Ready

- 모든 테스트 통과 (6개 이상)
- 코드 커버리지 90% 이상
- 성능 테스트 (배치 학습 latency < 50ms)

**의존성**: 1~3차 목표 모두 완료

## 기술적 접근 방법

### 자료구조 선택

- **Replay Buffer**: `collections.deque(maxlen=max_size)`
  - 이유: FIFO eviction 자동 처리, O(1) 추가/삭제
  - 대안: List (수동 eviction, O(n))

### 동시성 제어

- **Thread-Safe**: `asyncio.Lock`
  - 이유: add()와 sample() 동시 호출 가능성
  - 대안: Queue (더 무거움)

### 샘플링 전략

- **Random Sampling**: `random.sample()`
  - 이유: Decorrelation, Off-policy Learning
  - 대안: Sequential (On-policy, 편향 가능)

## Definition of Done (완료 기준)

### 코드 품질

- [ ] 모든 단위 테스트 통과 (4/4)
- [ ] 모든 통합 테스트 통과 (2/2)
- [ ] 코드 커버리지 90% 이상 (신규 코드 100%)
- [ ] Linter 경고 없음 (flake8, mypy)
- [ ] Type hints 완전 적용 (strict mode)

### 기능 완성도

- [ ] Replay Buffer 기본 동작 (add, sample, eviction)
- [ ] Batch Learning 통합 (batch_update)
- [ ] Feature Flag 통합 (experience_replay)
- [ ] 에러 처리 (비차단, 로깅)
- [ ] 비동기 실행 (메인 파이프라인 비차단)

### 문서화

- [ ] spec.md 최신 상태 유지
- [ ] plan.md 최신 상태 유지
- [ ] acceptance.md 모든 시나리오 검증
- [ ] Docstring 완전 작성 (모든 public 메서드)
- [ ] HISTORY 섹션 업데이트 (구현 완료 후)

### 성능 검증

- [ ] 배치 학습 latency < 50ms (batch_size=32)
- [ ] 메모리 사용량 < 2MB (max_size=10000)
- [ ] 메인 파이프라인 성능 저하 없음 (기존 대비 +5% 이내)

### 회귀 테스트

- [ ] 기존 Q-learning 테스트 모두 통과
- [ ] 기존 파이프라인 동작 보존 (Flag OFF 시)
- [ ] 기존 Feature Flags 동작 보존

## 다음 단계

### 즉시 실행 가능

- `/alfred:2-build REPLAY-001`: 구현 시작
- 테스트 파일부터 작성 (TDD)

### REPLAY-001 완료 후

- SPEC-DEBATE-001 통합 (Multi-agent Debate)
- SPEC-NEURAL-001 통합 (Neural CBR)
- Phase 4: PostgreSQL 영구 저장 (선택적)
