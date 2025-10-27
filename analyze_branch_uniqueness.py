#!/usr/bin/env python3
"""
각 브랜치의 고유 변경사항 분석
- 각 브랜치가 변경한 파일 목록
- 브랜치 간 겹치는 파일 vs 고유 파일
- 통합 전략 추천
"""
import subprocess
from pathlib import Path
from collections import defaultdict
import json

# Phase 2 브랜치 목록 (가이드에서 확인한 15개 + v1.8.1)
BRANCHES = [
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

def get_changed_files(branch):
    """브랜치에서 변경된 파일 목록 (master 대비)"""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", f"master...{branch}"],
            capture_output=True,
            text=True,
            check=True
        )
        files = [f for f in result.stdout.strip().split('\n') if f]
        return set(files)
    except subprocess.CalledProcessError:
        return set()

def categorize_file(filepath):
    """파일을 카테고리별로 분류"""
    if filepath.startswith('apps/'):
        return 'app_code'
    elif filepath.startswith('tests/'):
        return 'tests'
    elif filepath.startswith('.moai/specs/'):
        return 'specs'
    elif filepath.startswith('.claude/') or filepath.startswith('.moai/'):
        return 'infrastructure'
    elif filepath.startswith('.github/'):
        return 'ci_cd'
    elif filepath.endswith('.md'):
        return 'docs'
    else:
        return 'other'

def main():
    print("=" * 80)
    print("브랜치 고유성 분석 (Branch Uniqueness Analysis)")
    print("=" * 80)
    print()

    # 1. 각 브랜치의 변경 파일 수집
    print("📊 Step 1: 각 브랜치의 변경 파일 수집 중...")
    print()

    branch_files = {}
    for branch in BRANCHES:
        files = get_changed_files(branch)
        branch_files[branch] = files
        print(f"  {branch}: {len(files)} files")

    print()
    print("=" * 80)

    # 2. 파일별로 어느 브랜치에서 변경되었는지 추적
    print("📊 Step 2: 파일별 변경 브랜치 추적 중...")
    print()

    file_to_branches = defaultdict(set)
    for branch, files in branch_files.items():
        for file in files:
            file_to_branches[file].add(branch)

    # 3. 고유 파일 vs 공통 파일 분석
    unique_files = {f for f, branches in file_to_branches.items() if len(branches) == 1}
    shared_files = {f for f, branches in file_to_branches.items() if len(branches) > 1}

    print(f"총 고유 파일: {len(unique_files)}")
    print(f"총 공통 파일 (여러 브랜치가 변경): {len(shared_files)}")
    print()

    # 4. 각 브랜치의 고유 기여도
    print("=" * 80)
    print("📊 Step 3: 각 브랜치의 고유 기여도 분석")
    print("=" * 80)
    print()

    branch_stats = []
    for branch in BRANCHES:
        files = branch_files[branch]
        unique = [f for f in files if f in unique_files]
        shared = [f for f in files if f in shared_files]

        # 카테고리별 고유 파일
        unique_by_cat = defaultdict(int)
        for f in unique:
            cat = categorize_file(f)
            unique_by_cat[cat] += 1

        branch_stats.append({
            'branch': branch.split('/')[-1],
            'total_files': len(files),
            'unique_files': len(unique),
            'shared_files': len(shared),
            'uniqueness_ratio': len(unique) / len(files) if files else 0,
            'unique_by_category': dict(unique_by_cat)
        })

        print(f"{branch.split('/')[-1]}")
        print(f"  전체 변경: {len(files)} files")
        print(f"  고유 변경: {len(unique)} files ({len(unique)/len(files)*100:.1f}%)")
        print(f"  공통 변경: {len(shared)} files ({len(shared)/len(files)*100:.1f}%)")
        if unique_by_cat:
            print(f"  고유 파일 카테고리:")
            for cat, count in sorted(unique_by_cat.items(), key=lambda x: -x[1]):
                print(f"    - {cat}: {count} files")
        print()

    # 5. 공통 파일 상위 10개 (가장 많이 변경된 파일)
    print("=" * 80)
    print("📊 Step 4: 가장 많은 브랜치가 변경한 파일 (충돌 위험 높음)")
    print("=" * 80)
    print()

    most_changed = sorted(
        [(f, len(branches)) for f, branches in file_to_branches.items()],
        key=lambda x: -x[1]
    )[:20]

    for file, count in most_changed:
        if count > 1:
            print(f"  {file}")
            print(f"    → {count}개 브랜치에서 변경")

    print()

    # 6. 통합 전략 추천
    print("=" * 80)
    print("💡 통합 전략 추천")
    print("=" * 80)
    print()

    # 가장 많은 파일을 변경한 브랜치 찾기
    largest_branch = max(branch_stats, key=lambda x: x['total_files'])
    most_unique_branch = max(branch_stats, key=lambda x: x['unique_files'])

    print(f"🏆 가장 큰 브랜치: {largest_branch['branch']}")
    print(f"   → {largest_branch['total_files']} files 변경")
    print()
    print(f"🎯 가장 고유한 기여: {most_unique_branch['branch']}")
    print(f"   → {most_unique_branch['unique_files']} unique files")
    print()

    # 공통 파일 비율
    total_files = len(file_to_branches)
    overlap_ratio = len(shared_files) / total_files if total_files > 0 else 0

    print(f"📊 전체 통계:")
    print(f"   - 총 변경된 고유 파일: {total_files}")
    print(f"   - 여러 브랜치가 수정: {len(shared_files)} ({overlap_ratio*100:.1f}%)")
    print(f"   - 하나만 수정: {len(unique_files)} ({(1-overlap_ratio)*100:.1f}%)")
    print()

    if overlap_ratio > 0.7:
        print("⚠️  경고: 70% 이상의 파일이 여러 브랜치에서 변경됨")
        print("   → Fresh Start 시 하나만 선택하면 안전하지 않음")
        print("   → 권장: Layer-by-layer 통합 또는 수동 병합")
    elif overlap_ratio > 0.4:
        print("⚠️  주의: 40-70%의 파일이 여러 브랜치에서 변경됨")
        print("   → 가장 큰 브랜치를 base로 하고, 고유 파일만 추가 병합")
        print(f"   → 추천 base: {largest_branch['branch']}")
    else:
        print("✅ 양호: 대부분의 변경이 브랜치별로 독립적")
        print("   → 가장 큰 브랜치를 base로 사용 가능")
        print(f"   → 추천 base: {largest_branch['branch']}")

    print()
    print("=" * 80)
    print("✅ 분석 완료!")
    print()
    print("다음 단계:")
    print("1. 위 분석 결과를 바탕으로 통합 전략 결정")
    print("2. merge_branches_smart.py 스크립트로 자동 통합")
    print("   (충돌 파일은 수동 검토 필요)")
    print()

    # JSON 결과 저장
    with open('branch_analysis_result.json', 'w') as f:
        json.dump({
            'total_unique_files': total_files,
            'shared_files_count': len(shared_files),
            'unique_files_count': len(unique_files),
            'overlap_ratio': overlap_ratio,
            'branches': branch_stats,
            'recommended_base': largest_branch['branch'],
            'most_unique': most_unique_branch['branch']
        }, f, indent=2)

    print("📄 상세 결과가 branch_analysis_result.json에 저장되었습니다.")

if __name__ == "__main__":
    main()
