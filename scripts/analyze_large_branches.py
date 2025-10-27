#!/usr/bin/env python3
"""
대형 브랜치 상세 분석
- master에 없는 고유 파일 찾기
- 중요 변경사항 식별
- 병합 가치 판단
"""
import subprocess
from collections import defaultdict
from pathlib import Path

BRANCHES = [
    "feature/SPEC-API-INTEGRATION-001",
    "fix/reflection-batch-empty-db",
]

def run_cmd(cmd):
    """명령 실행"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip()

def get_unique_files(branch):
    """master에 없는 브랜치 고유 파일 찾기"""
    # 브랜치에만 있는 파일 (master에는 없음)
    cmd = f"git diff --name-only --diff-filter=A master...{branch}"
    result = run_cmd(cmd)

    added_files = [f for f in result.split('\n') if f]

    # 브랜치에서 수정된 파일 (master에도 있지만 내용이 다름)
    cmd = f"git diff --name-only --diff-filter=M master...{branch}"
    result = run_cmd(cmd)

    modified_files = [f for f in result.split('\n') if f]

    return added_files, modified_files

def categorize_files(files):
    """파일을 카테고리별로 분류"""
    categories = defaultdict(list)

    for f in files:
        if f.startswith('apps/'):
            if '/api/' in f:
                categories['api'].append(f)
            elif '/frontend' in f:
                categories['frontend'].append(f)
            elif '/core/' in f:
                categories['core'].append(f)
            elif '/ingestion/' in f:
                categories['ingestion'].append(f)
            elif '/classification/' in f:
                categories['classification'].append(f)
            elif '/evaluation/' in f:
                categories['evaluation'].append(f)
            elif '/orchestration/' in f:
                categories['orchestration'].append(f)
            else:
                categories['apps_other'].append(f)
        elif f.startswith('tests/'):
            categories['tests'].append(f)
        elif f.startswith('.moai/specs/'):
            categories['specs'].append(f)
        elif f.startswith('.github/'):
            categories['ci_cd'].append(f)
        elif f.endswith('.md'):
            categories['docs'].append(f)
        elif f.endswith(('.py', '.ts', '.tsx', '.js', '.jsx')):
            categories['code_other'].append(f)
        else:
            categories['other'].append(f)

    return categories

def check_file_in_master(filepath):
    """파일이 master에 존재하는지 확인"""
    cmd = f"git ls-tree -r master --name-only | grep -F '{filepath}'"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return bool(result.stdout.strip())

def get_file_diff_stats(branch, filepath):
    """파일의 변경 통계"""
    cmd = f"git diff --stat master...{branch} -- '{filepath}'"
    result = run_cmd(cmd)
    return result

def main():
    print("=" * 80)
    print("🔍 대형 브랜치 상세 분석")
    print("=" * 80)
    print()

    for branch in BRANCHES:
        print("=" * 80)
        print(f"📊 {branch}")
        print("=" * 80)
        print()

        # 브랜치 정보
        commits_ahead = run_cmd(f"git rev-list --count master..{branch}")
        commits_behind = run_cmd(f"git rev-list --count {branch}..master")

        print(f"Commits: +{commits_ahead} / -{commits_behind}")
        print()

        # 고유 파일 찾기
        added_files, modified_files = get_unique_files(branch)

        print(f"📁 파일 분류:")
        print(f"  - 신규 파일 (master에 없음): {len(added_files)}개")
        print(f"  - 수정된 파일 (master와 다름): {len(modified_files)}개")
        print()

        # 신규 파일 카테고리별 분석
        if added_files:
            print("🆕 신규 파일 (master에 없음)")
            print("-" * 80)

            added_by_cat = categorize_files(added_files)

            for cat, files in sorted(added_by_cat.items(), key=lambda x: -len(x[1])):
                print(f"\n### {cat.upper()} ({len(files)}개)")

                # 상위 10개만 표시
                for f in files[:10]:
                    # 파일 크기 확인
                    size_cmd = f"git show {branch}:'{f}' | wc -c"
                    size = run_cmd(size_cmd)
                    size_kb = int(size) / 1024 if size.isdigit() else 0

                    print(f"  - {f} ({size_kb:.1f} KB)")

                if len(files) > 10:
                    print(f"  ... (+{len(files)-10} more)")

        print()

        # 수정된 파일 중 중요한 것들
        if modified_files:
            print("✏️  수정된 주요 파일 (master에도 있지만 내용이 다름)")
            print("-" * 80)

            modified_by_cat = categorize_files(modified_files)

            # 중요 카테고리만 (api, core, frontend)
            important_cats = ['api', 'core', 'frontend', 'orchestration']

            for cat in important_cats:
                if cat in modified_by_cat:
                    files = modified_by_cat[cat]
                    print(f"\n### {cat.upper()} ({len(files)}개)")

                    for f in files[:5]:
                        stats = get_file_diff_stats(branch, f)
                        if stats:
                            # 통계에서 변경된 줄 수 추출
                            lines = stats.split('\n')[-1] if stats else ""
                            print(f"  - {f}")
                            if lines.strip():
                                print(f"    {lines.strip()}")

                    if len(files) > 5:
                        print(f"  ... (+{len(files)-5} more)")

        print()
        print()

    # 종합 분석
    print("=" * 80)
    print("💡 종합 분석 및 권장사항")
    print("=" * 80)
    print()

    for branch in BRANCHES:
        print(f"## {branch}")
        print("-" * 80)

        added_files, modified_files = get_unique_files(branch)
        added_by_cat = categorize_files(added_files)
        modified_by_cat = categorize_files(modified_files)

        # 중요도 평가
        critical_new = 0
        critical_modified = 0

        # 핵심 모듈의 신규 파일
        for cat in ['api', 'core', 'orchestration']:
            critical_new += len(added_by_cat.get(cat, []))

        # 핵심 모듈의 수정 파일
        for cat in ['api', 'core', 'orchestration']:
            critical_modified += len(modified_by_cat.get(cat, []))

        print(f"신규 파일: {len(added_files)}개")
        print(f"  - 핵심 모듈: {critical_new}개")
        print(f"  - 기타: {len(added_files) - critical_new}개")
        print()
        print(f"수정 파일: {len(modified_files)}개")
        print(f"  - 핵심 모듈: {critical_modified}개")
        print(f"  - 기타: {len(modified_files) - critical_modified}개")
        print()

        # 권장사항
        if critical_new > 10 or critical_modified > 20:
            print("⚠️  권장: 개별 검토 후 선택적 병합")
            print("   핵심 모듈에 중요한 변경사항이 많습니다.")
        elif critical_new > 0 or critical_modified > 0:
            print("⚠️  권장: 핵심 파일만 검토")
            print("   일부 중요 파일이 있을 수 있습니다.")
        else:
            print("✅ 권장: 삭제 가능")
            print("   핵심 변경사항이 없습니다.")

        print()

        # 상위 5개 신규 파일 경로
        if added_files:
            print("📌 확인 필요 신규 파일 (상위 5개):")
            for f in added_files[:5]:
                print(f"  - {f}")
            print()

    print("=" * 80)
    print("✅ 분석 완료")
    print()
    print("다음 단계:")
    print("1. 각 브랜치의 핵심 파일 목록 확인")
    print("2. master에 누락된 중요 파일 식별")
    print("3. 필요 시 선택적으로 파일 가져오기")
    print("4. 검증 후 브랜치 삭제")
    print()

if __name__ == "__main__":
    main()
