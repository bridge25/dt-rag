# Railway CLI Testing Guide

**Updated**: 2025-11-12
**Target**: Developers working on dt-rag project

---

## 🎯 Overview

Railway CLI enables you to run tests locally with the **exact same environment variables** as your Railway deployment. This eliminates the need to manually copy/paste secrets and ensures parity between local and cloud environments.

**Benefits**:
- ✅ **Fast feedback**: Test in seconds instead of waiting for CI/CD
- ✅ **Real environment**: Use actual production/staging databases
- ✅ **Zero configuration**: No manual environment variable setup
- ✅ **Secure**: Secrets never leave Railway's infrastructure

---

## 📦 One-Time Setup

### 1. Install Railway CLI

```bash
# Using npm (recommended)
npm install -g @railway/cli

# Using Homebrew (macOS)
brew install railway

# Verify installation
railway --version
```

### 2. Login to Railway

```bash
railway login
```

This will open your browser for authentication.

### 3. Link Project

```bash
# Run this command in the dt-rag-standalone directory
railway link

# Select your project:
#   → dt-rag (or your Railway project name)
```

**Verification**:
```bash
# Check linked project
railway status

# Expected output:
# 🎫 Project: dt-rag
# 🌍 Environment: production
# 📦 Service: dt-rag-backend
```

---

## 🧪 Running Tests

### Basic Usage

```bash
# Run all tests with Railway environment variables
railway run pytest -v

# Run specific test file
railway run pytest tests/unit/test_database.py -v

# Run with coverage
railway run pytest --cov=apps --cov-report=term-missing

# Run integration tests only
railway run pytest tests/integration/ -v
```

### Environment-Specific Testing

```bash
# Test against production environment (⚠️ USE WITH CAUTION)
railway run --environment production pytest tests/

# Test against staging environment (RECOMMENDED)
railway run --environment staging pytest tests/

# Test against PR environment
railway run --environment pr-123 pytest tests/
```

### Service-Specific Testing

If you have multiple services (e.g., backend, worker):

```bash
# Use backend service variables
railway run --service dt-rag-backend pytest tests/

# Use worker service variables
railway run --service dt-rag-worker pytest tests/worker/
```

---

## 🚀 Local Development

### Running the Application Locally

```bash
# Start FastAPI server with Railway environment variables
railway run uvicorn apps.api.main:app --reload

# Run database migrations
railway run alembic upgrade head

# Open a shell with Railway environment
railway run bash

# Inside the shell, all Railway env vars are available:
echo $DATABASE_URL
echo $REDIS_URL
echo $OPENAI_API_KEY
```

### Running Frontend with Backend Connection

```bash
# Terminal 1: Start backend with Railway env
railway run uvicorn apps.api.main:app --reload --port 8000

# Terminal 2: Start frontend (in frontend/ directory)
cd frontend
npm run dev
```

---

## 🔍 Debugging & Inspection

### View Environment Variables

```bash
# List all environment variables (without values)
railway variables

# Show environment variables (⚠️ contains secrets!)
railway run env | grep -E "DATABASE_URL|REDIS_URL|API_KEY"
```

### Check Deployment Logs

```bash
# View real-time logs
railway logs

# View logs for specific environment
railway logs --environment production

# Follow logs (like tail -f)
railway logs --follow
```

### Deployment Status

```bash
# Check current deployment status
railway status

# View deployment history
railway list deployments
```

---

## 📊 CI/CD Integration

### How Railway Pre-Deploy Works

When you push code to Railway, the following happens:

```
1. Code pushed to GitHub
2. Railway detects change
3. Railway builds Docker image
4. Railway runs Pre-Deploy Command (tests)
   ├─ If tests PASS → Continue to step 5
   └─ If tests FAIL → Abort deployment (rollback)
5. Railway deploys to environment
6. Railway runs health checks
```

### Pre-Deploy Commands (Configured in railway.toml)

```toml
# Default environment
[deploy]
preDeployCommand = "pytest tests/unit/ tests/integration/ -v --maxfail=3"

# PR environment (fast tests only)
[environments.pr.deploy]
preDeployCommand = "pytest tests/unit/ -v --maxfail=1"

# Production (comprehensive tests + migration)
[environments.production.deploy]
preDeployCommand = "pytest tests/ --cov=apps --cov-fail-under=85 && alembic upgrade head"
```

### Viewing Pre-Deploy Test Results

```bash
# View deployment logs (includes test output)
railway logs --deployment <deployment-id>

# Or view in Railway dashboard:
# https://railway.app/project/<project-id>/deployments
```

---

## 🎓 Best Practices

### ✅ DO

- **Use staging environment for testing**: `railway run --environment staging pytest`
- **Run tests before pushing**: Catch issues locally before CI/CD
- **Keep secrets secure**: Never log or print `RAILWAY_API_TOKEN` or API keys
- **Test migrations locally**: `railway run alembic upgrade head`

### ❌ DON'T

- **Don't test against production DB**: Use staging/PR environments
- **Don't commit `.railway/` directory**: Already in `.gitignore`
- **Don't share Railway tokens**: They provide full access to your project
- **Don't run destructive tests on production**: Create test fixtures instead

---

## 🔧 Troubleshooting

### Issue: "No project linked"

```bash
# Solution: Link your project
railway link
```

### Issue: "Command not found: railway"

```bash
# Solution: Install Railway CLI
npm install -g @railway/cli

# Or add to PATH if using Homebrew
export PATH="/opt/homebrew/bin:$PATH"
```

### Issue: "Authentication failed"

```bash
# Solution: Re-login
railway logout
railway login
```

### Issue: "DATABASE_URL not found"

```bash
# Check if environment variables exist
railway variables

# If missing, add in Railway dashboard:
# Project Settings → Variables → Add Variable
```

### Issue: Tests pass locally but fail on Railway

**Possible causes**:
1. Different Python version (Railway uses Python 3.11)
2. Missing dependencies in `requirements.txt`
3. Environment-specific behavior (file paths, etc.)

**Solution**:
```bash
# Test with exact Railway environment
railway run pytest -v

# Check Railway build logs
railway logs --deployment latest
```

---

## 📚 Additional Resources

- [Railway CLI Documentation](https://docs.railway.com/guides/cli)
- [Railway Config as Code](https://docs.railway.com/reference/config-as-code)
- [Railway Environments Guide](https://docs.railway.com/guides/environments)
- [dt-rag Deployment Guide](../DEPLOYMENT_GUIDE.md)

---

## 🚀 Quick Reference

```bash
# Setup (one-time)
npm install -g @railway/cli
railway login
railway link

# Run tests
railway run pytest -v
railway run pytest --cov=apps --cov-report=term-missing

# Run application
railway run uvicorn apps.api.main:app --reload

# Run migrations
railway run alembic upgrade head

# View logs
railway logs --follow

# Check status
railway status
```

---

**Need help?** Ask in the team Slack channel or check Railway's [Help Station](https://station.railway.com/).
