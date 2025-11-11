#!/bin/bash
# DT-RAG Deployment Script for Railway + Vercel
# This script automates the deployment process

set -e  # Exit on error

echo "🚀 DT-RAG Deployment Script"
echo "============================"
echo ""

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Install Railway CLI
echo "📦 Step 1: Installing Railway CLI..."
if ! command -v railway &> /dev/null; then
    echo "${YELLOW}Railway CLI not found. Installing...${NC}"
    npm install -g @railway/cli
    echo "${GREEN}✅ Railway CLI installed${NC}"
else
    echo "${GREEN}✅ Railway CLI already installed${NC}"
    railway --version
fi
echo ""

# Step 2: Install Vercel CLI
echo "📦 Step 2: Installing Vercel CLI..."
if ! command -v vercel &> /dev/null; then
    echo "${YELLOW}Vercel CLI not found. Installing...${NC}"
    npm install -g vercel
    echo "${GREEN}✅ Vercel CLI installed${NC}"
else
    echo "${GREEN}✅ Vercel CLI already installed${NC}"
    vercel --version
fi
echo ""

# Step 3: Login to Railway
echo "🔐 Step 3: Railway Authentication"
echo "${YELLOW}Opening browser for Railway login...${NC}"
railway login
echo "${GREEN}✅ Railway login complete${NC}"
echo ""

# Step 4: Create Railway Project
echo "🏗️  Step 4: Railway Project Setup"
echo "${YELLOW}This will create a new Railway project${NC}"
read -p "Do you want to create a new Railway project? (y/n): " create_railway
if [ "$create_railway" = "y" ]; then
    railway init
    echo "${GREEN}✅ Railway project created${NC}"
else
    railway link
    echo "${GREEN}✅ Linked to existing Railway project${NC}"
fi
echo ""

# Step 5: Add PostgreSQL
echo "🐘 Step 5: Adding PostgreSQL Database"
railway add --plugin postgresql
echo "${GREEN}✅ PostgreSQL added${NC}"
echo ""

# Step 6: Add Redis
echo "📮 Step 6: Adding Redis Cache"
railway add --plugin redis
echo "${GREEN}✅ Redis added${NC}"
echo ""

# Step 7: Enable pgvector Extension
echo "🔌 Step 7: Enabling pgvector Extension"
echo "${YELLOW}Please run the following SQL command in Railway PostgreSQL:${NC}"
echo "  CREATE EXTENSION IF NOT EXISTS vector;"
echo ""
echo "Press Enter after you've executed the SQL command..."
read

# Step 8: Set Environment Variables
echo "🔑 Step 8: Setting Environment Variables"
echo "${YELLOW}Generating API key...${NC}"
API_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
echo "Generated API_KEY: ${GREEN}$API_KEY${NC}"
echo ""

echo "${YELLOW}Please set the following environment variables in Railway:${NC}"
echo ""
echo "REQUIRED:"
echo "  ENVIRONMENT=production"
echo "  PYTHON_VERSION=3.11"
echo "  PYTHONUNBUFFERED=1"
echo "  PYTHONDONTWRITEBYTECODE=1"
echo "  API_V1_STR=/api/v1"
echo "  PROJECT_NAME=DT-RAG"
echo "  API_KEY=$API_KEY"
echo ""

# Save API key for later
echo "$API_KEY" > .api_key
echo "${YELLOW}API key saved to .api_key file${NC}"
echo ""

read -p "Enter your OPENAI_API_KEY: " OPENAI_KEY
railway variables set OPENAI_API_KEY="$OPENAI_KEY"

read -p "Do you have a GEMINI_API_KEY? (y/n): " has_gemini
if [ "$has_gemini" = "y" ]; then
    read -p "Enter your GEMINI_API_KEY: " GEMINI_KEY
    railway variables set GEMINI_API_KEY="$GEMINI_KEY"
fi

railway variables set ENVIRONMENT=production
railway variables set PYTHON_VERSION=3.11
railway variables set PYTHONUNBUFFERED=1
railway variables set PYTHONDONTWRITEBYTECODE=1
railway variables set API_V1_STR=/api/v1
railway variables set PROJECT_NAME=DT-RAG
railway variables set API_KEY="$API_KEY"

echo "${GREEN}✅ Environment variables set${NC}"
echo ""

# Step 9: Deploy to Railway
echo "🚢 Step 9: Deploying to Railway"
railway up
echo "${GREEN}✅ Railway deployment initiated${NC}"
echo ""

# Step 10: Get Railway URL
echo "🌐 Step 10: Getting Railway Backend URL"
RAILWAY_URL=$(railway domain)
echo "Railway Backend URL: ${GREEN}$RAILWAY_URL${NC}"
echo "$RAILWAY_URL" > .railway_url
echo ""

# Step 11: Update CORS Settings
echo "🔒 Step 11: Setting CORS Configuration"
echo "${YELLOW}CORS will be updated after Vercel deployment${NC}"
echo ""

# Step 12: Login to Vercel
echo "🔐 Step 12: Vercel Authentication"
echo "${YELLOW}Opening browser for Vercel login...${NC}"
vercel login
echo "${GREEN}✅ Vercel login complete${NC}"
echo ""

# Step 13: Deploy Frontend to Vercel
echo "🎨 Step 13: Deploying Frontend to Vercel"
cd frontend
vercel --prod --env VITE_API_BASE_URL="$RAILWAY_URL"
cd ..
echo "${GREEN}✅ Vercel deployment initiated${NC}"
echo ""

# Step 14: Get Vercel URL
echo "🌐 Step 14: Getting Vercel Frontend URL"
VERCEL_URL=$(vercel inspect --prod | grep "URL:" | awk '{print $2}')
echo "Vercel Frontend URL: ${GREEN}$VERCEL_URL${NC}"
echo "$VERCEL_URL" > .vercel_url
echo ""

# Step 15: Update Railway CORS
echo "🔒 Step 15: Updating Railway CORS Configuration"
railway variables set CORS_ORIGINS="$VERCEL_URL,http://localhost:3000"
echo "${GREEN}✅ CORS updated${NC}"
echo ""

# Step 16: Redeploy Railway (to apply CORS changes)
echo "🔄 Step 16: Redeploying Railway with CORS updates"
railway up
echo "${GREEN}✅ Railway redeployed${NC}"
echo ""

# Deployment Complete
echo "🎊 ============================================"
echo "🎊  DEPLOYMENT COMPLETE!"
echo "🎊 ============================================"
echo ""
echo "${GREEN}Backend (Railway):${NC} $RAILWAY_URL"
echo "${GREEN}Frontend (Vercel):${NC} $VERCEL_URL"
echo "${GREEN}API Key:${NC} $API_KEY"
echo ""
echo "📝 Next Steps:"
echo "  1. Test backend health: curl $RAILWAY_URL/health"
echo "  2. Open frontend: $VERCEL_URL"
echo "  3. Check deployment logs:"
echo "     - Railway: railway logs"
echo "     - Vercel: vercel logs"
echo ""
echo "📚 For troubleshooting, see:"
echo "  - DEPLOYMENT_GUIDE.md"
echo "  - ENV_VARIABLES_GUIDE.md"
echo ""
echo "${GREEN}Happy deploying! 🚀${NC}"
