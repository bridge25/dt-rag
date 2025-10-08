#!/usr/bin/env python3
"""
DT-RAG Requirements Installation Script
실제 PostgreSQL + pgvector 연결에 필요한 패키지들을 설치합니다.
"""

import subprocess
import sys
import os

def install_package(package_name: str, description: str = ""):
    """패키지 설치"""
    print(f"📦 Installing {package_name}...")
    if description:
        print(f"   Purpose: {description}")

    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"✅ {package_name} installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {package_name}: {e}")
        return False

def main():
    """메인 실행 함수"""
    print("🚀 DT-RAG Requirements Installation Starting...")
    print("=" * 60)

    # 필수 패키지 목록
    required_packages = [
        ("asyncpg", "PostgreSQL async driver"),
        ("psycopg2-binary", "PostgreSQL sync driver (backup)"),
        ("sqlalchemy[asyncio]", "Async SQLAlchemy ORM"),
        ("python-dotenv", "Environment variable management"),
        ("tiktoken", "OpenAI tokenizer"),
        ("scikit-learn", "ML algorithms for BM25"),
        ("numpy", "Numerical computing"),
        ("httpx", "Async HTTP client for OpenAI API"),
        ("uvicorn[standard]", "ASGI server"),
        ("fastapi", "Web framework"),
        ("pydantic", "Data validation"),
        ("python-multipart", "File upload support"),
        ("redis", "Redis client (optional)"),
        ("psutil", "System monitoring"),
    ]

    success_count = 0
    total_packages = len(required_packages)

    for package, description in required_packages:
        if install_package(package, description):
            success_count += 1
        print()

    print("=" * 60)
    print(f"📊 Installation Summary:")
    print(f"   ✅ Successful: {success_count}/{total_packages} packages")
    print(f"   ❌ Failed: {total_packages - success_count}/{total_packages} packages")

    if success_count == total_packages:
        print("\n🎉 All packages installed successfully!")
        print()
        print("📋 Next Steps:")
        print("   1. Start PostgreSQL: docker-compose up -d")
        print("   2. Setup database: python setup_database.py")
        print("   3. Generate embeddings: python generate_embeddings.py")
        print("   4. Start server: python full_server.py")
        print()
        print("🌐 Environment Check:")
        print(f"   - Python: {sys.version}")
        print(f"   - Platform: {sys.platform}")
        print(f"   - Working Directory: {os.getcwd()}")

        return True
    else:
        print("\n⚠️ Some packages failed to install!")
        print("Please check the error messages above and resolve any issues.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)