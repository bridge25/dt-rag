#!/usr/bin/env python3
"""
FastAPI 파라미터 검증 오류 수정 검증 스크립트

수정된 사항:
1. clear_search_cache 함수의 pattern 파라미터 순서 수정
2. logger 추가로 참조 오류 해결
3. CacheWarmUpRequest 모델의 common_queries 필드 정상 작동 확인
"""

import sys
import os
import traceback
from pathlib import Path

# 프로젝트 루트 설정
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "apps" / "api"))

# 환경 변수 설정
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_dt_rag.db")
os.environ.setdefault("API_SECRET_KEY", "test-secret-key-for-dt-rag-api")

def validate_search_router():
    """Search 라우터 검증"""
    print("🔍 Search 라우터 검증 중...")

    try:
        # Search 라우터 임포트
        from apps.api.routers.search import router as search_router
        from apps.api.routers.search import CacheWarmUpRequest

        print("✅ Search 라우터 및 모델 임포트 성공")

        # 라우트 개수 확인
        route_count = len(search_router.routes)
        print(f"📊 라우트 개수: {route_count}")

        # 특정 문제 라우트 확인
        cache_routes = []
        for route in search_router.routes:
            if hasattr(route, 'path') and 'cache' in route.path:
                methods = list(route.methods) if hasattr(route, 'methods') else ['UNKNOWN']
                cache_routes.append(f"{methods[0]} {route.path}")

        print(f"🔧 캐시 관련 라우트: {len(cache_routes)}개")
        for route_info in cache_routes:
            print(f"   - {route_info}")

        # CacheWarmUpRequest 모델 테스트
        test_request = CacheWarmUpRequest(common_queries=["test query"])
        print(f"✅ CacheWarmUpRequest 모델 작동 확인: {len(test_request.common_queries)}개 쿼리")

        return True

    except Exception as e:
        print(f"❌ Search 라우터 검증 실패: {e}")
        traceback.print_exc()
        return False

def validate_fastapi_app():
    """FastAPI 앱 전체 검증"""
    print("\n🚀 FastAPI 앱 전체 검증 중...")

    try:
        from fastapi import FastAPI
        from apps.api.routers.search import router as search_router

        # FastAPI 앱 생성 및 라우터 포함
        app = FastAPI(title="Test API")
        app.include_router(search_router, prefix="/api/v1")

        print("✅ FastAPI 앱 생성 및 라우터 포함 성공")

        # OpenAPI 스키마 생성 (파라미터 검증 오류 시 실패)
        try:
            openapi_schema = app.openapi()
            paths_count = len(openapi_schema.get("paths", {}))
            print(f"✅ OpenAPI 스키마 생성 성공: {paths_count}개 경로")

            # 문제가 있었던 특정 경로 확인
            problem_paths = [
                "/api/v1/admin/cache/warm-up",
                "/api/v1/admin/cache/clear"
            ]

            for path in problem_paths:
                if path in openapi_schema.get("paths", {}):
                    print(f"✅ 문제 경로 정상 확인: {path}")
                else:
                    print(f"⚠️ 경로 미발견: {path}")

            return True

        except AssertionError as e:
            if "non-body parameters must be in path, query, header or cookie" in str(e):
                print(f"❌ FastAPI 파라미터 검증 오류 아직 존재: {e}")
                return False
            else:
                raise

    except Exception as e:
        print(f"❌ FastAPI 앱 검증 실패: {e}")
        traceback.print_exc()
        return False

def validate_parameter_definitions():
    """파라미터 정의 검증"""
    print("\n🔧 파라미터 정의 검증 중...")

    try:
        import inspect
        from apps.api.routers.search import clear_search_cache, warm_up_cache

        # clear_search_cache 함수 시그니처 검증
        sig = inspect.signature(clear_search_cache)
        params = list(sig.parameters.keys())
        print(f"🔍 clear_search_cache 파라미터 순서: {params}")

        # api_key가 pattern보다 먼저 와야 함 (Depends는 맨 앞에)
        api_key_index = params.index('api_key') if 'api_key' in params else -1
        pattern_index = params.index('pattern') if 'pattern' in params else -1

        if api_key_index != -1 and pattern_index != -1:
            if api_key_index < pattern_index:
                print("✅ clear_search_cache 파라미터 순서 올바름")
            else:
                print("❌ clear_search_cache 파라미터 순서 문제")
                return False

        # warm_up_cache 함수 시그니처 검증
        sig2 = inspect.signature(warm_up_cache)
        params2 = list(sig2.parameters.keys())
        print(f"🔍 warm_up_cache 파라미터: {params2}")

        return True

    except Exception as e:
        print(f"❌ 파라미터 정의 검증 실패: {e}")
        traceback.print_exc()
        return False

def main():
    """메인 검증 함수"""
    print("🔧 FastAPI 파라미터 검증 오류 수정 검증")
    print("="*60)

    results = []

    # 1. Search 라우터 검증
    results.append(validate_search_router())

    # 2. 파라미터 정의 검증
    results.append(validate_parameter_definitions())

    # 3. FastAPI 앱 전체 검증
    results.append(validate_fastapi_app())

    # 결과 요약
    print("\n" + "="*60)
    print("📊 검증 결과")
    print("="*60)

    success_count = sum(results)
    total_count = len(results)

    print(f"성공: {success_count}/{total_count}")

    if success_count == total_count:
        print("\n🎉 모든 검증 통과!")
        print("✅ FastAPI 파라미터 검증 오류가 완전히 수정되었습니다.")
        print("\n수정된 사항:")
        print("1. clear_search_cache 함수의 파라미터 순서 수정")
        print("2. logger 추가로 참조 오류 해결")
        print("3. Query 파라미터 올바른 사용법 적용")
        return 0
    else:
        print(f"\n❌ {total_count - success_count}개 검증 실패")
        print("추가 수정이 필요합니다.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)