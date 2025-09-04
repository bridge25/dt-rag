# Multi-stage Dockerfile for Dynamic Taxonomy RAG API
# 최적화된 프로덕션 배포용 컨테이너

# ==============================================================================
# Build Stage - 의존성 설치 및 애플리케이션 빌드
# ==============================================================================
FROM python:3.11-slim as builder

# 빌드 도구 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    pkg-config \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 최적화
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 작업 디렉토리 설정
WORKDIR /build

# requirements.txt 먼저 복사 (도커 캐시 최적화)
COPY dt-rag/requirements.txt .

# Python 패키지 설치
RUN pip install --user --no-cache-dir -r requirements.txt

# 추가 의존성 설치 (PDF 파싱, 임베딩 등)
RUN pip install --user --no-cache-dir \
    PyMuPDF==1.23.26 \
    beautifulsoup4==4.12.2 \
    python-multipart==0.0.6 \
    prometheus-client==0.19.0 \
    psutil==5.9.6 \
    pyyaml==6.0.1 \
    celery==5.3.4

# ==============================================================================
# Runtime Stage - 최소한의 런타임 환경
# ==============================================================================
FROM python:3.11-slim as runtime

# 비root 사용자 생성 (보안)
RUN groupadd -r dtrag && useradd -r -g dtrag dtrag

# 시스템 의존성 (런타임만)
RUN apt-get update && apt-get install -y \
    libpq5 \
    libssl3 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 환경 변수 설정
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PATH=/home/dtrag/.local/bin:$PATH

# 작업 디렉토리 및 권한 설정
WORKDIR /app
RUN chown dtrag:dtrag /app

# 빌드 단계에서 설치된 패키지 복사
COPY --from=builder --chown=dtrag:dtrag /root/.local /home/dtrag/.local

# 애플리케이션 코드 복사
COPY --chown=dtrag:dtrag dt-rag/ /app/

# 비root 사용자로 전환
USER dtrag

# 헬스체크 설정
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 포트 노출
EXPOSE 8000

# 애플리케이션 실행
CMD ["python", "-m", "uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# ==============================================================================
# 메타데이터
# ==============================================================================
LABEL maintainer="A팀 (Taxonomy & Data Platform)" \
      version="1.8.1" \
      description="Dynamic Taxonomy RAG API with ingestion pipeline" \
      org.opencontainers.image.source="https://github.com/team-a/dt-rag"