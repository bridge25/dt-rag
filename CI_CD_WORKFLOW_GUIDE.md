# 🚀 CI/CD 워크플로우 가이드

> **프로젝트**: Dynamic Taxonomy RAG  
> **업데이트**: 2025-09-11  
> **대상**: 모든 개발팀 구성원

## 📋 목차

1. [개요](#-개요)
2. [워크플로우 작동 방식](#-워크플로우-작동-방식)
3. [PR 생성 가이드](#-pr-생성-가이드)
4. [CI 결과 해석](#-ci-결과-해석)
5. [문제 해결](#-문제-해결)
6. [특별 기능](#-특별-기능)
7. [FAQ](#-faq)

---

## 🎯 개요

이 프로젝트는 **자동화된 CI/CD 시스템**을 통해 코드 품질과 안전성을 보장합니다. 모든 Pull Request는 자동으로 검증되며, 통과한 경우에만 master 브랜치에 병합할 수 있습니다.

### ✨ 주요 특징
- **🔒 자동 품질 검증**: 테스트, 린트, 데이터베이스 마이그레이션 검증
- **⚡ 지능형 최적화**: 문서만 수정 시 CI 스킵으로 90% 시간 절약
- **🛡️ 안전한 배포**: Alembic 롤백 테스트로 데이터베이스 안전성 보장
- **🤖 AI 친화적**: 실패 시 Claude/GPT 수정 가이드 자동 생성

---

## 🔄 워크플로우 작동 방식

### 1️⃣ **PR 생성 시 자동 실행**
```
PR 생성/업데이트 → CI 워크플로우 자동 시작
```

### 2️⃣ **변경사항 분석**
- **문서만 변경** (`*.md`, `docs/`, `README.md`): CI 스킵 ⏭️
- **코드 변경**: 전체 검증 실행 🔍

### 3️⃣ **자동 검증 단계**

#### **Python 프로젝트** (requirements.txt 있을 시)
```yaml
✅ Python 3.11 설정
✅ 의존성 설치 (pip 캐시 활용)
✅ Alembic 데이터베이스 마이그레이션
✅ Alembic 롤백 스모크 테스트 (안전성 검증)
✅ Ruff 린트 검사
✅ Pytest 유닛 테스트
```

#### **Node.js 프로젝트** (package.json 있을 시)
Node.js 관련 단계는 **`package.json`이 존재할 때만** 자동 실행됩니다. (없으면 전부 스킵)

```yaml
✅ Node.js 22 설정
✅ 의존성 설치 (npm 캐시 활용)
✅ ESLint 린트 검사
✅ OpenAPI 스펙 검증 (있을 시)
✅ npm test 실행
```

### 4️⃣ **결과 리포팅**
- ✅ **성공**: PR 병합 가능
- ❌ **실패**: 수정 필요, AI 가이드 제공

---

## 📝 PR 생성 가이드

### **1. 브랜치 생성**
```bash
git checkout -b feature/your-feature-name
# 또는
git checkout -b fix/bug-description
```

### **2. 코드 작성 및 커밋**
```bash
git add .
git commit -m "feat: add new feature description"
```

### **3. PR 생성**
1. GitHub에서 **New Pull Request** 클릭
2. **PR 템플릿** 자동 로드됨 - 체크리스트 확인
3. **제목**: Conventional Commits 형식 사용
   - `feat:` 새 기능
   - `fix:` 버그 수정
   - `docs:` 문서 수정
   - `chore:` 기타 작업

### **4. 자동 CI 실행 대기**
- PR 생성 후 1-2분 내 CI 시작
- **실시간 진행상황**은 PR의 "Checks" 탭에서 확인

---

## 📊 CI 결과 해석

### ✅ **성공 케이스**
```
PR Validate (Build/Test/Lint/DB + Auto Report) ✅
```
- **의미**: 모든 검증 통과, 병합 가능
- **다음 단계**: 코드 리뷰 요청 후 병합

### ❌ **실패 케이스**
```
PR Validate (Build/Test/Lint/DB + Auto Report) ❌
```

#### **1. PR 댓글 확인**
자동 생성된 댓글에서 실패 정보 확인:
```markdown
**PR Validate Report**

- **Python tests exit**: 1 (실패)
- **Node tests exit**: 0 (성공)
- **DB**: Postgres16 + pgvector service is running
- **Alembic rollback**: smoke test completed
```

#### **2. 상세 로그 확인**
- **Logs**: 댓글의 링크 클릭하여 상세 로그 확인
- **Artifacts**: "reports" 다운로드하여 JUnit/XML 분석

#### **3. AI 수정 가이드 활용**
PR 댓글에 3가지 AI 가이드 제공:

<details>
<summary><b>🟣 Claude Code용 가이드</b></summary>

```
Role: Senior Dev (Claude Code)
Goal: Make CI green for PR #123

Context:
- Repo: your-org/dt-rag
- Branch: feature/your-branch
- CI run: [링크]

Tasks:
1) Reproduce locally per AGENTS.md
2) Minimal edits to pass tests/migrations/lint
3) Push commits to branch
4) Reply in PR with before/after & what changed
```
</details>

### ⏭️ **문서 전용 변경**
```
⏭️ Docs-only changes detected - CI steps skipped for efficiency
```
- **의미**: 문서만 수정되어 CI 스킵됨 (30초 내 완료)
- **다음 단계**: 즉시 병합 가능

---

## 🔧 문제 해결

### **일반적인 문제들**

#### **1. Python 테스트 실패**
```bash
# 로컬에서 동일한 환경 재현
python -m pip install -r requirements.txt
pytest -v

# 특정 테스트만 실행
pytest tests/test_specific.py -v
```

#### **2. Ruff 린트 에러**
```bash
# 자동 수정 가능한 이슈들 수정
ruff check . --fix

# 수동 수정이 필요한 이슈들 확인
ruff check .
```

#### **3. Alembic 마이그레이션 문제**
```bash
# 마이그레이션 상태 확인
alembic current

# 마이그레이션 실행
alembic upgrade head

# 롤백 테스트
alembic downgrade -1
alembic upgrade head
```

#### **4. Node.js 테스트 실패**
```bash
# 의존성 설치
npm ci

# 테스트 실행
npm test

# 린트 검사
npx eslint . --fix
```

### **로컬 개발 환경 설정**

```bash
# 1. Python 환경 (PostgreSQL + pgvector 필요)
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/app_test"
python -m pip install -r requirements.txt
python -m pip install pytest pytest-cov ruff alembic

# 2. Node.js 환경 (package.json 있을 시)
npm ci

# 3. 테스트 실행
pytest -v  # Python 테스트
npm test   # Node.js 테스트
```

---

## 🌟 특별 기능

### **1. 지능형 CI 스킵** ⏭️
문서만 수정된 PR은 자동으로 무거운 CI 단계를 스킵합니다:

**스킵되는 파일 패턴:**
- `docs/` 디렉토리의 모든 파일
- `README.md`
- `.github/pull_request_template.md`  
- 모든 `.md` 파일

**중요**: 코드 파일이 한 줄이라도 포함되면 **전체 검증**으로 전환됩니다.

**효과:**
- 처리시간: 5-10분 → 30초 (90% 단축)
- GitHub Actions 비용 절약
- 즉시 병합 가능

### **2. Alembic 롤백 안전성 테스트** 🛡️
모든 데이터베이스 마이그레이션의 롤백 안전성을 사전 검증:

```yaml
# 자동 실행되는 테스트 순서
alembic upgrade head    # 최신으로 업그레이드
alembic downgrade -1    # 한 단계 롤백
alembic upgrade head    # 다시 업그레이드
```

⚠️ **중요**: 리비전이 1개 이하인 경우에는 `alembic downgrade -1` 단계가 자동으로 **스킵**됩니다(로그에 안내가 출력됩니다).

**효과:**
- 배포 실패 시 안전한 롤백 보장
- 프로덕션 데이터 보호
- 롤백 신뢰도 99% 달성

### **3. 자동 AI 수정 가이드** 🤖
CI 실패 시 Claude/GPT/Codex용 맞춤형 프롬프트 자동 생성:

- **Claude Code**: 즉시 수정 가능한 상세 가이드
- **GPT**: diff 패치 생성 요청 형식
- **Codex**: 샌드박스 환경 수정 지침

---

## ❓ FAQ

### **Q1. PR을 올렸는데 CI가 실행되지 않아요**
**A**: GitHub Actions 권한을 확인하세요. 첫 기여자의 경우 승인이 필요할 수 있습니다.

### **Q2. 문서만 수정했는데 왜 전체 CI가 돌아가나요?**
**A**: 다음 조건을 확인하세요:
- 파일이 정확히 `.md` 확장자인지
- `docs/` 디렉토리나 `README.md`인지
- 코드 파일과 함께 수정하지 않았는지

### **Q3. CI가 실패했는데 어떻게 수정하나요?**
**A**: 
1. PR 댓글의 실패 요약 확인
2. Logs 링크 클릭하여 상세 에러 확인
3. 로컬에서 동일한 명령어로 재현
4. AI 가이드 프롬프트 활용

### **Q4. master 브랜치에 직접 푸시할 수 있나요?**
**A**: 아니요. master 브랜치는 보호되어 있어 반드시 PR을 통해서만 기여할 수 있습니다.

### **Q5. CI 시간이 너무 오래 걸려요**
**A**:
- **문서 수정**: 자동으로 30초 내 완료
- **코드 수정**: 캐시 활용으로 2-5분 (첫 실행은 더 길 수 있음)
- 병렬 처리로 최적화되어 있습니다

### **Q6. PostgreSQL 설정이 필요한가요?**
**A**: 로컬 개발 시에만 필요합니다. CI는 자동으로 PostgreSQL + pgvector 환경을 제공합니다.

### **Q7. 브랜치 보호 설정은 어디서 하나요?**
**A**: GitHub 웹 인터페이스에서 설정합니다:
1. **Settings** → **Branches** → **Add rule** 클릭
2. **Branch name pattern**: `master` 입력  
3. **Required status checks**: `PR Validate (Build/Test/Lint/DB + Auto Report)` 선택
4. **Required reviews**: 1명 이상 승인 설정
5. **Restrict pushes**: 직접 푸시 차단 체크

---

## 🎯 개발 워크플로우 권장사항

### **효율적인 개발을 위한 팁**

1. **🔄 작은 단위로 자주 커밋**
   ```bash
   git add specific-files
   git commit -m "feat: add specific feature component"
   ```

2. **📝 의미있는 커밋 메시지**
   ```bash
   # Good
   git commit -m "fix: resolve database connection timeout issue"
   
   # Bad  
   git commit -m "fix stuff"
   ```

3. **🧪 로컬에서 먼저 테스트**
   ```bash
   # CI 실행 전 로컬 검증
   pytest -v
   ruff check .
   npm test
   ```

4. **📚 문서 업데이트는 별도 PR**
   - 코드 변경과 문서 변경을 분리하면 더 빠른 검토 가능

---

## 📞 지원 및 문의

**문제가 발생했을 때:**

1. **🔍 자가 진단**: 이 가이드의 문제 해결 섹션 참조
2. **🤖 AI 활용**: PR 댓글의 AI 가이드 프롬프트 사용
3. **👥 팀 문의**: Slack/Discord에서 개발팀에 문의
4. **📋 이슈 등록**: GitHub Issues에 상세한 에러 로그와 함께 등록

---

**🎉 이제 안전하고 효율적인 개발을 위한 모든 준비가 완료되었습니다!**

> **마지막 업데이트**: 2025-09-11  
> **버전**: v1.0 (docs-only skip + rollback smoke test 포함)