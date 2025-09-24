# 🗃️ Dynamic Taxonomy RAG - 데이터베이스 설정 가이드

## 📋 시스템 요구사항

### 필수 소프트웨어
- PostgreSQL 15 이상
- pgvector extension
- Python 3.11 이상
- psycopg2-binary

## 🚀 1단계: PostgreSQL 설치

### Windows (권장)
```bash
# Windows 환경에서 PostgreSQL 설치
winget install PostgreSQL.PostgreSQL

# 또는 공식 설치파일 다운로드
# https://www.postgresql.org/download/windows/
```

### Ubuntu/WSL
```bash
# PostgreSQL 설치
sudo apt update
sudo apt install postgresql postgresql-contrib

# 서비스 시작
sudo service postgresql start
```

### macOS
```bash
# Homebrew를 사용한 설치
brew install postgresql@15
brew services start postgresql@15
```

## 🔧 2단계: pgvector Extension 설치

### Ubuntu/WSL
```bash
# 빌드 도구 설치
sudo apt install build-essential postgresql-server-dev-15

# pgvector 클론 및 빌드
git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
```

### Windows
```bash
# Docker를 사용한 pgvector 지원 PostgreSQL
docker run --name dt-rag-postgres -e POSTGRES_PASSWORD=password -p 5432:5432 -d pgvector/pgvector:pg15
```

### macOS
```bash
# Homebrew를 사용한 설치
brew install pgvector
```

## 🏗️ 3단계: 데이터베이스 초기화

### 데이터베이스 생성
```bash
# PostgreSQL 관리자로 접속
sudo -u postgres psql

# 데이터베이스 및 사용자 생성
CREATE DATABASE dt_rag;
CREATE USER dt_rag_user WITH PASSWORD 'secure_password_123';
GRANT ALL PRIVILEGES ON DATABASE dt_rag TO dt_rag_user;

# Extension 설치
\c dt_rag
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS btree_gist;

# 확인
\dx
\q
```

### 연결 테스트
```bash
# 연결 테스트
psql -h localhost -U dt_rag_user -d dt_rag -c "SELECT 1;"
```

## 📄 4단계: 스키마 마이그레이션

### 마이그레이션 실행
```bash
# 프로젝트 루트에서 실행
cd /path/to/dt-rag

# 순서대로 마이그레이션 실행
psql -h localhost -U dt_rag_user -d dt_rag -f migrations/0001_initial_schema.sql
psql -h localhost -U dt_rag_user -d dt_rag -f migrations/0002_span_range_and_indexes.sql
psql -h localhost -U dt_rag_user -d dt_rag -f migrations/0003_audit_hitl_ivfflat_and_rollback_proc.sql
```

### 스키마 검증
```bash
# 테이블 확인
psql -h localhost -U dt_rag_user -d dt_rag -c "\dt"

# 인덱스 확인
psql -h localhost -U dt_rag_user -d dt_rag -c "\di"

# Extension 확인
psql -h localhost -U dt_rag_user -d dt_rag -c "\dx"
```

## 🔑 5단계: 환경 변수 설정

### .env 파일 생성
```bash
# 프로젝트 루트에 .env 파일 생성
cat > .env << 'EOF'
# 데이터베이스 설정
DATABASE_URL=postgresql://dt_rag_user:secure_password_123@localhost:5432/dt_rag
TEST_DATABASE_URL=postgresql://dt_rag_user:secure_password_123@localhost:5432/dt_rag_test

# 환경 설정
DT_RAG_ENV=development
DEBUG=true

# API 키 (선택사항 - 개발환경에서는 fallback 모드 사용)
OPENAI_API_KEY=your_openai_api_key_here

# Redis (선택사항)
REDIS_URL=redis://localhost:6379
REDIS_ENABLED=false
EOF
```

### 권한 설정
```bash
chmod 600 .env
```

## 🧪 6단계: 연결 테스트

### Python 의존성 설치
```bash
# 필수 패키지 설치
pip install -r apps/api/requirements.txt
pip install psycopg2-binary asyncpg
```

### 연결 테스트 스크립트
```bash
# 테스트 스크립트 실행
python test_db_connection.py
```

### pytest 테스트
```bash
# 스키마 테스트 실행
cd tests
TEST_DATABASE_URL="postgresql://dt_rag_user:secure_password_123@localhost:5432/dt_rag" python -m pytest test_schema.py -v
```

## 🔧 문제 해결

### 일반적인 오류들

#### 1. 연결 거부 오류
```bash
# PostgreSQL 서비스 상태 확인
sudo service postgresql status

# 포트 확인
sudo netstat -tlnp | grep 5432

# 방화벽 확인 (Ubuntu)
sudo ufw status
```

#### 2. pgvector extension 없음
```bash
# Extension 재설치
sudo -u postgres psql -d dt_rag -c "DROP EXTENSION IF EXISTS vector; CREATE EXTENSION vector;"
```

#### 3. 권한 오류
```bash
# 사용자 권한 재설정
sudo -u postgres psql
GRANT ALL PRIVILEGES ON DATABASE dt_rag TO dt_rag_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO dt_rag_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO dt_rag_user;
```

#### 4. 테스트 데이터베이스 생성
```bash
# 테스트용 별도 데이터베이스
sudo -u postgres psql
CREATE DATABASE dt_rag_test;
GRANT ALL PRIVILEGES ON DATABASE dt_rag_test TO dt_rag_user;
\c dt_rag_test
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS btree_gist;
```

## 📊 성능 최적화

### PostgreSQL 설정 튜닝
```bash
# postgresql.conf 편집
sudo nano /etc/postgresql/15/main/postgresql.conf

# 추천 설정
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
```

### 인덱스 확인
```sql
-- 중요한 인덱스들이 생성되었는지 확인
SELECT indexname, tablename FROM pg_indexes WHERE schemaname = 'public';

-- 벡터 인덱스 상태 확인
SELECT * FROM pg_stat_user_indexes WHERE relname = 'embeddings';
```

## ✅ 설치 완료 체크리스트

- [ ] PostgreSQL 15+ 설치 완료
- [ ] pgvector extension 설치 완료
- [ ] dt_rag 데이터베이스 생성 완료
- [ ] dt_rag_user 사용자 생성 완료
- [ ] 마이그레이션 3개 파일 실행 완료
- [ ] .env 파일 설정 완료
- [ ] Python 의존성 설치 완료
- [ ] 연결 테스트 성공
- [ ] 스키마 테스트 통과

## 🆘 도움말

### 공식 문서
- [PostgreSQL 설치 가이드](https://www.postgresql.org/docs/15/installation.html)
- [pgvector 설치 가이드](https://github.com/pgvector/pgvector#installation)

### 지원
- GitHub Issues: 기술적 문제 신고
- 팀 연락처: database-team@company.com

---

**설치 완료 후 다음 명령어로 API 서버를 시작할 수 있습니다:**

```bash
cd apps/api
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```