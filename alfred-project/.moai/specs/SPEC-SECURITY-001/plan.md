# SPEC-SECURITY-001 Implementation Plan

## 구현 개요

Security & Authentication System은 이미 완전히 구현되어 프로덕션 환경에서 검증 완료되었습니다. 본 문서는 역공학된 시스템의 구현 전략과 아키텍처를 설명합니다.

DT-RAG v1.8.1의 통합 보안 시스템으로, API Key 기반 인증, JWT 토큰 세션 관리, RBAC 권한 체계, 보안 미들웨어, OWASP Top 10 대응을 제공합니다.

## 우선순위별 구현 마일스톤

### 1차 목표: API Key Authentication (완료)

**구현 완료 항목**:
- ✅ SecureAPIKeyGenerator 클래스 (암호학적 안전 키 생성)
- ✅ API Key 해시 저장 (PBKDF2-SHA256)
- ✅ APIKeyStorage 클래스 (CRUD + 감사 로그)
- ✅ API Key 검증 (해시 비교, 만료, IP 제한, Rate Limit)
- ✅ Usage tracking (api_key_usage 테이블)

**기술적 접근**:
```python
# API Key Generation
generated_key = SecureAPIKeyGenerator.generate_api_key(
    APIKeyConfig(
        length=40,
        format_type="base64",
        prefix="prod",
        checksum=True
    )
)
# key: "prod_Xz8vN4Kq2L9mW6jP1tH3Ry5Gc7Fb0Sd-a2c4"
# key_hash: PBKDF2-SHA256(key, salt, 100000 iterations)

# Verification
if SecureAPIKeyGenerator.verify_key_hash(plaintext_key, stored_hash):
    # Check expiration, IP restrictions, rate limits
    pass
```

**아키텍처 결정**:
- **PBKDF2-SHA256**: 100,000 iterations, 32-byte salt
- **Entropy**: ≥ 96 bits (암호학적 안전)
- **Format Types**: base64, hex, alphanumeric, mixed
- **Prefix**: 환경 구분 (prod_, dev_, admin_)
- **Checksum**: MD5 4자리 (무결성 검증)
- **Database**: PostgreSQL (api_keys, api_key_usage, api_key_audit_log)

### 2차 목표: JWT Token Authentication (완료)

**구현 완료 항목**:
- ✅ AuthService 클래스 (회원가입, 로그인, 토큰 검증)
- ✅ 비밀번호 해시 (bcrypt)
- ✅ JWT 토큰 생성 (HS256)
- ✅ 세션 관리 (활동 시간 추적)
- ✅ 계정 잠금 메커니즘 (Brute Force 방어)

**기술적 접근**:
```python
# User Registration
password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
user = User(
    user_id=str(uuid.uuid4()),
    password_hash=password_hash,
    roles={Role.VIEWER},
    permissions={Permission.READ_DOCUMENTS, Permission.SEARCH_DOCUMENTS}
)

# JWT Token Generation
payload = {
    'user_id': user.user_id,
    'session_id': session.session_id,
    'username': user.username,
    'roles': [role.value for role in user.roles],
    'iat': datetime.utcnow(),
    'exp': datetime.utcnow() + timedelta(hours=24)
}
token = jwt.encode(payload, JWT_SECRET, algorithm='HS256')

# Token Validation
payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
if token not in revoked_tokens and payload['exp'] > now():
    # Update session activity
    session.last_activity = datetime.utcnow()
```

**아키텍처 결정**:
- **bcrypt**: Password hashing (자동 salt 생성)
- **JWT HS256**: Symmetric key algorithm (32+ bytes secret)
- **Token Expiry**: 24시간 (configurable)
- **Session Timeout**: 30분 무활동 시 만료
- **Account Lockout**: 5회 실패 시 30분 잠금
- **Revocation**: In-memory revoked_tokens set (로그아웃, 강제 만료)

### 3차 목표: Security Middleware (완료)

