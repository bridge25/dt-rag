#!/bin/bash
# 시스템 자동 정리 스크립트
# 작성: 2025-11-05
# 목적: WSL 크래시 덤프, Python 캐시, 임시 파일 자동 정리

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 로그 함수
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 디스크 사용량 체크
check_disk_usage() {
    local disk_usage=$(df -h ~ | tail -1 | awk '{print $5}' | sed 's/%//')
    log_info "현재 디스크 사용률: ${disk_usage}%"

    if [ "$disk_usage" -gt 90 ]; then
        log_error "디스크 사용률이 90%를 초과했습니다! 긴급 정리 필요"
        return 1
    elif [ "$disk_usage" -gt 80 ]; then
        log_warn "디스크 사용률이 80%를 초과했습니다. 정리 권장"
        return 0
    else
        log_info "디스크 사용률 정상"
        return 0
    fi
}

# WSL 크래시 덤프 정리
cleanup_wsl_crashes() {
    log_info "WSL 크래시 덤프 정리 시작..."

    local crash_dir="/tmp/wsl-crashes"
    if [ -d "$crash_dir" ]; then
        local before_size=$(du -sh "$crash_dir" 2>/dev/null | cut -f1)

        # 7일 이상 된 덤프 파일 삭제
        find "$crash_dir" -name "*.dmp" -mtime +7 -delete 2>/dev/null

        local after_size=$(du -sh "$crash_dir" 2>/dev/null | cut -f1)
        log_info "크래시 덤프: $before_size → $after_size"
    else
        log_info "크래시 덤프 디렉토리 없음 (정상)"
    fi
}

# Python 캐시 정리
cleanup_python_cache() {
    log_info "Python 캐시 정리 시작..."

    local project_dirs=(
        "/c/MYCLAUDE_PROJECT/sonheungmin"
        "/home/a/projects"
    )

    local total_cleaned=0

    for dir in "${project_dirs[@]}"; do
        if [ -d "$dir" ]; then
            # __pycache__ 디렉토리 삭제 (30일 이상 미사용)
            local cleaned=$(find "$dir" -type d -name "__pycache__" -mtime +30 -exec du -sk {} \; 2>/dev/null | awk '{sum+=$1} END {print sum/1024}')
            find "$dir" -type d -name "__pycache__" -mtime +30 -exec rm -rf {} + 2>/dev/null

            # .pytest_cache 삭제
            find "$dir" -type d -name ".pytest_cache" -mtime +30 -exec rm -rf {} + 2>/dev/null

            if [ ! -z "$cleaned" ]; then
                total_cleaned=$(echo "$total_cleaned + $cleaned" | bc)
            fi
        fi
    done

    log_info "Python 캐시 정리 완료: ${total_cleaned}MB"
}

# 임시 파일 정리
cleanup_temp_files() {
    log_info "임시 파일 정리 시작..."

    # Office 임시 파일
    find /tmp -maxdepth 1 -name "~DF*.TMP" -mtime +1 -delete 2>/dev/null
    find /tmp -name "TCD*.tmp" -mtime +7 -delete 2>/dev/null

    # Node.js 컴파일 캐시 (오래된 것만)
    if [ -d "/tmp/node-compile-cache" ]; then
        find /tmp/node-compile-cache -mtime +30 -delete 2>/dev/null
    fi

    log_info "임시 파일 정리 완료"
}

# Claude Code 세션 로그 정리
cleanup_claude_logs() {
    log_info "Claude Code 세션 로그 정리 시작..."

    local claude_dir="$HOME/.claude"
    if [ -d "$claude_dir" ]; then
        # 30일 이상 된 디버그 로그 삭제
        find "$claude_dir/debug" -name "*.txt" -mtime +30 -delete 2>/dev/null

        # 큰 세션 파일 확인 (10MB 이상)
        local large_sessions=$(find "$claude_dir/projects" -name "*.jsonl" -size +10M 2>/dev/null | wc -l)
        if [ "$large_sessions" -gt 0 ]; then
            log_warn "10MB 이상의 세션 파일 ${large_sessions}개 발견 (수동 확인 권장)"
        fi

        log_info "Claude Code 로그 정리 완료"
    fi
}

# Docker 정리 (선택)
cleanup_docker() {
    if command -v docker &> /dev/null; then
        log_info "Docker 정리 시작..."

        # 사용하지 않는 이미지만 정리
        docker image prune -f 2>/dev/null || log_warn "Docker 데몬 연결 실패"

        log_info "Docker 정리 완료"
    fi
}

# 메인 실행
main() {
    log_info "=========================================="
    log_info "시스템 자동 정리 시작: $(date)"
    log_info "=========================================="

    # 디스크 사용량 체크
    check_disk_usage

    # 각종 정리 작업
    cleanup_wsl_crashes
    cleanup_python_cache
    cleanup_temp_files
    cleanup_claude_logs
    cleanup_docker

    # 최종 디스크 사용량
    log_info "=========================================="
    log_info "정리 완료: $(date)"
    check_disk_usage
    df -h ~ | grep -E "(Filesystem|/c)"
    log_info "=========================================="
}

# 스크립트 실행
main "$@"
