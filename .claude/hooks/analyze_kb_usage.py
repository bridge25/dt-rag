#!/usr/bin/env python3
"""
Knowledge Base Hook Usage Analysis
Analyzes logs and provides metrics on hook performance
"""

import json
import re
import os
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from typing import Dict, List, Any

LOG_PATH = Path(".claude/hooks/logs/kb_injection.log")
CACHE_PATH = Path(".claude/hooks/cache/kb_cache.json")

def analyze_logs():
    """Analyze the knowledge base injection logs"""

    if not LOG_PATH.exists():
        print("No log file found. Hook hasn't been used yet.")
        return

    with open(LOG_PATH, 'r', encoding='utf-8') as f:
        logs = f.readlines()

    print("=== Knowledge Base Hook Usage Analysis ===")
    print(f"Log file: {LOG_PATH}")
    print(f"Total log entries: {len(logs)}")
    print()

    # Parse logs
    invocations = 0
    successes = 0
    cache_hits = 0
    agent_usage = Counter()
    error_count = 0

    total_items_injected = []
    processing_times = []

    for line in logs:
        line = line.strip()
        if not line:
            continue

        if "Processing Task for" in line:
            invocations += 1
            # Extract agent name
            match = re.search(r"Processing Task for (\w+)", line)
            if match:
                agent_name = match.group(1)
                agent_usage[agent_name] += 1

        elif "Successfully injected knowledge" in line:
            successes += 1

        elif "Cache hit for" in line:
            cache_hits += 1

        elif "ERROR" in line:
            error_count += 1

        elif "Filtered" in line and "relevant items" in line:
            # Extract number of items
            match = re.search(r"Filtered (\d+) relevant items", line)
            if match:
                items = int(match.group(1))
                total_items_injected.append(items)

    # Calculate metrics
    success_rate = (successes / invocations * 100) if invocations > 0 else 0
    cache_hit_rate = (cache_hits / invocations * 100) if invocations > 0 else 0
    avg_items = sum(total_items_injected) / len(total_items_injected) if total_items_injected else 0

    print("1. Invocation Statistics:")
    print(f"   Total invocations: {invocations}")
    print(f"   Successful injections: {successes}")
    print(f"   Success rate: {success_rate:.1f}%")
    print(f"   Error count: {error_count}")
    print()

    print("2. Performance Metrics:")
    print(f"   Cache hit rate: {cache_hit_rate:.1f}%")
    print(f"   Average items injected: {avg_items:.1f}")
    print()

    print("3. Most Used Agents:")
    for agent, count in agent_usage.most_common(5):
        percentage = (count / invocations * 100) if invocations > 0 else 0
        print(f"   {agent}: {count} times ({percentage:.1f}%)")
    print()

    # Cache analysis
    if CACHE_PATH.exists():
        try:
            with open(CACHE_PATH, 'r', encoding='utf-8') as f:
                cache = json.load(f)

            print("4. Cache Analysis:")
            print(f"   Cached knowledge bases: {len(cache)}")

            current_time = datetime.now().timestamp()
            valid_entries = 0
            for key, entry in cache.items():
                if current_time - entry.get('timestamp', 0) < 300:  # 5 min TTL
                    valid_entries += 1

            print(f"   Valid cache entries: {valid_entries}")
            print(f"   Cache efficiency: {(valid_entries / len(cache) * 100):.1f}%" if cache else "0%")
            print()
        except Exception as e:
            print(f"4. Cache Analysis: Error reading cache - {e}")
            print()

    # Recent activity (last 24 hours)
    print("5. Recent Activity (Last 24 Hours):")
    recent_logs = []
    yesterday = datetime.now() - timedelta(hours=24)

    for line in logs:
        if line.strip():
            try:
                # Extract timestamp from log line
                timestamp_match = re.search(r'\[([\d-T:\.]+)\]', line)
                if timestamp_match:
                    timestamp_str = timestamp_match.group(1)
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00').split('.')[0])
                    if timestamp > yesterday:
                        recent_logs.append(line)
            except Exception:
                continue

    print(f"   Log entries in last 24h: {len(recent_logs)}")

    # Count recent agent usage
    recent_agents = Counter()
    for line in recent_logs:
        if "Processing Task for" in line:
            match = re.search(r"Processing Task for (\w+)", line)
            if match:
                recent_agents[match.group(1)] += 1

    if recent_agents:
        print("   Recent agent usage:")
        for agent, count in recent_agents.most_common(3):
            print(f"     {agent}: {count} times")
    else:
        print("   No recent activity")
    print()

    print("6. Recommendations:")

    if success_rate < 90:
        print("   - Success rate is below 90%. Check for errors in knowledge base files.")

    if cache_hit_rate < 30:
        print("   - Cache hit rate is low. Consider increasing cache TTL or using hooks more frequently.")

    if avg_items < 3:
        print("   - Average items injected is low. Check relevance filtering logic.")

    if error_count > invocations * 0.1:
        print("   - High error rate detected. Review error logs for issues.")

    if not any([success_rate < 90, cache_hit_rate < 30, avg_items < 3, error_count > invocations * 0.1]):
        print("   - System is performing well! No immediate issues detected.")


def analyze_knowledge_bases():
    """Analyze the knowledge base files themselves"""

    kb_dir = Path("knowledge-base")
    if not kb_dir.exists():
        print("Knowledge base directory not found.")
        return

    print("\n=== Knowledge Base Content Analysis ===")

    kb_files = list(kb_dir.glob("*_knowledge.json"))
    print(f"Knowledge base files found: {len(kb_files)}")
    print()

    total_items = 0
    agents_analysis = {}

    for kb_file in kb_files:
        agent_name = kb_file.stem.replace('_knowledge', '')

        try:
            with open(kb_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            items = data.get('search_results', [])
            frameworks = data.get('frameworks', {})
            best_practices = data.get('best_practices', [])

            agents_analysis[agent_name] = {
                'items': len(items),
                'frameworks': len(frameworks),
                'best_practices': len(best_practices),
                'avg_relevance': sum(item.get('relevance_score', 0) for item in items) / len(items) if items else 0
            }

            total_items += len(items)

        except Exception as e:
            agents_analysis[agent_name] = {'error': str(e)}

    print("Knowledge Base Statistics:")
    print(f"Total search results across all agents: {total_items}")
    print(f"Average items per agent: {total_items / len(kb_files):.1f}")
    print()

    print("Per-Agent Analysis:")
    for agent, stats in agents_analysis.items():
        if 'error' in stats:
            print(f"  {agent}: ERROR - {stats['error']}")
        else:
            print(f"  {agent}:")
            print(f"    Search results: {stats['items']}")
            print(f"    Frameworks: {stats['frameworks']}")
            print(f"    Best practices: {stats['best_practices']}")
            print(f"    Avg relevance: {stats['avg_relevance']:.2f}")


if __name__ == "__main__":
    try:
        analyze_logs()
        analyze_knowledge_bases()
    except Exception as e:
        print(f"Analysis failed: {e}")
        import traceback
        traceback.print_exc()