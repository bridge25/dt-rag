# 🚨 보안 사고 보고서 - API 키 노출

## 📋 사고 개요
- **발생일**: 2025-09-21 ~ 2025-09-23
- **영향도**: **HIGH** - Google Gemini API 키 공개 저장소 노출
- **발견일**: 2025-09-24
- **상태**: 🚨 **즉시 조치 필요**

## 🔍 노출된 API 키

### 1. **Gemini API 키 #1**
- **키**: `AIzaSyCKmR4jxB8Gg2TfCBqmz7k850YwplS9EhY`
- **위치**: `.env` 파일
- **커밋**: 7d72a38 (2025-09-23)
- **노출 기간**: 약 1일

### 2. **Gemini API 키 #2**
- **키**: `AIzaSyBlEJuO9LGLdCJRfhNU6QIKRUQ-Q22Vl7E`
- **위치**: `.github/workflows/ci.yml`
- **커밋**: 51594ba (2025-09-21)
- **노출 기간**: 약 3일

## ⚠️ 추가 발견사항
- **테스트용 키들도 노출**:
  - OpenAI: `test-key-for-ci`
  - Anthropic: `test-key-for-ci`
  - 다행히 실제 키가 아닌 테스트용

## 🚨 즉시 조치 사항

### **1. API 키 무효화 (최우선)**
```bash
# Google Cloud Console에서 즉시 실행:
# 1. https://console.cloud.google.com/apis/credentials 접속
# 2. 해당 API 키들 찾기:
#    - AIzaSyCKmR4jxB8Gg2TfCBqmz7k850YwplS9EhY
#    - AIzaSyBlEJuO9LGLdCJRfhNU6QIKRUQ-Q22Vl7E
# 3. "Delete" 또는 "Regenerate" 버튼 클릭
# 4. 새로운 키 생성 및 안전한 저장
```

### **2. 저장소에서 즉시 제거**
```bash
# .env 파일에서 실제 키 제거
echo "GEMINI_API_KEY=your_api_key_here" > .env.example
git rm .env
git add .env.example

# CI 파일에서 실제 키를 GitHub Secrets로 변경
# .github/workflows/ci.yml에서:
# GEMINI_API_KEY: AIzaSy...
# → GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
```

### **3. Git 히스토리에서 완전 제거**
```bash
# 🚨 경고: 이 작업은 force push가 필요함
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch .env' \
  --prune-empty --tag-name-filter cat -- --all

# 또는 BFG Repo-Cleaner 사용 (권장)
# java -jar bfg.jar --replace-text passwords.txt your-repo.git
```

## 📊 영향 평가

### **잠재적 피해**
- ✅ **낮음**: 키가 임베딩 용도로만 사용됨
- ⚠️ **중간**: Google Gemini API 할당량 남용 가능
- 🚨 **높음**: 무료 할당량 소진 또는 요금 청구 위험

### **실제 사용량 확인 필요**
```bash
# Google Cloud Console에서 확인:
# 1. API & Services → Dashboard
# 2. Gemini API 사용량 모니터링
# 3. 비정상적인 트래픽 패턴 확인
```

## 🛡️ 예방 조치

### **1. .gitignore 강화**
```gitignore
# API Keys and Secrets
.env
.env.local
.env.production
*.key
*api_key*
*secret*
credentials.json
service-account-*.json
```

### **2. GitHub Secrets 사용**
```yaml
# .github/workflows/ci.yml
env:
  GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

### **3. 사전 커밋 훅 설정**
```bash
# .git/hooks/pre-commit
#!/bin/sh
if grep -r "AIzaSy" --include="*.py" --include="*.yml" --include="*.json" .; then
    echo "❌ API 키가 감지되었습니다!"
    exit 1
fi
```

### **4. 정기 보안 스캔**
- GitHub Secret Scanning 활성화
- gitleaks, truffleHog 등 도구 사용
- 주간 보안 리뷰 실시

## ✅ 완료 체크리스트

- [ ] Google Cloud Console에서 노출된 API 키 무효화
- [ ] 새로운 API 키 생성 및 GitHub Secrets에 저장
- [ ] .env 파일 저장소에서 제거
- [ ] CI 워크플로우를 GitHub Secrets 사용하도록 수정
- [ ] Git 히스토리에서 API 키 완전 제거
- [ ] .gitignore에 보안 항목 추가
- [ ] 팀원들에게 보안 가이드라인 공유
- [ ] 사전 커밋 훅 설정
- [ ] Google Cloud Console에서 API 사용량 모니터링 설정

## 🔗 참고 자료
- [GitHub Secrets 사용법](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Git에서 민감한 데이터 제거](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
- [Google Cloud API 키 보안](https://cloud.google.com/docs/authentication/api-keys)

---
**⚡ 긴급도**: 최우선 처리 필요
**담당자**: 프로젝트 관리자 + 동료 개발자
**예상 처리 시간**: 30분 ~ 2시간