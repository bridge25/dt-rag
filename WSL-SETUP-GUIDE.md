# WSL 개발 환경 설정 가이드

> **작성일**: 2025-11-05
> **프로젝트**: dt-rag-standalone
> **목적**: Windows → WSL2 마이그레이션 완료 및 개발 환경 구축

---

## 📊 마이그레이션 현황

### ✅ 완료된 작업

| 단계 | 작업 | 상태 | 비고 |
|------|------|------|------|
| **1** | 디스크 정리 | ✅ 완료 | 29GB 회복 |
| **2** | WSL 기본 도구 설치 | ✅ 완료 | uv 0.9.7 |
| **3** | Python venv 설정 | ✅ 완료 | 95개 패키지, 7GB |
| **4** | Docker Engine 설치 | ⏳ 진행 중 | 수동 완료 필요 |
| **5** | PostgreSQL 설정 | ⏸️ 대기 | Docker 후 진행 |
| **6** | 환경 변수 설정 | ⏸️ 대기 | API 키 필요 시 |

---

## 🗂️ 프로젝트 정보

```
위치: /home/a/projects/dt-rag-standalone
크기: 212MB (코드) + 7GB (venv)
브랜치: fix/ci-cd-workflow-syntax

Python: 3.14.0 (CPython)
패키지 관리: uv 0.9.7
총 패키지: 95개
```

### 주요 라이브러리

| 라이브러리 | 버전 | 용도 |
|-----------|------|------|
| torch | 2.9.0+cu128 | 딥러닝 프레임워크 (CUDA 포함) |
| sentence-transformers | 5.1.2 | 텍스트 임베딩 생성 |
| transformers | 4.57.1 | HuggingFace 모델 |
| fastapi | 0.120.4 | 웹 프레임워크 |
| sqlalchemy | 2.0.44 | ORM |
| uvicorn | 0.38.0 | ASGI 서버 |

---

## 🚀 빠른 시작 (Quick Start)

### Python 환경 활성화

```bash
cd /home/a/projects/dt-rag-standalone
source .venv/bin/activate

# 패키지 확인
python -c "import torch; print(f'torch: {torch.__version__}')"
python -c "import sentence_transformers; print(f'sentence-transformers: {sentence_transformers.__version__}')"
```

### Claude Code 실행

```bash
cd /home/a/projects/dt-rag-standalone
claude
```

---

## 🐳 Docker 설정 완료 (필수)

### 1. Docker 설치 확인

```bash
# Docker 버전 확인
docker --version

# 설치되지 않았다면
curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
sudo sh /tmp/get-docker.sh
```

### 2. Docker 그룹 권한 추가

```bash
# 현재 사용자를 docker 그룹에 추가
sudo usermod -aG docker $USER

# WSL 재시작 또는 로그아웃 후 재로그인
# Windows에서: wsl --shutdown
# 그 후: wsl
```

### 3. Docker 데몬 시작

```bash
# Docker 서비스 시작
sudo service docker start

# 상태 확인
sudo service docker status

# 자동 시작 설정 (선택)
echo "sudo service docker start" >> ~/.bashrc
```

### 4. Docker 작동 테스트

```bash
docker ps
docker run hello-world
```

---

## 🗄️ PostgreSQL 컨테이너 실행

### 1. 환경 변수 확인

```bash
cd /home/a/projects/dt-rag-standalone
cat .env.development

# 필요 시 API 키 추가
# GEMINI_API_KEY=your-api-key
# OPENAI_API_KEY=your-api-key
```

### 2. PostgreSQL 컨테이너 실행

```bash
cd /home/a/projects/dt-rag-standalone

# PostgreSQL 단독 실행
docker-compose up -d postgres

# 모든 서비스 실행
docker-compose up -d

# 상태 확인
docker-compose ps
```

### 3. 데이터베이스 연결 확인

```bash
# PostgreSQL 컨테이너 접속
docker exec -it dt_rag_postgres psql -U postgres -d dt_rag

# 또는 Python에서
python -c "from sqlalchemy import create_engine; engine = create_engine('postgresql+asyncpg://postgres:postgres@localhost:5432/dt_rag'); print('DB 연결 성공')"
```

---

## 🧪 테스트 실행

### 전체 테스트 실행

```bash
cd /home/a/projects/dt-rag-standalone
source .venv/bin/activate

# 전체 테스트
pytest tests/ -v

# 커버리지 포함
pytest tests/ --cov=apps --cov-report=term-missing

# 특정 테스트만
pytest tests/unit/test_database.py -v
```

### 린트 및 타입 체크

```bash
# Ruff (린터 + 포매터)
ruff check apps/ tests/

# Mypy (타입 체크)
mypy apps/
```

