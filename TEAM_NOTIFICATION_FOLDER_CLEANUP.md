# 📁 프로젝트 폴더 구조 정리 알림

## 🎯 요약
프로젝트의 중복 폴더 구조 문제를 해결했습니다.

## 🔍 문제 상황
- 기존에 `dt-rag/dt-rag/` 이중 중첩 구조가 존재했습니다
- 루트에 이미 있는 `docs/`, `scripts/` 폴더와 중복된 경로가 있었습니다

## ✅ 해결 내용
**PR #11**: https://github.com/bridge25/Unmanned/pull/11

### 이동된 파일들:
- `dt-rag/dt-rag/docs/bridge/ACCESS_CARD.md` → `docs/bridge/ACCESS_CARD.md`
- `dt-rag/dt-rag/docs/seeds/minimal/*` → `docs/seeds/minimal/*`
- `dt-rag/dt-rag/scripts/smoke.sh` → `scripts/smoke.sh`

### Git 히스토리 보존:
- 모든 파일 이동이 "rename"으로 처리되어 히스토리가 보존됩니다
- 파일 추적성에 문제가 없습니다

## 🚨 팀원 액션 아이템

### 1. PR 리뷰 및 승인
- **PR #11**을 확인하고 승인해 주세요
- 변경 내용이 단순한 파일 이동임을 확인할 수 있습니다

### 2. 머지 후 로컬 저장소 업데이트
PR이 머지된 후에는 다음 명령어로 로컬 저장소를 업데이트해 주세요:

```bash
# 최신 변경사항 가져오기
git fetch origin
git pull origin master

# 불필요한 로컬 브랜치 정리 (선택사항)
git branch -d fix/duplicate-folder-structure
```

### 3. 향후 올바른 경로 사용
앞으로는 다음 경로를 사용해 주세요:
- ✅ `docs/bridge/ACCESS_CARD.md`
- ✅ `docs/seeds/minimal/`
- ✅ `scripts/smoke.sh`
- ❌ ~~`dt-rag/dt-rag/docs/`~~ (더 이상 사용하지 않음)

## 📞 문의사항
이 변경사항에 대해 질문이 있으시면 언제든 연락주세요.

---
*정리 완료 일시: 2025-09-17*  
*작업자: Claude Code*