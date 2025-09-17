# 🚨 긴급 복구 가이드: agents & knowledge-base 폴더

## 📍 삭제된 폴더
- `dt-rag/dt-rag/agents/` - subagents 시스템용 폴더
- `dt-rag/dt-rag/knowledge-base/` - 지식 베이스 데이터 폴더

## 🔧 복구 방법 (우선순위 순)

### 방법 1: Windows 파일 이전 버전 (권장 ⭐)

1. **Windows 탐색기 열기**
   ```
   C:\MYCLAUDE_PROJECT\sonheungmin\Unmanned\dt-rag
   ```

2. **폴더 우클릭**
   - `dt-rag` 폴더 우클릭
   - "속성(Properties)" 선택

3. **이전 버전 탭**
   - "이전 버전(Previous Versions)" 탭 클릭
   - 9월 17일 이전 버전 찾기
   - "열기(Open)" 또는 "복원(Restore)" 클릭

4. **폴더 복사**
   - `dt-rag/agents/` 폴더를 현재 위치로 복사
   - `dt-rag/knowledge-base/` 폴더를 현재 위치로 복사

### 방법 2: Windows File Recovery (명령줄)

**PowerShell을 관리자 권한으로 실행:**

```powershell
# Windows File Recovery 설치 (Microsoft Store에서)
# 복구 시도 (E: 드라이브에 복구)
winfr C: E: /n \MYCLAUDE_PROJECT\sonheungmin\Unmanned\dt-rag\dt-rag\agents\
winfr C: E: /n \MYCLAUDE_PROJECT\sonheungmin\Unmanned\dt-rag\dt-rag\knowledge-base\
```

### 방법 3: 무료 복구 프로그램

1. **Recuva (권장)**
   - https://www.ccleaner.com/recuva 다운로드
   - 삭제된 파일 검색 및 복구

2. **PhotoRec/TestDisk**
   - 오픈소스 무료 도구
   - https://www.cgsecurity.org/wiki/PhotoRec

### 방법 4: 폴더 구조 재생성 (최후 수단)

만약 복구가 불가능하다면:

```bash
# WSL에서 실행
cd /mnt/c/MYCLAUDE_PROJECT/sonheungmin/Unmanned/dt-rag

# agents 폴더 재생성
mkdir -p agents
mkdir -p agents/subagents
mkdir -p agents/configs
mkdir -p agents/scripts
mkdir -p agents/templates

# knowledge-base 폴더 재생성
mkdir -p knowledge-base
mkdir -p knowledge-base/documents
mkdir -p knowledge-base/embeddings
mkdir -p knowledge-base/metadata
mkdir -p knowledge-base/indexes
mkdir -p knowledge-base/backups

# 기본 파일 생성
echo "# Agents Directory" > agents/README.md
echo "# Knowledge Base Directory" > knowledge-base/README.md

# Git에 추가하여 향후 보호
git add agents knowledge-base
git commit -m "Recreate essential agents and knowledge-base folders"
```

## ⚠️ 중요 사항

1. **즉시 작업 중단**: 디스크 사용을 최소화하여 덮어쓰기 방지
2. **우선순위**: Windows 이전 버전 → 복구 프로그램 → 재생성
3. **향후 보호**: 복구 후 반드시 Git에 추가하여 추적

## 📞 추가 도움이 필요한 경우

- 이 가이드대로 진행해도 복구되지 않으면 즉시 알려주세요
- 복구된 데이터가 있으면 즉시 Git에 커밋하겠습니다

---
*긴급 복구 가이드 생성 시간: 2025-09-17*