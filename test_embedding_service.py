#!/usr/bin/env python3
"""
임베딩 서비스 테스트 스크립트
실제 Sentence Transformers 모델을 사용한 벡터 생성 테스트
"""
# @TEST:EMBED-001 | SPEC: .moai/specs/SPEC-EMBED-001/spec.md

import asyncio
import logging
import sys
import os
from typing import List, Dict, Any

# 모듈 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps', 'api'))

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_embedding_service():
    """임베딩 서비스 종합 테스트"""
    try:
        from embedding_service import (
            embedding_service,
            generate_embedding,
            generate_embeddings,
            calculate_similarity,
            get_service_info,
            health_check
        )

        print("임베딩 서비스 테스트 시작")
        print("=" * 60)

        # 1. 서비스 정보 확인
        print("\n1. 서비스 정보 확인")
        service_info = get_service_info()
        print(f"   모델: {service_info.get('model_name')}")
        print(f"   목표 차원: {service_info.get('target_dimensions')}")
        print(f"   모델 로드 상태: {service_info.get('model_loaded')}")
        print(f"   Sentence Transformers 사용 가능: {service_info.get('sentence_transformers_available')}")

        # 2. 헬스체크
        print("\n2. 헬스체크")
        health_status = health_check()
        print(f"   상태: {health_status.get('status')}")
        if health_status.get('status') == 'healthy':
            print(f"   테스트 임베딩 차원: {health_status.get('test_embedding_shape')}")
        elif health_status.get('status') == 'degraded':
            print(f"   폴백 모드 실행: {health_status.get('fallback_mode')}")

        # 3. 단일 임베딩 생성 테스트
        print("\n3. 단일 임베딩 생성 테스트")
        test_text = "Dynamic Taxonomy RAG 시스템은 문서 검색과 분류를 위한 고급 AI 시스템입니다."

        embedding = await generate_embedding(test_text)
        print(f"   텍스트: {test_text[:50]}...")
        print(f"   생성된 임베딩 차원: {len(embedding)}")
        print(f"   임베딩 값 샘플: {embedding[:5]}")

        # 4. 배치 임베딩 생성 테스트
        print("\n4. 배치 임베딩 생성 테스트")
        test_texts = [
            "RAG 시스템은 검색 증강 생성 모델입니다.",
            "벡터 임베딩은 텍스트를 수치 벡터로 변환합니다.",
            "pgvector는 PostgreSQL용 벡터 확장입니다.",
            "Sentence Transformers는 문장 임베딩을 생성합니다."
        ]

        embeddings = await generate_embeddings(test_texts, batch_size=2)
        print(f"   배치 크기: {len(test_texts)}")
        print(f"   생성된 임베딩 수: {len(embeddings)}")
        print(f"   각 임베딩 차원: {len(embeddings[0]) if embeddings else 0}")

        # 5. 유사도 계산 테스트
        print("\n5. 유사도 계산 테스트")
        if len(embeddings) >= 2:
            similarity = calculate_similarity(embeddings[0], embeddings[1])
            print(f"   임베딩 1과 2의 유사도: {similarity:.4f}")

            # 자기 자신과의 유사도 (1.0에 가까워야 함)
            self_similarity = calculate_similarity(embeddings[0], embeddings[0])
            print(f"   자기 자신과의 유사도: {self_similarity:.4f}")

        # 6. 캐시 테스트
        print("\n6. 캐시 테스트")
        print("   캐시 사용하여 동일 텍스트 재요청...")
        cached_embedding = await generate_embedding(test_text, use_cache=True)
        print(f"   캐시된 임베딩 차원: {len(cached_embedding)}")

        # 원본과 캐시된 임베딩이 동일한지 확인
        is_same = all(abs(a - b) < 1e-10 for a, b in zip(embedding, cached_embedding))
        print(f"   원본과 캐시 임베딩 일치: {is_same}")

        # 7. 현재 캐시 크기
        cache_size = embedding_service.clear_cache()
        print(f"   클리어된 캐시 항목 수: {cache_size}")

        print("\n✅ 모든 테스트 완료!")
        return True

    except ImportError as e:
        print(f"❌ 모듈 import 실패: {e}")
        print("💡 다음 패키지를 설치해주세요:")
        print("   pip install sentence-transformers torch transformers scikit-learn")
        return False
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        logger.exception("테스트 실행 중 오류 발생")
        return False