**구현 완료 항목**:
- ✅ SecurityMiddleware FastAPI 통합
- ✅ Input Sanitization (SQL Injection, XSS, Command Injection)
- ✅ Security Headers (OWASP 권장)
- ✅ Rate Limiting (Sliding Window)
- ✅ Output Sanitization (PII 마스킹)
- ✅ Audit Logging

**기술적 접근**:
```python
# Middleware Flow
async def dispatch(request: Request, call_next):
    # 1. Pre-request checks
    if not await self._check_rate_limit(ip_address):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    # 2. Authentication
    token = request.headers.get("Authorization") or request.headers.get("X-API-Key")
    context = await security_manager.authenticate_request(token, ip, user_agent)
    request.state.security_context = context

    # 3. Input sanitization
    json_data = await request.json()
    sanitized_data = security_manager.sanitize_request_data(json_data, context)
    request.state.sanitized_data = sanitized_data

    # 4. Execute endpoint
    response = await call_next(request)

    # 5. Add security headers
    for header, value in SecurityHeaders.get_default_headers().items():
        response.headers[header] = value

    # 6. Output sanitization (if PII detected)
    response_data = await self._sanitize_response(response, context)

    return response
```

**아키텍처 결정**:
- **Middleware Order**: Rate Limit → Auth → Sanitization → Endpoint → Headers → Audit
- **SQL Injection Patterns**: `'; DROP TABLE`, `UNION SELECT`, `OR 1=1`, `--`, `/**/`
- **XSS Patterns**: `<script>`, `javascript:`, `onload=`, `onerror=`, `<iframe>`
- **Command Injection Patterns**: `;`, `&&`, `||`, `|`, `` ` ``, `../`, `/etc/passwd`
- **JSON Complexity Limit**: 1000 fields, 10 levels deep
- **Request Size Limit**: 10MB

### 4차 목표: RBAC Authorization (완료)

**구현 완료 항목**:
- ✅ Role 정의 (7개 역할)
- ✅ Permission 정의 (12개 권한)
- ✅ Role-Permission 매핑
- ✅ Context-Based Authorization (시간, 위험 점수, IP)
- ✅ SecurityDependency (FastAPI 의존성)

**기술적 접근**:
```python
# Role Hierarchy
Role.ANONYMOUS         → []
Role.VIEWER            → [READ_DOCUMENTS, SEARCH_DOCUMENTS]
Role.EDITOR            → VIEWER + [WRITE_DOCUMENTS, CLASSIFY_DOCUMENTS]
Role.CLASSIFIER        → VIEWER + [CLASSIFY_DOCUMENTS]
Role.REVIEWER          → CLASSIFIER + [MANAGE_TAXONOMY]
Role.ADMIN             → REVIEWER + [DELETE_DOCUMENTS, VIEW_AUDIT_LOGS, ACCESS_PII, EXPORT_DATA]
Role.SUPER_ADMIN       → All Permissions + [MANAGE_USERS, ADMIN_SYSTEM]

# Authorization Check
permissions = get_permissions_for_roles(user.roles)
if required_permission not in permissions:
    raise HTTPException(status_code=403, detail="Insufficient permissions")

# Context-Based Authorization
if permission == Permission.DELETE_DOCUMENTS:
    if context.timestamp.hour < 8 or context.timestamp.hour > 18:
        raise HTTPException(403, "Operation not allowed outside business hours")
    if context.risk_score > 0.7:
        raise HTTPException(403, "High risk score, operation denied")
