# CORS Security Configuration Guide

## Overview

This document explains the CORS (Cross-Origin Resource Sharing) security configuration for the Dynamic Taxonomy RAG API v1.8.1. Proper CORS configuration is critical for preventing cross-origin attacks while enabling legitimate cross-origin requests.

## Security Vulnerabilities Fixed

### 🔴 HIGH RISK: Wildcard CORS Headers
**Problem**: The previous configuration used `allow_headers: ["*"]` which allows any header from any origin, creating a security vulnerability.

**Solution**: Replaced with specific, necessary headers:
```python
allow_headers: [
    "Accept",
    "Accept-Language",
    "Content-Language",
    "Content-Type",
    "Authorization",
    "X-API-Key",
    "X-Requested-With",
    "X-Request-ID",
    "Cache-Control"
]
```

### 🟡 MEDIUM RISK: Production Wildcard Origins
**Problem**: Default configuration could allow wildcard origins in production if not properly configured.

**Solution**: Added strict validation that prevents wildcard origins in production environments.

## Environment-Specific CORS Settings

### Development Environment
```bash
DT_RAG_ENV=development
CORS_ORIGINS=http://localhost:3000,http://localhost:8080,http://127.0.0.1:3000
```

**Characteristics**:
- Allows HTTP origins (localhost only)
- Multiple localhost ports supported
- 5-minute cache (300 seconds)
- Flexible for development needs

### Staging Environment
```bash
DT_RAG_ENV=staging
CORS_ORIGINS=https://staging.dt-rag.com,https://staging-app.dt-rag.com
```

**Characteristics**:
- HTTPS origins only
- Specific staging domains
- 30-minute cache (1800 seconds)
- Production-like security

### Production Environment
```bash
DT_RAG_ENV=production
CORS_ORIGINS=https://dt-rag.com,https://app.dt-rag.com
```

**Characteristics**:
- HTTPS origins only (strictly enforced)
- No wildcards allowed
- 1-hour cache (3600 seconds)
- Maximum security restrictions

## CORS Configuration Options

### Required Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `CORS_ORIGINS` | Comma-separated list of allowed origins | Production: Yes | Environment-specific |
| `CORS_HEADERS` | Custom headers (optional) | No | Secure defaults |
| `CORS_CREDENTIALS` | Enable credentials | No | `true` |

### Example Configurations

#### Frontend React App (Development)
```bash
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
CORS_CREDENTIALS=true
```

#### Multiple Frontend Domains (Production)
```bash
CORS_ORIGINS=https://app.dt-rag.com,https://admin.dt-rag.com,https://dashboard.dt-rag.com
CORS_CREDENTIALS=true
```

#### API-Only Access (Production)
```bash
CORS_ORIGINS=https://api-client.dt-rag.com
CORS_CREDENTIALS=false
```

## Security Validations

The API automatically validates CORS configuration on startup:

### Production Validations
1. **No Wildcard Origins**: `"*"` is not allowed in `CORS_ORIGINS`
2. **HTTPS Only**: All origins must use HTTPS (except localhost)
3. **No Wildcard Headers**: `"*"` is not allowed in headers
4. **Credentials Security**: Credentials cannot be enabled with wildcard origins

### Error Examples
```python
# ❌ This will fail in production:
CORS_ORIGINS=*

# ❌ This will fail in production:
CORS_ORIGINS=http://example.com

# ❌ This will fail in production:
CORS_HEADERS=*

# ✅ This is correct for production:
CORS_ORIGINS=https://app.dt-rag.com,https://admin.dt-rag.com
```

## Security Headers

### Allowed Headers (Default)
- `Accept`: Content type acceptance
- `Accept-Language`: Language preferences
- `Content-Language`: Content language
- `Content-Type`: Request content type
- `Authorization`: Bearer tokens, API keys
- `X-API-Key`: Custom API key header
- `X-Requested-With`: AJAX request identification
- `X-Request-ID`: Request tracking
- `Cache-Control`: Cache directives

### Exposed Headers
- `X-Request-ID`: Request tracking for debugging
- `X-RateLimit-Remaining`: Rate limiting information
- `X-RateLimit-Limit`: Rate limiting information

## Common CORS Issues & Solutions

### Issue 1: CORS Error in Development
**Symptom**: Browser shows CORS error when accessing API from localhost:3000

**Solution**:
```bash
# Add your development origin
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

### Issue 2: Credentials Not Working
**Symptom**: Authentication cookies/headers not sent

**Solution**:
```bash
# Ensure credentials are enabled and origins are specific
CORS_CREDENTIALS=true
CORS_ORIGINS=https://app.dt-rag.com  # No wildcards!
```

### Issue 3: Custom Headers Blocked
**Symptom**: Custom headers (like X-Custom-Header) are rejected

**Solution**:
```bash
# Add your custom headers
CORS_HEADERS=Accept,Content-Type,Authorization,X-API-Key,X-Custom-Header
```

### Issue 4: Production Deployment Fails
**Symptom**: API fails to start in production with CORS error

**Solution**:
```bash
# Ensure HTTPS and no wildcards
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

## Security Best Practices

### 1. Principle of Least Privilege
- Only allow origins that need access
- Only allow headers that are necessary
- Disable credentials if not needed

### 2. Environment Separation
- Use different origins for dev/staging/production
- Never use production secrets in development
- Test CORS configuration in staging before production

### 3. Regular Auditing
- Review CORS origins regularly
- Remove unused origins
- Monitor for suspicious cross-origin requests

### 4. Header Security
- Avoid wildcard headers
- Only expose necessary response headers
- Use specific, known headers

## Troubleshooting

### Check Current CORS Configuration
```bash
curl http://localhost:8000/api/v1/monitoring/health
```

### Validate Configuration
The API provides security recommendations:
```python
from config import get_security_info
info = get_security_info()
print(info['security_recommendations'])
```

### Test CORS in Browser
```javascript
// In browser console:
fetch('http://localhost:8000/health', {
  method: 'GET',
  headers: {
    'Content-Type': 'application/json'
  },
  credentials: 'include'
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error('CORS Error:', error));
```

## Migration from Wildcard Configuration

If upgrading from a wildcard CORS configuration:

### Step 1: Identify Current Origins
Review your application to identify all legitimate origins that need API access.

### Step 2: Set Environment Variables
```bash
# Replace wildcards with specific origins
CORS_ORIGINS=https://your-app.com,https://your-admin.com
```

### Step 3: Test Configuration
Test in staging environment before deploying to production.

### Step 4: Monitor Logs
Monitor for CORS errors after deployment and add legitimate origins as needed.

## API Endpoints for CORS Information

### Security Information
```
GET /api/v1/monitoring/health
```
Returns security configuration status including CORS settings.

### Rate Limiting (CORS-related)
```
GET /api/v1/rate-limits
```
Shows rate limiting information that may be affected by CORS origin.

## Compliance Notes

This CORS configuration helps meet security compliance requirements:
- **OWASP**: Prevents unauthorized cross-origin access
- **PCI DSS**: Restricts origin access for payment-related endpoints
- **SOC 2**: Implements access controls for sensitive data
- **GDPR/CCPA**: Prevents unauthorized data access from untrusted origins

---

**Last Updated**: September 2024
**Configuration Version**: 1.8.1
**Security Level**: Production Ready