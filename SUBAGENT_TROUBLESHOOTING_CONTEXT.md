# Subagent 인식 문제 해결 과정

## 현재 상황
- Claude Code에서 `/agents` 명령어가 subagent들을 인식하지 못함
- `.claude/agents/` 폴더에 12개의 subagent 파일 존재

## 문제 원인 (분석 완료)
YAML frontmatter 형식이 Claude Code 공식 문서 요구사항과 다름:

### 기존 형식 (문제)
```yaml
---
name: database-architect
tools:
  - Read
  - Write
  - Edit
  - MultiEdit
  - Bash
  - Grep
---
```

### 올바른 형식 (해결책)
```yaml
---
name: database-architect
description: PostgreSQL + pgvector database architect specialized in designing high-performance vector database schemas for RAG systems
tools: Read, Write, Edit, MultiEdit, Bash, Grep
model: sonnet
---
```

## 수정 완료된 파일
- ✅ `database-architect.md` - 테스트용으로 올바른 형식으로 수정 완료

## 수정 필요한 파일들 (11개)
- agent-factory-builder.md
- api-designer.md
- classification-pipeline-expert.md
- document-ingestion-specialist.md
- hybrid-search-specialist.md
- langgraph-orchestrator.md
- observability-engineer.md
- rag-evaluation-specialist.md
- security-compliance-auditor.md
- taxonomy-architect.md
- tree-ui-developer.md

## 다음 단계
1. Claude Code 재시작 후 `/agents` 명령어로 `database-architect` 인식 확인
2. 인식되면 나머지 11개 파일도 같은 형식으로 일괄 수정
3. 모든 subagent 정상 작동 확인

## 필수 형식 요구사항
- `name`: kebab-case (소문자, 하이픈)
- `description`: subagent 역할/용도 설명 (필수)
- `tools`: 콤마로 구분된 문자열
- `model`: sonnet (권장)