```

**아키텍처 결정**:
- **7개 역할**: ANONYMOUS, VIEWER, EDITOR, CLASSIFIER, REVIEWER, ADMIN, SUPER_ADMIN
- **12개 권한**: READ/WRITE/DELETE_DOCUMENTS, SEARCH/CLASSIFY_DOCUMENTS, MANAGE_TAXONOMY, VIEW_AUDIT_LOGS, MANAGE_USERS, ACCESS_PII, VIEW_PII, EXPORT_DATA, ADMIN_SYSTEM
- **다중 역할**: 사용자는 여러 역할 동시 보유 가능 (권한 합집합)
- **Context 조건**: 업무 시간(8-18시), 위험 점수(< 0.7), IP 대역
- **역할 상속**: 상위 역할은 하위 역할 권한 포함

### 5차 목표: Security Manager Orchestration (완료)

**구현 완료 항목**:
- ✅ SecurityManager 중앙 집중식 관리
- ✅ 위험 점수 계산 (IP, User-Agent, 시간)
- ✅ 세션 관리 (active_sessions)
- ✅ 감사 로그 통합
- ✅ SecurityContext 생성 및 검증

**기술적 접근**:
```python
# Security Manager Orchestration
async def authenticate_request(token, ip, user_agent, operation):
    # 1. Validate token format
    if len(token) < 32:
        raise SecurityException("Invalid token format")

    # 2. Authenticate user (JWT or API Key)
    user_info = await auth_service.validate_token(token)

    # 3. Check session validity
    if session_id in active_sessions:
        if is_session_expired(active_sessions[session_id]):
            await invalidate_session(session_id)
            raise SecurityException("Session expired")

    # 4. Rate limiting check
    if not await check_rate_limit(ip):
        raise SecurityException("Rate limit exceeded")

    # 5. Risk assessment
    risk_score = await calculate_risk_score(user_info, ip, user_agent)

    # 6. Create security context
    context = SecurityContext(
        user_id=user_info['user_id'],
        session_id=session_id,
        ip_address=ip,
        permissions=permissions,
        clearance_level=clearance_level,
        risk_score=risk_score,
        timestamp=datetime.utcnow()
    )

    # 7. Store active session
    active_sessions[session_id] = context

    return context
```

**위험 점수 계산**:
```python
risk_score = 0.0
if is_suspicious_ip(ip):         # 127.0.0.1, 10.0.0.x, 192.168.x.x
    risk_score += 0.3
if is_suspicious_user_agent(ua):  # curl, wget, bot, scraper
    risk_score += 0.2
if is_unusual_access_time():      # 2-6시
    risk_score += 0.1
return min(risk_score, 1.0)
```

**아키텍처 결정**:
- **중앙 집중식**: 모든 보안 작업은 SecurityManager를 통해 처리
- **위험 점수**: 0.0 (안전) ~ 1.0 (위험), 0.7 이상 시 민감 작업 차단
- **세션 스토어**: In-memory dict (프로덕션에서는 Redis 권장)
- **세션 만료**: 30분 무활동 or 24시간 절대 만료
- **감사 로그**: 모든 인증, 권한 부여, 보안 이벤트 기록

## 기술 스택 및 구현 세부사항

### Core Dependencies

```python
# Cryptography
import bcrypt                      # Password hashing
import jwt                         # JWT token generation
import secrets                     # Cryptographic random
import hashlib                     # PBKDF2-SHA256

# FastAPI
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware

# Database
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Index
from sqlalchemy.ext.asyncio import AsyncSession

# Internal
from apps.api.database import Base
from apps.api.monitoring.sentry_reporter import sentry_reporter
```

### Core Algorithms

**1. API Key Generation**:
```python
# Base64 format (most common)
random_bytes = secrets.token_bytes(40)  # 320 bits entropy
base64_key = base64.urlsafe_b64encode(random_bytes).decode().rstrip('=')
key = f"{prefix}_{base64_key}-{checksum}"

# PBKDF2-SHA256 hashing
salt = secrets.token_bytes(32)
key_hash = hashlib.pbkdf2_hmac('sha256', key.encode(), salt, 100000)
stored_hash = f"{salt.hex()}${key_hash.hex()}"
```

**2. JWT Token Generation**:
```python
payload = {
    'user_id': user.user_id,
    'session_id': session.session_id,
    'username': user.username,
    'roles': [role.value for role in user.roles],
    'iat': datetime.utcnow(),
    'exp': datetime.utcnow() + timedelta(hours=24)
}
token = jwt.encode(payload, JWT_SECRET, algorithm='HS256')

