#!/bin/bash
# Railway API Token Setup Guide
#
# 1. Railway 대시보드 접속: https://railway.app
# 2. 우측 상단 프로필 → Account Settings
# 3. Tokens 탭 → "Create Token" 클릭
# 4. 토큰 이름 입력 (예: "dt-rag-deployment")
# 5. 생성된 토큰을 복사
# 6. 아래 명령 실행:
#
#    export RAILWAY_TOKEN="복사한_토큰"
#    railway whoami  # 인증 확인
#
# 7. 영구 저장 (선택사항):
#    echo 'export RAILWAY_TOKEN="복사한_토큰"' >> ~/.bashrc
#    source ~/.bashrc

echo "Railway Token Setup Instructions"
echo "================================="
echo ""
echo "Step 1: Visit https://railway.app/account/tokens"
echo "Step 2: Click 'Create Token'"
echo "Step 3: Copy the generated token"
echo "Step 4: Run: export RAILWAY_TOKEN='<your-token>'"
echo "Step 5: Verify: railway whoami"
echo ""
echo "Then you can run:"
echo "  railway run psql \$DATABASE_URL -c \"CREATE EXTENSION IF NOT EXISTS vector;\""
