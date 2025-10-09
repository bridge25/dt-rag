# 🎯 실제 사용자 체감 동작 확인 가이드

> **목적**: GitHub 마스터 브랜치의 코드가 실제 사용자가 체감할 수 있게 동작하는지 확인
> **대상**: 프로젝트 완성도를 실제로 검증하고 싶은 사용자
> **시간**: 약 5-10분

## 🚀 **1단계: 기본 동작 확인 (2분)**

### ✅ **핵심 컴포넌트 테스트**
```bash
# 1. 테스트 스크립트 실행
PYTHONIOENCODING=utf-8 /c/Users/a/AppData/Local/Programs/Python/Python313/python.exe quick_test.py

# 기대 결과:
# ✅ FASTAPI: 성공
# ✅ PYDANTIC: 성공
# ✅ UVICORN: 성공
# 🎯 전체 결과: 3/3 성공
```

**✅ 성공 시**: 모든 핵심 웹 서버 컴포넌트가 정상 동작
**❌ 실패 시**: 필수 패키지 누락 (pip3 install 필요)

## 🌐 **2단계: 실제 웹 서버 실행 (3분)**

### **방법 A: 테스트 서버 (간단)**
```bash
# 1. 테스트 서버 실행
PYTHONIOENCODING=utf-8 /c/Users/a/AppData/Local/Programs/Python/Python313/python.exe test_server.py

# 2. 브라우저 또는 curl로 접속
curl http://localhost:8001
curl http://localhost:8001/health
```

**기대 결과**:
```json
{
  "name": "Dynamic Taxonomy RAG API - Test Server",
  "status": "✅ 실제 동작 중",
  "message": "서버가 정상적으로 실행되고 있습니다!"
}
```

### **방법 B: 풀 서버 (완전한 기능)**
```bash
# 1. API 서버 디렉토리로 이동
cd apps/api

# 2. 풀 서버 실행 (데이터베이스 없이도 동작)
PYTHONIOENCODING=utf-8 /c/Users/a/AppData/Local/Programs/Python/Python313/python.exe main.py

# 3. 브라우저에서 확인
# http://localhost:8000 - 메인 API
# http://localhost:8000/docs - Swagger 문서
# http://localhost:8000/health - 헬스체크
```

**기대 결과**:
```json
{
  "name": "Dynamic Taxonomy RAG API",
  "version": "1.8.1",
  "status": "Production Ready",
  "features": {
    "classification": "ML-based with HITL support",
    "search": "BM25 + Vector hybrid with reranking"
  }
}
```

## 🧪 **3단계: API 기능 테스트 (5분)**

### **A. 헬스체크 엔드포인트**
```bash
curl http://localhost:8000/health

# 기대 결과: {"status": "healthy", "version": "1.8.1"}
```

### **B. API 문서 접속**
브라우저에서 `http://localhost:8000/docs` 접속

**기대 결과**:
- 📋 Swagger UI 인터페이스
- 🔧 Interactive API 테스트 가능
- 📖 모든 엔드포인트 문서화

### **C. 검색 API 테스트** (데이터베이스 없어도 폴백 모드로 동작)
```bash
curl -X POST "http://localhost:8000/api/v1/search" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "테스트 검색",
       "max_results": 5
     }'
```

### **D. 분류 API 테스트**
```bash
curl -X POST "http://localhost:8000/api/v1/classify" \
     -H "Content-Type: application/json" \
     -d '{
       "text": "이것은 테스트 문서입니다",
       "confidence_threshold": 0.7
     }'
```

## 📊 **4단계: 실제 동작 확인 체크리스트**

사용자가 직접 확인할 수 있는 항목들:

### ✅ **기본 동작 확인**
- [ ] `quick_test.py` 실행 시 3/3 성공
- [ ] 서버 실행 시 오류 없이 시작
- [ ] `curl http://localhost:8000/health` 응답 정상

### ✅ **웹 인터페이스 확인**
- [ ] http://localhost:8000 접속 시 JSON 응답
- [ ] http://localhost:8000/docs 접속 시 Swagger UI 표시
- [ ] API 문서에서 엔드포인트들이 모두 보임

### ✅ **API 기능 확인**
- [ ] POST 요청이 정상적으로 처리됨
- [ ] JSON 응답이 올바른 형식으로 반환
- [ ] 오류 처리가 적절히 동작

### ✅ **성능 확인**
- [ ] 서버 시작 시간 < 10초
- [ ] API 응답 시간 < 3초
- [ ] 메모리 사용량이 안정적

## 🎯 **성공 기준**

### **🏆 완전 성공** (100% 동작)
- 모든 컴포넌트 테스트 통과
- 서버가 오류 없이 시작 및 실행
- 모든 API 엔드포인트가 정상 응답
- Swagger 문서가 완전히 로드

### **✅ 부분 성공** (폴백 모드)
- 핵심 컴포넌트는 동작
- 서버는 시작되지만 일부 기능 제한
- 기본 API는 응답하지만 고급 기능은 데이터베이스 필요

### **❌ 실패**
- 컴포넌트 테스트 실패
- 서버 시작 불가
- API 엔드포인트 무응답

## 🔧 **문제 해결**

### **일반적인 문제들**

#### **1. 모듈 임포트 오류**
```bash
# 해결: 패키지 설치
pip3 install --break-system-packages fastapi uvicorn pydantic
```

#### **2. 포트 충돌**
```bash
# 해결: 다른 포트 사용
python3 test_server.py  # 포트 8001 사용
```

#### **3. 경로 문제**
```bash
# 해결: 절대 경로 사용
PYTHONIOENCODING=utf-8 /c/Users/a/AppData/Local/Programs/Python/Python313/python.exe [스크립트]
```

## 📝 **결론**

이 가이드를 통해 사용자는:

1. **✅ 코드가 실제로 실행되는지** 확인 가능
2. **✅ 웹 서버가 정상 동작하는지** 확인 가능
3. **✅ API가 실제 요청에 응답하는지** 확인 가능
4. **✅ 프로덕션 배포 준비 상태인지** 확인 가능

**🎉 모든 단계를 통과하면 GitHub 마스터 브랜치의 코드가 실제 사용자가 체감할 수 있게 완전히 동작한다고 확신할 수 있습니다!**

---
**⚡ 빠른 확인**: `PYTHONIOENCODING=utf-8 /c/Users/a/AppData/Local/Programs/Python/Python313/python.exe quick_test.py` 한 번만 실행해도 기본 동작을 즉시 확인 가능!