#!/bin/bash
# =============================================================================
# test-with-postgres.sh - Run tests with PostgreSQL test environment
# =============================================================================
#
# Usage:
#   ./scripts/test-with-postgres.sh           # Run all tests
#   ./scripts/test-with-postgres.sh unit      # Run unit tests only
#   ./scripts/test-with-postgres.sh integration  # Run integration tests only
#   ./scripts/test-with-postgres.sh -v        # Verbose output
#   ./scripts/test-with-postgres.sh --keep    # Keep containers running after tests
#
# Environment Variables:
#   TEST_DATABASE_URL - Override database URL
#   TEST_REDIS_URL - Override Redis URL
#   COVERAGE_THRESHOLD - Minimum coverage (default: 80)
#
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="docker-compose.test.yml"
DOCKER_COMPOSE="docker-compose -f ${COMPOSE_FILE}"
COVERAGE_THRESHOLD="${COVERAGE_THRESHOLD:-80}"

# Default test paths
TEST_PATHS="apps/api tests/"
VERBOSE=""
KEEP_CONTAINERS=false
TEST_TYPE="all"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        unit)
            TEST_PATHS="tests/unit"
            TEST_TYPE="unit"
            shift
            ;;
        integration)
            TEST_PATHS="tests/integration"
            TEST_TYPE="integration"
            shift
            ;;
        e2e)
            TEST_PATHS="tests/e2e"
            TEST_TYPE="e2e"
            shift
            ;;
        -v|--verbose)
            VERBOSE="-v"
            shift
            ;;
        --keep)
            KEEP_CONTAINERS=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [unit|integration|e2e] [-v|--verbose] [--keep]"
            echo ""
            echo "Options:"
            echo "  unit          Run unit tests only"
            echo "  integration   Run integration tests only"
            echo "  e2e           Run end-to-end tests only"
            echo "  -v, --verbose Verbose output"
            echo "  --keep        Keep containers running after tests"
            echo "  -h, --help    Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Functions
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

cleanup() {
    if [ "$KEEP_CONTAINERS" = false ]; then
        log_info "Stopping test containers..."
        cd "$PROJECT_ROOT"
        $DOCKER_COMPOSE down -v --remove-orphans 2>/dev/null || true
    else
        log_warning "Containers kept running (--keep flag). Run 'docker-compose -f docker-compose.test.yml down -v' to stop."
    fi
}

wait_for_postgres() {
    local max_attempts=30
    local attempt=1

    log_info "Waiting for PostgreSQL to be ready..."

    while [ $attempt -le $max_attempts ]; do
        if docker exec norade_postgres_test pg_isready -U postgres -d dt_rag_test &>/dev/null; then
            log_success "PostgreSQL is ready!"
            return 0
        fi
        echo -n "."
        sleep 1
        attempt=$((attempt + 1))
    done

    echo ""
    log_error "PostgreSQL failed to start within ${max_attempts} seconds"
    return 1
}

wait_for_redis() {
    local max_attempts=15
    local attempt=1

    log_info "Waiting for Redis to be ready..."

    while [ $attempt -le $max_attempts ]; do
        if docker exec norade_redis_test redis-cli ping &>/dev/null; then
            log_success "Redis is ready!"
            return 0
        fi
        echo -n "."
        sleep 1
        attempt=$((attempt + 1))
    done

    echo ""
    log_error "Redis failed to start within ${max_attempts} seconds"
    return 1
}

# Trap for cleanup on exit
trap cleanup EXIT

# Main execution
main() {
    cd "$PROJECT_ROOT"

    echo ""
    echo "=============================================="
    echo "  Norade Test Runner (PostgreSQL Backend)"
    echo "=============================================="
    echo ""

    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi

    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        exit 1
    fi

    # Stop any existing test containers
    log_info "Cleaning up existing test containers..."
    $DOCKER_COMPOSE down -v --remove-orphans 2>/dev/null || true

    # Start test containers
    log_info "Starting test containers..."
    $DOCKER_COMPOSE up -d

    # Wait for services
    wait_for_postgres || exit 1
    wait_for_redis || exit 1

    # Set environment variables
    export DATABASE_URL="${TEST_DATABASE_URL:-postgresql+asyncpg://postgres:postgres@localhost:5433/dt_rag_test}"
    export REDIS_URL="${TEST_REDIS_URL:-redis://localhost:6380}"
    export SECRET_KEY="test-secret-key-for-testing"
    export ENVIRONMENT="test"

    log_info "Environment configured:"
    log_info "  DATABASE_URL: $DATABASE_URL"
    log_info "  REDIS_URL: $REDIS_URL"
    log_info "  TEST_TYPE: $TEST_TYPE"
    echo ""

    # Run Alembic migrations
    log_info "Running database migrations..."
    cd "$PROJECT_ROOT"

    if [ -f "alembic.ini" ]; then
        alembic upgrade head
        log_success "Migrations completed"
    else
        log_warning "No alembic.ini found, skipping migrations"
    fi

    # Run tests
    log_info "Running ${TEST_TYPE} tests..."
    echo ""

    pytest_args=(
        $TEST_PATHS
        --cov=apps/api
        --cov-report=term-missing
        --cov-report=html:htmlcov
        --cov-report=xml:coverage.xml
        --cov-fail-under=$COVERAGE_THRESHOLD
        $VERBOSE
        --tb=short
    )

    if pytest "${pytest_args[@]}"; then
        echo ""
        log_success "All tests passed!"
        log_info "Coverage report: htmlcov/index.html"
        exit 0
    else
        echo ""
        log_error "Some tests failed!"
        exit 1
    fi
}

main
