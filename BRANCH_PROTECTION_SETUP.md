# 🔒 브랜치 보호 설정 가이드

> **⚠️ 필수 설정**: 이 설정을 완료해야 CI/CD 거버넌스가 정상 작동합니다.

## 📋 브랜치 보호 규칙 설정

### **1. GitHub 웹 인터페이스 접속**
```
Repository → Settings → Branches → Add rule (또는 기존 master 규칙 편집)
```

### **2. 기본 설정**
- **Branch name pattern**: `master`
- **Restrict pushes that create files**: ✅ 체크
- **Require a pull request before merging**: ✅ 체크
  - **Required number of reviewers**: `1`
  - **Dismiss stale reviews**: ✅ 체크 (권장)

### **3. Required Status Checks (핵심!)**
**⚠️ 중요**: 반드시 아래 정확한 이름을 선택하세요:

1. **Require status checks to pass before merging**: ✅ 체크
2. **Require branches to be up to date**: ✅ 체크 (권장)
3. **Status checks 목록에서 선택**:
   ```
   PR Validate (Build/Test/Lint/DB + Auto Report) / validate
   ```

**📝 참고**: 이 이름은 첫 PR이 실행된 후에 목록에 나타납니다. 
만약 목록에 없다면:
1. 테스트 PR을 하나 생성하여 CI 실행
2. CI 완료 후 다시 이 설정 페이지로 돌아와서 선택

### **4. 추가 보안 설정 (권장)**
- **Require signed commits**: ✅ 체크 (높은 보안이 필요한 경우)
- **Include administrators**: ✅ 체크 (관리자도 규칙 적용)
- **Allow force pushes**: ❌ 체크 해제
- **Allow deletions**: ❌ 체크 해제

### **5. 설정 완료 확인**
설정 완료 후 다음을 확인하세요:
```bash
# 로컬에서 master 브랜치 직접 푸시 시도 (실패해야 정상)
git checkout master
git push origin master
# → "remote rejected" 메시지가 나와야 함
```

---

## 🏷️ GitHub 라벨 설정

### **필수 라벨 생성**
Repository → Issues → Labels → New label

1. **ci-failed**
   - **Color**: `#d73a49` (빨간색)
   - **Description**: `CI validation failed - needs fixing`

2. **needs-tests**
   - **Color**: `#fbca04` (노란색)  
   - **Description**: `Requires additional test coverage`

3. **docs-only** (선택사항)
   - **Color**: `#0075ca` (파란색)
   - **Description**: `Documentation-only changes`

---

## 👥 CODEOWNERS 파일 업데이트

### **현재 파일 위치**
`.github/CODEOWNERS`

### **업데이트 필요**
```bash
# 현재 (플레이스홀더)
* @member1 @member2 @member3

# 실제 GitHub 핸들로 변경 (예시)
* @actual-username1 @actual-username2 @team-name
```

**📋 실제 핸들 확인 방법**:
1. 팀원의 GitHub 프로필 URL 확인 (`github.com/username`)
2. 또는 `@팀명` (GitHub Teams 사용 시)

---

## ✅ 설정 완료 체크리스트

- [ ] 브랜치 보호 규칙 생성 완료
- [ ] Required status check 정확한 이름으로 설정
- [ ] ci-failed, needs-tests 라벨 생성
- [ ] CODEOWNERS 실제 핸들로 업데이트  
- [ ] master 직접 푸시 차단 확인

**🎯 모든 설정이 완료되면 가이드북의 QA 시나리오를 진행하세요!**