#!/bin/bash
# @CODE:CICD-001:HOOK | SPEC: SPEC-CICD-001.md | Phase 2
# Install Git pre-commit hook for Python import validation
#
# USAGE: ./scripts/install-git-hooks.sh
#
# HISTORY:
# v0.0.1 (2025-01-24): INITIAL - Git hook installation script

set -e

echo "🔧 MoAI-ADK Git Hooks 설치 중..."
echo ""

# Get repository root (parent of dt-rag)
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
HOOKS_DIR="$REPO_ROOT/.git/hooks"
HOOK_FILE="$HOOKS_DIR/pre-commit"

# Check if .git directory exists
if [ ! -d "$REPO_ROOT/.git" ]; then
    echo "❌ 오류: Git 저장소를 찾을 수 없습니다."
    echo "   현재 디렉토리: $REPO_ROOT"
    exit 1
fi

# Backup existing pre-commit hook if exists
if [ -f "$HOOK_FILE" ]; then
    BACKUP_FILE="$HOOK_FILE.backup.$(date +%Y%m%d_%H%M%S)"
    echo "📦 기존 pre-commit hook 백업 중: $(basename "$BACKUP_FILE")"
    cp "$HOOK_FILE" "$BACKUP_FILE"
fi

# Create pre-commit hook
echo "📝 pre-commit hook 생성 중..."
cat > "$HOOK_FILE" << 'EOF'
#!/bin/bash
# @CODE:CICD-001:HOOK | SPEC: dt-rag/.moai/specs/SPEC-CICD-001/spec.md | Phase 2
# Git pre-commit hook for dt-rag Python import validation
#
# HISTORY:
# v0.0.1 (2025-01-24): INITIAL - Pre-commit import validation

# Check if any Python files in dt-rag are being committed
PYTHON_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep "^dt-rag/.*\.py$")

if [ -z "$PYTHON_FILES" ]; then
    # No Python files changed in dt-rag, skip validation
    exit 0
fi

echo "📝 Python 파일 변경 감지 - import 검증 실행 중..."
echo ""

# Run the import validator from dt-rag directory
cd dt-rag || exit 1

# Execute the import validator
python3 .claude/hooks/alfred/import-validator.py

# Capture exit code
EXIT_CODE=$?

# Return to repository root
cd ..

# Exit with the validator's exit code
exit $EXIT_CODE
EOF

# Make hook executable
chmod +x "$HOOK_FILE"

echo "✅ pre-commit hook 설치 완료!"
echo ""
echo "📍 설치 위치: $HOOK_FILE"
echo ""
echo "🧪 테스트 방법:"
echo "   1. dt-rag 디렉토리에서 Python 파일 수정"
echo "   2. git add <file>"
echo "   3. git commit -m \"test\""
echo ""
echo "⚠️  검증 건너뛰기 (권장하지 않음):"
echo "   git commit --no-verify"
echo ""
