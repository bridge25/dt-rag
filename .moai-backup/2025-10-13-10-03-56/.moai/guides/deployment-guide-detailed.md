# 상세 배포 가이드: Phase 0-3.3

## 목차
1. [로컬 브랜치 통합](#1-로컬-브랜치-통합-personal-모드)
2. [프로덕션 환경 설정](#2-프로덕션-환경-설정)
3. [단계적 롤아웃](#3-단계적-롤아웃-전략)
4. [모니터링 및 검증](#4-모니터링-및-검증)
5. [롤백 절차](#5-롤백-절차)

---

## 1. 로컬 브랜치 통합 (Personal 모드)

### 1.1 사전 준비

#### 현재 상태 확인
```bash
# 현재 브랜치 확인
git branch --list
# 출력:
#   feature/SPEC-DEBATE-001
#   feature/SPEC-FOUNDATION-001
# * feature/SPEC-REPLAY-001  ← 현재 위치
#   feature/SPEC-SOFTQ-001
#   main
#   master

# 변경사항 확인
git status
# 출력: "nothing to commit, working tree clean" 확인

# 커밋 히스토리 확인
git log --oneline -5
# 출력:
# 8007779 docs(integration): Add Phase 0-3.3 final integration report
# 76952d0 docs(SPEC-REPLAY-001): Add final verification report
# 2e14670 docs(SPEC-REPLAY-001): Sync Living Document
# d17ff55 feat(SPEC-REPLAY-001): Implement Experience Replay Buffer
# ea4913a feat(SPEC-REPLAY-001): Add specification
```

**확인 사항**:
- ✅ 모든 변경사항이 커밋되었는지 확인
- ✅ working tree가 clean한지 확인
- ✅ 최신 커밋이 통합 보고서인지 확인

---

### 1.2 백업 생성 (안전장치)

```bash
# 현재 상태 백업 태그 생성
git tag backup-before-integration-$(date +%Y%m%d-%H%M%S)

# 예시:
# backup-before-integration-20251009-162500

# 백업 확인
git tag | grep backup
```

**목적**: 통합 중 문제 발생 시 즉시 복구 가능

---

### 1.3 Master 브랜치로 전환

```bash
# master 브랜치로 전환
git checkout master

# 출력:
# Switched to branch 'master'
# Your branch is up to date with 'origin/master'.

# 현재 커밋 확인
git log --oneline -3
# 출력: master 브랜치의 마지막 커밋들
```

**주의**: master 브랜치가 최신 상태인지 확인 (원격과 동기화)

---

### 1.4 Phase 0 (Foundation) 통합

```bash
# Phase 0 브랜치 머지
git merge feature/SPEC-FOUNDATION-001 --no-ff

# --no-ff: Fast-forward 하지 않고 머지 커밋 생성
# 이유: 각 Phase를 명확히 구분하기 위함
```

#### 예상 출력
```
Merge made by the 'recursive' strategy.
 apps/api/env_manager.py                           | 15 ++++++++++
 apps/orchestration/src/langgraph_pipeline.py      | 45 +++++++++++++++++++++++
 tests/unit/test_feature_flags.py                  | 32 ++++++++++++++++++
 tests/integration/test_pipeline_steps.py          | 67 +++++++++++++++++++++++++++++++++++
 4 files changed, 159 insertions(+)
```

#### 충돌 발생 시
```bash
# 충돌 확인
git status
# 출력: "both modified: 파일명" 표시

# 충돌 파일 수동 편집
# <<<<<<< HEAD
# 현재 브랜치 내용
# =======
# 머지하려는 브랜치 내용
# >>>>>>> feature/SPEC-FOUNDATION-001

# 충돌 해결 후
git add <충돌_파일명>
git commit
```

**하지만**: Phase 0-3.3은 순차적으로 구현되어 충돌 가능성 **매우 낮음**

#### 검증
```bash
# 머지 후 테스트 실행
python3 -m pytest tests/unit/test_feature_flags.py -v

# 출력:
# ========================= 7 passed in 0.5s =========================

# 커밋 히스토리 확인
git log --oneline --graph -5
# 출력: 머지 커밋이 그래프로 표시됨
```

---

### 1.5 Phase 3.1 (Soft Q-learning) 통합

```bash
# Phase 3.1 브랜치 머지
git merge feature/SPEC-SOFTQ-001 --no-ff

# 예상 출력
Merge made by the 'recursive' strategy.
 apps/orchestration/src/bandit/q_learning.py       | 156 ++++++++++++++++
 tests/unit/test_q_learning.py                     | 95 ++++++++++++
 2 files changed, 251 insertions(+)
```

#### 검증
```bash
# Q-learning 테스트 실행
python3 -m pytest tests/unit/test_q_learning.py -v

# Feature Flag 확인
python3 -c "from apps.api.env_manager import get_env_manager; print(get_env_manager().get_feature_flags()['soft_q_bandit'])"
# 출력: False (기본값)
```

---

### 1.6 Phase 3.2 (Debate Mode) 통합

```bash
# Phase 3.2 브랜치 머지
git merge feature/SPEC-DEBATE-001 --no-ff

# 예상 출력
Merge made by the 'recursive' strategy.
 apps/orchestration/src/debate/debate_engine.py    | 318 +++++++++++++++++++
 apps/orchestration/src/debate/agent_prompts.py    | 84 ++++++
 tests/unit/test_debate_engine.py                  | 339 +++++++++++++++++++++
 tests/integration/test_debate_integration.py      | 327 +++++++++++++++++++
 4 files changed, 1068 insertions(+)
```

**주의**: Phase 3.2는 Phase 3.1을 이미 포함하고 있음 (59ce583 커밋)
- 중복 머지 가능성: Git이 자동으로 처리 (이미 포함된 커밋은 스킵)

#### 검증
```bash
# Debate 테스트 실행
python3 -m pytest tests/unit/test_debate_engine.py -v
python3 -m pytest tests/integration/test_debate_integration.py -v

# 출력:
# ========================= 16 passed in 5.2s =========================
```

---

### 1.7 Phase 3.3 (Experience Replay) 통합

```bash
# Phase 3.3 브랜치 머지 (현재 브랜치)
git merge feature/SPEC-REPLAY-001 --no-ff

# 예상 출력
Merge made by the 'recursive' strategy.
 apps/orchestration/src/bandit/replay_buffer.py    | 113 ++++++++++++++++
 apps/orchestration/src/bandit/q_learning.py       | 50 ++++++++ (추가)
 apps/orchestration/src/langgraph_pipeline.py      | 60 ++++++++ (수정)
 tests/unit/test_replay_buffer.py                  | 64 +++++++++++
 tests/integration/test_pipeline_replay.py         | 52 +++++++++++
 .moai/reports/final-integration-phase-0-3.3.md    | 521 ++++++++++++++++
 7 files changed, 860 insertions(+)
```

#### 검증
```bash
# 전체 통합 테스트 실행
python3 -m pytest tests/unit/test_replay_buffer.py tests/unit/test_q_learning.py tests/integration/test_pipeline_replay.py -v

# 출력:
# ========================= 9 passed in 1.5s =========================

# 전체 테스트 실행 (선택적, 시간 소요)
python3 -m pytest tests/integration/ -v --tb=short

# 출력:
# ========================= 35 passed in 15s =========================
```

---

### 1.8 최종 검증

```bash
# 전체 커밋 그래프 확인
git log --oneline --graph --all | head -30

# 예상 출력:
# *   abc1234 Merge branch 'feature/SPEC-REPLAY-001' into master
# |\
# | * 8007779 docs(integration): Add Phase 0-3.3 final integration report
# | * 76952d0 docs(SPEC-REPLAY-001): Add final verification report
# | * 2e14670 docs(SPEC-REPLAY-001): Sync Living Document
# | * d17ff55 feat(SPEC-REPLAY-001): Implement Experience Replay Buffer
# | * ea4913a feat(SPEC-REPLAY-001): Add specification
# |/
# *   def5678 Merge branch 'feature/SPEC-DEBATE-001' into master
# |\
# ...

# 브랜치 정리 (선택적)
git branch -d feature/SPEC-FOUNDATION-001
git branch -d feature/SPEC-SOFTQ-001
git branch -d feature/SPEC-DEBATE-001
git branch -d feature/SPEC-REPLAY-001

# 주의: 원격에 push하지 않았다면 브랜치 유지 권장
```

#### 최종 파일 구조 확인
```bash
# 구현 파일 확인
ls -la apps/api/env_manager.py
ls -la apps/orchestration/src/bandit/
ls -la apps/orchestration/src/debate/

# 테스트 파일 확인
ls -la tests/unit/test_*replay*.py
ls -la tests/integration/test_pipeline_replay.py

# 문서 확인
ls -la .moai/reports/final-integration-phase-0-3.3.md
```

---

## 2. 프로덕션 환경 설정

### 2.1 시스템 요구사항 확인

#### Python 환경
```bash
# Python 버전 확인
python3 --version
# 필요: Python 3.11+
# 출력 예시: Python 3.12.3

# pip 업데이트
python3 -m pip install --upgrade pip
```

#### PostgreSQL 설정
```bash
# PostgreSQL 버전 확인
psql --version
# 필요: PostgreSQL 15+
# 출력 예시: psql (PostgreSQL) 15.4

# pgvector extension 확인
psql -U postgres -d dt_rag -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
# 출력: vector 확장이 설치되어 있어야 함

# 없다면 설치
psql -U postgres -d dt_rag -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

#### 의존성 설치
```bash
# 프로덕션 의존성 설치
pip install -r requirements.txt

# 주요 패키지 확인
pip list | grep -E "(fastapi|uvicorn|sqlalchemy|langchain|psycopg)"

# 출력 예시:
# fastapi==0.104.1
# uvicorn==0.24.0
# sqlalchemy==2.0.23
# langchain==0.1.0
# psycopg[binary]==3.1.13
```

---

### 2.2 환경 변수 설정

#### 프로덕션 환경 변수 파일 생성
```bash
# .env.production 파일 생성
cat > .env.production << 'EOF'
# ====================================
# DT-RAG 프로덕션 환경 변수
# ====================================

# 환경 설정
ENVIRONMENT=production

# 데이터베이스 (PostgreSQL)
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/dt_rag

# Gemini LLM API
GEMINI_API_KEY=your_actual_gemini_api_key_here

# 보안 설정
SECRET_KEY=your_secure_random_secret_key_here_min_32_chars

# Feature Flags (Phase별 단계적 활성화)
FEATURE_SOFT_Q_BANDIT=false
FEATURE_DEBATE_MODE=false
FEATURE_EXPERIENCE_REPLAY=false
FEATURE_META_PLANNER=false
FEATURE_MCP_TOOLS=false
FEATURE_NEURAL_CASE_SELECTOR=false
FEATURE_TOOLS_POLICY=false

# 성능 설정
DB_POOL_SIZE=50
DB_MAX_OVERFLOW=100
WORKER_PROCESSES=8

# 로깅
LOG_LEVEL=WARNING

# Redis (선택적, 캐싱용)
# REDIS_URL=redis://localhost:6379/0
EOF

# 권한 설정 (보안)
chmod 600 .env.production
```

#### 환경 변수 로드
```bash
# 방법 1: export 사용 (현재 세션만)
export $(cat .env.production | grep -v '^#' | xargs)

# 방법 2: source 사용 (권장)
set -a
source .env.production
set +a

# 확인
echo $ENVIRONMENT
# 출력: production

echo $FEATURE_EXPERIENCE_REPLAY
# 출력: false
```

**중요**: `.env.production` 파일은 **절대 Git에 커밋하지 않음** (`.gitignore`에 추가)

---

### 2.3 데이터베이스 마이그레이션

#### Alembic 설정 확인
```bash
# Alembic 버전 확인
alembic --version
# 출력: alembic 1.12.0

# 현재 마이그레이션 상태 확인
alembic current
# 출력: 현재 적용된 revision

# 대기 중인 마이그레이션 확인
alembic history
```

#### 마이그레이션 실행
```bash
# 프로덕션 데이터베이스로 마이그레이션
export DATABASE_URL=postgresql+asyncpg://username:password@prod-host:5432/dt_rag

# 모든 마이그레이션 적용
alembic upgrade head

# 예상 출력:
# INFO  [alembic.runtime.migration] Running upgrade abc123 -> def456, Add experience_replay table
# INFO  [alembic.runtime.migration] Running upgrade def456 -> ghi789, Add q_table column
```

#### 마이그레이션 검증
```bash
# 데이터베이스 연결 테스트
python3 << 'EOF'
import asyncio
from apps.api.database import get_db_engine

async def test_connection():
    engine = await get_db_engine()
    async with engine.connect() as conn:
        result = await conn.execute("SELECT version();")
        print("✅ Database connected:", result.fetchone())

asyncio.run(test_connection())
EOF

# 출력:
# ✅ Database connected: ('PostgreSQL 15.4 ...',)
```

#### 백업 생성 (필수)
```bash
# 프로덕션 데이터베이스 백업
pg_dump -U username -h prod-host -d dt_rag -F c -f dt_rag_backup_$(date +%Y%m%d).dump

# 백업 확인
ls -lh dt_rag_backup_*.dump
# 출력: -rw-r--r-- 1 user user 150M Oct 09 16:30 dt_rag_backup_20251009.dump
```

---

### 2.4 애플리케이션 설정 검증

#### 설정 파일 확인
```bash
# Feature Flag 동작 테스트
python3 << 'EOF'
from apps.api.env_manager import get_env_manager

env_mgr = get_env_manager()

print("🔍 Environment:", env_mgr.current_env.value)
print("\n📋 Feature Flags:")
for flag, value in env_mgr.get_feature_flags().items():
    if flag.startswith(('soft_q', 'debate', 'experience', 'meta', 'mcp', 'neural', 'tools')):
        print(f"  {flag}: {value}")

print("\n🗄️ Database Config:")
db_config = env_mgr.get_database_config()
print(f"  Pool Size: {db_config['pool_size']}")
print(f"  Max Overflow: {db_config['max_overflow']}")
EOF

# 예상 출력:
# 🔍 Environment: production
#
# 📋 Feature Flags:
#   soft_q_bandit: False
#   debate_mode: False
#   experience_replay: False
#   meta_planner: False
#   mcp_tools: False
#   ...
#
# 🗄️ Database Config:
#   Pool Size: 50
#   Max Overflow: 100
```

#### 헬스 체크 엔드포인트 테스트
```bash
# 애플리케이션 시작 (백그라운드)
uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 &

# PID 저장
APP_PID=$!
echo $APP_PID > /tmp/dt_rag.pid

# 3초 대기 (앱 시작 시간)
sleep 3

# 헬스 체크
curl http://localhost:8000/health

# 예상 출력:
# {
#   "status": "healthy",
#   "version": "1.8.1",
#   "environment": "production"
# }

# 앱 종료 (테스트 후)
kill $APP_PID
```

---

## 3. 단계적 롤아웃 전략

### 3.1 Week 1: 베이스라인 설정 (모든 Flag OFF)

#### 목표
- 기존 동작 100% 유지
- 프로덕션 환경 안정성 확인
- 베이스라인 성능 지표 수집

#### 설정
```bash
# Week 1 Feature Flags (모두 OFF)
export FEATURE_SOFT_Q_BANDIT=false
export FEATURE_DEBATE_MODE=false
export FEATURE_EXPERIENCE_REPLAY=false
```

#### 모니터링 항목
```bash
# 1. 파이프라인 latency 측정
curl -X POST http://localhost:8000/api/v1/search/ \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key" \
  -d '{"q":"machine learning","final_topk":5}' \
  -w "\nTime: %{time_total}s\n"

# 예상: Time: ~2.5s (p95 baseline)

# 2. 메모리 사용량
ps aux | grep uvicorn | awk '{print $6/1024 " MB"}'

# 예상: ~500 MB (baseline)

# 3. 에러 로그 모니터링
tail -f logs/app.log | grep ERROR

# 예상: 에러 없음
```

#### 성공 기준
- ✅ API 응답 시간 p95 < 4s
- ✅ 에러율 < 0.1%
- ✅ 메모리 사용량 안정 (< 1GB)
- ✅ 기존 기능 100% 동작

---

### 3.2 Week 2: Experience Replay 활성화 (10% 트래픽)

#### 목표
- Experience Replay Buffer 실전 검증
- 학습 효율성 모니터링
- 부작용 조기 발견

#### 설정
```bash
# Week 2 Feature Flags
export FEATURE_SOFT_Q_BANDIT=false
export FEATURE_DEBATE_MODE=false
export FEATURE_EXPERIENCE_REPLAY=true  # ← 활성화

# 앱 재시작
kill $(cat /tmp/dt_rag.pid)
uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 &
echo $! > /tmp/dt_rag.pid
```

#### A/B 테스트 설정 (10% 트래픽)

**방법 1: Nginx 로드 밸런서** (권장)
```nginx
# /etc/nginx/sites-available/dt-rag
upstream dt_rag_backend {
    # 90% 트래픽: Feature Flag OFF
    server 127.0.0.1:8000 weight=9;

    # 10% 트래픽: Feature Flag ON
    server 127.0.0.1:8001 weight=1;
}

server {
    listen 80;
    server_name api.dt-rag.com;

    location / {
        proxy_pass http://dt_rag_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**방법 2: 애플리케이션 레벨 샘플링**
```python
# apps/orchestration/src/langgraph_pipeline.py 수정
import random

async def _save_experience_to_replay_buffer(self, state: PipelineState) -> None:
    flags = get_env_manager().get_feature_flags()

    # 10% 샘플링 (Week 2)
    if not flags.get("experience_replay", False) or random.random() > 0.1:
        return

    # 기존 로직...
```

#### 모니터링 (Week 2)
```bash
# 1. Replay Buffer 크기 모니터링
python3 << 'EOF'
from apps.orchestration.src.langgraph_pipeline import get_pipeline

pipeline = get_pipeline()
print(f"Replay Buffer Size: {len(pipeline.replay_buffer)}")
EOF

# 예상: 0 → 1000+ (1주일 동안 점진적 증가)

# 2. 메모리 증가 확인
ps aux | grep uvicorn | awk '{print $6/1024 " MB"}'

# 예상: 500 MB → 502 MB (~2MB 증가, 정상)

# 3. 파이프라인 latency 변화
# Baseline (Week 1): 2.5s
# Week 2: 2.52s (+ ~20ms overhead, 정상)

# 4. 에러 로그
tail -f logs/app.log | grep -E "(ERROR|Replay Buffer)"

# 예상: "Experience added to Replay Buffer" DEBUG 로그만 표시
```

#### 성공 기준 (Week 2)
- ✅ Replay Buffer 크기: 1000-5000 experiences
- ✅ 메모리 증가: < 5MB
- ✅ Latency 증가: < 50ms
- ✅ 에러율 변화: < 0.05%

---

### 3.3 Week 3: Soft Q-learning + Experience Replay (50% 트래픽)

#### 목표
- Soft Q-learning과 Experience Replay 통합 검증
- Q-table 수렴 관찰
- 검색 품질 개선 측정

#### 설정
```bash
# Week 3 Feature Flags
export FEATURE_SOFT_Q_BANDIT=true       # ← 활성화
export FEATURE_DEBATE_MODE=false
export FEATURE_EXPERIENCE_REPLAY=true   # ← 유지

# A/B 테스트: 50% 트래픽
# Nginx weight 조정: weight=5 (ON) vs weight=5 (OFF)
```

#### 모니터링 (Week 3)
```bash
# 1. Q-table 크기 및 수렴 확인
python3 << 'EOF'
from apps.orchestration.src.bandit.q_learning import get_q_learning

q_learning = get_q_learning()
print(f"Q-table Size: {len(q_learning.q_table)} states")

# Top 5 Q-values 출력 (수렴 확인)
for state, q_values in list(q_learning.q_table.items())[:5]:
    print(f"  {state[:20]}: {max(q_values):.3f}")
EOF

# 예상:
# Q-table Size: 50-100 states
#   query_high_conf_low: 0.850
#   query_med_conf_med_: 0.720
#   ...

# 2. Batch Learning 성공률
tail -f logs/app.log | grep "Batch update"

# 예상:
# INFO: Batch update completed: 32 samples, Q-table size: 75

# 3. 검색 품질 개선 (A/B 비교)
# Baseline (Feature OFF): precision@5 = 0.75
# Week 3 (Feature ON): precision@5 = 0.78 (+4% 개선 목표)
```

#### 성공 기준 (Week 3)
- ✅ Q-table 크기: 50-100 states
- ✅ Batch learning 성공률: > 95%
- ✅ 검색 품질 개선: precision@5 +2% 이상
- ✅ Latency 증가: < 100ms

---

### 3.4 Week 4: 100% 롤아웃 (전체 트래픽)

#### 목표
- 모든 트래픽에 새 기능 적용
- 안정성 최종 확인
- Debate Mode 준비 (선택적)

#### 설정
```bash
# Week 4 Feature Flags (100% 트래픽)
export FEATURE_SOFT_Q_BANDIT=true
export FEATURE_DEBATE_MODE=false        # 추후 Phase 4에서 활성화
export FEATURE_EXPERIENCE_REPLAY=true

# A/B 테스트 종료: 모든 서버에 동일 설정
```

#### 최종 검증
```bash
# 1. 전체 시스템 스트레스 테스트
ab -n 1000 -c 10 \
  -p query.json \
  -T "application/json" \
  -H "X-API-Key: your_api_key" \
  http://localhost:8000/api/v1/search/

# query.json:
# {"q":"artificial intelligence","final_topk":5}

# 예상:
# Requests per second: 20 req/s
# Time per request: 50ms (p50), 120ms (p95)

# 2. 24시간 모니터링
# - Replay Buffer 크기: 8000-10000 (FIFO 정상)
# - Q-table 크기: 100-108 (수렴)
# - 메모리: ~505 MB (안정)
# - 에러율: < 0.1%

# 3. 롤백 테스트 (안전장치)
export FEATURE_EXPERIENCE_REPLAY=false
export FEATURE_SOFT_Q_BANDIT=false

# 즉시 기존 동작으로 복귀 확인
curl http://localhost:8000/health
# 출력: "status": "healthy"
```

#### 성공 기준 (Week 4)
- ✅ 100% 트래픽 안정 처리
- ✅ 메모리 사용량: < 600 MB
- ✅ Latency p95: < 3.5s (개선)
- ✅ 검색 품질 개선: +5% 이상 (목표 달성)

---

## 4. 모니터링 및 검증

### 4.1 실시간 모니터링 대시보드

#### Prometheus + Grafana 설정 (권장)
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'dt-rag'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

#### 주요 메트릭
```python
# apps/api/main.py에 메트릭 추가
from prometheus_client import Counter, Histogram, Gauge

# Replay Buffer 크기
replay_buffer_size = Gauge(
    'replay_buffer_size',
    'Current size of Replay Buffer'
)

# Q-table 크기
q_table_size = Gauge(
    'q_table_size',
    'Number of states in Q-table'
)

# 파이프라인 latency
pipeline_latency = Histogram(
    'pipeline_latency_seconds',
    'Pipeline execution time',
    buckets=[0.5, 1.0, 2.0, 3.0, 4.0, 5.0]
)

# Batch learning 성공
batch_learning_success = Counter(
    'batch_learning_success_total',
    'Number of successful batch updates'
)
```

---

### 4.2 알람 설정

#### CloudWatch / Datadog 알람 예시
```yaml
# 1. 메모리 사용량 알람
alarm_memory_high:
  metric: memory_usage_mb
  threshold: 800
  condition: greater_than
  duration: 5_minutes
  action: email_team

# 2. Latency 알람
alarm_latency_high:
  metric: pipeline_latency_p95
  threshold: 5.0  # 5초
  condition: greater_than
  duration: 5_minutes
  action: email_team + slack_notification

# 3. 에러율 알람
alarm_error_rate:
  metric: error_rate_percent
  threshold: 1.0  # 1%
  condition: greater_than
  duration: 2_minutes
  action: page_oncall + email_team

# 4. Replay Buffer 메모리 누수
alarm_buffer_overflow:
  metric: replay_buffer_size
  threshold: 12000  # max_size=10000 초과
  condition: greater_than
  duration: 10_minutes
  action: email_team
```

---

### 4.3 로그 분석

#### 로그 레벨 설정
```python
# apps/orchestration/src/bandit/replay_buffer.py
import logging

# 프로덕션: INFO 레벨
logger.setLevel(logging.INFO)

# 주요 이벤트만 기록
logger.info(f"Replay Buffer initialized: max_size={self.max_size}")
logger.info(f"FIFO eviction: buffer_size={len(self.buffer)}")
logger.warning(f"Buffer add failed: {error}")
```

#### 로그 분석 쿼리 (ELK Stack)
```json
// Replay Buffer 추가 성공률
{
  "query": {
    "bool": {
      "must": [
        {"match": {"message": "Experience added"}},
        {"range": {"@timestamp": {"gte": "now-1h"}}}
      ]
    }
  },
  "aggs": {
    "success_rate": {
      "terms": {"field": "level.keyword"}
    }
  }
}

// 예상: INFO: 95%, WARNING: 5%
```

---

## 5. 롤백 절차

### 5.1 즉시 롤백 (긴급)

#### 시나리오: 프로덕션 에러율 급증

```bash
# 1. Feature Flag 즉시 OFF (0 downtime)
export FEATURE_EXPERIENCE_REPLAY=false
export FEATURE_SOFT_Q_BANDIT=false

# 2. 애플리케이션 재시작 불필요 (환경 변수 재로드)
# FastAPI는 다음 요청부터 새 설정 적용

# 3. 확인
curl http://localhost:8000/health
python3 -c "from apps.api.env_manager import get_env_manager; print(get_env_manager().get_feature_flags()['experience_replay'])"
# 출력: False

# 4. 모니터링
tail -f logs/app.log | grep ERROR
# 예상: 에러 감소 확인
```

**소요 시간**: **< 1분** (즉시 복구)

---

### 5.2 부분 롤백 (단계적)

#### 시나리오: Experience Replay만 문제

```bash
# 1. Experience Replay만 OFF
export FEATURE_EXPERIENCE_REPLAY=false

# 2. Soft Q-learning은 유지
export FEATURE_SOFT_Q_BANDIT=true

# 3. Nginx weight 조정 (50% 트래픽만 영향)
# 기존: weight=5 (ON) vs weight=5 (OFF)
# 변경: weight=0 (ON) vs weight=10 (OFF)

# 4. 10분 모니터링 후 결정
# - 문제 해결: weight 원복
# - 문제 지속: 전체 롤백
```

---

### 5.3 코드 롤백 (최후 수단)

#### 시나리오: 코드 버그 발견, Feature Flag로 해결 불가

```bash
# 1. 백업 태그로 롤백
git tag | grep backup-before-integration
# 출력: backup-before-integration-20251009-162500

# 2. 백업 시점으로 복원
git checkout backup-before-integration-20251009-162500

# 3. 강제 푸시 (주의: 팀 모드에서는 위험)
git push origin master --force

# 4. 애플리케이션 재배포
# ... (배포 프로세스 반복)
```

**주의**: 코드 롤백은 **최후의 수단**. Feature Flag 롤백이 우선.

---

### 5.4 롤백 후 조치

```bash
# 1. 근본 원인 분석
# - 로그 분석
# - 에러 재현
# - 코드 리뷰

# 2. 수정 및 재배포
# - 버그 수정
# - 테스트 추가
# - 다시 Week 1부터 롤아웃

# 3. 포스트모템 작성
# - 문제 원인
# - 영향 범위
# - 재발 방지책
```

---

## 6. 배포 체크리스트 (최종)

### 배포 전 (Pre-Deployment)
- [ ] 로컬 브랜치 통합 완료
- [ ] 모든 테스트 통과 (500+ tests)
- [ ] 환경 변수 설정 완료
- [ ] 데이터베이스 백업 생성
- [ ] 마이그레이션 스크립트 검증
- [ ] 모니터링 대시보드 준비
- [ ] 알람 설정 완료
- [ ] 롤백 절차 숙지

### Week 1 (Baseline)
- [ ] 모든 Feature Flag OFF
- [ ] 베이스라인 성능 측정 (latency, memory, error rate)
- [ ] 7일 모니터링 (안정성 확인)

### Week 2 (10% Rollout)
- [ ] Experience Replay ON (10% 트래픽)
- [ ] Replay Buffer 크기 모니터링
- [ ] 메모리 증가 < 5MB 확인
- [ ] Latency 증가 < 50ms 확인

### Week 3 (50% Rollout)
- [ ] Soft Q-learning + Experience Replay ON (50% 트래픽)
- [ ] Q-table 수렴 확인
- [ ] 검색 품질 개선 측정 (+2% 목표)
- [ ] Batch learning 성공률 > 95%

### Week 4 (100% Rollout)
- [ ] 100% 트래픽 전환
- [ ] 24시간 안정성 모니터링
- [ ] 최종 성능 벤치마크
- [ ] 롤백 테스트 실행 (안전장치)

### 배포 후 (Post-Deployment)
- [ ] 1주일 집중 모니터링
- [ ] 사용자 피드백 수집
- [ ] 성능 개선 측정 (목표: +5%)
- [ ] 포스트모템 작성 (문제 발생 시)

---

## 7. FAQ

### Q1: 브랜치 통합 시 충돌 발생하면?
**A**: Phase 0-3.3은 순차적으로 구현되어 충돌 가능성 매우 낮습니다. 만약 발생 시:
1. `git status`로 충돌 파일 확인
2. 수동으로 `<<<<<<<`, `=======`, `>>>>>>>` 마커 제거
3. `git add <파일>` 후 `git commit`

### Q2: Feature Flag 변경 시 재시작 필요?
**A**: **아니요**. 환경 변수 변경 후 다음 요청부터 자동 적용됩니다. 단, 애플리케이션 재시작 권장 (확실성).

### Q3: Replay Buffer 메모리 누수 의심 시?
**A**:
1. `len(replay_buffer)` 확인 → max_size=10000 초과 시 비정상
2. FIFO 정책 확인: 오래된 경험이 제거되는지 로그 확인
3. Python 메모리 프로파일러 사용: `memory_profiler`

### Q4: 롤백 후 다시 롤아웃?
**A**:
1. 근본 원인 분석 및 수정
2. 테스트 추가 (재발 방지)
3. Week 1부터 다시 단계적 롤아웃 (단, 기간 단축 가능)

### Q5: Debate Mode는 언제 활성화?
**A**: **Phase 4 권장**. Phase 3.3 안정화 후 (1-2주 후) 별도로 롤아웃.

---

**작성일**: 2025-10-09
**작성자**: @claude
**버전**: 1.0.0
**다음 업데이트**: Phase 4 Debate Mode 롤아웃 후
