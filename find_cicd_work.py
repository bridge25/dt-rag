#!/usr/bin/env python3
"""
최근 CI/CD 파이프라인 수정 작업 추적
- 며칠 전 밤새 작업한 200+ 에러 수정 찾기
- 어느 브랜치에 있는지 확인
- Fresh Start 시 보존 필요 여부 판단
"""
import subprocess
from datetime import datetime, timedelta
from collections import defaultdict
import re

BRANCHES = [
    "master",
    "feat/dt-rag-v1.8.1-implementation",
    "feature/SPEC-FOUNDATION-001",
    "feature/SPEC-ENV-VALIDATE-001",
    "feature/SPEC-REDIS-COMPAT-001",
    "feature/SPEC-AGENT-GROWTH-001",
    "feature/SPEC-AGENT-GROWTH-002",
    "feature/SPEC-AGENT-GROWTH-004",
    "feature/SPEC-AGENT-GROWTH-005",
    "feature/SPEC-CASEBANK-002",
    "feature/SPEC-CONSOLIDATION-001",
    "feature/SPEC-DEBATE-001",
    "feature/SPEC-JOB-OPTIMIZE-001",
    "feature/SPEC-REFLECTION-001",
    "feature/SPEC-REPLAY-001",
    "feature/SPEC-SOFTQ-001",
    "feature/SPEC-UI-INTEGRATION-001",
]

# CI/CD 관련 키워드
CICD_KEYWORDS = [
    'ci', 'cd', 'pipeline', 'workflow', 'github action',
    'mypy', 'pytest', 'lint', 'flake8', 'ruff', 'black',
    'test', 'error', 'fix', 'build', 'deploy'
]

def get_recent_commits(branch, days=14):
    """최근 N일 내의 커밋 가져오기"""
    try:
        since_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        result = subprocess.run(
            ['git', 'log', branch,
             '--since', since_date,
             '--format=%H|%ai|%s|%an',
             '--'],
            capture_output=True,
            text=True,
            check=True
        )

        commits = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            parts = line.split('|', 3)
            if len(parts) == 4:
                hash, date, msg, author = parts
                commits.append({
                    'hash': hash,
                    'date': date,
                    'message': msg,
                    'author': author,
                    'branch': branch
                })
        return commits
    except subprocess.CalledProcessError:
        return []

def is_cicd_related(commit_msg):
    """CI/CD 관련 커밋인지 판단"""
    msg_lower = commit_msg.lower()
    return any(keyword in msg_lower for keyword in CICD_KEYWORDS)

