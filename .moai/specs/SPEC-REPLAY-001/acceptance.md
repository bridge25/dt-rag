# @ACCEPT:REPLAY-001: Experience Replay Buffer 수락 기준

## 개요

이 문서는 SPEC-REPLAY-001 (Experience Replay Buffer) 구현의 수락 기준을 정의합니다. 모든 시나리오는 Given-When-Then 형식으로 작성되었습니다.

## 시나리오 1: Replay Buffer 저장

### Given-When-Then

**Given**:
- Feature Flag `experience_replay=True`로 설정됨
- LangGraph Pipeline이 step7_respond를 실행 중
- PipelineState에 다음 정보가 포함됨:
  - `state_hash`: "state_12345"
  - `selected_action_idx`: 2
  - `confidence`: 0.85
  - `latency`: 0.12
  - `next_state_hash`: "state_12345" (terminal state)

**When**:
- step7_respond() 메서드가 완료됨

**Then**:
- Replay Buffer에 (state, action, reward, next_state) tuple이 저장됨
- Replay Buffer 크기가 1 증가함
- DEBUG 로그가 기록됨: "Experience added to Replay Buffer: size=X"
- 메인 파이프라인이 정상 진행됨 (차단 없음)

### 검증 방법

```python
# 테스트 코드
async def test_replay_buffer_add_on_step7():
    # Given
    flags = {"experience_replay": True}
    state = PipelineState(
        state_hash="state_12345",
        selected_action_idx=2,
        confidence=0.85,
        latency=0.12
    )

    # When
    await pipeline.step7_respond(state)

    # Then
    assert len(pipeline.replay_buffer) == 1
    batch = await pipeline.replay_buffer.sample(batch_size=1)
    assert batch[0][0] == "state_12345"
    assert batch[0][1] == 2
```

### 완료 조건

- [x] Replay Buffer에 정확한 tuple 저장
- [x] Buffer 크기 정확히 증가
- [x] 로그 기록 확인
- [x] 메인 파이프라인 비차단

---

## 시나리오 2: 배치 학습

### Given-When-Then

**Given**:
- Replay Buffer에 100개 경험이 저장되어 있음
- SoftQLearning 인스턴스가 초기화됨
- Q-table은 비어있음

**When**:
- `batch_update(replay_buffer, batch_size=32)` 호출됨

**Then**:
- Replay Buffer에서 32개 경험이 랜덤 샘플링됨
- 32개 경험에 대해 Q-table이 업데이트됨
- Q-table에 최소 1개 이상의 state_hash 키가 추가됨
- INFO 로그가 기록됨: "Batch update completed: 32 samples, Q-table size: X"
- 메서드가 32를 반환함 (업데이트된 샘플 수)

### 검증 방법

```python
# 테스트 코드
async def test_batch_learning_from_buffer():
    # Given
    q_learning = SoftQLearning()
    buffer = ReplayBuffer(max_size=1000)

    for i in range(100):
        await buffer.add(f"state{i}", i % 6, 0.5, f"state{i+1}")

    # When
    updated = await q_learning.batch_update(buffer, batch_size=32)

    # Then
    assert updated == 32
    assert len(q_learning.q_table) > 0
    assert all(len(q_values) == 6 for q_values in q_learning.q_table.values())
```

### 완료 조건

- [x] 정확히 32개 샘플 처리
- [x] Q-table 업데이트 확인
- [x] 로그 기록 확인
- [x] 반환값 검증

---

## 시나리오 3: FIFO Eviction

### Given-When-Then

**Given**:
- Replay Buffer의 max_size=10으로 설정됨
- Buffer에 10개 경험이 이미 저장되어 있음:
  - (state0, 0, 0.5, state1)
  - (state1, 1, 0.5, state2)
  - ...
  - (state9, 0, 0.5, state10)

**When**:
- 11번째 경험 (state10, 0, 0.5, state11)이 추가됨

**Then**:
- Buffer 크기는 여전히 10임
- 가장 오래된 경험 (state0, 0, 0.5, state1)이 제거됨
- 새 경험 (state10, 0, 0.5, state11)이 추가됨
- Buffer에서 샘플링 시 state0이 포함되지 않음

### 검증 방법

```python
# 테스트 코드
async def test_replay_buffer_fifo_eviction():
    # Given
    buffer = ReplayBuffer(max_size=10)

    for i in range(10):
        await buffer.add(f"state{i}", 0, 0.5, f"state{i+1}")

    # When
    await buffer.add("state10", 0, 0.5, "state11")

    # Then
    assert len(buffer) == 10
    batch = await buffer.sample(batch_size=10)

    # state0이 eviction되었는지 확인
    assert all(exp[0] != "state0" for exp in batch)
    assert any(exp[0] == "state10" for exp in batch)
```

### 완료 조건