# Validation
payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
```

**3. Rate Limiting (Sliding Window)**:
```python
# In-memory sliding window
request_counts = {}  # identifier -> [timestamp1, timestamp2, ...]

def check_rate_limit(identifier, window=3600, limit=100):
    current_time = time.time()
    window_start = current_time - window

    # Clean old requests
    if identifier in request_counts:
        request_counts[identifier] = [
            t for t in request_counts[identifier] if t > window_start
        ]

    # Check limit
    if len(request_counts.get(identifier, [])) >= limit:
        return False

    # Add current request
    request_counts.setdefault(identifier, []).append(current_time)
    return True
```

**4. Input Sanitization**:
```python
def sanitize_sql_injection(value: str) -> str:
    patterns = [
        "'; DROP TABLE", "'; DELETE FROM", "'; UPDATE", "'; INSERT INTO",
        "UNION SELECT", "OR 1=1", "AND 1=1", "--", "/*", "*/"
    ]
    sanitized = value
    for pattern in patterns:
        sanitized = sanitized.replace(pattern, "")
        sanitized = sanitized.replace(pattern.lower(), "")
    return sanitized

def sanitize_xss(value: str) -> str:
    patterns = [
        "<script>", "</script>", "javascript:", "onload=", "onerror=",
        "onclick=", "onmouseover=", "<iframe>", "</iframe>"
    ]
    sanitized = value
    for pattern in patterns:
        sanitized = sanitized.replace(pattern, "")
        sanitized = sanitized.replace(pattern.upper(), "")
    return sanitized
