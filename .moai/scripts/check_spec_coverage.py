#!/usr/bin/env python3
"""
SPEC 문서화율 자동 체크 스크립트
실행: python .moai/scripts/check_spec_coverage.py
"""
import os
from pathlib import Path
from collections import defaultdict

def count_python_files(apps_dir: Path) -> dict:
    """모듈별 Python 파일 수 계산"""
    modules = defaultdict(int)
    for py_file in apps_dir.rglob("*.py"):
        if "__pycache__" in str(py_file) or "test_" in py_file.name:
            continue
        module = py_file.relative_to(apps_dir).parts[0]
        modules[module] += 1
    return dict(modules)

def count_spec_documents(specs_dir: Path) -> dict:
    """SPEC 문서 상태 확인"""
    specs = {}
    if not specs_dir.exists():
        return specs

    for spec_dir in specs_dir.iterdir():
        if not spec_dir.is_dir() or not spec_dir.name.startswith("SPEC-"):
            continue

        has_spec = (spec_dir / "spec.md").exists()
        has_plan = (spec_dir / "plan.md").exists()
        has_acceptance = (spec_dir / "acceptance.md").exists()

        status = "완료" if (has_spec and has_plan and has_acceptance) else "불완전"
        specs[spec_dir.name] = {
            "status": status,
            "spec.md": has_spec,
            "plan.md": has_plan,
            "acceptance.md": has_acceptance
        }

    return specs

def main():
    project_root = Path(__file__).parent.parent.parent
    apps_dir = project_root / "apps"
    specs_dir = project_root / ".moai" / "specs"

    print("=" * 60)
    print("📊 SPEC 문서화율 분석 리포트")
    print("=" * 60)
    print()

    # 모듈 분석
    modules = count_python_files(apps_dir)
    print(f"✅ 구현된 모듈: {len(modules)}개")
    for module, count in sorted(modules.items(), key=lambda x: x[1], reverse=True):
        print(f"   - {module}: {count}개 파일")
    print()

    # SPEC 분석
    specs = count_spec_documents(specs_dir)
    complete_specs = sum(1 for s in specs.values() if s["status"] == "완료")
    incomplete_specs = len(specs) - complete_specs

    print(f"📝 SPEC 문서: {len(specs)}개 (완료 {complete_specs}개, 불완전 {incomplete_specs}개)")
    for spec_name, info in sorted(specs.items()):
        status_icon = "✅" if info["status"] == "완료" else "⚠️"
        print(f"   {status_icon} {spec_name}: {info['status']}")
        if info["status"] == "불완전":
            missing = [k for k, v in info.items() if k != "status" and not v]
            print(f"      누락: {', '.join(missing)}")
    print()

    # 문서화율 계산
    coverage = (len(specs) / len(modules)) * 100 if modules else 0
    quality = (complete_specs / len(specs)) * 100 if specs else 0

    print(f"📈 문서화율: {coverage:.1f}% ({len(specs)}/{len(modules)} 모듈)")
    print(f"📈 SPEC 완성도: {quality:.1f}% ({complete_specs}/{len(specs)} 문서)")
    print()

    # 권장사항
    if coverage < 50:
        print("⚠️  권장: Phase 1~2 우선순위 SPEC 작성 필요")
    if quality < 75:
        print("⚠️  권장: 기존 SPEC에 plan.md, acceptance.md 추가 필요")

    print("=" * 60)

if __name__ == "__main__":
    main()
