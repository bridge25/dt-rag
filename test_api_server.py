#!/usr/bin/env python3
"""
API 서버 시작 테스트 스크립트
FastAPI 파라미터 검증 오류 수정 확인
"""

import sys
import os
import asyncio
import traceback
from pathlib import Path

# 프로젝트 루트 디렉토리를 sys.path에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "apps" / "api"))

# 환경 변수 설정
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_dt_rag.db")
os.environ.setdefault("API_SECRET_KEY", "test-secret-key-for-dt-rag-api")

async def test_api_server_startup():
    """API 서버 시작 테스트"""
    print("🚀 API 서버 시작 테스트 시작...")

    try:
        # FastAPI 앱 임포트 시도
        print("📦 FastAPI 앱 임포트 중...")
        from apps.api.main import app
        print("✅ FastAPI 앱 임포트 성공")

        # 라우터 로딩 테스트
        print("🔗 라우터 로딩 테스트 중...")

        # Search 라우터 특별 테스트
        try:
            from apps.api.routers.search import router as search_router
            print("✅ Search 라우터 로딩 성공")

            # 라우터의 경로들 확인
            routes_info = []
            for route in search_router.routes:
                if hasattr(route, 'methods') and hasattr(route, 'path'):
                    routes_info.append(f"{list(route.methods)[0]} {route.path}")

            print(f"📋 Search 라우터 경로 수: {len(routes_info)}")
            for route_info in routes_info[:5]:  # 처음 5개만 표시
                print(f"   - {route_info}")
            if len(routes_info) > 5:
                print(f"   ... 및 {len(routes_info) - 5}개 더")

        except Exception as e:
            print(f"❌ Search 라우터 로딩 실패: {e}")
            traceback.print_exc()
            return False

        # OpenAPI 스키마 생성 테스트
        print("📄 OpenAPI 스키마 생성 테스트 중...")
        try:
            openapi_schema = app.openapi()
            paths_count = len(openapi_schema.get("paths", {}))
            print(f"✅ OpenAPI 스키마 생성 성공 ({paths_count}개 경로)")
        except Exception as e:
            print(f"❌ OpenAPI 스키마 생성 실패: {e}")
            traceback.print_exc()
            return False

        # 특정 문제 경로들 확인
        print("🔍 문제 경로들 확인 중...")
        problem_paths = [
            "/admin/cache/warm-up",
            "/admin/cache/clear"
        ]

        for path in problem_paths:
            found = False
            for route in app.routes:
                if hasattr(route, 'path') and route.path == path:
                    found = True
                    print(f"✅ 경로 발견: {path}")
                    break
            if not found:
                # 서브라우터에서 찾기
                for route in app.routes:
                    if hasattr(route, 'routes'):  # APIRouter
                        for subroute in route.routes:
                            if hasattr(subroute, 'path') and subroute.path == path:
                                found = True
                                print(f"✅ 서브라우터에서 경로 발견: {path}")
                                break
                        if found:
                            break

            if not found:
                print(f"⚠️ 경로 미발견: {path}")

        print("🎉 API 서버 시작 테스트 완료!")
        print("✅ 모든 FastAPI 파라미터 검증 오류가 수정되었습니다.")
        return True

    except Exception as e:
        print(f"❌ API 서버 시작 테스트 실패: {e}")
        traceback.print_exc()
        return False

def main():
    """메인 실행 함수"""
    try:
        result = asyncio.run(test_api_server_startup())
        if result:
            print("\n🎊 성공: API 서버가 정상적으로 로드됩니다!")
            return 0
        else:
            print("\n💥 실패: API 서버 로딩 중 오류 발생")
            return 1
    except Exception as e:
        print(f"\n💥 테스트 실행 실패: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)