```

### Security Headers (OWASP)

```python
SECURITY_HEADERS = {
    # A05:2021 – Security Misconfiguration
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Referrer-Policy": "strict-origin-when-cross-origin",

    # Content Security Policy
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self'; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    ),

    # Permissions Policy
    "Permissions-Policy": (
        "geolocation=(), microphone=(), camera=(), payment=(), "
        "usb=(), magnetometer=(), gyroscope=(), speaker=()"
    ),

    # Cache Control
    "Cache-Control": "no-store, no-cache, must-revalidate, private",
    "Pragma": "no-cache",
    "Expires": "0"
}
```

### Performance Metrics

**Latency Targets**:
- API Key 검증: p95 ≤ 10ms, p99 ≤ 20ms
- JWT 검증: p95 ≤ 5ms, p99 ≤ 10ms
- Rate Limit 체크: ≤ 1ms (in-memory)
- Input Sanitization: ≤ 5ms (1KB text)
- Security Middleware: ≤ 20ms (total overhead)

**Security Metrics**:
- Authentication Success Rate: ≥ 95%
- Failed Login Rate: < 5% (excluding brute force)
- Rate Limit Violations: < 1%
- Security Incidents (High): 0/day (target)
- PII Detection Accuracy: ≥ 95%

**Concurrent Sessions**:
- Maximum active sessions: 10,000 (in-memory)
- Session timeout: 30분 무활동
- Token TTL: 24시간
- API Key TTL: 365일 (default)

## 위험 요소 및 완화 전략

### 1. 인메모리 세션 스토어

**위험**: 서버 재시작 시 모든 세션 손실
**완화**:
- Redis Session Store 연동 (Phase 2)
- Session 재생성 메커니즘 (자동 재로그인)
- 짧은 TTL (24시간)

### 2. Brute Force 공격

**위험**: 무차별 대입으로 비밀번호 유출
**완화**:
- 계정 잠금 (5회 실패 시 30분)
- Rate Limiting (IP별 100 req/hour)
- CAPTCHA 통합 (추후)
- 비밀번호 정책 (최소 12자, 특수문자 필수)

### 3. JWT 토큰 탈취

**위험**: XSS/Network 공격으로 토큰 유출
**완화**:
- HTTPOnly Cookie (추후)
- Refresh Token 패턴 (추후)
- 짧은 TTL (24시간)
- 토큰 취소 목록 (revoked_tokens)
- 위험 점수 기반 차단

### 4. SQL Injection

**위험**: 사용자 입력을 통한 DB 조작
**완화**:
- 입력 Sanitization (패턴 제거)
- Parameterized Queries (SQLAlchemy)
- Whitelist Validation (taxonomy_path, content_type)
- 정규식 검증 `[a-zA-Z0-9_\- ]`

### 5. Rate Limit 우회

**위험**: 분산 IP로 Rate Limit 우회
**완화**:
- IP별 + API Key별 이중 제한
- Sliding Window 알고리즘
- Redis 기반 분산 Rate Limiting (추후)
- API Key별 개별 제한 설정

## 테스트 전략

### Unit Tests (완료)

- ✅ API Key 생성 (base64, hex, alphanumeric)
- ✅ API Key 해시 검증 (PBKDF2)
- ✅ JWT 토큰 생성 및 검증
- ✅ 비밀번호 해시 (bcrypt)
- ✅ SQL Injection 패턴 탐지
- ✅ XSS 패턴 탐지
- ✅ Command Injection 패턴 탐지
- ✅ Rate Limiting 알고리즘
- ✅ RBAC 권한 체크
- ✅ Context-Based Authorization
- ✅ 위험 점수 계산

### Integration Tests (완료)

- ✅ SecurityMiddleware FastAPI 통합
- ✅ API Key 검증 (Database)
- ✅ JWT 토큰 검증 (In-memory)
- ✅ 엔드포인트 보안 (401/403 응답)
- ✅ Security Headers 자동 추가
- ✅ Input Sanitization (JSON, query params)
- ✅ Audit Logging (api_key_audit_log)
- ✅ Rate Limiting (429 응답)

### Security Tests (완료)

- ✅ SQL Injection 방어
- ✅ XSS 방어
- ✅ Command Injection 방어
- ✅ Brute Force 방어 (계정 잠금)
- ✅ Session Fixation 방어
- ✅ CSRF 방어 (SameSite Cookie 준비)
- ✅ Rate Limit 우회 시도

### Penetration Testing Scenarios

**시나리오**:
1. **API Key Brute Force**: 1000개 랜덤 키로 인증 시도 → 모두 401
2. **JWT Token Forgery**: 서명 없는 토큰 전송 → 401
3. **SQL Injection Payload**: `'; DROP TABLE users--` → Sanitized or 400
4. **XSS Script Injection**: `<script>alert('xss')</script>` → Sanitized
5. **Rate Limit Bypass**: 동일 IP로 200회 요청 → 100회 후 429
6. **Account Takeover**: 10회 잘못된 비밀번호 → 5회 후 계정 잠금
7. **Session Hijacking**: 만료된 토큰으로 요청 → 401

## 배포 및 운영 계획

### 프로덕션 체크리스트

**환경 변수 설정**:
```bash
# JWT Configuration
JWT_SECRET=<32+ bytes random secret>
JWT_ALGORITHM=HS256
JWT_EXPIRY_HOURS=24

# Password Policy
PASSWORD_MIN_LENGTH=12
REQUIRE_SPECIAL_CHARS=true
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=30

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600

# Session Management
SESSION_TIMEOUT_MINUTES=30
MAX_CONCURRENT_SESSIONS=10000

# Security Headers
ENABLE_SECURITY_HEADERS=true
ENABLE_CSP=true
ENABLE_HSTS=true
```

