# Environment Configuration Guide - DT-RAG v1.8.1

This guide explains the improved environment configuration system for DT-RAG v1.8.1, which includes secure API key management, environment-specific settings, and comprehensive fallback mechanisms.

## Overview

The new configuration system provides:

- **Multi-environment support** (development, testing, staging, production)
- **Secure API key management** with fallback to dummy services
- **Comprehensive validation** and health checks
- **Environment-specific security policies**
- **Automatic configuration migration** from previous versions

## Quick Start

### 1. Choose Your Environment

```bash
# Development (default)
cp .env.template .env

# Production
cp .env.production.template .env
```

### 2. Configure Required Settings

Edit `.env` file with your specific configuration:

```bash
# Set your environment
DT_RAG_ENV=development

# Configure database (SQLite for dev, PostgreSQL for production)
DATABASE_URL=sqlite+aiosqlite:///./dt_rag.db

# Add API keys (optional - system works without them)
OPENAI_API_KEY=sk-your-api-key-here

# Set a secure secret key for production
SECRET_KEY=your-32-character-secret-key
```

### 3. Validate Configuration

```bash
python scripts/validate_config.py
```

### 4. Start the System

```bash
# The system will automatically use appropriate fallbacks
python -m apps.api.main
```

## Environment Types

### Development
- SQLite database (no PostgreSQL required)
- Dummy LLM/embedding services (no API keys required)
- Debug mode enabled
- API documentation available
- Relaxed CORS policies

### Testing
- SQLite database with test isolation
- Dummy services for consistent testing
- Higher rate limits
- Test data cleanup enabled

### Production
- PostgreSQL database required
- Real LLM services recommended
- Security hardening enabled
- API documentation disabled
- Strict CORS policies

## Configuration Structure

### Core Environment Variables

```bash
# Environment
DT_RAG_ENV=development|testing|staging|production
DEBUG=true|false
TEST_MODE=true|false

# Database
DATABASE_URL=sqlite+aiosqlite:///./dt_rag.db
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10

# Security
SECRET_KEY=your-secure-secret-key
JWT_EXPIRATION_MINUTES=30
PASSWORD_MIN_LENGTH=8

# LLM Services
LLM_SERVICE_MODE=dummy|openai|anthropic|azure
OPENAI_API_KEY=sk-your-api-key-here
EMBEDDING_SERVICE_MODE=dummy|openai|azure
```

## API Key Management

### Service Modes

The system supports multiple LLM service modes with automatic fallback:

1. **dummy** - No API keys required, generates placeholder responses
2. **openai** - Uses OpenAI API (requires OPENAI_API_KEY)
3. **anthropic** - Uses Anthropic API (requires ANTHROPIC_API_KEY)
4. **azure** - Uses Azure OpenAI (requires AZURE_OPENAI_API_KEY + AZURE_OPENAI_ENDPOINT)

### Automatic Fallback

If API keys are not configured or invalid, the system automatically falls back to dummy mode:

- **LLM responses**: Placeholder text responses
- **Embeddings**: Random vectors with correct dimensions
- **System status**: Remains operational with warnings

### API Key Validation

The system validates API keys on startup:

```bash
# Check system status
curl http://localhost:8000/system/status

# Check configuration
python scripts/validate_config.py
```

## Database Configuration

### SQLite (Development/Testing)

```bash
DATABASE_URL=sqlite+aiosqlite:///./dt_rag.db
```

- No external dependencies
- Automatic database creation
- Perfect for development and testing

### PostgreSQL (Staging/Production)

```bash
# Option 1: Connection string
DATABASE_URL=postgresql+asyncpg://user:password@host:port/database

# Option 2: Component variables
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=dt_rag
POSTGRES_USER=dt_rag_user
POSTGRES_PASSWORD=secure_password
DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}
```

## Security Configuration

### JWT Secret Key

```bash
# Generate a secure secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Set in .env
SECRET_KEY=your-generated-secret-key-here
```

### CORS Configuration

```bash
# Development (multiple local origins)
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# Production (specific domains only)
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

### Password Policies

```bash
PASSWORD_MIN_LENGTH=8
PASSWORD_REQUIRE_SPECIAL=true
PASSWORD_REQUIRE_UPPERCASE=true
PASSWORD_REQUIRE_NUMBERS=true
```

## Migration from Previous Versions

### Automatic Migration

```bash
# Migrate existing .env file
python scripts/migrate_config.py
```

The migration script:
1. Backs up your existing `.env` file
2. Detects your environment type
3. Generates new configuration format
4. Preserves your existing settings
5. Provides migration summary

### Manual Migration

If you prefer manual migration:

1. Backup your current `.env` file
2. Copy the appropriate template
3. Transfer your settings manually
4. Validate the new configuration

## Validation and Health Checks

### Configuration Validation

```bash
# Comprehensive validation
python scripts/validate_config.py

# Quick status check
curl http://localhost:8000/system/status
```

### Health Check Endpoints

```bash
# System health
GET /health

# Detailed system status
GET /system/status

# Configuration recommendations
GET /system/recommendations
```

## Troubleshooting

### Common Issues

#### 1. "SECRET_KEY not configured"
```bash
# Generate and set a secure secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Add to .env: SECRET_KEY=generated-key-here
```

#### 2. "Database connection failed"
```bash
# Check database URL format
# SQLite: sqlite+aiosqlite:///./path/to/database.db
# PostgreSQL: postgresql+asyncpg://user:pass@host:port/db
```

#### 3. "LLM service unavailable"
```bash
# Check API key configuration
OPENAI_API_KEY=sk-your-key-here

# Or use dummy mode for testing
LLM_SERVICE_MODE=dummy
```

#### 4. "CORS policy error"
```bash
# Add your frontend URL to CORS_ORIGINS
CORS_ORIGINS=http://localhost:3000,https://yourapp.com
```

### Debug Mode

Enable debug mode for detailed error information:

```bash
DEBUG=true
LOG_LEVEL=DEBUG
ENABLE_SQL_LOGGING=true
```

### Environment Validation

```bash
# Check environment configuration
python -c "
from apps.api.env_manager import get_env_manager
manager = get_env_manager()
validation = manager.validate_environment()
print(f'Environment: {validation[\"environment\"]}')
print(f'Valid: {validation[\"is_valid\"]}')
for error in validation['errors']:
    print(f'Error: {error}')
for warning in validation['warnings']:
    print(f'Warning: {warning}')
"
```

## Best Practices

### Development
- Use SQLite for simplicity
- Enable debug mode and API documentation
- Use dummy LLM services initially
- Set relaxed rate limits

### Testing
- Use isolated test database
- Enable test mode and data cleanup
- Use dummy services for consistency
- Higher rate limits for test automation

### Production
- Use PostgreSQL with connection pooling
- Configure real LLM services
- Disable debug mode and API docs
- Set strict CORS and security policies
- Enable monitoring and error tracking
- Use environment variables for all secrets

### Security
- Never commit `.env` files with real secrets
- Use strong, random secret keys
- Rotate API keys regularly
- Enable HTTPS in production
- Use specific CORS origins (not wildcards)
- Regularly review security recommendations

## Configuration Reference

For complete configuration options, see:

- `.env.template` - Development template
- `.env.production.template` - Production template
- `apps/api/config.py` - Configuration classes
- `apps/api/env_manager.py` - Environment management
- `apps/api/llm_config.py` - LLM service configuration

## Support

If you encounter issues:

1. Run `python scripts/validate_config.py` for detailed diagnostics
2. Check the logs for specific error messages
3. Review this guide for common solutions
4. Check system status with `GET /system/status`