def get_file_changes(branch, commit_hash):
    """특정 커밋의 변경 파일 목록"""
    try:
        result = subprocess.run(
            ['git', 'diff-tree', '--no-commit-id', '--name-only', '-r', commit_hash],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip().split('\n')
    except subprocess.CalledProcessError:
        return []

def count_night_work_session(commits):
    """밤 시간대 연속 작업 세션 찾기 (22시~6시)"""
    night_sessions = []
    current_session = []

    for commit in commits:
        try:
            commit_time = datetime.fromisoformat(commit['date'].replace(' ', 'T'))
            hour = commit_time.hour

            # 밤 시간 (22시~6시)
            if 22 <= hour or hour < 6:
                current_session.append(commit)
            else:
                if len(current_session) > 3:  # 3개 이상 연속 커밋
                    night_sessions.append(current_session[:])
                current_session = []
        except:
            continue

    if len(current_session) > 3:
        night_sessions.append(current_session)

    return night_sessions

def main():
    print("=" * 80)
    print("🔍 CI/CD 파이프라인 수정 작업 추적")
    print("=" * 80)
    print()
    print("최근 2주간의 모든 브랜치를 검색합니다...")
    print()

    # 1. 모든 브랜치의 최근 커밋 수집
    all_commits = []
    for branch in BRANCHES:
        commits = get_recent_commits(branch, days=14)
        all_commits.extend(commits)
        print(f"  {branch}: {len(commits)} commits")

    print()
    print(f"총 {len(all_commits)} commits 수집 완료")
    print()

    # 2. CI/CD 관련 커밋 필터링
    cicd_commits = [c for c in all_commits if is_cicd_related(c['message'])]

    print("=" * 80)
    print(f"📊 CI/CD 관련 커밋: {len(cicd_commits)}개 발견")
    print("=" * 80)
    print()

    if not cicd_commits:
        print("⚠️  CI/CD 관련 커밋을 찾지 못했습니다.")
        return

    # 3. 브랜치별 그룹화
    by_branch = defaultdict(list)
    for commit in cicd_commits:
        by_branch[commit['branch']].append(commit)

    # 4. 날짜순 정렬 (최신순)
    cicd_commits.sort(key=lambda x: x['date'], reverse=True)

    # 5. 최근 CI/CD 커밋 표시
    print("🕐 최근 CI/CD 관련 커밋 (최신 20개):")
    print()
    for i, commit in enumerate(cicd_commits[:20], 1):
        date_obj = datetime.fromisoformat(commit['date'].replace(' ', 'T'))
        date_str = date_obj.strftime('%Y-%m-%d %H:%M')
        branch_name = commit['branch'].split('/')[-1]

        # 밤 시간 강조
        hour = date_obj.hour
        time_marker = " 🌙" if (22 <= hour or hour < 6) else ""

        print(f"{i:2d}. [{date_str}{time_marker}] {branch_name}")
        print(f"    {commit['message'][:80]}")
        print(f"    Hash: {commit['hash'][:8]}")
        print()

    # 6. 밤샘 작업 세션 찾기
    print("=" * 80)
    print("🌙 밤샘 작업 세션 분석 (22시~6시, 3+ 연속 커밋)")
    print("=" * 80)
    print()

    for branch in BRANCHES:
        branch_commits = [c for c in cicd_commits if c['branch'] == branch]
        if not branch_commits:
            continue

        night_sessions = count_night_work_session(branch_commits)

        if night_sessions:
            print(f"📍 {branch}")
            for session_idx, session in enumerate(night_sessions, 1):
                print(f"   Session {session_idx}: {len(session)} commits")
                start_time = datetime.fromisoformat(session[0]['date'].replace(' ', 'T'))
                end_time = datetime.fromisoformat(session[-1]['date'].replace(' ', 'T'))
                duration = end_time - start_time

                print(f"   시작: {start_time.strftime('%Y-%m-%d %H:%M')}")
                print(f"   종료: {end_time.strftime('%Y-%m-%d %H:%M')}")
                print(f"   지속시간: {duration}")
                print()

                for commit in session[:5]:  # 최대 5개만
                    print(f"      - {commit['message'][:60]}")
                if len(session) > 5:
                    print(f"      ... (+{len(session)-5} more)")
                print()

    # 7. 브랜치별 CI/CD 커밋 통계
    print("=" * 80)
    print("📊 브랜치별 CI/CD 작업 통계")
    print("=" * 80)
    print()

    branch_stats = []
    for branch in BRANCHES:
        commits = by_branch[branch]
        if not commits:
            continue

        # .github/workflows/ 변경 확인
        workflow_changes = 0
        for commit in commits:
            files = get_file_changes(branch, commit['hash'])
            workflow_changes += sum(1 for f in files if '.github/workflows/' in f)

        branch_stats.append({
            'branch': branch.split('/')[-1],
            'commits': len(commits),
            'workflow_changes': workflow_changes,
            'latest_date': commits[0]['date']
        })

    branch_stats.sort(key=lambda x: x['commits'], reverse=True)

    for stat in branch_stats:
        print(f"{stat['branch']}")
        print(f"  CI/CD 커밋: {stat['commits']}개")
        print(f"  Workflow 파일 변경: {stat['workflow_changes']}개")
        print(f"  최근 작업: {stat['latest_date'][:10]}")
        print()

    # 8. 결론 및 권장사항
    print("=" * 80)
    print("💡 결론 및 권장사항")
    print("=" * 80)
    print()

    if branch_stats:
        top_branch = branch_stats[0]
        print(f"🎯 가장 많은 CI/CD 작업: {top_branch['branch']}")
        print(f"   → {top_branch['commits']}개 커밋, {top_branch['workflow_changes']}개 파일 변경")
        print()

    # SPEC-AGENT-GROWTH-005와 비교
    growth005_commits = by_branch.get('feature/SPEC-AGENT-GROWTH-005', [])
    print(f"📍 선택된 Base 브랜치 (SPEC-AGENT-GROWTH-005):")
    print(f"   CI/CD 커밋: {len(growth005_commits)}개")
    print()

    if growth005_commits:
        print("✅ SPEC-AGENT-GROWTH-005에 CI/CD 작업 포함됨")
        print("   → Fresh Start 시 자동으로 보존됨")
    else:
        print("⚠️  SPEC-AGENT-GROWTH-005에 CI/CD 작업이 없음!")
        print()
        if branch_stats:
            cicd_branch = branch_stats[0]['branch']
            print(f"❗ 권장: {cicd_branch}의 CI/CD 변경사항을 수동으로 추가해야 함")
            print()
            print("실행 명령:")
            print(f"  git checkout feature/SPEC-AGENT-GROWTH-005")
            print(f"  git checkout {cicd_branch} -- .github/workflows/")
            print(f"  git add .github/workflows/")
            print(f"  git commit -m 'chore: Preserve CI/CD pipeline fixes from {cicd_branch}'")

    print()
    print("=" * 80)
    print("✅ 분석 완료!")
    print()

if __name__ == "__main__":
    main()
