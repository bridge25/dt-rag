# 🚀 B팀 (Orchestration & API) 온보딩 가이드

## 📋 PR-1 완료! 이제 B팀 착수 가능

**A팀의 common-schemas 패키지가 준비되었습니다.** PR #3에서 CI가 통과했으며, B팀이 안전하게 작업을 시작할 수 있습니다.

## 🎯 B팀 첫 실행 명령어

### 1단계: 환경 설정
```bash
# 저장소 클론 및 이동 
git clone https://github.com/bridge25/Unmanned.git
cd Unmanned

# common-schemas 패키지 설치
pip install -e dt-rag/packages/common-schemas

# 설치 확인
python -c "from common_schemas.models import SearchRequest, ClassifyResponse; print('✅ Contract ready')"
```

### 2단계: B팀 스택드 PR 생성
```bash
# 최신 상태 가져오기
git fetch origin

# PR-1 기반으로 B팀 브랜치 생성
git switch -c dt-rag/feat/b-manifest origin/dt-rag/feat/common-schemas-sync

# B팀 앱 디렉토리 초기화
mkdir -p dt-rag/apps/orchestration/{src,tests,docs}
echo "# Orchestration & API (Team B)" > dt-rag/apps/orchestration/README.md

# 초기 커밋
git add dt-rag/apps/orchestration
git commit -m "chore(dt-rag/orchestration): scaffold app directory"
git push -u origin dt-rag/feat/b-manifest

# 스택드 드래프트 PR 생성
gh pr create --repo bridge25/Unmanned \
  --base dt-rag/feat/common-schemas-sync \
  --head dt-rag/feat/b-manifest \
  --title "feat(dt-rag/orchestration): scaffold & initial manifest builder" \
  --body "Stacked on PR-1; uses common-schemas; path-filtered CI" --draft
```

### 3단계: 개발 환경 준비
```bash
# Python 의존성 설치
cd dt-rag/apps/orchestration
pip install fastapi uvicorn langgraph langchain

# requirements.txt 생성
cat > requirements.txt << EOF
fastapi>=0.104.0
uvicorn>=0.24.0
langgraph>=0.1.0
langchain>=0.1.0
python-multipart>=0.0.6
EOF

# 초기 FastAPI 앱 생성
mkdir src
cat > src/main.py << EOF
from fastapi import FastAPI
from common_schemas.models import ClassifyRequest, ClassifyResponse

app = FastAPI(title="Dynamic Taxonomy RAG - Orchestration")

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "orchestration"}

@app.post("/classify", response_model=ClassifyResponse)
async def classify(request: ClassifyRequest):
    # TODO: LangGraph 7-Step 매니페스트 빌더 구현
    return ClassifyResponse(
        canonical=["AI", "RAG"],
        candidates=[],
        confidence=0.8,
        reasoning=["스캐폴딩 단계", "실제 구현 필요"]
    )
EOF
```

## 🛠️ B팀 주요 작업 범위

### Phase 1: 7-Step LangGraph 매니페스트 빌더 
1. **룰 기반 1차 분류** (민감도/패턴 매칭)
2. **LLM 2차 분류** (후보 경로 + 근거≥2)
3. **교차검증 로직** (룰 vs LLM 결과 비교)
4. **Confidence<0.7 → HITL** 처리
5. **하이브리드 검색** (BM25 + Vector)
6. **Cross-Encoder Reranking** (50→5)
7. **성능 모니터링** (p95≤4s 보장)

### Phase 2: FastAPI 서버 구현
- `/classify` 엔드포인트 (classification pipeline)
- `/search` 엔드포인트 (hybrid search + rerank)
- `/taxonomy/{version}/tree` 엔드포인트 (트리 구조 조회)
- NFR 준수: p95≤4s, p50≤1.5s, 비용≤₩10/쿼리

### Phase 3: PostgreSQL + pgvector 연동
- A팀의 DDL 스키마 활용 (PR-2 대기 중)
- Alembic 마이그레이션 연동
- 벡터 검색 최적화 (ivfflat 인덱스)

## 📊 CI/CD 자동화

B팀 전용 CI가 자동 설정됩니다:
- 경로 필터: `dt-rag/apps/orchestration/**`
- contract-test 자동 실행
- FastAPI 서버 빌드 테스트

## 🔗 의존성 관리

### 필수 패키지
```python
# B팀만의 공통 스키마 사용
from common_schemas.models import (
    ClassifyRequest, ClassifyResponse,
    SearchRequest, SearchResponse,
    TaxonomyNode, SourceMeta
)
```

### 금지 사항
- `dt-rag/packages/common-schemas/` 수정 금지
- `dt-rag/docs/openapi.yaml` 직접 수정 금지
- 다른 팀 디렉토리 수정 금지

## 🚨 중요 규칙

1. **폴더 규칙**: `dt-rag/apps/orchestration/` 내에서만 작업
2. **스키마 변경**: A팀과 사전 협의 후 별도 PR
3. **드래프트 PR**: CI 그린 + 리뷰 1+ 후 머지
4. **시크릿 관리**: `.env`, `*.key` 파일은 절대 커밋 금지

## 📞 지원 채널

- **기술 문의**: Slack #dynamic-taxonomy-rag
- **A팀 연락**: team-a@example.com  
- **GitHub 이슈**: PR 코멘트 활용

---
**Generated**: 2025-09-04  
**Base PR**: #3 (dt-rag/feat/common-schemas-sync)  
**Team**: B팀 (Orchestration & API)