# GitHub Codespace 테스트 가이드

## 📋 현재 상황 분석 (2025-09-25)

### 🔍 GitHub 마스터 브랜치 구조
```
/Unmanned/ (GitHub 루트)
├── apps/ (75개 기본 파일 - 불완전한 뼈대)
├── README.md
├── ...기타 루트 파일들 (총 75개 파일)
└── dt-rag/ ⭐ PR16에서 추가된 완전한 DT-RAG 시스템!
    ├── apps/
    │   ├── frontend-admin/ ← 프론트엔드 (Next.js v1.8.1)
    │   └── api/ ← 완전한 백엔드 (FastAPI)
    ├── full_server.py ← 완전 기능 서버
    ├── tests/ ← 완전한 테스트 인프라
    └── ...9만줄 완전한 코드
```

### ✅ 검증된 사실들
- **PR16 정상 병합**: `[RAG v1.8.1] Complete Dynamic Taxonomy RAG System - Production Ready` (2025-09-19 병합)
- **9만줄 코드 존재**: 모두 `/dt-rag/` 서브디렉토리에 위치
- **로컬 완전 동작**: 포트 8002(백엔드) + 포트 3000(프론트엔드) 정상 실행
- **커밋 동기화**: 로컬(`f6cf259`) = GitHub(`f6cf259`) - 완전히 동일

### 🎯 **핵심 발견**: 디렉토리 구조 차이
- **로컬 작업 위치**: `/Unmanned/dt-rag/` 안에서 작업 중
- **GitHub 실제 구조**: 루트 75개 파일 + `dt-rag/` 서브디렉토리
- **혼란의 원인**: 루트에서 파일 수를 확인하면 75개, dt-rag 안을 보면 수만개

## 🎯 테스트 목표

### 주요 목표
1. **순수 GitHub 마스터 브랜치 테스트**: 로컬 변경사항과 완전 분리된 환경에서 검증
2. **클라우드 환경 동작 확인**: GitHub Codespace에서 완전한 시스템 동작 검증
3. **신뢰성 보장**: 로컬 환경의 의존성 없이 완전 자율 동작 확인

### 테스트 항목
- [ ] API 서버 정상 실행 (full_server.py)
- [ ] 프론트엔드 정상 실행 (Next.js)
- [ ] 하이브리드 검색 기능 동작
- [ ] 문서 분류 기능 동작
- [ ] 모든 API 엔드포인트 응답 확인

## 🚀 추천 해결책: Codespace + dt-rag 이동

### 방법 1: 즉시 해결 (추천)
```bash
# 1. 코드스페이스 생성
gh codespace create --repo bridge25/Unmanned --branch master

# 2. 코드스페이스 접속 후 dt-rag로 이동
cd dt-rag

# 3. 의존성 설치 및 서버 실행
pip install -r requirements.txt  # 필요시
python full_server.py

# 4. 프론트엔드 실행 (새 터미널)
cd apps/frontend-admin
npm install
npm run dev
```

### 방법 2: 구조 재편 (장기적)
- dt-rag 내용을 루트로 이동
- 기존 루트 파일들 정리
- 모든 경로 참조 수정
- **권장 안함**: 위험도 높고 시간 소요

## 🔧 예상 이슈 및 해결책

### Issue 1: Import 경로 오류
```bash
# 문제: 상대 import 오류
ImportError: attempted relative import beyond top-level package

# 해결: Python 모듈로 실행
python -m uvicorn apps.api.main:app --host 0.0.0.0 --port 8002
```

### Issue 2: 의존성 누락
```bash
# 필요시 설치
pip install tiktoken psycopg2-binary aiosqlite
```

### Issue 3: 포트 포워딩
- Codespace에서 자동 포트 포워딩 설정
- 8002 (API), 3000 (Frontend) 포트 확인

## 📊 테스트 체크리스트

### 백엔드 테스트
- [ ] `curl http://localhost:8002/health` - 헬스체크
- [ ] `curl http://localhost:8002/docs` - Swagger UI 접근
- [ ] POST `/api/v1/search` - 검색 기능
- [ ] POST `/api/v1/classify` - 분류 기능
- [ ] GET `/api/v1/taxonomy` - 분류체계 조회

### 프론트엔드 테스트
- [ ] `http://localhost:3000` 접근 가능
- [ ] 검색 폼 동작
- [ ] 분류 폼 동작
- [ ] API 연동 정상 (백엔드와 통신)

## 🎯 성공 기준

### 완료 조건
1. **GitHub Codespace에서 전체 시스템 정상 동작**
2. **프론트엔드-백엔드 완전 연동**
3. **모든 핵심 기능 동작 확인**
4. **로컬 의존성 없는 완전 자율 실행**

### 검증 방법
- 실제 검색 쿼리 입력 및 결과 확인
- 문서 분류 테스트 및 결과 확인
- 모든 API 엔드포인트 응답 시간 측정
- 시스템 안정성 확인 (최소 10분간 지속 실행)

## 📝 다음 단계

1. **즉시**: Codespace 생성 및 dt-rag 이동 테스트
2. **단기**: 발견된 이슈들 문서화 및 수정
3. **장기**: 필요시 구조 재편 검토

---

**작성일**: 2025-09-25
**상태**: 테스트 준비 완료
**다음 작업**: GitHub Codespace에서 dt-rag 디렉토리 테스트 실행