- [x] Buffer 크기 제한 준수
- [x] 가장 오래된 경험 제거
- [x] 새 경험 추가 확인
- [x] FIFO 순서 검증

---

## 시나리오 4: Feature Flag OFF

### Given-When-Then

**Given**:
- Feature Flag `experience_replay=False`로 설정됨
- LangGraph Pipeline이 step7_respond를 실행 중
- Replay Buffer가 초기화되어 있음 (비어있음)

**When**:
- step7_respond() 메서드가 완료됨

**Then**:
- Replay Buffer에 경험이 저장되지 않음
- Replay Buffer 크기가 0으로 유지됨
- DEBUG 로그가 기록되지 않음 ("Experience added to Replay Buffer" 없음)
- 기존 Q-learning 동작이 정상 진행됨 (단일 샘플 업데이트)

### 검증 방법

```python
# 테스트 코드
async def test_experience_replay_flag_off(mocker):
    # Given
    mocker.patch(
        "apps.api.env_manager.get_feature_flags",
        return_value={"experience_replay": False}
    )
    state = PipelineState(...)

    # When
    await pipeline.step7_respond(state)

    # Then
    assert len(pipeline.replay_buffer) == 0
    # 기존 Q-learning은 정상 동작
    assert len(pipeline.q_learning.q_table) > 0
```

### 완료 조건

- [x] Replay Buffer에 저장 없음
- [x] 기존 Q-learning 동작 보존
- [x] 로그 기록 없음
- [x] 성능 영향 없음

---

## 시나리오 5: 비동기 배치 학습

### Given-When-Then

**Given**:
- Replay Buffer에 200개 경험이 저장되어 있음
- SoftQLearning 인스턴스가 초기화됨
- 메인 파이프라인이 실행 중

**When**:
- `batch_update()` 메서드가 비동기로 호출됨 (asyncio.create_task)
- 동시에 메인 파이프라인이 다른 작업을 수행함

**Then**:
- 배치 학습이 백그라운드에서 실행됨
- 메인 파이프라인이 차단되지 않음 (동시 실행)
- 배치 학습이 완료되면 50개 샘플이 업데이트됨
- Q-table이 정상적으로 갱신됨

### 검증 방법

```python
# 테스트 코드
async def test_async_batch_learning():
    # Given
    q_learning = SoftQLearning()
    buffer = ReplayBuffer(max_size=1000)

    for i in range(200):
        await buffer.add(f"state{i}", i % 6, 0.5, f"state{i+1}")

    # When
    task = asyncio.create_task(
        q_learning.batch_update(buffer, batch_size=50)
    )

    # 메인 파이프라인 작업 시뮬레이션
    await asyncio.sleep(0.01)

    # Then
    updated = await task

    assert updated == 50
    assert len(q_learning.q_table) > 0
```

### 완료 조건

- [x] 비동기 실행 확인
- [x] 메인 파이프라인 비차단
- [x] 배치 학습 정상 완료
- [x] Q-table 갱신 검증

---

## 시나리오 6: 에러 처리 - Buffer 저장 실패

### Given-When-Then

**Given**:
- Feature Flag `experience_replay=True`로 설정됨
- Replay Buffer의 add() 메서드가 예외를 발생시킴 (Mock)

**When**:
- step7_respond() 메서드가 실행됨

**Then**:
- ERROR 로그가 기록됨: "Failed to add experience to Replay Buffer: {exception}"
- 예외가 전파되지 않음 (파이프라인 계속 진행)
- 메인 파이프라인이 정상 완료됨
- Response가 정상적으로 생성됨

### 검증 방법

```python
# 테스트 코드
async def test_buffer_add_failure_non_blocking(mocker, caplog):
    # Given
    mocker.patch.object(
        ReplayBuffer,
        "add",
        side_effect=Exception("Buffer full")
    )
    flags = {"experience_replay": True}
    state = PipelineState(...)

    # When
    result = await pipeline.step7_respond(state)

    # Then
    assert "Failed to add experience to Replay Buffer" in caplog.text
    assert result.response is not None  # 정상 완료
```

### 완료 조건

- [x] ERROR 로그 기록
- [x] 예외 비전파 (try-except)
- [x] 파이프라인 정상 진행
- [x] Response 생성 확인

---

## 시나리오 7: 배치 크기 미달

### Given-When-Then

**Given**:
- Replay Buffer에 5개 경험만 저장되어 있음
- SoftQLearning 인스턴스가 초기화됨

**When**:
- `batch_update(replay_buffer, batch_size=32)` 호출됨

**Then**:
- DEBUG 로그가 기록됨: "Buffer too small for batch learning: 5 < 32"
- 배치 학습이 스킵됨
- 메서드가 0을 반환함 (업데이트된 샘플 수 없음)
- Q-table이 변경되지 않음

