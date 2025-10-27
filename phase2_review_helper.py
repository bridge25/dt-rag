#!/usr/bin/env python3
"""
Phase 2 브랜치 검토 도우미
- SPEC 메타데이터 자동 추출
- 판정 기록 템플릿 생성
"""
import subprocess
from pathlib import Path
from typing import Dict, Optional

SPEC_IDS = [
    "AGENT-GROWTH-001", "AGENT-GROWTH-002", "AGENT-GROWTH-004", "AGENT-GROWTH-005",
    "CASEBANK-002", "CONSOLIDATION-001", "DEBATE-001", "ENV-VALIDATE-001",
    "FOUNDATION-001", "JOB-OPTIMIZE-001", "REDIS-COMPAT-001", "REFLECTION-001",
    "REPLAY-001", "SOFTQ-001", "UI-INTEGRATION-001"
]

BRANCH_INFO = {
    "AGENT-GROWTH-001": {"files": 781, "ahead": 79, "behind": 29},
    "AGENT-GROWTH-002": {"files": 791, "ahead": 81, "behind": 29},
    "AGENT-GROWTH-004": {"files": 809, "ahead": 83, "behind": 29},
    "AGENT-GROWTH-005": {"files": 1121, "ahead": 86, "behind": 29},
    "CASEBANK-002": {"files": 664, "ahead": 54, "behind": 29},
    "CONSOLIDATION-001": {"files": 664, "ahead": 54, "behind": 29},
    "DEBATE-001": {"files": 651, "ahead": 43, "behind": 29},
    "ENV-VALIDATE-001": {"files": 771, "ahead": 77, "behind": 29},
    "FOUNDATION-001": {"files": 627, "ahead": 35, "behind": 29},
    "JOB-OPTIMIZE-001": {"files": 765, "ahead": 73, "behind": 29},
    "REDIS-COMPAT-001": {"files": 763, "ahead": 71, "behind": 29},
    "REFLECTION-001": {"files": 664, "ahead": 54, "behind": 29},
    "REPLAY-001": {"files": 640, "ahead": 41, "behind": 29},
    "SOFTQ-001": {"files": 639, "ahead": 37, "behind": 29},
    "UI-INTEGRATION-001": {"files": 745, "ahead": 88, "behind": 29},
}


def extract_spec_metadata(spec_id: str) -> Dict[str, str]:
    """SPEC 메타데이터 추출"""
    spec_path = Path(f".moai/specs/SPEC-{spec_id}/spec.md")
    if not spec_path.exists():
        return {"error": "SPEC not found"}

    try:
        content = spec_path.read_text(encoding="utf-8")
    except Exception as e:
        return {"error": f"Read error: {e}"}

    lines = content.split("\n")
    metadata = {}
    in_frontmatter = False

    for line in lines[:100]:  # 앞 100줄만 확인
        if line.strip() == "---":
            in_frontmatter = not in_frontmatter
            if not in_frontmatter:
                break
            continue

        if in_frontmatter and ":" in line:
            key, value = line.split(":", 1)
            metadata[key.strip()] = value.strip()

    # 제목 추출 (# @SPEC:ID: Title)
    for line in lines:
        if line.startswith("# @SPEC:"):
            metadata["title"] = line.split(":", 2)[-1].strip() if ":" in line else "?"
            break

    return metadata


def get_priority_emoji(priority: str) -> str:
    """Priority 이모지 반환"""
    priority_lower = priority.lower()
    if priority_lower == "critical":
        return "🔴"
    elif priority_lower == "high":
        return "🟠"
    elif priority_lower == "medium":
        return "🟡"
    elif priority_lower == "low":
        return "🟢"
    else:
        return "⚪"


def main():
    print("=" * 80)
    print("Phase 2 SPEC 메타데이터 추출")
    print("=" * 80)
    print()

    results = []

    for spec_id in SPEC_IDS:
        print(f"Processing: SPEC-{spec_id}...", end=" ")

        metadata = extract_spec_metadata(spec_id)

        if "error" in metadata:
            print(f"❌ {metadata['error']}")
            continue

        priority = metadata.get("priority", "?")
        category = metadata.get("category", "?")
        status = metadata.get("status", "?")
        title = metadata.get("title", "?")

        branch_stats = BRANCH_INFO.get(spec_id, {})

        results.append({
            "spec_id": spec_id,
            "priority": priority,
            "category": category,
            "status": status,
            "title": title,
            "files": branch_stats.get("files", "?"),
            "ahead": branch_stats.get("ahead", "?"),
            "behind": branch_stats.get("behind", "?"),
        })

        print(f"✅ {get_priority_emoji(priority)} {priority}")

    print()
    print("=" * 80)
    print("결과 요약")
    print("=" * 80)
    print()

    # 콘솔 출력
    for r in results:
        print(f"SPEC-{r['spec_id']}")
        print(f"  {get_priority_emoji(r['priority'])} Priority: {r['priority']}")
        print(f"  Category: {r['category']}")
        print(f"  Status: {r['status']}")
        print(f"  Title: {r['title']}")
        print(f"  Changes: {r['files']} files, {r['ahead']} ahead, {r['behind']} behind")
        print()

    # Markdown 파일 생성
    with open("phase2_spec_metadata.md", "w", encoding="utf-8") as f:
        f.write("# Phase 2 SPEC 메타데이터\n\n")
        f.write("**생성일**: 2025-10-27\n\n")
        f.write("---\n\n")

        f.write("## 전체 요약표\n\n")
        f.write("| SPEC ID | Priority | Category | Status | 파일 수 |\n")
        f.write("|---------|----------|----------|--------|--------|\n")

        for r in results:
            emoji = get_priority_emoji(r['priority'])
            f.write(f"| SPEC-{r['spec_id']} | {emoji} {r['priority']} | {r['category']} | {r['status']} | {r['files']} |\n")

        f.write("\n---\n\n")
        f.write("## 상세 정보\n\n")

        for r in results:
            emoji = get_priority_emoji(r['priority'])
            f.write(f"### SPEC-{r['spec_id']}\n\n")
            f.write(f"- **Priority**: {emoji} {r['priority']}\n")
            f.write(f"- **Category**: {r['category']}\n")
            f.write(f"- **Status**: {r['status']}\n")
            f.write(f"- **Title**: {r['title']}\n")
            f.write(f"- **Changes**: {r['files']} files, {r['ahead']} ahead, {r['behind']} behind\n")
            f.write(f"- **Branch**: feature/SPEC-{r['spec_id']}\n")
            f.write(f"- **SPEC Path**: `.moai/specs/SPEC-{r['spec_id']}/spec.md`\n")
            f.write("\n")
            f.write("**판정**: ⬜ 미결정\n\n")
            f.write("**사유**:\n")
            f.write("```\n")
            f.write("(여기에 판정 사유를 작성하세요)\n")
            f.write("```\n\n")
            f.write("---\n\n")

    print()
    print("✅ phase2_spec_metadata.md 생성 완료!")
    print()
    print("다음 단계:")
    print("1. phase2_spec_metadata.md 파일을 열어 각 SPEC 검토")
    print("2. 각 SPEC의 '판정' 항목을 다음 중 하나로 변경:")
    print("   - ✅ PR 생성 (필요)")
    print("   - ⏸️ 보류")
    print("   - ❌ 삭제")
    print("3. '사유' 항목에 판정 이유 작성")
    print("4. phase2_create_prs.py 스크립트로 선택된 브랜치 PR 생성")


if __name__ == "__main__":
    main()