async def test_database_integration():
    """데이터베이스 통합 테스트"""
    try:
        from embedding_service import (
            document_embedding_service,
            get_embedding_status,
            update_document_embeddings
        )
        from database import test_database_connection

        print("\n🗄️ 데이터베이스 통합 테스트")
        print("=" * 60)

        # 1. 데이터베이스 연결 확인
        print("\n1. 데이터베이스 연결 확인")
        db_connected = await test_database_connection()
        print(f"   연결 상태: {'성공' if db_connected else '실패'}")

        if not db_connected:
            print("   데이터베이스 연결이 필요합니다.")
            return False

        # 2. 임베딩 상태 조회
        print("\n2. 임베딩 상태 조회")
        status = await get_embedding_status()

        if 'error' in status:
            print(f"   오류: {status['error']}")
        else:
            stats = status.get('statistics', {})
            print(f"   전체 청크 수: {stats.get('total_chunks', 0)}")
            print(f"   임베딩된 청크 수: {stats.get('embedded_chunks', 0)}")
            print(f"   누락된 임베딩: {stats.get('missing_embeddings', 0)}")
            print(f"   임베딩 커버리지: {status.get('embedding_coverage_percent', 0):.1f}%")

        # 3. 문서 임베딩 업데이트 테스트 (소규모)
        print("\n3. 문서 임베딩 업데이트 테스트")
        update_result = await update_document_embeddings(
            document_ids=None,  # 모든 문서 (실제로는 누락된 것만)
            batch_size=5  # 작은 배치 크기로 테스트
        )

        if update_result.get('success'):
            print(f"   업데이트된 청크 수: {update_result.get('updated_count', 0)}")
            print(f"   전체 청크 수: {update_result.get('total_chunks', 0)}")
            print(f"   사용된 모델: {update_result.get('model_name')}")
        else:
            print(f"   업데이트 실패: {update_result.get('error')}")

        print("\n✅ 데이터베이스 통합 테스트 완료!")
        return True

    except ImportError as e:
        print(f"❌ 데이터베이스 모듈 import 실패: {e}")
        return False
    except Exception as e:
        print(f"❌ 데이터베이스 테스트 실패: {e}")
        logger.exception("데이터베이스 테스트 중 오류 발생")
        return False

def print_installation_guide():
    """설치 가이드 출력"""
    print("\n📦 필수 패키지 설치 가이드")
    print("=" * 60)
    print("1. 기본 설치:")
    print("   pip install sentence-transformers torch transformers scikit-learn")
    print()
    print("2. 또는 프로젝트 의존성 설치:")
    print("   pip install -e .")
    print()
    print("3. GPU 지원 (선택사항):")
    print("   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")
    print()
    print("4. 데이터베이스 설정:")
    print("   - PostgreSQL + pgvector 확장 필요")
    print("   - DATABASE_URL 환경변수 설정")
    print()

async def main():
    """메인 테스트 함수"""
    print("🧪 DT-RAG 임베딩 서비스 종합 테스트")
    print("=" * 80)

    # 임베딩 서비스 테스트
    service_success = await test_embedding_service()

    if service_success:
        # 데이터베이스 통합 테스트
        db_success = await test_database_integration()

        if service_success and db_success:
            print("\n🎉 모든 테스트 성공!")
            print("\n📋 다음 단계:")
            print("1. FastAPI 서버 시작: python apps/api/main.py")
            print("2. 임베딩 API 테스트: curl http://localhost:8000/api/v1/embeddings/health")
            print("3. Swagger UI 확인: http://localhost:8000/docs")
        else:
            print("\n⚠️ 일부 테스트 실패")
    else:
        print_installation_guide()

if __name__ == "__main__":
    asyncio.run(main())