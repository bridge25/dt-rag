#!/usr/bin/env python3
"""
DT-RAG Production System Launcher
전체 DT-RAG 시스템을 프로덕션 환경으로 시작합니다.
"""

import asyncio
import os
import sys
import subprocess
import time
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def check_docker_services():
    """Docker 서비스 상태 확인"""
    print("🐳 Checking Docker services...")

    try:
        # PostgreSQL 컨테이너 확인
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=dt_rag_postgres", "--format", "{{.Status}}"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0 and "Up" in result.stdout:
            print("   ✅ PostgreSQL container is running")
            postgres_running = True
        else:
            print("   ❌ PostgreSQL container not running")
            postgres_running = False

        # Redis 컨테이너 확인 (선택사항)
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=dt_rag_redis", "--format", "{{.Status}}"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0 and "Up" in result.stdout:
            print("   ✅ Redis container is running")
            redis_running = True
        else:
            print("   ⚠️ Redis container not running (optional)")
            redis_running = False

        return postgres_running, redis_running

    except FileNotFoundError:
        print("   ❌ Docker not found - please install Docker")
        return False, False

def start_docker_services():
    """Docker 서비스 시작"""
    print("🚀 Starting Docker services...")

    try:
        result = subprocess.run(
            ["docker-compose", "up", "-d"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print("   ✅ Docker services started")
            return True
        else:
            print(f"   ❌ Failed to start Docker services: {result.stderr}")
            return False

    except FileNotFoundError:
        print("   ❌ docker-compose not found")
        return False

async def verify_system_readiness():
    """시스템 준비 상태 확인"""
    print("\n🔍 Verifying system readiness...")

    try:
        from apps.api.database import test_database_connection

        # 데이터베이스 연결 확인
        print("   Testing database connection...")
        db_connected = await test_database_connection()

        if not db_connected:
            print("   ❌ Database connection failed")
            return False

        print("   ✅ Database connection successful")

        # 테이블 존재 확인
        from apps.api.database import db_manager
        from sqlalchemy import text

        async with db_manager.async_session() as session:
            result = await session.execute(
                text("SELECT COUNT(*) FROM documents")
            )
            doc_count = result.scalar()

        print(f"   📊 Documents in database: {doc_count}")

        if doc_count == 0:
            print("   ⚠️ No documents found - consider running setup_database.py first")

        return True

    except Exception as e:
        print(f"   ❌ System verification failed: {e}")
        return False

def choose_server_mode():
    """서버 모드 선택"""
    print("\n🎯 Choose server mode:")
    print("   1. Full Feature Server (port 8001) - Complete functionality")
    print("   2. Main API Server (port 8000) - Comprehensive API")
    print("   3. Both servers")

    while True:
        choice = input("   Enter your choice (1/2/3): ").strip()
        if choice in ["1", "2", "3"]:
            return int(choice)
        print("   Invalid choice. Please enter 1, 2, or 3.")

async def start_servers(mode: int):
    """서버 시작"""
    print("\n🚀 Starting DT-RAG servers...")

    servers = []

    if mode in [1, 3]:  # Full Feature Server
        print("   Starting Full Feature Server (port 8001)...")
        try:
            server1 = subprocess.Popen([
                sys.executable, "full_server.py"
            ])
            servers.append(("Full Feature Server", server1, 8001))
            print("   ✅ Full Feature Server started")
        except Exception as e:
            print(f"   ❌ Failed to start Full Feature Server: {e}")

    if mode in [2, 3]:  # Main API Server
        print("   Starting Main API Server (port 8000)...")
        try:
            server2 = subprocess.Popen([
                sys.executable, "-m", "apps.api.main"
            ])
            servers.append(("Main API Server", server2, 8000))
            print("   ✅ Main API Server started")
        except Exception as e:
            print(f"   ❌ Failed to start Main API Server: {e}")

    if not servers:
        print("   ❌ No servers started")
        return []

    # 서버 시작 대기
    print("   ⏳ Waiting for servers to initialize...")
    await asyncio.sleep(3)

    return servers

def display_system_info(servers):
    """시스템 정보 표시"""
    print("\n🎉 DT-RAG Production System Started!")
    print("=" * 60)

    if servers:
        print("🌐 Active Servers:")
        for name, _, port in servers:
            print(f"   {name}: http://localhost:{port}")
            print(f"   Documentation: http://localhost:{port}/docs")

        print("\n📚 API Documentation:")
        for name, _, port in servers:
            print(f"   {name} Swagger UI: http://localhost:{port}/docs")
            print(f"   {name} ReDoc: http://localhost:{port}/redoc")

        print("\n🔍 Health Checks:")
        for name, _, port in servers:
            print(f"   {name}: http://localhost:{port}/health")

        print("\n📊 Monitoring:")
        for name, _, port in servers:
            if port == 8000:  # Main API has monitoring
                print(f"   System Monitoring: http://localhost:{port}/api/v1/monitoring/health")

    print("\n💡 Tips:")
    print("   - Use Ctrl+C to stop all servers")
    print("   - Check server logs for any issues")
    print("   - Test endpoints using the Swagger UI")
    print("   - Upload documents via /api/v1/ingestion/upload")
    print("   - Search documents via /api/v1/search")

    print("\n🔧 Development Commands:")
    print("   Setup database: python setup_database.py")
    print("   Generate embeddings: python generate_embeddings.py")
    print("   Test system: python test_production_system.py")

async def main():
    """메인 실행 함수"""
    print("🚀 DT-RAG Production System Launcher")
    print("=" * 60)

    # 1. Docker 서비스 확인
    postgres_running, redis_running = await check_docker_services()

    if not postgres_running:
        print("\n🔧 PostgreSQL not running. Starting Docker services...")
        if not start_docker_services():
            print("❌ Failed to start Docker services")
            print("📋 Manual start: docker-compose up -d")
            return False

        # Docker 서비스 시작 대기
        print("   ⏳ Waiting for services to initialize...")
        await asyncio.sleep(5)

    # 2. 시스템 준비 상태 확인
    system_ready = await verify_system_readiness()

    if not system_ready:
        print("\n⚠️ System not fully ready. Some features may not work.")
        print("💡 Consider running: python setup_database.py")

        continue_anyway = input("\n Continue anyway? (y/N): ").strip().lower()
        if continue_anyway != 'y':
            print("❌ Startup cancelled")
            return False

    # 3. 서버 모드 선택
    server_mode = choose_server_mode()

    # 4. 서버 시작
    servers = await start_servers(server_mode)

    if not servers:
        print("❌ No servers could be started")
        return False

    # 5. 시스템 정보 표시
    display_system_info(servers)

    # 6. 서버 모니터링 및 종료 대기
    try:
        print("\n⏳ Servers running... Press Ctrl+C to stop")
        while True:
            await asyncio.sleep(1)

            # 서버 프로세스 상태 확인
            active_servers = []
            for name, process, port in servers:
                if process.poll() is None:  # 프로세스가 아직 실행 중
                    active_servers.append((name, process, port))
                else:
                    print(f"⚠️ {name} stopped unexpectedly")

            if not active_servers:
                print("❌ All servers stopped")
                break

            servers = active_servers

    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down servers...")

        for name, process, port in servers:
            print(f"   Stopping {name}...")
            process.terminate()

        # 종료 대기
        await asyncio.sleep(2)

        for name, process, port in servers:
            if process.poll() is None:
                print(f"   Force killing {name}...")
                process.kill()

        print("✅ All servers stopped")

    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Startup interrupted")
        sys.exit(1)