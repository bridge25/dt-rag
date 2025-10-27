#!/usr/bin/env python3
"""
남은 16개 브랜치 분석 및 정리 전략 수립
"""
import subprocess
from datetime import datetime

def run_cmd(cmd):
    """명령 실행"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip()

def get_branch_info(branch):
    """브랜치 정보 수집"""
    # Commits ahead/behind master
    ahead = run_cmd(f"git rev-list --count master..{branch} 2>/dev/null || echo 0")
    behind = run_cmd(f"git rev-list --count {branch}..master 2>/dev/null || echo 0")

    # Last commit date
    last_commit = run_cmd(f"git log -1 --format=%ai {branch} 2>/dev/null || echo 'N/A'")

    # Changed files count
    changed_files = run_cmd(f"git diff --name-only master...{branch} 2>/dev/null | wc -l")

    # Last commit message
    last_msg = run_cmd(f"git log -1 --format=%s {branch} 2>/dev/null || echo 'N/A'")

    return {
        'branch': branch,
        'ahead': int(ahead) if ahead.isdigit() else 0,
        'behind': int(behind) if behind.isdigit() else 0,
        'last_commit': last_commit,
        'changed_files': int(changed_files) if changed_files.isdigit() else 0,
        'last_msg': last_msg
    }

def categorize_branch(branch_name):
    """브랜치를 카테고리별로 분류"""
    if branch_name.startswith('backup'):
        return 'backup'
    elif branch_name.startswith('test'):
        return 'test'
    elif branch_name.startswith('feat'):
        return 'feature'
    elif branch_name.startswith('feature'):
        return 'feature'
    elif branch_name.startswith('fix'):
        return 'fix'
    elif branch_name.startswith('recovery'):
        return 'recovery'
    elif branch_name.startswith('integration'):
        return 'integration'
    elif branch_name == 'main':
        return 'legacy'
    else:
        return 'other'

def main():
    print("=" * 80)
    print("남은 브랜치 분석 및 정리 전략")
    print("=" * 80)
    print()

    # 현재 로컬 브랜치 목록
    branches_raw = run_cmd("git branch | grep -v '^\*' | sed 's/^[ \t]*//'")
    branches = [b.strip() for b in branches_raw.split('\n') if b.strip()]

    print(f"📊 총 로컬 브랜치: {len(branches)}개 (master 제외)")
    print()

    # 카테고리별 그룹화
    by_category = {}
    for branch in branches:
        cat = categorize_branch(branch)
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(branch)

    print("📂 카테고리별 분포:")
    for cat, items in sorted(by_category.items()):
        print(f"  {cat}: {len(items)}개")
    print()

    # 각 브랜치 상세 분석
    all_info = []
    for branch in branches:
        info = get_branch_info(branch)
        info['category'] = categorize_branch(branch)
        all_info.append(info)

    print("=" * 80)
    print("🔍 브랜치별 상세 분석")
    print("=" * 80)
    print()

    # 카테고리별로 출력
    for cat in sorted(by_category.keys()):
        print(f"## {cat.upper()} 브랜치")
        print("-" * 80)

        cat_branches = [b for b in all_info if b['category'] == cat]

        for info in cat_branches:
            print(f"\n### {info['branch']}")
            print(f"  Commits ahead/behind: +{info['ahead']} / -{info['behind']}")
            print(f"  Changed files: {info['changed_files']}")
            print(f"  Last commit: {info['last_commit'][:19] if len(info['last_commit']) > 19 else info['last_commit']}")
            print(f"  Last message: {info['last_msg'][:60]}")

        print()

    # 정리 권장사항
    print("=" * 80)
    print("💡 정리 권장사항")
    print("=" * 80)
    print()

    # 1. Backup 브랜치
    backup_branches = [b for b in all_info if b['category'] == 'backup']
    if backup_branches:
        print("1️⃣  BACKUP 브랜치 ({}개)".format(len(backup_branches)))
        print("   현재 상태: master-backup-before-consolidation 태그 존재")
        print("   권장 조치: 태그가 있으므로 오래된 백업 브랜치는 삭제 가능")
        print()
        for b in backup_branches:
            days_old = "N/A"
            if b['last_commit'] != 'N/A':
                try:
                    commit_date = datetime.fromisoformat(b['last_commit'][:19])
                    days_old = (datetime.now() - commit_date).days
                except:
                    pass
            print(f"   - {b['branch']}: {days_old}일 전")
        print()
        print("   실행 명령:")
        for b in backup_branches:
            print(f"   git branch -D {b['branch']}")
        print()

    # 2. Test 브랜치
    test_branches = [b for b in all_info if b['category'] == 'test']
    if test_branches:
        print("2️⃣  TEST 브랜치 ({}개)".format(len(test_branches)))
        print("   목적: 임시 테스트 브랜치")
        print("   권장 조치: 검증 완료 후 삭제")
        print()
        for b in test_branches:
            print(f"   - {b['branch']}: {b['changed_files']} files")
        print()
        print("   실행 명령:")
        for b in test_branches:
            print(f"   git branch -D {b['branch']}")
        print()

    # 3. Feature/Fix 브랜치
    feature_branches = [b for b in all_info if b['category'] in ['feature', 'fix']]
    if feature_branches:
        print("3️⃣  FEATURE/FIX 브랜치 ({}개)".format(len(feature_branches)))
        print("   상태: 개별 검토 필요")
        print()
        for b in feature_branches:
            status = "✅ Merged" if b['ahead'] == 0 else f"⚠️  Ahead +{b['ahead']}"
            print(f"   - {b['branch']}")
            print(f"     {status}, {b['changed_files']} files")
        print()

        merged = [b for b in feature_branches if b['ahead'] == 0]
        unmerged = [b for b in feature_branches if b['ahead'] > 0]

        if merged:
            print("   ✅ 병합 완료 (삭제 가능):")
            for b in merged:
                print(f"   git branch -D {b['branch']}")
            print()

        if unmerged:
            print("   ⚠️  미병합 (검토 필요):")
            for b in unmerged:
                print(f"   - {b['branch']}: +{b['ahead']} commits")
                print(f"     git diff master...{b['branch']} --stat")
            print()

    # 4. Legacy (main)
    legacy = [b for b in all_info if b['category'] == 'legacy']
    if legacy:
        print("4️⃣  LEGACY 브랜치 (main)")
        print("   현재 브랜치: master")
        print("   권장 조치: main 브랜치는 master와 동일하면 삭제")
        print()
        main_info = legacy[0]
        if main_info['ahead'] == 0 and main_info['behind'] == 0:
            print("   ✅ main과 master가 동일함 → 삭제 가능")
            print("   git branch -D main")
        else:
            print(f"   ⚠️  main이 master와 다름: +{main_info['ahead']} / -{main_info['behind']}")
            print("   git diff master...main --stat")
        print()

    # 5. Recovery/Integration
    other = [b for b in all_info if b['category'] in ['recovery', 'integration', 'other']]
    if other:
        print("5️⃣  RECOVERY/INTEGRATION ({}개)".format(len(other)))
        print("   권장 조치: 개별 검토")
        print()
        for b in other:
            print(f"   - {b['branch']}: +{b['ahead']} commits, {b['changed_files']} files")
        print()

    # 요약
    print("=" * 80)
    print("📋 정리 요약")
    print("=" * 80)
    print()

    safe_to_delete = len(backup_branches) + len(test_branches)
    needs_review = len(feature_branches) + len(other) + len(legacy)

    print(f"✅ 안전하게 삭제 가능: {safe_to_delete}개 (backup + test)")
    print(f"🔍 검토 필요: {needs_review}개 (feature/fix + legacy + other)")
    print()
    print(f"예상 결과: {len(branches)}개 → {needs_review}개 ({(1-needs_review/len(branches))*100:.1f}% 감소)")
    print()

if __name__ == "__main__":
    main()
