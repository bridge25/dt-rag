#!/usr/bin/env python3
"""
Document Ingestion Pipeline Test

문서 처리 파이프라인 기능 테스트:
- 파서 테스트
- 청킹 테스트
- PII 필터링 테스트
- 통합 파이프라인 테스트
"""

import asyncio
import tempfile
import logging
from pathlib import Path
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_document_parsers():
    """문서 파서 테스트"""
    print("\n=== 문서 파서 테스트 ===")

    from apps.ingestion.document_parser import get_parser_factory

    factory = get_parser_factory()

    # 지원되는 확장자 확인
    print(f"지원되는 확장자: {factory.get_supported_extensions()}")

    # 텍스트 파일 테스트
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        test_content = """
        이것은 테스트 문서입니다.

        여러 줄로 구성되어 있으며, 한국어와 English가 혼재되어 있습니다.
        PII 테스트를 위해 가짜 이메일 test@example.com을 포함합니다.
        전화번호 010-1234-5678도 포함되어 있습니다.
        """
        f.write(test_content)
        f.flush()

        try:
            parser = factory.get_parser(f.name)
            print(f"텍스트 파서: {parser.__class__.__name__}")

            parsed_doc = await factory.parse_document(f.name)
            print(f"파싱 결과:")
            print(f"  - 콘텐츠 길이: {len(parsed_doc.content)}")
            print(f"  - 인코딩: {parsed_doc.encoding}")
            print(f"  - 소스 타입: {parsed_doc.source_type}")
            print(f"  - 체크섬: {parsed_doc.get_checksum()[:8]}...")

        except Exception as e:
            print(f"텍스트 파서 테스트 실패: {e}")
        finally:
            os.unlink(f.name)

    # JSON 파일 테스트
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        test_json = '''
        {
            "title": "테스트 문서",
            "content": "JSON 형태의 문서입니다",
            "metadata": {
                "author": "test@example.com",
                "phone": "010-9999-8888"
            },
            "sections": [
                {"name": "섹션 1", "text": "첫 번째 섹션"},
                {"name": "섹션 2", "text": "두 번째 섹션"}
            ]
        }
        '''
        f.write(test_json)
        f.flush()

        try:
            parser = factory.get_parser(f.name)
            print(f"\nJSON 파서: {parser.__class__.__name__}")

            parsed_doc = await factory.parse_document(f.name)
            print(f"파싱 결과:")
            print(f"  - 콘텐츠 길이: {len(parsed_doc.content)}")
            print(f"  - 소스 타입: {parsed_doc.source_type}")
            print(f"  - 콘텐츠 미리보기: {parsed_doc.content[:100]}...")

        except Exception as e:
            print(f"JSON 파서 테스트 실패: {e}")
        finally:
            os.unlink(f.name)

async def test_chunking_strategies():
    """청킹 전략 테스트"""
    print("\n=== 청킹 전략 테스트 ===")

    from apps.ingestion.chunking_strategy import ChunkingStrategyFactory

    test_text = """
    인공지능(AI)은 현대 기술의 핵심 분야입니다. 머신러닝과 딥러닝 기술의 발전으로
    다양한 응용 분야에서 혁신이 일어나고 있습니다.

    RAG(Retrieval-Augmented Generation) 시스템은 정보 검색과 생성을 결합한
    새로운 패러다임입니다. 이 시스템은 대용량 문서에서 관련 정보를 찾아
    정확하고 신뢰할 수 있는 답변을 생성합니다.

    자연어 처리 기술의 발전으로 사람과 기계 간의 상호작용이 더욱 자연스러워지고 있습니다.
    분류체계(Taxonomy)를 통해 정보를 체계적으로 구조화할 수 있습니다.

    이러한 기술들은 교육, 의료, 금융 등 다양한 분야에서 활용되고 있으며,
    앞으로도 지속적인 발전이 예상됩니다.
    """

    # Token-based 청킹 테스트
    try:
        token_chunker = ChunkingStrategyFactory.create_strategy(
            "token_based",
            chunk_size=200,
            chunk_overlap=50
        )

        chunks = await token_chunker.chunk_text(test_text)
        print(f"Token-based 청킹 결과: {len(chunks)}개 청크")
        for i, chunk in enumerate(chunks):
            print(f"  청크 {i+1}: {chunk.token_count}토큰, {len(chunk.text)}자")
            print(f"    시작: {chunk.text[:50]}...")

    except Exception as e:
        print(f"Token-based 청킹 테스트 실패: {e}")

    # Semantic 청킹 테스트
    try:
        semantic_chunker = ChunkingStrategyFactory.create_strategy(
            "semantic",
            max_chunk_size=300,
            prefer_paragraphs=True
        )

        chunks = await semantic_chunker.chunk_text(test_text)
        print(f"\nSemantic 청킹 결과: {len(chunks)}개 청크")
        for i, chunk in enumerate(chunks):
            print(f"  청크 {i+1}: {chunk.token_count}토큰")
            print(f"    내용: {chunk.text[:80]}...")

    except Exception as e:
        print(f"Semantic 청킹 테스트 실패: {e}")