**Database Schema**:
```sql
-- API Keys
CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    key_id VARCHAR(32) UNIQUE NOT NULL,
    key_hash VARCHAR(256) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    owner_id VARCHAR(50),
    permissions TEXT NOT NULL DEFAULT '[]',
    scope VARCHAR(50) NOT NULL DEFAULT 'read',
    allowed_ips TEXT,
    rate_limit INTEGER NOT NULL DEFAULT 100,
    is_active BOOLEAN NOT NULL DEFAULT true,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_used_at TIMESTAMPTZ,
    total_requests INTEGER NOT NULL DEFAULT 0,
    failed_requests INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX idx_key_hash_active ON api_keys(key_hash, is_active);
CREATE INDEX idx_owner_active ON api_keys(owner_id, is_active);
CREATE INDEX idx_expires_at ON api_keys(expires_at);

-- API Key Usage
CREATE TABLE api_key_usage (
    id SERIAL PRIMARY KEY,
    key_id VARCHAR(32) NOT NULL,
    endpoint VARCHAR(200) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER NOT NULL,
    ip_address VARCHAR(50),
    user_agent TEXT,
    request_size INTEGER,
    response_size INTEGER,
    latency_ms INTEGER,
    error_message TEXT,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_usage_key_timestamp ON api_key_usage(key_id, timestamp);
CREATE INDEX idx_usage_timestamp ON api_key_usage(timestamp);

-- API Key Audit Log
CREATE TABLE api_key_audit_log (
    id SERIAL PRIMARY KEY,
    operation VARCHAR(20) NOT NULL,
    key_id VARCHAR(32) NOT NULL,
    performed_by VARCHAR(50) NOT NULL,
    client_ip VARCHAR(50),
    old_values TEXT,
    new_values TEXT,
    reason TEXT,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_operation_timestamp ON api_key_audit_log(operation, timestamp);
CREATE INDEX idx_audit_key_id ON api_key_audit_log(key_id);
```

**모니터링 메트릭**:
- **Authentication**:
  - Authentication attempts (success/failure)
  - Authentication latency (p50, p95, p99)
  - Failed login rate
  - Account lockout events
- **Authorization**:
  - Permission denied events (403)
  - Context-based denials (time/risk)
  - Role distribution
- **Security**:
  - SQL Injection attempts
  - XSS attempts
  - Rate limit violations
  - Suspicious IP traffic
  - High-risk sessions
- **API Keys**:
  - Active keys count
  - Expired keys
  - Usage per key
  - Rate limit hits

**Alert Conditions**:
- **Critical (즉시 대응)**:
  - Authentication bypass 시도 감지
  - SQL Injection 패턴 5회 이상 (10분)
  - Rate Limit 초과 100회 이상 (1시간)
  - Failed Login 50회 이상 (동일 IP, 10분)
  - Database credential exposure 감지
- **High (1시간 이내)**:
  - PII 무단 접근 시도
  - Suspicious User-Agent 트래픽 증가 (>50%)
  - 업무 외 시간 관리 작업 시도
  - API Key 만료 7일 전
- **Medium (24시간 이내)**:
  - Rate Limit 90% 도달
  - Session timeout 증가 추세
  - Failed login rate > 10%

### OWASP Top 10 Compliance

| OWASP 위험 | 대응 메커니즘 | 구현 파일 |
|-----------|-------------|----------|
| A01:2021 – Broken Access Control | RBAC, Context-Based Auth | auth_service.py, security_manager.py |
| A02:2021 – Cryptographic Failures | PBKDF2, bcrypt, JWT HS256 | api_key_generator.py, auth_service.py |
| A03:2021 – Injection | Input Sanitization (SQL, XSS, Cmd) | security_manager.py, security_middleware.py |
| A04:2021 – Insecure Design | Rate Limiting, Account Lockout | security_middleware.py, auth_service.py |
| A05:2021 – Security Misconfiguration | Security Headers (CSP, HSTS) | security_middleware.py |
| A07:2021 – Identification Failures | JWT, API Key, Session Management | auth_service.py, security_manager.py |
| A08:2021 – Software and Data Integrity | Audit Logging, Checksum | api_key_storage.py |
| A09:2021 – Security Logging Failures | Comprehensive Audit Logs | api_key_storage.py, security_manager.py |

### 향후 개선사항

