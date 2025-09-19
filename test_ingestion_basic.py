#!/usr/bin/env python3
"""
Basic Document Ingestion Test (without database)

데이터베이스 연결 없이 기본 문서 처리 기능 테스트:
- 파서 테스트
- 청킹 테스트
- PII 필터링 테스트
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

    try:
        from apps.ingestion.document_parser import get_parser_factory

        factory = get_parser_factory()

        # 지원되는 확장자 확인
        print(f"지원되는 확장자: {factory.get_supported_extensions()}")

        # 텍스트 파일 테스트
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            test_content = """이것은 테스트 문서입니다.

여러 줄로 구성되어 있으며, 한국어와 English가 혼재되어 있습니다.
PII 테스트를 위해 가짜 이메일 test@example.com을 포함합니다.
전화번호 010-1234-5678도 포함되어 있습니다."""
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
                print(f"  - 파일 크기: {parsed_doc.get_file_size()} bytes")

            except Exception as e:
                print(f"텍스트 파서 테스트 실패: {e}")
            finally:
                os.unlink(f.name)

        # JSON 파일 테스트
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            test_json = '''{
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
}'''
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

    except ImportError as e:
        print(f"파서 모듈 import 실패: {e}")
    except Exception as e:
        print(f"파서 테스트 실패: {e}")

async def test_chunking_strategies():
    """청킹 전략 테스트"""
    print("\n=== 청킹 전략 테스트 ===")

    try:
        from apps.ingestion.chunking_strategy import ChunkingStrategyFactory

        test_text = """인공지능(AI)은 현대 기술의 핵심 분야입니다. 머신러닝과 딥러닝 기술의 발전으로 다양한 응용 분야에서 혁신이 일어나고 있습니다.

RAG(Retrieval-Augmented Generation) 시스템은 정보 검색과 생성을 결합한 새로운 패러다임입니다. 이 시스템은 대용량 문서에서 관련 정보를 찾아 정확하고 신뢰할 수 있는 답변을 생성합니다.

자연어 처리 기술의 발전으로 사람과 기계 간의 상호작용이 더욱 자연스러워지고 있습니다. 분류체계(Taxonomy)를 통해 정보를 체계적으로 구조화할 수 있습니다.

이러한 기술들은 교육, 의료, 금융 등 다양한 분야에서 활용되고 있으며, 앞으로도 지속적인 발전이 예상됩니다."""

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

        # Sliding Window 청킹 테스트
        try:
            sliding_chunker = ChunkingStrategyFactory.create_strategy(
                "sliding_window",
                window_size=150,
                step_size=100
            )

            chunks = await sliding_chunker.chunk_text(test_text)
            print(f"\nSliding Window 청킹 결과: {len(chunks)}개 청크")
            for i, chunk in enumerate(chunks):
                print(f"  청크 {i+1}: {len(chunk.text)}자 (위치: {chunk.start_idx}-{chunk.end_idx})")

        except Exception as e:
            print(f"Sliding Window 청킹 테스트 실패: {e}")

    except ImportError as e:
        print(f"청킹 모듈 import 실패: {e}")
    except Exception as e:
        print(f"청킹 테스트 실패: {e}")

async def test_pii_filtering():
    """PII 필터링 테스트"""
    print("\n=== PII 필터링 테스트 ===")

    try:
        from apps.ingestion.pii_filter import PIIFilter, MaskingStrategy, PIIType

        test_text = """안녕하세요. 제 이름은 김철수이고, 연락처는 다음과 같습니다.

이메일: kim.chulsu@example.com
휴대폰: 010-1234-5678
주민등록번호: 900101-1234567
신용카드: 4532-1234-5678-9012

회사 이메일은 chulsu@company.co.kr이고,
사무실 전화번호는 02-1234-5678입니다.

추가 연락처: jane.doe@gmail.com, john@test.org
국제 전화: +82-10-9876-5432"""

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
            print(result.filtered_text)

        except Exception as e:
            print(f"PII 필터링 테스트 실패: {e}")
            import traceback
            print(traceback.format_exc())

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
            print(result.filtered_text)

        except Exception as e:
            print(f"엄격 모드 테스트 실패: {e}")

    except ImportError as e:
        print(f"PII 필터 모듈 import 실패: {e}")
    except Exception as e:
        print(f"PII 필터 테스트 실패: {e}")

async def test_pipeline_components():
    """파이프라인 컴포넌트 테스트"""
    print("\n=== 파이프라인 컴포넌트 테스트 ===")

    try:
        # 테스트 파일 생성
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            test_content = """RAG 시스템 개발 가이드

1. 문서 처리
- 다양한 포맷 지원: PDF, HTML, TXT, JSON
- 청킹 전략: 토큰 기반, 의미 기반
- PII 필터링: 개인정보 보호

2. 벡터화
- 임베딩 모델 선택
- 벡터 저장소 구축

연락처: support@example.com
전화: 02-123-4567"""
            f.write(test_content)
            f.flush()

            # 단계별 처리 테스트
            print("1. 문서 파싱...")
            from apps.ingestion.document_parser import get_parser_factory
            factory = get_parser_factory()
            parsed_doc = await factory.parse_document(f.name)
            print(f"   파싱 완료: {len(parsed_doc.content)}자")

            print("2. 청킹...")
            from apps.ingestion.chunking_strategy import ChunkingStrategyFactory
            chunker = ChunkingStrategyFactory.create_strategy("token_based", chunk_size=150)
            chunks = await chunker.chunk_text(parsed_doc.content)
            print(f"   청킹 완료: {len(chunks)}개 청크")

            print("3. PII 필터링...")
            from apps.ingestion.pii_filter import PIIFilter
            pii_filter = PIIFilter()
            filtered_chunks = []
            total_pii = 0

            for chunk in chunks:
                result = await pii_filter.filter_text(chunk.text)
                filtered_chunks.append(result)
                total_pii += len(result.detected_pii)

            print(f"   PII 필터링 완료: {total_pii}개 PII 탐지")

            print("\n처리 결과:")
            for i, (chunk, filter_result) in enumerate(zip(chunks, filtered_chunks)):
                print(f"  청크 {i+1}:")
                print(f"    원본: {chunk.text[:50]}...")
                print(f"    필터링: {filter_result.filtered_text[:50]}...")
                print(f"    PII: {len(filter_result.detected_pii)}개")

            # Windows에서 파일 핸들이 열려있어 삭제 건너뜀
            # os.unlink(f.name)

    except Exception as e:
        print(f"파이프라인 컴포넌트 테스트 실패: {e}")
        import traceback
        print(traceback.format_exc())

async def main():
    """메인 테스트 함수"""
    print("Document Ingestion Pipeline 기본 테스트 시작")
    print("=" * 60)

    # 파서 테스트
    await test_document_parsers()

    # 청킹 테스트
    await test_chunking_strategies()

    # PII 필터링 테스트
    await test_pii_filtering()

    # 통합 테스트
    await test_pipeline_components()

    print("\n" + "=" * 60)
    print("모든 기본 테스트 완료")
    print("\n참고: 데이터베이스 연결이 필요한 기능은 별도로 테스트하세요.")

if __name__ == "__main__":
    asyncio.run(main())