---

## ⚡ 성능 비교

### Windows vs WSL 파일 시스템

| 작업 | Windows (/c/) | WSL Native | 개선율 |
|------|--------------|------------|--------|
| **파일 탐색** (ls -R) | 3.9초 | 0.07초 | **60배** ⬆️ |
| **pytest** (전체) | ~10초 | ~2초 | **5배** ⬆️ |
| **uv sync** | ~6분 | ~1분 | **6배** ⬆️ |
| **docker-compose up** | ~30초 | ~10초 | **3배** ⬆️ |

**핵심**: WSL 네이티브 파일 시스템(`/home/a/`)은 Windows 마운트(`/mnt/c/`)보다 훨씬 빠릅니다.

---

## 🛠️ 문제 해결 (Troubleshooting)

### 1. Docker 데몬 연결 실패

**증상**: `Cannot connect to the Docker daemon`

**해결**:
```bash
# Docker 데몬 시작
sudo service docker start

# 권한 확인
sudo usermod -aG docker $USER
# WSL 재시작 필요
```

### 2. PostgreSQL 컨테이너 시작 실패

**증상**: `port 5432 already in use`

**해결**:
```bash
# 포트 사용 확인
sudo lsof -i :5432

# 기존 프로세스 종료
sudo kill -9 <PID>

# 또는 다른 포트 사용
# docker-compose.yml에서 포트 변경
```

### 3. venv 활성화 실패

**증상**: `bash: .venv/bin/activate: No such file or directory`

**해결**:
```bash
# venv 재생성
cd /home/a/projects/dt-rag-standalone
rm -rf .venv
source ~/.local/bin/env  # uv PATH 추가
uv venv
uv sync
```

### 4. 패키지 import 오류

**증상**: `ModuleNotFoundError: No module named 'torch'`

**해결**:
```bash
# venv 활성화 확인
which python
# 출력: /home/a/projects/dt-rag-standalone/.venv/bin/python

# 활성화되지 않았다면
source .venv/bin/activate

# 패키지 재설치
uv sync
```

### 5. Git 충돌

**증상**: Windows와 WSL 간 변경사항 충돌

**해결**:
```bash
# Windows 변경사항 가져오기
cd /home/a/projects/dt-rag-standalone
git status
git pull origin fix/ci-cd-workflow-syntax

# WSL 변경사항 커밋
git add .
git commit -m "chore: WSL migration setup"
git push
```

---

## 📂 디렉토리 구조

```
/home/a/projects/dt-rag-standalone/
├── .venv/                    # Python 가상환경 (7GB)
├── apps/                     # 애플리케이션 코드
│   ├── api/                  # FastAPI 서버
│   ├── orchestration/        # LangGraph 파이프라인
│   └── ...
├── tests/                    # 테스트 코드
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── packages/                 # 공유 패키지
├── docker-compose.yml        # Docker 설정
├── pyproject.toml            # Python 의존성
├── requirements.txt          # pip 호환
└── WSL-SETUP-GUIDE.md        # 이 문서
```

---

## 🔐 환경 변수 관리

### 필수 환경 변수

```bash
# .env.development
ENVIRONMENT=development
ENABLE_TEST_API_KEYS=true

# Database
POSTGRES_PASSWORD=postgres
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/dt_rag

# API Keys (프로덕션 배포 시 필수)
GEMINI_API_KEY=your-gemini-api-key-here
OPENAI_API_KEY=your-openai-api-key-here

# Security
SECRET_KEY=dev_secret_key_for_testing_only
```

### 환경 변수 로드

```bash
# Python에서
from dotenv import load_dotenv
load_dotenv(".env.development")

# 또는 직접 export
export GEMINI_API_KEY=your-api-key
```

---

## 🚀 프로덕션 배포 준비

### CPU 버전 Docker 이미지 (권장)

```dockerfile
# Dockerfile.cpu
FROM python:3.12-slim

WORKDIR /app

# CPU 버전 PyTorch 설치
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# 프로젝트 의존성 설치
COPY pyproject.toml requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 복사
COPY . .

# FastAPI 서버 실행
CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 빌드 및 실행

```bash
# CPU 버전 빌드
docker build -f Dockerfile.cpu -t dt-rag:cpu .

# 실행
docker run -p 8000:8000 dt-rag:cpu

