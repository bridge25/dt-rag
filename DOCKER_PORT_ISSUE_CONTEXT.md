# Docker Desktop WSL2 포트 바인딩 문제 - 현재 상황 정리

## 문제 요약
Windows 11 환경에서 Docker Desktop + WSL2로 dt-rag 프로젝트 실행 시, API(8000)와 Frontend(3000) 포트만 호스트에 바인딩되지 않는 문제

## 환경 정보
- OS: Windows 11 (Build 26100.6584)
- Docker Desktop: 최신 버전 (WSL2 backend)
- Docker Compose: v2.39.4-desktop.1
- WSL2: Ubuntu 배포판
- WSL2 IP: 192.168.0.22
- 작업 디렉토리: C:\MYCLAUDE_PROJECT\sonheungmin\Unmanned\dt-rag

## 현재 컨테이너 상태
```
dt_rag_frontend        Up (healthy)   3000/tcp
dt_rag_api             Up (healthy)   8000/tcp
dt_rag_postgres_test   Up (healthy)   0.0.0.0:5433->5432/tcp, [::]:5433->5432/tcp
dt_rag_postgres        Up (healthy)   0.0.0.0:5432->5432/tcp, [::]:5432->5432/tcp
dt_rag_redis           Up (healthy)   0.0.0.0:6379->6379/tcp, [::]:6379->6379/tcp
```

**문제**: API와 Frontend만 `0.0.0.0:포트->포트`가 아닌 `포트/tcp`만 표시됨

## 확인된 사실들

### 1. 서비스는 정상 작동 중
- WSL2 내부에서 `docker exec dt_rag_api curl http://localhost:8000/health` → 정상 응답
- API 로그에서 `Uvicorn running on http://0.0.0.0:8000` 확인
- 모든 컨테이너 health check 통과

### 2. Docker 설정은 올바름
- `docker inspect dt_rag_api --format='{{json .HostConfig.PortBindings}}'` 결과:
  ```json
  {"8000/tcp":[{"HostIp":"0.0.0.0","HostPort":"8000"}]}
  ```
- docker-compose.yml의 ports 설정 올바름
- `docker compose config`에서 파싱 결과 올바름

### 3. PostgreSQL과 Redis는 정상 바인딩
- postgres, postgres_test, redis는 `0.0.0.0:포트`에 정상 바인딩
- 동일한 docker-compose.yml 파일에서 일부만 바인딩 실패

### 4. docker run은 정상 작동
- 테스트: `docker run -d --name test_nginx -p 8888:80 nginx:alpine`
- 결과: `0.0.0.0:8888->80/tcp` 정상 바인딩
- docker-compose.test.yml로 간단한 nginx 테스트도 정상 바인딩

### 5. Windows 호스트에서 접근 불가
- `curl http://localhost:8000` → 타임아웃
- `curl http://192.168.0.22:8000` (WSL2 IP) → 타임아웃
- WSL2 호스트에서 `ss -tlnp | grep 8000` → 포트 리스닝 없음

### 6. Hyper-V 포트 제외 없음
- `netsh interface ipv4 show excludedportrange protocol=tcp`
- 결과: 50000-50059만 제외됨, 8000/3000 제외 없음

## 시도한 해결 방법들

### 1. WSL2 재시작
```bash
wsl --shutdown
```
→ 효과 없음, Docker 이미지 캐시 손상으로 재빌드 필요했음

### 2. Docker Desktop 재시작
```bash
taskkill /F /IM "Docker Desktop.exe"
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
```
→ 효과 없음

### 3. docker-compose.yml 포트 설정 변경 시도
- `"${API_PORT:-8000}:8000"` → `"0.0.0.0:8000:8000"` → 효과 없음
- long-form syntax with `mode: host` → 효과 없음
- 최종적으로 `"8000:8000"` 단순 형식으로 복귀

### 4. 컨테이너 재생성
```bash
docker compose down
docker compose up -d
docker compose up -d --force-recreate api frontend
```
→ 모두 효과 없음

### 5. 수동 포트 포워딩 시도 (관리자 권한)
```powershell
netsh interface portproxy add v4tov4 listenport=8000 listenaddress=0.0.0.0 connectport=8000 connectaddress=192.168.0.22
netsh interface portproxy add v4tov4 listenport=3000 listenaddress=0.0.0.0 connectport=3000 connectaddress=192.168.0.22
```
- portproxy 설정은 성공적으로 추가됨
- `netstat -ano | findstr 8000` → `0.0.0.0:8000 LISTENING 3992` 확인
- 하지만 여전히 접근 불가 (WSL2 호스트에 포트가 리스닝하지 않음)

## 현재 docker-compose.yml 포트 설정
```yaml
# API
api:
  ports:
    - "8000:8000"

# Frontend
frontend:
  ports:
    - "3000:3000"

# PostgreSQL (정상 작동)
postgres:
  ports:
    - "${POSTGRES_PORT:-5432}:5432"

# Redis (정상 작동)
redis:
  ports:
    - "${REDIS_PORT:-6379}:6379"
```

## 컨테이너 네트워크 정보
- Network: dt-rag_dt_rag_network (bridge driver)
- API Container IP: 172.19.0.5
- Frontend Container IP: 172.19.0.6
- Windows에서 172.19.0.x 네트워크로 직접 접근 불가

## 핵심 문제점

**Docker Compose가 API와 Frontend 컨테이너에 대해서만 포트 바인딩을 실제로 적용하지 않음**

증거:
1. HostConfig.PortBindings에는 설정이 있음
2. NetworkSettings.Ports는 비어있음: `{"8000/tcp": []}`
3. `docker ps`에 포트 매핑이 표시되지 않음
4. 같은 파일의 다른 서비스(postgres, redis)는 정상 작동
5. `docker run` 직접 실행 시 정상 작동
6. 간단한 docker-compose.test.yml은 정상 작동

## 다음 단계 제안

### Option 1: docker-compose.yml 문제 원인 규명
- API와 Frontend 서비스 정의에 postgres/redis와 다른 특이사항 확인
- depends_on, healthcheck, volumes 등의 영향 가능성 조사

### Option 2: Docker Desktop 설정 문제 해결
- Docker Desktop → Settings → Resources → WSL Integration 확인
- .wslconfig에 mirrored networking 설정 시도

### Option 3: 임시 우회 방법
- docker run으로 API와 Frontend 수동 실행
- 또는 별도의 간소화된 docker-compose 파일 사용

## 추가 디버깅 정보

### 컨테이너 로그 (API)
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     127.0.0.1:46986 - "GET /health HTTP/1.1" 200 OK
```

### Docker Inspect 상세 (API)
```json
HostConfig.PortBindings: {"8000/tcp":[{"HostIp":"0.0.0.0","HostPort":"8000"}]}
Config.ExposedPorts: {"8000/tcp":{}}
NetworkSettings.Ports: {"8000/tcp": []}  ← 문제!
```

## 참고 자료
- WSL2 Docker 포트 포워딩 문제는 알려진 이슈
- Docker Desktop의 WSL2 통합 문제로 sleep/wake 후 localhost 접근 실패 보고 다수
- 일부 사용자는 Docker Desktop 재설치로 해결

## 현재 상태로 작업 인계
- 모든 컨테이너 실행 중 (healthy)
- API와 Frontend는 내부적으로 정상 작동
- 포트 바인딩만 누락된 상태
- docker-compose.yml은 최종적으로 단순한 `"포트:포트"` 형식으로 설정됨
