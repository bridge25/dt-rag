# DT-RAG 기능 직접 체험 가이드

## 🚀 접속 정보

### 서비스 URL
- **API Server**: http://localhost:8000
- **OpenAPI Docs**: http://localhost:8000/docs
- **Frontend**: http://localhost:3000

### Admin API Key
```
admin_WLYyK1OiTfjKF3vdb1mXyvsDog-3jMe_MtX69_uA-ed9b
```
(Key ID: c00067cad271ad49)

---

## 📝 방법 1: 브라우저에서 OpenAPI Docs 사용 (가장 쉬움)

### 1단계: OpenAPI Docs 열기
브라우저에서 접속:
```
http://localhost:8000/docs
```

### 2단계: 인증 설정
1. 우측 상단 **"Authorize"** 버튼 클릭
2. "X-API-Key" 필드에 다음 키 입력:
   ```
   admin_WLYyK1OiTfjKF3vdb1mXyvsDog-3jMe_MtX69_uA-ed9b
   ```
3. **"Authorize"** 클릭 후 **"Close"**

### 3단계: API Key 생성 테스트
1. **"API Key Management"** 섹션 찾기
2. **POST /api/v1/admin/api-keys/** 클릭
3. **"Try it out"** 클릭
4. Request body 입력:
   ```json
   {
     "name": "My Test Key",
     "description": "Testing the API",
     "scope": "read",
     "rate_limit": 100
   }
   ```
5. **"Execute"** 클릭
6. Response에서 생성된 API key 확인 (한 번만 보임!)

### 4단계: API Key 업데이트 테스트
1. **PUT /api/v1/admin/api-keys/{key_id}** 클릭
2. **"Try it out"** 클릭
3. `key_id`에 생성된 키의 ID 입력 (예: b50c87342434415c)
4. Request body 입력:
   ```json
   {
     "name": "Updated Test Key",
     "description": "Updated description",
     "rate_limit": 200
   }
   ```
5. **"Execute"** 클릭
6. Response에서 업데이트된 정보 확인

### 5단계: Usage Statistics 조회
1. 생성한 API key로 몇 번 요청 보내기:
   - **POST /api/v1/search/** 에서 검색 요청 3-5회 실행
2. **GET /api/v1/admin/api-keys/{key_id}/usage** 클릭
3. **"Try it out"** 클릭
4. `key_id` 입력
5. `days` 파라미터: 7 (기본값)
6. **"Execute"** 클릭
7. Response 확인:
   ```json
   {
     "key_id": "...",
     "total_requests": 5,
     "failed_requests": 0,
     "requests_last_24h": 5,
     "requests_last_7d": 5,
     "most_used_endpoints": [
       {"endpoint": "/api/v1/search/", "method": "POST", "count": 5}
     ]
   }
   ```

---

## 💻 방법 2: curl 명령어 사용

### 1. API Key 생성
```bash
curl -X POST http://localhost:8000/api/v1/admin/api-keys/ \
  -H "Content-Type: application/json" \
  -H "X-API-Key: admin_WLYyK1OiTfjKF3vdb1mXyvsDog-3jMe_MtX69_uA-ed9b" \
  -d '{
    "name": "My Test Key",
    "description": "Testing the API",
    "scope": "read",
    "rate_limit": 100
  }'
```

**결과 예시**:
```json
{
  "api_key": "read_xxxxxx...",
  "key_info": {
    "key_id": "abc123...",
    "name": "My Test Key",
    ...
  }
}
```

### 2. API Key 목록 조회
```bash
curl -X GET http://localhost:8000/api/v1/admin/api-keys/ \
  -H "X-API-Key: admin_WLYyK1OiTfjKF3vdb1mXyvsDog-3jMe_MtX69_uA-ed9b"
```

### 3. API Key 업데이트
```bash
# {key_id}를 실제 key_id로 교체
curl -X PUT http://localhost:8000/api/v1/admin/api-keys/{key_id} \
  -H "Content-Type: application/json" \
  -H "X-API-Key: admin_WLYyK1OiTfjKF3vdb1mXyvsDog-3jMe_MtX69_uA-ed9b" \
  -d '{
    "name": "Updated Name",
    "description": "Updated description",
    "rate_limit": 200
  }'
```

### 4. 생성한 키로 검색 요청 (Usage 데이터 생성)
```bash
# {your_api_key}를 생성한 API key로 교체
curl -X POST http://localhost:8000/api/v1/search/ \
  -H "Content-Type: application/json" \
  -H "X-API-Key: {your_api_key}" \
  -d '{
    "q": "test query",
    "final_topk": 3
  }'
```

이 요청을 3-5번 반복해서 사용 데이터를 생성하세요.

### 5. Usage Statistics 조회
```bash
# {key_id}를 실제 key_id로 교체
curl -X GET "http://localhost:8000/api/v1/admin/api-keys/{key_id}/usage?days=7" \
  -H "X-API-Key: admin_WLYyK1OiTfjKF3vdb1mXyvsDog-3jMe_MtX69_uA-ed9b"
```

---

## 🎨 방법 3: Postman/Insomnia 사용

### 1. 새 Request 생성
- Method: POST
- URL: `http://localhost:8000/api/v1/admin/api-keys/`

### 2. Headers 설정
```
Content-Type: application/json
X-API-Key: admin_WLYyK1OiTfjKF3vdb1mXyvsDog-3jMe_MtX69_uA-ed9b
```

### 3. Body (JSON)
```json
{
  "name": "My Test Key",
  "description": "Testing the API",
  "scope": "read",
  "rate_limit": 100
}
```

### 4. Send 클릭

나머지 엔드포인트도 동일한 방식으로 테스트 가능합니다.

---

## 📊 테스트 시나리오 예시

### 완전한 테스트 플로우
1. **API Key 생성**: 새로운 read scope 키 생성
2. **정보 확인**: 생성된 키의 정보 조회
3. **사용 데이터 생성**: 생성한 키로 검색 요청 5회 실행
4. **Statistics 확인**: Usage statistics 조회 → 5 requests 확인
5. **업데이트**: Name과 rate_limit 변경
6. **재확인**: 변경된 정보 확인
7. **Revoke**: 테스트 완료 후 키 비활성화

---

## 🔍 Audit Log 확인 (추가)

데이터베이스에서 직접 확인:
```bash
docker exec dt_rag_postgres psql -U postgres -d dt_rag -c \
  "SELECT operation, key_id, reason, timestamp
   FROM api_key_audit_log
   ORDER BY timestamp DESC
   LIMIT 10;"
```

모든 API key 변경사항과 보안 이벤트가 기록되어 있습니다.

---

## ⚠️ 주의사항

1. **API Key는 한 번만 표시됩니다**
   - 생성 시 plaintext key를 반드시 저장하세요
   - 이후에는 key_id로만 관리됩니다

2. **Admin 권한 필요**
   - API Key 관리 엔드포인트는 admin scope 필요
   - 제공된 admin key를 사용하세요

3. **Test 환경**
   - 현재 development 모드 (ENABLE_TEST_API_KEYS=true)
   - Production에서는 test key가 자동 비활성화됩니다

---

## 🎯 기대 결과

✅ API Key 생성 → 즉시 사용 가능한 키 발급
✅ API Key 업데이트 → Name, description, rate_limit 변경 확인
✅ Usage Statistics → Real-time 사용 통계 확인
✅ Audit Logging → 모든 변경사항 추적 가능

---

**작성일**: 2025-10-08
**API Version**: v1.8.1
**Status**: Production Ready ✅