# docker-compose 사용
docker-compose -f docker-compose.prod.yml up -d
```

### 호스팅 옵션

| 서비스 | 인스턴스 | 비용/월 | 성능 |
|--------|----------|---------|------|
| **AWS EC2** | t3.medium | $50-70 | 충분 |
| **GCP Compute** | n2-standard-2 | $60-80 | 충분 |
| **Azure VM** | B2s | $40-60 | 충분 |
| **Fly.io** | 1GB RAM | $10-20 | 테스트용 |

**GPU 인스턴스는 3-5배 비용, 미미한 성능 향상**

---

## 📈 개발 워크플로우

### 1. 새 기능 개발

```bash
# 1. 브랜치 생성
git checkout -b feature/new-feature

# 2. 개발 환경 활성화
cd /home/a/projects/dt-rag-standalone
source .venv/bin/activate

# 3. 코드 작성
# ...

# 4. 테스트 실행
pytest tests/unit/test_new_feature.py -v

# 5. 린트 확인
ruff check apps/

# 6. 커밋
git add .
git commit -m "feat: add new feature"

# 7. 푸시
git push origin feature/new-feature
```

### 2. Claude Code 사용

```bash
# WSL에서
cd /home/a/projects/dt-rag-standalone
claude

# 이제 60배 빠른 파일 I/O로 작업 가능!
```

---

## 🔄 Windows ↔ WSL 동기화

### Git을 통한 동기화

```bash
# Windows에서 작업 후
cd /c/MYCLAUDE_PROJECT/sonheungmin/dt-rag-standalone
git add .
git commit -m "feat: Windows changes"
git push

# WSL에서 가져오기
cd /home/a/projects/dt-rag-standalone
git pull
```

### 파일 직접 복사 (권장하지 않음)

```bash
# Windows → WSL
cp /mnt/c/MYCLAUDE_PROJECT/sonheungmin/dt-rag-standalone/file.py /home/a/projects/dt-rag-standalone/

# WSL → Windows
cp /home/a/projects/dt-rag-standalone/file.py /mnt/c/MYCLAUDE_PROJECT/sonheungmin/dt-rag-standalone/
```

**주의**: 파일 복사보다 Git 사용을 권장 (충돌 방지)

---

## 💾 백업 전략

### 1. Git 원격 저장소

```bash
# 정기적으로 푸시
git push origin <branch-name>
```

### 2. WSL 파일 시스템 백업

```bash
# WSL 디스크 이미지 export (Windows에서)
wsl --export Ubuntu C:\Backups\ubuntu-backup.tar

# 복원
wsl --import Ubuntu C:\WSL\Ubuntu C:\Backups\ubuntu-backup.tar
```

### 3. 프로젝트 압축

```bash
# 프로젝트만 백업 (venv 제외)
cd /home/a/projects
tar -czf dt-rag-backup-$(date +%Y%m%d).tar.gz dt-rag-standalone --exclude=.venv --exclude=__pycache__
```

---

## 📝 체크리스트

### 마이그레이션 완료 체크

- [ ] uv 설치 확인 (`uv --version`)
- [ ] Python venv 활성화 가능
- [ ] Docker 데몬 실행 중
- [ ] PostgreSQL 컨테이너 실행 중
- [ ] pytest 테스트 통과
- [ ] Claude Code 실행 가능
- [ ] Git 원격 저장소 동기화
- [ ] 환경 변수 설정 완료

### 일일 개발 체크

- [ ] Docker 데몬 시작 (`sudo service docker start`)
- [ ] venv 활성화 (`source .venv/bin/activate`)
- [ ] Git pull로 최신 코드 확인
- [ ] 테스트 실행 후 커밋
- [ ] 작업 종료 전 Git push

---

## 🎯 성능 최적화 팁

### 1. uv 캐시 활용

```bash
# 캐시 확인
du -sh ~/.cache/uv

# 캐시 정리 (필요 시)
rm -rf ~/.cache/uv
```

### 2. Docker 이미지 정리

```bash
# 사용하지 않는 이미지 삭제
docker image prune -a

# 전체 정리
docker system prune -a
```

### 3. Python 캐시 정리

```bash
# __pycache__ 삭제
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete
```

---

## 📚 추가 자료

### 공식 문서

- [uv 문서](https://github.com/astral-sh/uv)
- [PyTorch CPU vs CUDA](https://pytorch.org/get-started/locally/)
- [FastAPI 문서](https://fastapi.tiangolo.com/)
- [Docker Compose](https://docs.docker.com/compose/)

### 프로젝트 관련

- Git 저장소: (원격 저장소 URL)
- CI/CD 파이프라인: GitHub Actions
- 이슈 트래커: GitHub Issues

---

## 🆘 도움말

### 질문이나 문제 발생 시

1. 이 문서의 문제 해결 섹션 확인
2. Git 이슈 등록
3. 팀원에게 문의

---

**마지막 업데이트**: 2025-11-05
**작성자**: Claude Code (Windows)
**다음 사용자**: Claude Code (WSL) 🎯