async def test_pii_filtering():
    """PII 필터링 테스트"""
    print("\n=== PII 필터링 테스트 ===")

    from apps.ingestion.pii_filter import PIIFilter, MaskingStrategy, PIIType

    test_text = """
    안녕하세요. 제 이름은 김철수이고, 연락처는 다음과 같습니다.

    이메일: kim.chulsu@example.com
    휴대폰: 010-1234-5678
    주민등록번호: 900101-1234567
    신용카드: 4532-1234-5678-9012

    회사 이메일은 chulsu@company.co.kr이고,
    사무실 전화번호는 02-1234-5678입니다.

    추가 연락처: jane.doe@gmail.com, john@test.org
    국제 전화: +82-10-9876-5432
    """

    # 기본 PII 필터 테스트
    try:
        pii_filter = PIIFilter(compliance_mode="balanced")

        result = await pii_filter.filter_text(test_text)

        print(f"PII 필터링 결과:")
        print(f"  - 탐지된 PII: {len(result.detected_pii)}개")
        print(f"  - 처리 시간: {result.processing_time:.3f}초")
        print(f"  - 준수 플래그: {result.compliance_flags}")

        print(f"\n탐지된 PII 목록:")
        for pii in result.detected_pii:
            print(f"  - {pii.pii_type.value}: '{pii.text}' (신뢰도: {pii.confidence:.2f})")

        print(f"\n필터링된 텍스트:")
        print(result.filtered_text[:200] + "...")

    except Exception as e:
        print(f"PII 필터링 테스트 실패: {e}")

    # 엄격 모드 테스트
    try:
        strict_filter = PIIFilter(compliance_mode="strict")

        custom_strategies = {
            PIIType.EMAIL: MaskingStrategy.REDACT,
            PIIType.PHONE: MaskingStrategy.REDACT,
            PIIType.SSN_KR: MaskingStrategy.REDACT
        }

        result = await strict_filter.filter_text(
            test_text,
            custom_strategies=custom_strategies
        )

        print(f"\n엄격 모드 PII 필터링:")
        print(f"  - GDPR 준수: {result.compliance_flags['gdpr_compliant']}")
        print(f"  - PIPA 준수: {result.compliance_flags['pipa_compliant']}")
        print(f"\n엄격 필터링된 텍스트:")
        print(result.filtered_text[:200] + "...")

    except Exception as e:
        print(f"엄격 모드 테스트 실패: {e}")

