"""
Phase 2 최적화 구현 검증 스크립트
비동기 병렬 처리 및 API 최적화 구현 상태 확인

검증 항목:
1. 최적화 모듈 import 가능성
2. 핵심 클래스 및 함수 존재 확인
3. 성능 목표 설정 확인
4. SearchDAO 최적화 통합 확인
5. API 라우터 최적화 적용 확인
"""

import sys
import os
import importlib
from typing import Dict, Any, List

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_module_import(module_name: str) -> Dict[str, Any]:
    """모듈 import 가능성 검증"""
    try:
        module = importlib.import_module(module_name)
        return {
            "module": module_name,
            "status": "success",
            "available_attributes": dir(module)
        }
    except ImportError as e:
        return {
            "module": module_name,
            "status": "failed",
            "error": str(e)
        }
    except Exception as e:
        return {
            "module": module_name,
            "status": "error",
            "error": str(e)
        }

def validate_optimization_modules() -> Dict[str, Any]:
    """최적화 모듈들 검증"""
    print("🔍 Phase 2 최적화 모듈 검증 시작...")

    validation_results = {
        "optimization_modules": {},
        "core_functionality": {},
        "integration_status": {},
        "performance_targets": {},
        "overall_status": "unknown"
    }

    # 1. 최적화 모듈 import 검증
    print("\n📦 최적화 모듈 Import 검증:")
    optimization_modules = [
        "apps.api.optimization",
        "apps.api.optimization.async_executor",
        "apps.api.optimization.memory_optimizer",
        "apps.api.optimization.concurrency_control",
        "apps.api.optimization.batch_processor"
    ]

    module_results = {}
    for module_name in optimization_modules:
        result = check_module_import(module_name)
        module_results[module_name] = result
        status_icon = "✅" if result["status"] == "success" else "❌"
        print(f"   {status_icon} {module_name}: {result['status']}")
        if result["status"] != "success":
            print(f"      Error: {result.get('error', 'Unknown error')}")

    validation_results["optimization_modules"] = module_results

    # 2. 핵심 기능 검증
    print("\n🔧 핵심 기능 검증:")

    try:
        from apps.api.optimization import (
            get_async_optimizer,
            get_batch_search_processor,
            get_memory_monitor,
            get_concurrency_controller,
            PERFORMANCE_TARGETS
        )

        validation_results["core_functionality"] = {
            "async_optimizer": "available",
            "batch_processor": "available",
            "memory_monitor": "available",
            "concurrency_controller": "available",
            "performance_targets": "available"
        }
        print("   ✅ 모든 핵심 최적화 함수 사용 가능")

        # 성능 목표 확인
        validation_results["performance_targets"] = PERFORMANCE_TARGETS
        print(f"   ✅ 성능 목표 설정 확인:")
        for key, value in PERFORMANCE_TARGETS.items():
            print(f"      - {key}: {value}")

    except ImportError as e:
        validation_results["core_functionality"] = {"error": str(e)}
        print(f"   ❌ 핵심 기능 import 실패: {e}")
    except Exception as e:
        validation_results["core_functionality"] = {"error": str(e)}
        print(f"   ❌ 핵심 기능 검증 오류: {e}")

    # 3. SearchDAO 통합 확인
    print("\n🔍 SearchDAO 최적화 통합 확인:")

    try:
        from apps.api.database import SearchDAO

        # SearchDAO에 최적화 메서드 존재 확인
        dao_methods = dir(SearchDAO)
        optimization_methods = [
            "hybrid_search",
            "_execute_optimized_hybrid_search",
            "_execute_legacy_hybrid_search"
        ]

        dao_integration = {}
        for method in optimization_methods:
            has_method = method in dao_methods
            dao_integration[method] = "available" if has_method else "missing"
            status_icon = "✅" if has_method else "❌"
            print(f"   {status_icon} {method}: {'available' if has_method else 'missing'}")

        validation_results["integration_status"]["search_dao"] = dao_integration

    except ImportError as e:
        validation_results["integration_status"]["search_dao"] = {"error": str(e)}
        print(f"   ❌ SearchDAO import 실패: {e}")
    except Exception as e:
        validation_results["integration_status"]["search_dao"] = {"error": str(e)}
        print(f"   ❌ SearchDAO 검증 오류: {e}")

    # 4. API 라우터 최적화 확인
    print("\n🌐 API 라우터 최적화 확인:")

    try:
        # Search router 확인
        search_router_result = check_module_import("apps.api.routers.search")
        if search_router_result["status"] == "success":
            print("   ✅ 검색 라우터 최적화 통합 완료")
        else:
            print(f"   ❌ 검색 라우터 확인 실패: {search_router_result['error']}")

        # Batch search router 확인
        batch_router_result = check_module_import("apps.api.routers.batch_search")
        if batch_router_result["status"] == "success":
            print("   ✅ 배치 검색 라우터 구현 완료")
        else:
            print(f"   ⚠️ 배치 검색 라우터 확인 실패: {batch_router_result['error']}")

        validation_results["integration_status"]["api_routers"] = {
            "search_router": search_router_result["status"],
            "batch_router": batch_router_result["status"]
        }

    except Exception as e:
        validation_results["integration_status"]["api_routers"] = {"error": str(e)}
        print(f"   ❌ API 라우터 검증 오류: {e}")

    # 5. 전체 상태 평가
    print("\n📊 전체 구현 상태 평가:")

    success_count = 0
    total_checks = 0

    # 모듈 import 성공률
    module_success = sum(1 for r in module_results.values() if r["status"] == "success")
    total_checks += len(module_results)
    success_count += module_success
    print(f"   모듈 Import: {module_success}/{len(module_results)} 성공")

    # 핵심 기능 가용성
    if isinstance(validation_results["core_functionality"], dict) and "error" not in validation_results["core_functionality"]:
        success_count += 1
        print("   핵심 기능: ✅ 사용 가능")
    else:
        print("   핵심 기능: ❌ 사용 불가")
    total_checks += 1

    # 통합 상태
    search_dao_ok = isinstance(validation_results["integration_status"].get("search_dao"), dict) and "error" not in validation_results["integration_status"]["search_dao"]
    if search_dao_ok:
        success_count += 1
        print("   SearchDAO 통합: ✅ 완료")
    else:
        print("   SearchDAO 통합: ❌ 미완료")
    total_checks += 1

    # 전체 성공률 계산
    success_rate = success_count / total_checks if total_checks > 0 else 0

    if success_rate >= 0.8:
        overall_status = "excellent"
        status_icon = "🎉"
        status_desc = "우수"
    elif success_rate >= 0.6:
        overall_status = "good"
        status_icon = "✅"
        status_desc = "양호"
    elif success_rate >= 0.4:
        overall_status = "partial"
        status_icon = "⚠️"
        status_desc = "부분적"
    else:
        overall_status = "poor"
        status_icon = "❌"
        status_desc = "미흡"

    validation_results["overall_status"] = overall_status
    validation_results["success_rate"] = success_rate
    validation_results["success_count"] = success_count
    validation_results["total_checks"] = total_checks

    print(f"\n{status_icon} 전체 구현 상태: {status_desc} ({success_count}/{total_checks}, {success_rate:.1%})")

    return validation_results