### 검증 방법

```python
# 테스트 코드
async def test_batch_update_insufficient_samples(caplog):
    # Given
    q_learning = SoftQLearning()
    buffer = ReplayBuffer(max_size=100)

    for i in range(5):
        await buffer.add(f"state{i}", 0, 0.5, f"state{i+1}")

    # When
    updated = await q_learning.batch_update(buffer, batch_size=32)

    # Then
    assert updated == 0
    assert "Buffer too small for batch learning" in caplog.text
    assert len(q_learning.q_table) == 0
```

### 완료 조건

- [x] DEBUG 로그 기록
- [x] 배치 학습 스킵
- [x] 반환값 0
- [x] Q-table 변경 없음

---

## 통합 품질 게이트

### 테스트 통과율

- [ ] 단위 테스트: 4/4 통과 (100%)
- [ ] 통합 테스트: 3/3 통과 (100%)
- [ ] 총 테스트: 7/7 통과 (100%)

### 코드 커버리지

- [ ] Replay Buffer: 100% (신규 코드)
- [ ] Q-learning 수정: 100% (신규 메서드)
- [ ] Pipeline 통합: 90% 이상
- [ ] 전체: 90% 이상

### 성능 검증

- [ ] 배치 학습 latency: < 50ms (batch_size=32)
- [ ] 메모리 사용량: < 2MB (max_size=10000)
- [ ] 메인 파이프라인 overhead: < 5% (Flag ON 시)
- [ ] 비동기 실행: 메인 파이프라인 차단 없음

### 회귀 테스트

- [ ] 기존 Q-learning 테스트: 모두 통과
- [ ] 기존 파이프라인 테스트: 모두 통과
- [ ] 기존 Feature Flags: 정상 동작

### 문서화

- [ ] spec.md HISTORY 업데이트
- [ ] Docstring 완전 작성 (모든 public 메서드)
- [ ] Type hints 완전 적용 (strict mode)
- [ ] README 업데이트 (선택적)

## 검증 도구

### 단위 테스트 실행

```bash
pytest tests/unit/test_replay_buffer.py -v --cov=apps/orchestration/src/bandit/replay_buffer.py
```

### 통합 테스트 실행

```bash
pytest tests/integration/test_replay_learning.py -v --cov=apps/orchestration/src/bandit/
```

### 전체 테스트 실행

```bash
pytest tests/ -v --cov=apps/orchestration/src/bandit/ --cov-report=html
```

### 성능 테스트

```python
# 배치 학습 latency 측정
import time

async def benchmark_batch_update():
    q_learning = SoftQLearning()
    buffer = ReplayBuffer(max_size=10000)

    for i in range(1000):
        await buffer.add(f"state{i}", i % 6, 0.5, f"state{i+1}")

    start = time.time()
    await q_learning.batch_update(buffer, batch_size=32)
    latency = time.time() - start

    assert latency < 0.05  # 50ms
    print(f"Batch learning latency: {latency*1000:.2f}ms")
```

## Definition of Done (최종 체크리스트)

### 기능 완성도

- [ ] 시나리오 1: Replay Buffer 저장 (통과)
- [ ] 시나리오 2: 배치 학습 (통과)
- [ ] 시나리오 3: FIFO Eviction (통과)
- [ ] 시나리오 4: Feature Flag OFF (통과)
- [ ] 시나리오 5: 비동기 배치 학습 (통과)
- [ ] 시나리오 6: 에러 처리 - Buffer 저장 실패 (통과)
- [ ] 시나리오 7: 배치 크기 미달 (통과)

### 코드 품질

- [ ] Linter 경고 없음 (flake8)
- [ ] Type checker 경고 없음 (mypy --strict)
- [ ] 코드 커버리지 90% 이상
- [ ] Docstring 완전 작성

### 문서화

- [ ] spec.md 최신 상태
- [ ] plan.md 최신 상태
- [ ] acceptance.md 최신 상태
- [ ] HISTORY 섹션 업데이트

### 회귀 방지

- [ ] 기존 테스트 모두 통과
- [ ] 기존 동작 보존 (Flag OFF 시)
- [ ] 성능 저하 없음

## 승인 기준

다음 조건이 모두 충족되어야 SPEC-REPLAY-001이 승인됩니다:

1. **모든 시나리오 통과**: 7/7
2. **테스트 통과율**: 100% (7/7)
3. **코드 커버리지**: 90% 이상
4. **성능 검증**: 모든 성능 기준 충족
5. **회귀 테스트**: 모든 기존 테스트 통과
6. **문서화**: 모든 문서 최신 상태
7. **코드 리뷰**: 최소 1명 승인 (선택적, Team 모드)

---

**최종 업데이트**: 2025-10-09
**작성자**: @claude
**관련 SPEC**: @SPEC:REPLAY-001
