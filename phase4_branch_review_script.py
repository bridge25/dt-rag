#!/usr/bin/env python3
"""
Phase 4 브랜치 빠른 스캔 스크립트
"""
import subprocess
from typing import Dict, List

PHASE4_BRANCHES = [
    "chore/bootstrap-ci-governance",
    "chore/codex-auto-review",
    "dt-rag/chore/a-readme-hardening",
    "dt-rag/feat/a-api-services",
    "dt-rag/feat/a-hitl-worker",
    "dt-rag/feat/a-ingest-pipeline",
    "dt-rag/feat/a-observability",
    "dt-rag/feat/a-packaging",
    "dt-rag/feat/c-frontend",
    "feat/dt-rag-v1.8.1-implementation",
]


def run_git(cmd: str) -> str:
    """Git 명령 실행"""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=30
        )
        return result.stdout.strip()
    except Exception as e:
        return f"ERROR: {e}"


def analyze_branch(branch: str) -> Dict:
    """브랜치 분석"""
    # 최근 커밋 5개
    commits = run_git(f"git log --oneline -5 {branch}")

    # diff 통계
    diff_stat = run_git(f"git diff --stat master...{branch} 2>&1 | tail -1")

    # ahead/behind
    ahead = run_git(f"git rev-list --count master..{branch}")
    behind = run_git(f"git rev-list --count {branch}..master")

    return {
        "commits": commits,
        "diff_stat": diff_stat,
        "ahead": ahead,
        "behind": behind,
    }


def main():
    print("=" * 80)
    print("Phase 4: SPEC 없는 브랜치 빠른 스캔")
    print("=" * 80)
    print()

    results = {}

    for branch in PHASE4_BRANCHES:
        print(f"Analyzing: {branch}...")
        results[branch] = analyze_branch(branch)

    # 리포트 생성
    with open("phase4_quick_scan.txt", "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("Phase 4 브랜치 빠른 스캔 결과\n")
        f.write("=" * 80 + "\n\n")

        for branch, data in results.items():
            f.write(f"\n브랜치: {branch}\n")
            f.write(f"{'-' * 80}\n")
            f.write(f"Ahead: {data['ahead']} | Behind: {data['behind']}\n\n")
            f.write(f"Diff 통계:\n{data['diff_stat']}\n\n")
            f.write(f"최근 커밋:\n{data['commits']}\n\n")

    print()
    print("✅ 스캔 완료: phase4_quick_scan.txt")


if __name__ == "__main__":
    main()