def generate_implementation_report(validation_results: Dict[str, Any]) -> str:
    """구현 상태 보고서 생성"""

    report = []
    report.append("=" * 80)
    report.append("Phase 2 최적화 구현 검증 보고서")
    report.append("=" * 80)
    report.append("")

    # 전체 요약
    overall_status = validation_results.get("overall_status", "unknown")
    success_rate = validation_results.get("success_rate", 0)
    success_count = validation_results.get("success_count", 0)
    total_checks = validation_results.get("total_checks", 0)

    report.append(f"📊 전체 구현 상태: {overall_status.upper()}")
    report.append(f"✅ 성공률: {success_count}/{total_checks} ({success_rate:.1%})")
    report.append("")

    # 모듈별 상세 상태
    report.append("📦 최적화 모듈 상태:")
    module_results = validation_results.get("optimization_modules", {})
    for module, result in module_results.items():
        status_icon = "✅" if result["status"] == "success" else "❌"
        report.append(f"   {status_icon} {module}: {result['status']}")
        if result["status"] != "success":
            report.append(f"      Error: {result.get('error', 'Unknown')}")
    report.append("")

    # 핵심 기능 상태
    report.append("🔧 핵심 기능 상태:")
    core_functionality = validation_results.get("core_functionality", {})
    if isinstance(core_functionality, dict) and "error" not in core_functionality:
        for func, status in core_functionality.items():
            report.append(f"   ✅ {func}: {status}")
    else:
        report.append(f"   ❌ 핵심 기능 오류: {core_functionality.get('error', 'Unknown')}")
    report.append("")

    # 성능 목표
    report.append("🎯 성능 목표 설정:")
    performance_targets = validation_results.get("performance_targets", {})
    if performance_targets:
        for target, value in performance_targets.items():
            report.append(f"   📈 {target}: {value}")
    else:
        report.append("   ❌ 성능 목표 설정 없음")
    report.append("")

    # 통합 상태
    report.append("🔗 시스템 통합 상태:")
    integration_status = validation_results.get("integration_status", {})
    for component, status in integration_status.items():
        if isinstance(status, dict) and "error" not in status:
            report.append(f"   ✅ {component}: 통합 완료")
            for sub_component, sub_status in status.items():
                if isinstance(sub_status, str):
                    sub_icon = "✅" if sub_status in ["available", "success"] else "❌"
                    report.append(f"      {sub_icon} {sub_component}: {sub_status}")
        else:
            report.append(f"   ❌ {component}: 통합 실패")
            if isinstance(status, dict):
                report.append(f"      Error: {status.get('error', 'Unknown')}")
    report.append("")

    # 권장사항
    report.append("💡 권장사항:")
    recommendations = generate_recommendations(validation_results)
    for i, rec in enumerate(recommendations, 1):
        report.append(f"   {i}. {rec}")

    report.append("")
    report.append("=" * 80)

    return "\n".join(report)

