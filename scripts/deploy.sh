#!/bin/bash
# Dynamic Taxonomy RAG 배포 스크립트

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로깅 함수
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 배포 환경 (기본값: dev)
ENVIRONMENT=${1:-dev}
COMPOSE_FILE="docker-compose.yml"

# 환경별 설정
case $ENVIRONMENT in
    "dev")
        COMPOSE_PROFILE="dev"
        log_info "개발 환경으로 배포합니다"
        ;;
    "prod")
        COMPOSE_PROFILE=""
        log_info "프로덕션 환경으로 배포합니다"
        ;;
    *)
        log_error "지원하지 않는 환경입니다: $ENVIRONMENT (dev 또는 prod 사용)"
        exit 1
        ;;
esac

# 필수 파일 확인
log_info "배포 전 준비사항을 확인합니다..."

if [ ! -f ".env" ]; then
    log_warning ".env 파일이 없습니다. .env.example을 참고하여 생성하세요."
    if [ ! -f ".env.example" ]; then
        log_error ".env.example 파일도 찾을 수 없습니다."
        exit 1
    fi
    
    log_info ".env.example을 .env로 복사합니다..."
    cp .env.example .env
    log_warning ".env 파일의 API 키 등 설정값을 확인하고 수정하세요."
    
    # 프로덕션 환경이면 배포 중단
    if [ "$ENVIRONMENT" = "prod" ]; then
        log_error "프로덕션 배포 전에 .env 파일을 반드시 설정하세요."
        exit 1
    fi
fi

if [ ! -f "$COMPOSE_FILE" ]; then
    log_error "docker-compose.yml 파일을 찾을 수 없습니다."
    exit 1
fi

# Docker 및 Docker Compose 버전 확인
log_info "Docker 환경을 확인합니다..."

if ! command -v docker &> /dev/null; then
    log_error "Docker가 설치되어 있지 않습니다."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    log_error "Docker Compose가 설치되어 있지 않습니다."
    exit 1
fi

DOCKER_VERSION=$(docker --version)
COMPOSE_VERSION=$(docker-compose --version)
log_info "Docker: $DOCKER_VERSION"
log_info "Docker Compose: $COMPOSE_VERSION"

# 기존 컨테이너 정리 (선택적)
read -p "기존 컨테이너를 정리하시겠습니까? [y/N]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_info "기존 컨테이너를 정리합니다..."
    
    if [ -n "$COMPOSE_PROFILE" ]; then
        docker-compose --profile $COMPOSE_PROFILE down -v
    else
        docker-compose down -v
    fi
    
    # dangling 이미지 정리
    docker image prune -f
    log_success "컨테이너 정리 완료"
fi

# 이미지 빌드
log_info "Docker 이미지를 빌드합니다..."

if [ -n "$COMPOSE_PROFILE" ]; then
    docker-compose --profile $COMPOSE_PROFILE build --no-cache
else
    docker-compose build --no-cache
fi

log_success "이미지 빌드 완료"

# 데이터베이스 마이그레이션 준비
log_info "데이터베이스 마이그레이션을 준비합니다..."

# PostgreSQL 먼저 시작
docker-compose up -d postgres
log_info "PostgreSQL 시작 대기 중..."

# PostgreSQL 준비 상태 확인 (최대 60초)
timeout=60
counter=0

while [ $counter -lt $timeout ]; do
    if docker-compose exec -T postgres pg_isready -U postgres &> /dev/null; then
        log_success "PostgreSQL이 준비되었습니다"
        break
    fi
    
    echo -n "."
    sleep 1
    counter=$((counter + 1))
done

echo

if [ $counter -eq $timeout ]; then
    log_error "PostgreSQL 시작 타임아웃"
    exit 1
fi

# 마이그레이션 실행 (Alembic)
log_info "데이터베이스 마이그레이션을 실행합니다..."

# 임시 컨테이너로 마이그레이션 실행
docker-compose run --rm api alembic upgrade head

if [ $? -eq 0 ]; then
    log_success "데이터베이스 마이그레이션 완료"
else
    log_error "데이터베이스 마이그레이션 실패"
    exit 1
fi

# 전체 시스템 시작
log_info "전체 시스템을 시작합니다..."

if [ -n "$COMPOSE_PROFILE" ]; then
    docker-compose --profile $COMPOSE_PROFILE up -d
else
    docker-compose up -d
fi

# 서비스 상태 확인
log_info "서비스 상태를 확인합니다..."
sleep 10

# API 헬스체크
API_URL="http://localhost:8000"
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s "$API_URL/health" > /dev/null; then
        log_success "API 서비스가 정상적으로 시작되었습니다"
        break
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo -n "."
    sleep 2
done

echo

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    log_error "API 서비스 시작 확인 실패"
    log_info "로그를 확인하세요: docker-compose logs api"
    exit 1
fi

# 모니터링 서비스 확인
if curl -s "http://localhost:9090" > /dev/null; then
    log_success "Prometheus가 정상적으로 시작되었습니다 (포트 9090)"
else
    log_warning "Prometheus 시작 확인 실패"
fi

if curl -s "http://localhost:3000" > /dev/null; then
    log_success "Grafana가 정상적으로 시작되었습니다 (포트 3000)"
else
    log_warning "Grafana 시작 확인 실패"
fi

# 배포 완료 정보
echo
log_success "=== 배포 완료 ==="
echo
log_info "서비스 접속 정보:"
echo "  • API Server: http://localhost:8000"
echo "  • API Docs: http://localhost:8000/docs"
echo "  • Health Check: http://localhost:8000/health"
echo "  • Metrics: http://localhost:8000/metrics"
echo "  • Prometheus: http://localhost:9090"
echo "  • Grafana: http://localhost:3000 (admin/admin123)"

if [ "$ENVIRONMENT" = "dev" ]; then
    echo "  • pgAdmin: http://localhost:5050 (admin@dtrag.com/admin123)"
fi

echo
log_info "추가 명령어:"
echo "  • 로그 확인: docker-compose logs -f [service_name]"
echo "  • 서비스 재시작: docker-compose restart [service_name]"
echo "  • 전체 중지: docker-compose down"
echo "  • 볼륨까지 삭제: docker-compose down -v"

echo
log_success "배포가 성공적으로 완료되었습니다! 🎉"