#!/bin/bash
# 자동 정리 설정 스크립트
# WSL .bashrc에 자동 실행 설정 추가

BASHRC="$HOME/.bashrc"
PROJECT_DIR="/home/a/projects/dt-rag-standalone"
CLEANUP_SCRIPT="$PROJECT_DIR/scripts/cleanup-system.sh"

echo "=========================================="
echo "자동 정리 설정 시작"
echo "=========================================="

# 1. .bashrc에 별칭 추가
if ! grep -q "alias cleanup=" "$BASHRC" 2>/dev/null; then
    echo "" >> "$BASHRC"
    echo "# 시스템 정리 별칭" >> "$BASHRC"
    echo "alias cleanup='bash $CLEANUP_SCRIPT'" >> "$BASHRC"
    echo "✅ cleanup 별칭 추가 완료"
else
    echo "⏭️  cleanup 별칭 이미 존재"
fi

# 2. 주간 정리 알림 추가 (선택)
if ! grep -q "weekly-cleanup-reminder" "$BASHRC" 2>/dev/null; then
    cat >> "$BASHRC" << 'EOF'

# 주간 정리 알림 (매주 월요일)
weekly-cleanup-reminder() {
    local last_cleanup_file="$HOME/.last_cleanup"
    local current_date=$(date +%Y%m%d)

    if [ -f "$last_cleanup_file" ]; then
        local last_cleanup=$(cat "$last_cleanup_file")
        local days_since=$((( $(date +%s) - $(date -d "${last_cleanup:0:4}-${last_cleanup:4:2}-${last_cleanup:6:2}" +%s) ) / 86400))

        if [ "$days_since" -gt 7 ]; then
            echo "⚠️  마지막 시스템 정리: ${days_since}일 전"
            echo "💡 정리 실행: cleanup"
        fi
    else
        echo "$current_date" > "$last_cleanup_file"
    fi
}
EOF
    echo "✅ 주간 정리 알림 추가 완료"
else
    echo "⏭️  주간 정리 알림 이미 존재"
fi

# 3. 디스크 사용률 경고 함수 추가
if ! grep -q "disk-usage-warning" "$BASHRC" 2>/dev/null; then
    cat >> "$BASHRC" << 'EOF'

# 디스크 사용률 경고
disk-usage-warning() {
    local disk_usage=$(df -h ~ | tail -1 | awk '{print $5}' | sed 's/%//')

    if [ "$disk_usage" -gt 85 ]; then
        echo "🚨 디스크 사용률: ${disk_usage}% (85% 초과!)"
        echo "💡 정리 권장: cleanup"
    fi
}

# 로그인 시 자동 체크 (주석 해제하여 활성화)
# disk-usage-warning
EOF
    echo "✅ 디스크 경고 함수 추가 완료"
else
    echo "⏭️  디스크 경고 함수 이미 존재"
fi

# 4. 프로젝트 디렉토리 진입 시 자동 Docker 시작 (선택)
if ! grep -q "auto-start-docker" "$BASHRC" 2>/dev/null; then
    cat >> "$BASHRC" << 'EOF'

# 프로젝트 디렉토리 진입 시 Docker 자동 시작
cdp() {
    cd "$1"
    if [ "$(basename $(pwd))" = "dt-rag-standalone" ]; then
        # Docker 데몬 확인
        if ! docker ps &> /dev/null; then
            echo "🐳 Docker 데몬 시작 중..."
            sudo service docker start &> /dev/null
        fi
    fi
}
EOF
    echo "✅ Docker 자동 시작 함수 추가 완료"
else
    echo "⏭️  Docker 자동 시작 함수 이미 존재"
fi

echo ""
echo "=========================================="
echo "설정 완료!"
echo "=========================================="
echo ""
echo "📝 추가된 기능:"
echo "  1. cleanup         - 시스템 정리 실행"
echo "  2. weekly-cleanup-reminder() - 주간 정리 알림"
echo "  3. disk-usage-warning()     - 디스크 경고"
echo "  4. cdp <dir>       - Docker 자동 시작 cd"
echo ""
echo "🔄 적용하려면 다음 명령 실행:"
echo "  source ~/.bashrc"
echo ""
echo "✅ 또는 WSL 재시작:"
echo "  wsl --shutdown (Windows에서)"
echo "  wsl (재시작)"
echo ""