**Phase 2 계획**:
- [ ] Redis Session Store (분산 세션 관리)
- [ ] OAuth2 Integration (Google, GitHub, Azure AD)
- [ ] MFA / TOTP (2단계 인증)
- [ ] WebAuthn (생체 인증, FIDO2)
- [ ] API Key Rotation (자동 갱신, grace period)
- [ ] IP Geolocation (위험 점수 향상)
- [ ] Threat Intelligence (IP/Domain 평판 조회)
- [ ] Security Dashboard (실시간 모니터링 UI)

**최적화 기회**:
- [ ] Rate Limit Redis 분산 처리
- [ ] JWT Refresh Token 패턴 (Access + Refresh)
- [ ] API Key Scoping (엔드포인트별 세밀한 권한)
- [ ] Audit Log Retention (자동 아카이빙, 압축)
- [ ] Password Breach Detection (HaveIBeenPwned API)
- [ ] Anomaly Detection (ML 기반 이상 탐지)

## 구현 타임라인 (역공학)

| 단계 | 기간 | 상태 |
|-----|------|------|
| 1. API Key 생성 및 해시 구현 | 2일 | ✅ 완료 |
| 2. API Key CRUD 및 검증 | 2일 | ✅ 완료 |
| 3. JWT 인증 (회원가입, 로그인) | 2일 | ✅ 완료 |
| 4. JWT 검증 및 세션 관리 | 1일 | ✅ 완료 |
| 5. RBAC 역할 및 권한 체계 | 2일 | ✅ 완료 |
| 6. Context-Based Authorization | 1일 | ✅ 완료 |
| 7. Security Middleware 구현 | 3일 | ✅ 완료 |
| 8. Input/Output Sanitization | 2일 | ✅ 완료 |
| 9. Rate Limiting | 1일 | ✅ 완료 |
| 10. Security Manager 통합 | 2일 | ✅ 완료 |
| 11. Audit Logging | 1일 | ✅ 완료 |
| 12. Security Router (API 엔드포인트) | 2일 | ✅ 완료 |
| 13. Testing 및 검증 | 4일 | ✅ 완료 |
| 14. Security Hardening | 2일 | ✅ 완료 |
| 15. Production 배포 | 1일 | ✅ 완료 |

**총 구현 기간**: 28일 (역공학 기준 추정)

## 참조 문서

### 내부 문서
- `.moai/specs/SPEC-SECURITY-001/spec.md` - 상세 요구사항 (1,382줄)
- `.moai/specs/SPEC-MONITORING-001/spec.md` - 보안 메트릭 모니터링
- `.moai/specs/SPEC-COMPLIANCE-001/spec.md` - GDPR/CCPA PII 처리
- `.moai/specs/SPEC-AUDIT-001/spec.md` - 감사 로그 및 추적성

### 구현 파일
- `apps/security/core/security_manager.py` (613줄)
- `apps/security/middleware/security_middleware.py` (727줄)
- `apps/security/auth/auth_service.py` (576줄)
- `apps/security/routers/security_router.py` (706줄)
- `apps/api/security/api_key_generator.py` (334줄)
- `apps/api/security/api_key_storage.py` (695줄)

**총 코드**: 3,651줄 (주석 및 공백 포함)

### Database Schema
- `api_keys` - API 키 메타데이터 및 해시
- `api_key_usage` - 요청별 사용 로그
- `api_key_audit_log` - 관리 작업 감사 로그

### 외부 문서
- [OWASP Top 10 2021](https://owasp.org/Top10/)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [JWT Best Practices](https://datatracker.ietf.org/doc/html/rfc8725)
- [NIST Password Guidelines](https://pages.nist.gov/800-63-3/sp800-63b.html)
- [bcrypt Documentation](https://pypi.org/project/bcrypt/)
- [PyJWT Documentation](https://pyjwt.readthedocs.io/)

---

**문서 버전**: v0.1.0
**최종 업데이트**: 2025-10-09
**작성자**: @Claude
**상태**: Completed