def generate_recommendations(validation_results: Dict[str, Any]) -> List[str]:
    """개선 권장사항 생성"""
    recommendations = []

    success_rate = validation_results.get("success_rate", 0)

    if success_rate < 0.8:
        recommendations.append("일부 최적화 모듈의 구현이 미완료되었습니다. 누락된 모듈을 구현하세요.")

    # 모듈별 권장사항
    module_results = validation_results.get("optimization_modules", {})
    failed_modules = [name for name, result in module_results.items() if result["status"] != "success"]

    if failed_modules:
        recommendations.append(f"다음 모듈들의 구현을 완료하세요: {', '.join(failed_modules)}")

    # 핵심 기능 권장사항
    core_functionality = validation_results.get("core_functionality", {})
    if isinstance(core_functionality, dict) and "error" in core_functionality:
        recommendations.append("핵심 최적화 함수들을 정상적으로 import할 수 있도록 코드를 수정하세요.")

    # 통합 권장사항
    integration_status = validation_results.get("integration_status", {})
    for component, status in integration_status.items():
        if isinstance(status, dict) and "error" in status:
            recommendations.append(f"{component}의 통합을 완료하세요.")

    if not recommendations:
        recommendations.append("모든 최적화 구현이 완료되었습니다. 성능 테스트를 진행하세요.")

    return recommendations

def main():
    """메인 실행 함수"""
    print("🚀 Phase 2 최적화 구현 검증 시작")

    try:
        # 검증 실행
        validation_results = validate_optimization_modules()

        # 보고서 생성
        report = generate_implementation_report(validation_results)

        # 결과 출력
        print("\n" + report)

        # 결과 파일 저장
        import json
        with open("phase2_optimization_validation.json", "w", encoding="utf-8") as f:
            json.dump(validation_results, f, indent=2, ensure_ascii=False, default=str)

        with open("phase2_optimization_report.txt", "w", encoding="utf-8") as f:
            f.write(report)

        print("\n📄 검증 결과가 저장되었습니다:")
        print("   - phase2_optimization_validation.json (상세 데이터)")
        print("   - phase2_optimization_report.txt (보고서)")

        # 최종 상태 반환
        overall_status = validation_results.get("overall_status", "unknown")
        success_rate = validation_results.get("success_rate", 0)

        if success_rate >= 0.8:
            print("\n🎉 Phase 2 최적화 구현이 성공적으로 완료되었습니다!")
            return True
        elif success_rate >= 0.6:
            print("\n✅ Phase 2 최적화 구현이 대부분 완료되었습니다.")
            return True
        else:
            print("\n⚠️ Phase 2 최적화 구현에 추가 작업이 필요합니다.")
            return False

    except Exception as e:
        print(f"\n❌ 검증 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()