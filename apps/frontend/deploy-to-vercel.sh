#!/bin/bash
# Vercel CLI 배포 스크립트
# 사용법: bash deploy-to-vercel.sh

set -e  # 에러 발생 시 중단

echo "========================================="
echo "🚀 Vercel Frontend 배포 시작"
echo "========================================="
echo ""

# 현재 디렉토리 확인
echo "📁 현재 디렉토리: $(pwd)"
if [[ ! -f "package.json" ]]; then
    echo "❌ 에러: apps/frontend 디렉토리에서 실행하세요"
    exit 1
fi

echo "✅ package.json 확인 완료"
echo ""

# Node.js 버전 확인
echo "📦 Node.js 환경:"
echo "   Node: $(node --version)"
echo "   npm: $(npm --version)"
echo ""

# Vercel CLI 확인
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI가 설치되지 않았습니다."
    echo "📥 설치 중..."
    npm install -g vercel
fi

echo "✅ Vercel CLI: $(vercel --version)"
echo ""

# 1단계: Vercel 로그인
echo "========================================="
echo "1️⃣ Vercel 로그인"
echo "========================================="
echo "브라우저가 열리면 GitHub 계정으로 로그인하세요..."
echo ""

vercel login

echo ""
echo "✅ 로그인 완료!"
echo "   계정: $(vercel whoami)"
echo ""

# 2단계: 환경 변수 파일 생성 (선택사항)
echo "========================================="
echo "2️⃣ 환경 변수 준비"
echo "========================================="

cat > .env.production.local << EOF
NEXT_PUBLIC_API_URL=https://dt-rag-production.up.railway.app
NEXT_PUBLIC_API_TIMEOUT=30000
EOF

echo "✅ .env.production.local 생성 완료"
echo ""

# 3단계: Preview 배포 (테스트)
echo "========================================="
echo "3️⃣ Preview 배포 (테스트)"
echo "========================================="
echo ""
echo "다음 질문에 답변하세요:"
echo "  - Set up and deploy? → Y"
echo "  - Which scope? → [계정 선택]"
echo "  - Link to existing project? → N"
echo "  - Project name? → dt-rag-frontend"
echo "  - Code directory? → ./ (Enter)"
echo "  - Modify settings? → N"
echo ""
read -p "준비되셨으면 Enter를 누르세요..."

vercel

echo ""
echo "✅ Preview 배포 완료!"
echo ""

# 4단계: 환경 변수 설정
echo "========================================="
echo "4️⃣ 환경 변수 설정"
echo "========================================="
echo ""
echo "환경 변수 2개를 추가합니다..."
echo ""

# NEXT_PUBLIC_API_URL 추가
echo "📌 NEXT_PUBLIC_API_URL 추가 중..."
vercel env add NEXT_PUBLIC_API_URL production << EOF
https://dt-rag-production.up.railway.app
EOF

echo "✅ NEXT_PUBLIC_API_URL 추가 완료"
echo ""

# NEXT_PUBLIC_API_TIMEOUT 추가
echo "📌 NEXT_PUBLIC_API_TIMEOUT 추가 중..."
vercel env add NEXT_PUBLIC_API_TIMEOUT production << EOF
30000
EOF

echo "✅ NEXT_PUBLIC_API_TIMEOUT 추가 완료"
echo ""

# 5단계: Production 배포
echo "========================================="
echo "5️⃣ Production 배포"
echo "========================================="
echo ""
echo "Production 환경으로 최종 배포를 시작합니다..."
read -p "계속하시겠습니까? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    vercel --prod

    echo ""
    echo "========================================="
    echo "🎉 배포 완료!"
    echo "========================================="
    echo ""
    echo "배포된 URL을 확인하세요:"
    vercel ls
    echo ""
    echo "다음 명령어로 상세 정보 확인:"
    echo "  vercel inspect"
    echo "  vercel logs"
    echo ""
else
    echo "배포가 취소되었습니다."
    exit 0
fi

echo "========================================="
echo "✅ 모든 단계 완료!"
echo "========================================="
