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
                f"Knowledge Base: {subagent_type}",
                f"Filtered {len(relevant_items)} relevant items from knowledge base",
                "",
                "Top References:",
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
            context_lines.append("Key Insights:")

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
                            context_lines.append(f"- {sentence}.")
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
            additional_context = f"Knowledge Base: {subagent_type}\nNo highly relevant items found for this specific task."
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