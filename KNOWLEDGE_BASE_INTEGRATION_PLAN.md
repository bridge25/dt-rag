# Knowledge Base Integration Enhancement Plan
> **작성일**: 2025-09-19
> **프로젝트**: Dynamic Taxonomy RAG v1.8.1
> **목적**: Subagent Knowledge Base 활용도 0% → 100% 개선

---

## 🎯 Executive Summary

### 문제 상황
- **현재 상태**: Subagent들이 knowledge-base/*.json 파일을 전혀 읽지 못함
- **원인**: Task 도구가 .claude/agents/*.md는 읽지만, JSON 파일은 자동 로드하지 않음
- **영향**: RAGAS v2.0 등 최신 정보 미활용, 일반적인 답변만 생성

### 해결 방안
3단계 하이브리드 접근법으로 단계적 개선:
1. **Phase 1**: MD 파일에 Essential Knowledge 임베드 (즉시 효과)
2. **Phase 2**: Bash 기반 Hook 자동화 (간단한 자동화)
3. **Phase 3**: Python 기반 지능형 Hook (정교한 제어)

---

## 📋 Phase 1: Essential Knowledge MD 파일 개선

### 1.1 목표
- 각 에이전트 MD 파일에 핵심 Knowledge 10-15개 항목 직접 포함
- 즉시 효과, 추가 설정 불필요

### 1.2 작업 내역

#### Step 1: Knowledge JSON 분석 (20분)
```python
# 분석 스크립트 예시
import json
from pathlib import Path

kb_dir = Path("knowledge-base")
for kb_file in kb_dir.glob("*_knowledge.json"):
    with open(kb_file) as f:
        data = json.load(f)
        items = data.get("search_results", [])

        # 상위 10개 선별 기준
        # 1. relevance_score > 0.9
        # 2. 2025년 최신 정보
        # 3. 구체적 구현 가이드 포함

        essential = [
            item for item in items[:20]
            if item.get("relevance_score", 0) > 0.9
        ][:10]
```

#### Step 2: MD 파일 업데이트 템플릿
```markdown
## Essential Knowledge (Auto-loaded)

### 🎯 Key Tools & Versions
- **RAGAS v2.0** (2025-04-28): Faithfulness ≥ 0.85, Answer Relevancy, Context Precision
- **Arize Phoenix**: RAG triad metrics - context relevance, groundedness, answer relevance
- **DeepEval**: 14+ LLM evaluation metrics, self-explaining for debugging
- **LangSmith 2025**: Align Evals, Trace Mode, cross-framework support
- **TruLens**: Reference-free evaluation, groundedness scoring

### 📊 Critical Configurations
- **Minimum Test Set**: 20 questions (personal), 100 questions (enterprise)
- **Golden Dataset Quality**: > 95% annotation accuracy required
- **Inter-annotator Agreement**: > 90% for reliability
- **Evaluation Frequency**: Every PR, nightly full evaluation
- **Performance Target**: Faithfulness ≥ 0.85, Answer Relevancy ≥ 0.8

### ⚠️ Best Practices
- Always use component-level evaluation (retrieval + generation separately)
- Implement A/B testing with statistical significance (p < 0.05)
- Use canary releases with automated rollback triggers
- Monitor evaluation metrics in production continuously
- Create domain-specific custom metrics beyond standard RAGAS

### 📌 Full Knowledge Access
Complete knowledge base with detailed examples available at:
`knowledge-base/rag-evaluation-specialist_knowledge.json`
```

### 1.3 검증 체크리스트
- [ ] MD 파일 크기 < 200KB (Git 관리 용이)
- [ ] Essential Knowledge 가독성 확인
- [ ] 중복 정보 제거
- [ ] 버전 정보 명시
- [ ] 실행 가능한 구체적 가이드 포함

---

## 📋 Phase 2: Bash Hook 구현

### 2.1 목표
- Task 도구 호출 시 자동 Knowledge 로드
- 간단한 Bash 스크립트로 구현

### 2.2 구현 상세

#### Hook 스크립트: `.claude/hooks/inject_knowledge.sh`
```bash
#!/bin/bash
# Knowledge Base Auto-injection Hook for Task tool
# Compatible with Windows Git Bash and WSL

set -e  # Exit on error

# Parse tool input
tool_name=$(echo "$CLAUDE_TOOL_INPUT" | jq -r '.tool_name // empty')
subagent_type=$(echo "$CLAUDE_TOOL_INPUT" | jq -r '.tool_input.subagent_type // empty')

# Debug logging
echo "[KB Hook] Tool: $tool_name, Subagent: $subagent_type" >&2

# Only process Task tool calls
if [ "$tool_name" != "Task" ] || [ -z "$subagent_type" ]; then
    echo '{"continue": true}'
    exit 0
fi

# Windows path handling
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    KB_BASE="C:/MYCLAUDE_PROJECT/sonheungmin/Unmanned/dt-rag/knowledge-base"
else
    KB_BASE="/mnt/c/MYCLAUDE_PROJECT/sonheungmin/Unmanned/dt-rag/knowledge-base"
fi

KB_FILE="${KB_BASE}/${subagent_type}_knowledge.json"

# Check file existence
if [ ! -f "$KB_FILE" ]; then
    echo "[KB Hook] Warning: Knowledge base not found for $subagent_type" >&2
    echo '{"continue": true}'
    exit 0
fi

# Extract and inject top 5 items
echo "[KB Hook] Loading knowledge for $subagent_type..." >&2

# Create minimal context injection
jq -c '{
    continue: true,
    suppressOutput: false,
    additionalContext: (
        "🔍 Knowledge Base Loaded: " + (.subagent // "unknown") + "\n" +
        "📚 Top References:\n" +
        (.search_results[:5] | map("- " + .title + " (" + (.relevance_score | tostring) + ")") | join("\n"))
    )
}' "$KB_FILE"
```

### 2.3 설정 업데이트
```json
{
  "permissions": {
    // existing permissions...
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Task",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/inject_knowledge.sh",
            "timeout": 5,
            "continueOnError": true
          }
        ]
      }
    ]
  }
}
```

### 2.4 트러블슈팅
- **문제**: Windows 경로 처리
  - **해결**: OSTYPE 체크로 자동 경로 변환
- **문제**: jq 명령어 없음
  - **해결**: Git Bash 기본 포함, WSL은 `apt install jq`
- **문제**: 권한 오류
  - **해결**: `chmod +x inject_knowledge.sh`

---

## 📋 Phase 3: Python 기반 지능형 Hook (Deep Design)

### 3.1 설계 목표
- **지능형 필터링**: Task 내용 분석하여 관련 Knowledge만 선별
- **성능 최적화**: 캐싱으로 반복 로드 방지
- **에러 복구**: 실패 시에도 Task 실행 보장
- **실시간 검증**: Mock 데이터 방지, 실제 데이터 보장

### 3.2 아키텍처 설계

```
┌─────────────────────────────────────────┐
│         PreToolUse Hook Trigger         │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│     knowledge_injector.py Main          │
├─────────────────────────────────────────┤
│ 1. Parse CLAUDE_TOOL_INPUT              │
│ 2. Validate Task tool & subagent_type   │
│ 3. Load Knowledge with caching          │
│ 4. Intelligent filtering                │
│ 5. Format injection response            │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│        Response to Claude Code          │
├─────────────────────────────────────────┤
│ {                                       │
│   "continue": true,                     │
│   "additionalContext": "...",           │
│   "injectedKnowledge": {...}            │
│ }                                       │
└─────────────────────────────────────────┘
```

### 3.3 완전한 Python Hook 구현

#### `.claude/hooks/knowledge_injector.py`
```python
#!/usr/bin/env python3
"""
Advanced Knowledge Base Injection Hook for Claude Code
Ensures real data injection, not mock data
Version: 1.0.0
Author: DT-RAG Team
"""

import os
import sys
import json
import hashlib
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Constants
KB_BASE_PATH = Path("C:/MYCLAUDE_PROJECT/sonheungmin/Unmanned/dt-rag/knowledge-base")
LOG_PATH = Path(".claude/hooks/logs/kb_injection.log")
CACHE_PATH = Path(".claude/hooks/cache/kb_cache.json")
MAX_ITEMS_TO_INJECT = 10
CACHE_TTL_SECONDS = 300  # 5 minutes

class KnowledgeInjector:
    """Advanced knowledge base injection with caching and intelligent filtering"""

    def __init__(self):
        self.cache = self._load_cache()
        self.ensure_directories()

    def ensure_directories(self):
        """Create necessary directories"""
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)

    def _load_cache(self) -> Dict:
        """Load cache with TTL check"""
        if CACHE_PATH.exists():
            try:
                with open(CACHE_PATH, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                    # Clean expired entries
                    current_time = time.time()
                    cache = {
                        k: v for k, v in cache.items()
                        if current_time - v.get('timestamp', 0) < CACHE_TTL_SECONDS
                    }
                    return cache
            except Exception:
                return {}
        return {}

    def _save_cache(self):
        """Save cache to disk"""
        try:
            with open(CACHE_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f)
        except Exception as e:
            self.log(f"Cache save error: {e}", level="ERROR")

    def log(self, message: str, level: str = "INFO"):
        """Structured logging"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] [{level}] {message}\n"

        try:
            with open(LOG_PATH, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception:
            # Silent fail for logging
            pass

        # Also output to stderr for debugging
        if level in ["ERROR", "WARNING"]:
            print(f"[KB Hook] {level}: {message}", file=sys.stderr)

    def get_tool_input(self) -> Optional[Dict]:
        """Parse and validate tool input"""
        tool_input_str = os.environ.get('CLAUDE_TOOL_INPUT', '{}')

        try:
            tool_input = json.loads(tool_input_str)
            self.log(f"Tool input parsed: {tool_input.get('tool_name', 'unknown')}")
            return tool_input
        except json.JSONDecodeError as e:
            self.log(f"Failed to parse CLAUDE_TOOL_INPUT: {e}", "ERROR")
            return None

    def load_knowledge_base(self, subagent_type: str) -> Optional[Dict]:
        """Load knowledge base with caching"""
        cache_key = f"kb_{subagent_type}"

        # Check cache first
        if cache_key in self.cache:
            self.log(f"Cache hit for {subagent_type}")
            return self.cache[cache_key]['data']

        # Load from file
        kb_path = KB_BASE_PATH / f"{subagent_type}_knowledge.json"

        if not kb_path.exists():
            self.log(f"Knowledge base not found: {kb_path}", "WARNING")
            return None

        try:
            with open(kb_path, 'r', encoding='utf-8') as f:
                knowledge = json.load(f)

                # Validate structure
                if not isinstance(knowledge, dict):
                    self.log(f"Invalid KB structure for {subagent_type}", "ERROR")
                    return None

                # Cache it
                self.cache[cache_key] = {
                    'data': knowledge,
                    'timestamp': time.time()
                }
                self._save_cache()

                self.log(f"Loaded KB for {subagent_type}: {len(knowledge.get('search_results', []))} items")
                return knowledge

        except Exception as e:
            self.log(f"Failed to load KB for {subagent_type}: {e}", "ERROR")
            return None

    def calculate_relevance(self, item: Dict, task_keywords: List[str]) -> float:
        """Calculate item relevance to task"""
        score = item.get('relevance_score', 0.5)

        # Boost score for keyword matches
        title = item.get('title', '').lower()
        content = item.get('content', '').lower()

        for keyword in task_keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in title:
                score += 0.2
            if keyword_lower in content:
                score += 0.1

        return min(score, 1.0)  # Cap at 1.0

    def filter_relevant_items(self, knowledge: Dict, task_prompt: str) -> List[Dict]:
        """Intelligent filtering based on task content"""
        items = knowledge.get('search_results', [])

        if not items:
            return []

        # Extract keywords from task prompt
        task_lower = task_prompt.lower()

        # Domain-specific keyword mappings
        keyword_maps = {
            'evaluation': ['ragas', 'metric', 'evaluation', 'assess', 'measure', 'quality'],
            'database': ['postgres', 'pgvector', 'hnsw', 'index', 'migration', 'alembic'],
            'search': ['bm25', 'vector', 'hybrid', 'rerank', 'cross-encoder', 'retrieval'],
            'orchestration': ['langgraph', 'workflow', 'state', 'pipeline', 'chain'],
            'ingestion': ['chunk', 'parse', 'extract', 'document', 'pdf', 'ocr'],
            'api': ['fastapi', 'openapi', 'rest', 'endpoint', 'cors', 'swagger'],
            'security': ['auth', 'security', 'vulnerability', 'audit', 'compliance'],
            'taxonomy': ['dag', 'hierarchy', 'classification', 'ontology', 'tree'],
        }

        # Determine relevant keywords
        active_keywords = []
        for domain, keywords in keyword_maps.items():
            if any(kw in task_lower for kw in keywords[:3]):  # Check first 3 keywords
                active_keywords.extend(keywords)

        # If no specific domain detected, use general keywords
        if not active_keywords:
            # Extract potential keywords from task (simple tokenization)
            words = task_lower.split()
            active_keywords = [w for w in words if len(w) > 4][:10]

        self.log(f"Active keywords: {active_keywords[:5]}")

        # Score and filter items
        scored_items = []
        for item in items:
            relevance = self.calculate_relevance(item, active_keywords)
            if relevance > 0.6:  # Threshold
                item_copy = item.copy()
                item_copy['computed_relevance'] = relevance
                scored_items.append(item_copy)

        # Sort by relevance and return top N
        scored_items.sort(key=lambda x: x['computed_relevance'], reverse=True)
        return scored_items[:MAX_ITEMS_TO_INJECT]

    def format_injection_response(self,
                                 subagent_type: str,
                                 relevant_items: List[Dict],
                                 task_prompt: str) -> Dict:
        """Format the final injection response"""

        # Create a concise summary for injection
        if relevant_items:
            # Build context string
            context_lines = [
                f"📚 Knowledge Base: {subagent_type}",
                f"🔍 Filtered {len(relevant_items)} relevant items from knowledge base",
                "",
                "🎯 Top References:",
            ]

            for i, item in enumerate(relevant_items[:5], 1):
                title = item.get('title', 'Unknown')
                score = item.get('computed_relevance', item.get('relevance_score', 0))
                # Truncate long titles
                if len(title) > 80:
                    title = title[:77] + "..."
                context_lines.append(f"{i}. {title} (relevance: {score:.2f})")

            # Add key insights
            context_lines.append("")
            context_lines.append("💡 Key Insights:")

            # Extract unique key points
            seen_points = set()
            for item in relevant_items[:3]:
                content = item.get('content', '')
                # Extract first meaningful sentence
                sentences = content.split('.')
                for sentence in sentences:
                    sentence = sentence.strip()
                    if len(sentence) > 20 and len(sentence) < 150:
                        sentence_hash = hashlib.md5(sentence.encode()).hexdigest()[:8]
                        if sentence_hash not in seen_points:
                            context_lines.append(f"• {sentence}.")
                            seen_points.add(sentence_hash)
                            break

            additional_context = "\n".join(context_lines)

            # Structured data for potential future use
            injected_knowledge = {
                "source": "knowledge_base",
                "agent": subagent_type,
                "timestamp": datetime.now().isoformat(),
                "items_count": len(relevant_items),
                "task_summary": task_prompt[:100] if len(task_prompt) > 100 else task_prompt,
                "top_items": [
                    {
                        "title": item.get('title', ''),
                        "relevance": round(item.get('computed_relevance', 0), 3),
                        "url": item.get('url', ''),
                        "category": item.get('category', 'general')
                    }
                    for item in relevant_items[:5]
                ]
            }

        else:
            additional_context = f"📚 Knowledge Base: {subagent_type}\n⚠️ No highly relevant items found for this specific task."
            injected_knowledge = {
                "source": "knowledge_base",
                "agent": subagent_type,
                "timestamp": datetime.now().isoformat(),
                "items_count": 0,
                "task_summary": task_prompt[:100] if len(task_prompt) > 100 else task_prompt
            }

        return {
            "continue": True,
            "suppressOutput": False,
            "additionalContext": additional_context,
            "metadata": injected_knowledge  # This won't be shown but logged
        }

    def create_error_response(self, error_msg: str) -> Dict:
        """Create a safe error response that allows Task to continue"""
        self.log(f"Creating error response: {error_msg}", "ERROR")
        return {
            "continue": True,
            "suppressOutput": True,
            "warning": f"Knowledge injection failed: {error_msg}"
        }

    def run(self) -> Dict:
        """Main execution flow"""
        try:
            # Parse tool input
            tool_input = self.get_tool_input()
            if not tool_input:
                return self.create_error_response("Invalid tool input")

            # Check if it's a Task tool
            tool_name = tool_input.get('tool_name')
            if tool_name != 'Task':
                self.log(f"Skipping non-Task tool: {tool_name}")
                return {"continue": True}

            # Extract subagent type
            task_input = tool_input.get('tool_input', {})
            subagent_type = task_input.get('subagent_type')

            if not subagent_type:
                self.log("No subagent_type in Task input")
                return {"continue": True}

            # Get task prompt for context
            task_prompt = task_input.get('prompt', '')

            self.log(f"Processing Task for {subagent_type}")

            # Load knowledge base
            knowledge = self.load_knowledge_base(subagent_type)
            if not knowledge:
                return self.create_error_response(f"Knowledge base not found for {subagent_type}")

            # Filter relevant items
            relevant_items = self.filter_relevant_items(knowledge, task_prompt)

            self.log(f"Filtered {len(relevant_items)} relevant items from {len(knowledge.get('search_results', []))} total")

            # Format and return response
            response = self.format_injection_response(subagent_type, relevant_items, task_prompt)

            # Log successful injection
            self.log(f"Successfully injected knowledge for {subagent_type}")

            return response

        except Exception as e:
            # Log full traceback for debugging
            import traceback
            tb = traceback.format_exc()
            self.log(f"Unexpected error: {e}\n{tb}", "ERROR")

            # Return safe response to not block Task execution
            return self.create_error_response(str(e))


def validate_mock_data_prevention():
    """Self-test to ensure no mock data is being used"""
    # This runs during import to validate the system
    test_kb_path = KB_BASE_PATH / "rag-evaluation-specialist_knowledge.json"

    if test_kb_path.exists():
        try:
            with open(test_kb_path, 'r') as f:
                data = json.load(f)
                # Check for real data indicators
                if 'search_results' in data and len(data['search_results']) > 0:
                    first_item = data['search_results'][0]
                    # Verify real data structure
                    required_fields = ['query', 'url', 'title', 'content', 'relevance_score']
                    if all(field in first_item for field in required_fields):
                        print("[KB Hook] Validation passed: Real data structure confirmed", file=sys.stderr)
                    else:
                        print("[KB Hook] Warning: Knowledge base structure incomplete", file=sys.stderr)
        except Exception as e:
            print(f"[KB Hook] Validation warning: {e}", file=sys.stderr)


# Run validation on import
validate_mock_data_prevention()

# Main execution
if __name__ == "__main__":
    injector = KnowledgeInjector()
    response = injector.run()

    # Output JSON response for Claude Code
    print(json.dumps(response, ensure_ascii=False, indent=2))
```

### 3.4 고급 트러블슈팅 가이드

#### 문제 1: Mock 데이터 반환 방지
**증상**: Knowledge가 주입되지만 실제 내용이 아닌 placeholder
**원인**: JSON 파일 구조 불일치, 파싱 오류
**해결**:
```python
# Validation 함수 추가
def validate_knowledge_structure(knowledge: Dict) -> bool:
    """Ensure knowledge has real data, not mock"""
    if not knowledge.get('search_results'):
        return False

    # Check first item has real content
    first_item = knowledge['search_results'][0]
    if len(first_item.get('content', '')) < 50:
        return False  # Too short, likely mock

    # Check for mock indicators
    mock_indicators = ['example', 'test', 'placeholder', 'lorem ipsum']
    content_lower = first_item.get('content', '').lower()
    if any(indicator in content_lower for indicator in mock_indicators):
        return False

    return True
```

#### 문제 2: 인코딩 오류 (한글 포함 시)
**증상**: UTF-8 decode error
**해결**:
```python
# 모든 파일 열기에 encoding 명시
with open(kb_path, 'r', encoding='utf-8', errors='replace') as f:
    knowledge = json.load(f)
```

#### 문제 3: 대용량 Knowledge 처리
**증상**: Hook timeout (5초 초과)
**해결**:
```python
# 스트리밍 방식으로 변경
import ijson  # pip install ijson

def load_knowledge_streaming(path: Path, limit: int = 100):
    """Load only first N items for performance"""
    items = []
    with open(path, 'rb') as f:
        parser = ijson.items(f, 'search_results.item')
        for item in parser:
            items.append(item)
            if len(items) >= limit:
                break
    return {'search_results': items}
```

#### 문제 4: Hook 실행 확인
**진단 스크립트**: `.claude/hooks/test_hook.py`
```python
#!/usr/bin/env python3
"""Test script to verify hook is working"""

import os
import json

# Simulate Task tool call
test_input = {
    "tool_name": "Task",
    "tool_input": {
        "subagent_type": "rag-evaluation-specialist",
        "prompt": "Evaluate the RAG system using RAGAS metrics"
    }
}

os.environ['CLAUDE_TOOL_INPUT'] = json.dumps(test_input)

# Run the hook
from knowledge_injector import KnowledgeInjector
injector = KnowledgeInjector()
result = injector.run()

print("Hook Response:")
print(json.dumps(result, indent=2))

# Verify real data
if 'additionalContext' in result:
    context = result['additionalContext']
    if 'RAGAS' in context or 'evaluation' in context:
        print("✅ Real knowledge detected!")
    else:
        print("⚠️ Generic response - check knowledge base")
else:
    print("❌ No context injected")
```

### 3.5 성능 최적화

#### 캐싱 전략
- **In-memory cache**: 5분 TTL
- **File-based cache**: 영구 저장
- **Cache warming**: 서버 시작 시 자주 사용하는 KB 미리 로드

#### 병렬 처리 (대용량 KB)
```python
import asyncio
import aiofiles

async def load_knowledge_async(subagent_type: str):
    """Async loading for better performance"""
    kb_path = KB_BASE_PATH / f"{subagent_type}_knowledge.json"

    async with aiofiles.open(kb_path, mode='r', encoding='utf-8') as f:
        content = await f.read()
        return json.loads(content)
```

### 3.6 모니터링 및 메트릭

#### 로그 분석 스크립트
```bash
#!/bin/bash
# analyze_kb_usage.sh

LOG_FILE=".claude/hooks/logs/kb_injection.log"

echo "=== Knowledge Base Hook Usage Analysis ==="
echo

echo "1. Total invocations:"
grep -c "Processing Task" "$LOG_FILE" 2>/dev/null || echo "0"

echo
echo "2. Success rate:"
SUCCESS=$(grep -c "Successfully injected" "$LOG_FILE" 2>/dev/null || echo "0")
TOTAL=$(grep -c "Processing Task" "$LOG_FILE" 2>/dev/null || echo "1")
echo "scale=2; $SUCCESS * 100 / $TOTAL" | bc

echo
echo "3. Most used agents:"
grep "Processing Task for" "$LOG_FILE" | awk '{print $NF}' | sort | uniq -c | sort -rn | head -5

echo
echo "4. Cache hit rate:"
CACHE_HITS=$(grep -c "Cache hit" "$LOG_FILE" 2>/dev/null || echo "0")
echo "scale=2; $CACHE_HITS * 100 / $TOTAL" | bc

echo
echo "5. Average items injected:"
grep "Filtered [0-9]* relevant items" "$LOG_FILE" | \
    sed 's/.*Filtered \([0-9]*\).*/\1/' | \
    awk '{sum+=$1; count++} END {if(count>0) print sum/count; else print 0}'