async def test_integrated_pipeline():
    """통합 파이프라인 테스트"""
    print("\n=== 통합 파이프라인 테스트 ===")

    from apps.ingestion.ingestion_pipeline import IngestionPipeline, ProgressCallback

    # 진행률 콜백 함수
    async def progress_callback(current, total, status, details):
        percentage = (current / total * 100) if total > 0 else 0
        print(f"진행률: {current}/{total} ({percentage:.1f}%) - {status}")
        if details:
            print(f"  세부사항: {details}")

    callback = ProgressCallback(progress_callback)

    # 테스트 문서 생성
    test_files = []

    # 텍스트 파일
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("""
        RAG(Retrieval-Augmented Generation) 시스템 설계 문서

        1. 개요
        RAG는 정보 검색과 생성 AI를 결합한 하이브리드 시스템입니다.

        2. 아키텍처
        - 문서 저장소
        - 벡터 임베딩
        - 검색 엔진
        - 생성 모델

        연락처: admin@example.com
        전화: 02-123-4567
        """)
        test_files.append(f.name)

    # JSON 파일
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('''
        {
            "project": "Dynamic Taxonomy RAG",
            "version": "1.8.1",
            "description": "동적 분류체계 기반 RAG 시스템",
            "features": [
                "다중 포맷 문서 처리",
                "PII 필터링",
                "임베딩 생성",
                "하이브리드 검색"
            ],
            "contact": {
                "email": "project@company.com",
                "phone": "010-9999-8888"
            }
        }
        ''')
        test_files.append(f.name)

    try:
        # 파이프라인 초기화 (임베딩 비활성화로 테스트 간소화)
        pipeline = IngestionPipeline(
            chunking_strategy="semantic",
            chunking_params={"max_chunk_size": 300},
            enable_embeddings=False,  # 테스트용
            batch_size=5
        )

        print(f"파이프라인 설정:")
        stats = pipeline.get_statistics()
        print(f"  - 청킹 전략: {stats['configuration']['chunking_strategy']}")
        print(f"  - PII 필터 모드: {stats['configuration']['pii_filter_mode']}")
        print(f"  - 지원 형식: {stats['capabilities']['supported_formats']}")

        # 배치 처리 실행
        print(f"\n배치 처리 시작: {len(test_files)}개 파일")

        batch_result = await pipeline.process_batch(
            test_files,
            progress_callback=callback
        )

        print(f"\n배치 처리 결과:")
        print(f"  - 전체 문서: {batch_result.total_documents}")
        print(f"  - 성공: {batch_result.successful}")
        print(f"  - 실패: {batch_result.failed}")
        print(f"  - 총 청크: {batch_result.total_chunks}")
        print(f"  - 처리 시간: {batch_result.processing_time:.2f}초")

        if batch_result.error_summary:
            print(f"  - 에러 요약: {batch_result.error_summary}")

        # 개별 결과 확인
        print(f"\n개별 문서 결과:")
        for result in batch_result.results:
            print(f"  {Path(result.source).name}:")
            print(f"    상태: {result.status.value}")
            print(f"    청크: {result.chunks_created}개")
            print(f"    PII 탐지: {result.pii_detected}개")
            print(f"    처리 시간: {result.processing_time:.2f}초")
            if result.error_message:
                print(f"    에러: {result.error_message}")

    except Exception as e:
        print(f"통합 파이프라인 테스트 실패: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # 임시 파일 정리
        for file_path in test_files:
            try:
                os.unlink(file_path)
            except:
                pass

async def test_database_connection():
    """데이터베이스 연결 테스트"""
    print("\n=== 데이터베이스 연결 테스트 ===")

    try:
        from apps.api.database import test_database_connection, init_database

        # 연결 테스트
        print("데이터베이스 연결 확인 중...")
        connection_ok = await test_database_connection()
        print(f"연결 상태: {'성공' if connection_ok else '실패'}")

        if connection_ok:
            # 초기화 테스트
            print("데이터베이스 초기화 확인 중...")
            init_ok = await init_database()
            print(f"초기화 상태: {'성공' if init_ok else '실패'}")

        return connection_ok

    except Exception as e:
        print(f"데이터베이스 테스트 실패: {e}")
        return False

async def main():
    """메인 테스트 함수"""
    print("Document Ingestion Pipeline 테스트 시작")
    print("=" * 50)

    # 데이터베이스 연결 확인
    db_ok = await test_database_connection()

    # 파서 테스트
    await test_document_parsers()

    # 청킹 테스트
    await test_chunking_strategies()

    # PII 필터링 테스트
    await test_pii_filtering()

    # 통합 파이프라인 테스트 (DB 연결시에만)
    if db_ok:
        await test_integrated_pipeline()
    else:
        print("\n데이터베이스 연결이 없어 통합 파이프라인 테스트를 건너뜁니다.")
        print("PostgreSQL 데이터베이스를 설정하고 DATABASE_URL 환경변수를 확인하세요.")

    print("\n" + "=" * 50)
    print("모든 테스트 완료")

if __name__ == "__main__":
    asyncio.run(main())