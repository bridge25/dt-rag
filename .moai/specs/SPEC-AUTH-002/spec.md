---
id: AUTH-002
title: API 키 생성 및 검증 시스템
domain: auth
version: 1.0.0
status: completed
created: 2025-10-24
author: spec-builder
---

# SPEC-AUTH-002: API 키 생성 및 검증 시스템

## HISTORY

### v1.0.0 (2025-10-24)
- **RETROACTIVE DOCUMENTATION**: 기존 구현 완료된 API 키 관리 시스템을 문서화
- UUID 기반 API 키 생성 로직 구현 (`crypto.randomUUID()`)
- API 키 저장 및 검증 엔드포인트 구현 (`/api/key/`)
- 환경 변수 기반 키 검증 구현 (`.env.local` 연동)

---

## Environment

**WHEN** 외부 클라이언트가 보호된 API 엔드포인트에 접근하려는 경우

---

## Assumptions

- Next.js 15 App Router 환경에서 실행
- Node.js 18 이상 (crypto.randomUUID 지원)
- 환경 변수 관리는 `.env.local` 사용
- API 키는 `NEXT_PUBLIC_API_KEY` 환경 변수에 저장

---

## Requirements

**R1**: 시스템은 UUID v4 형식의 고유한 API 키를 생성할 수 있어야 한다
**R2**: 시스템은 생성된 API 키를 안전하게 저장하고 검증할 수 있어야 한다
**R3**: API 키 검증은 환경 변수와의 비교를 통해 수행되어야 한다
**R4**: 잘못된 API 키 요청 시 401 Unauthorized 응답을 반환해야 한다

---

## Specifications

### API 키 생성 (`/api/key/route.ts`)

**Endpoint**: `POST /api/key`

**Request**:
```json
{}
```

**Response (200 OK)**:
```json
{
  "apiKey": "550e8400-e29b-41d4-a716-446655440000"
}
```

**구현 로직**:
- `crypto.randomUUID()` 사용하여 UUID v4 생성
- 생성된 키를 JSON 응답으로 반환

### API 키 검증 미들웨어 (개념적)

**검증 로직**:
1. 요청 헤더 또는 쿼리 파라미터에서 `apiKey` 추출
2. `process.env.NEXT_PUBLIC_API_KEY`와 비교
3. 일치 시 요청 허용, 불일치 시 401 반환

**환경 변수 구조 (`.env.local`)**:
```bash
NEXT_PUBLIC_API_KEY=550e8400-e29b-41d4-a716-446655440000
```

### 파일 구조

```
app/
└── api/
    └── key/
        └── route.ts                # @CODE:AUTH-002:API
.env.local                          # @CODE:AUTH-002:INFRA
```

---

## Traceability

- **@SPEC:AUTH-002**: 본 문서
- **@CODE:AUTH-002:API**: `app/api/key/route.ts`
- **@CODE:AUTH-002:INFRA**: `.env.local` (환경 변수 관리)
- **@TEST:AUTH-002**: (미구현 - 테스트 누락 상태)

---

## Acceptance Criteria

### AC1: API 키 생성

**Given** `/api/key` 엔드포인트가 존재하고
**When** POST 요청을 전송하면
**Then**
- 200 OK 응답을 받아야 함
- 응답 본문에 `apiKey` 필드가 있어야 함
- `apiKey`는 UUID v4 형식이어야 함

### AC2: API 키 검증

**Given** 환경 변수에 유효한 API 키가 설정되어 있고
**When** 올바른 API 키로 보호된 엔드포인트에 요청하면
**Then**
- 요청이 허용되어야 함

**Given** 잘못된 API 키로 요청하면
**Then**
- 401 Unauthorized 응답을 받아야 함

### AC3: 환경 변수 통합

**Given** `.env.local` 파일에 `NEXT_PUBLIC_API_KEY`가 설정되어 있고
**When** 애플리케이션이 시작되면
**Then**
- 환경 변수가 정상적으로 로드되어야 함
- 키 검증 로직에서 해당 값을 참조할 수 있어야 함

---

## Notes

- 본 SPEC은 이미 구현 완료된 코드를 소급 문서화한 것임
- 실제 구현은 2025-10-24 이전에 완료되었으며, TAG는 누락된 상태
- **테스트 누락**: `/api/key/route.ts`에 대한 단위 테스트 없음
- **보안 권장사항**: 프로덕션 환경에서는 API 키를 서버 전용 환경 변수로 이동 필요 (`NEXT_PUBLIC_` 접두사 제거)
- 다음 단계: `/alfred:3-sync`를 통해 TAG 추가 및 테스트 보완 필요