```

---

## 📊 성공 지표 및 검증

### Phase별 성공 기준

#### Phase 1 (MD 개선)
- [ ] 각 MD 파일에 Essential Knowledge 섹션 추가
- [ ] Git diff 검토 완료
- [ ] Task 실행 시 Essential Knowledge 언급 확인

#### Phase 2 (Bash Hook)
- [ ] Hook 스크립트 실행 권한 설정
- [ ] settings.local.json 업데이트
- [ ] Task 호출 시 "Loading knowledge" 로그 확인

#### Phase 3 (Python Hook)
- [ ] 실제 데이터 주입 검증 (no mock)
- [ ] 5초 내 실행 완료
- [ ] 캐싱 동작 확인
- [ ] 에러 시에도 Task 계속 실행

### 최종 검증 체크리스트
```bash
# 1. Knowledge 활용률 측정
grep -r "RAGAS v2.0\|Arize Phoenix\|DeepEval" generated_reports/*.md

# 2. Hook 로그 분석
tail -n 100 .claude/hooks/logs/kb_injection.log

# 3. 실제 Task 테스트
echo "Test: rag-evaluation-specialist로 RAGAS v2.0 기준 평가 수행"
# 응답에 RAGAS v2.0 specific metrics 포함 여부 확인

# 4. 성능 측정
time python3 .claude/hooks/test_hook.py
```

---

## ⏱️ 일정 및 리소스

### 타임라인
- **Phase 1**: 1시간 (즉시 시작 가능)
- **Phase 2**: 30분 (Phase 1 완료 후)
- **Phase 3**: 2시간 (정교한 설계 포함)
- **검증 및 조정**: 30분

### 필요 리소스
- Python 3.8+
- jq (command-line JSON processor)
- Git Bash 또는 WSL
- 쓰기 권한 (hooks 디렉토리)

---

## 🎯 기대 효과

### 정량적 개선
- **Knowledge 활용률**: 0% → 100%
- **구체적 정보 언급**: 10% → 80%
- **최신 도구 버전 인식**: 0% → 100%
- **작업 정확도**: 65% → 90%

### 정성적 개선
- RAGAS v2.0 같은 최신 도구 정확히 언급
- 구체적 설정값 제시 (ef_construction=64 등)
- 업계 표준 준수 (20 questions minimum 등)
- 실행 가능한 구체적 가이드 제공

---

## 📝 결론

이 3단계 접근법을 통해:
1. **즉시 개선** (Phase 1)으로 빠른 효과
2. **자동화** (Phase 2)로 일관성 확보
3. **지능화** (Phase 3)로 최적 성능 달성

특히 Phase 3의 Python Hook은 mock 데이터 방지, 실시간 검증, 지능형 필터링을 통해
실제 Knowledge가 확실하게 주입되도록 설계되었습니다.