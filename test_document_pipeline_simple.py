#!/usr/bin/env python3
"""
간소화된 문서 수집 파이프라인 테스트 스크립트

이 스크립트는 문서 수집 파이프라인의 핵심 기능을 테스트합니다:
1. 기본 파일 포맷 지원 (TXT, MD, HTML, CSV, JSON)
2. 텍스트 추출 및 기본 청킹
3. PII 기본 탐지
4. 성능 메트릭 수집
"""

import os
import sys
import json
import time
import tempfile
import shutil
from pathlib import Path
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import traceback

# 기본 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleDocumentTester:
    """간소화된 문서 테스터"""

    def __init__(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="simple_test_"))
        self.results = {}
        self.start_time = time.time()

        logger.info(f"테스트 디렉토리: {self.temp_dir}")

    def __del__(self):
        if hasattr(self, 'temp_dir') and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_test_files(self) -> Dict[str, Path]:
        """테스트 파일 생성"""
        logger.info("테스트 파일 생성 중...")
        files = {}

        # 1. 한글 텍스트 파일
        txt_content = """
안녕하세요! 이것은 한글 테스트 파일입니다.

개인정보 테스트:
- 이메일: test@example.com
- 전화번호: 010-1234-5678
- 주민등록번호: 123456-1234567

기술 문서:
Dynamic Taxonomy RAG 시스템은 문서 분류와 검색을 제공합니다.
이 시스템은 자동으로 문서를 분류하고 검색할 수 있습니다.

Lorem ipsum dolor sit amet, consectetur adipiscing elit.
Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        """.strip()

        txt_file = self.temp_dir / "test_korean.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(txt_content)
        files['txt'] = txt_file

        # 2. Markdown 파일
        md_content = """
# 한글 마크다운 문서

## 개요
이것은 **마크다운** 테스트 파일입니다.

### 개인정보
- 사용자: 김철수
- 이메일: kim@company.com
- 연락처: 02-123-4567

### 코드 예시
```python
def process_text(text):
    return text.strip()
```

> 인용문 예시입니다.
        """.strip()

        md_file = self.temp_dir / "test_korean.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(md_content)
        files['md'] = md_file

        # 3. HTML 파일
        html_content = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>한글 HTML 테스트</title>
</head>
<body>
    <h1>한글 HTML 문서</h1>
    <p>이것은 HTML 테스트 파일입니다.</p>

    <h2>개인정보</h2>
    <ul>
        <li>이름: 박영희</li>
        <li>이메일: park@test.com</li>
        <li>전화: 010-9876-5432</li>
    </ul>

    <script>
        console.log("스크립트는 제거됩니다");
    </script>
</body>
</html>
        """.strip()

        html_file = self.temp_dir / "test_korean.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        files['html'] = html_file

        # 4. CSV 파일
        csv_content = """이름,이메일,전화번호,부서
김민수,kim@company.com,010-1111-2222,개발팀
이영희,lee@company.com,010-3333-4444,마케팅팀
박철수,park@company.com,010-5555-6666,영업팀"""

        csv_file = self.temp_dir / "test_korean.csv"
        with open(csv_file, 'w', encoding='utf-8') as f:
            f.write(csv_content)
        files['csv'] = csv_file

        # 5. JSON 파일
        json_data = {
            "title": "한글 JSON 문서",
            "description": "JSON 포맷 테스트",
            "users": [
                {
                    "name": "홍길동",
                    "email": "hong@example.org",
                    "phone": "010-1234-0000"
                }
            ],
            "content": {
                "korean": "한글 콘텐츠입니다.",
                "english": "This is English content."
            }
        }

        json_file = self.temp_dir / "test_korean.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        files['json'] = json_file

        # 6. 빈 파일
        empty_file = self.temp_dir / "empty.txt"
        empty_file.touch()
        files['empty'] = empty_file

        # 7. 대용량 파일
        large_content = "한글 대용량 테스트 콘텐츠. " * 5000
        large_file = self.temp_dir / "large_test.txt"
        with open(large_file, 'w', encoding='utf-8') as f:
            f.write(large_content)
        files['large'] = large_file

        logger.info(f"총 {len(files)}개 테스트 파일 생성 완료")
        return files

    def test_basic_file_reading(self, files: Dict[str, Path]) -> Dict[str, Any]:
        """기본 파일 읽기 테스트"""
        logger.info("=== 기본 파일 읽기 테스트 ===")
        results = {}

        for fmt, file_path in files.items():
            start_time = time.time()

            try:
                if fmt == 'empty':
                    # 빈 파일 처리
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    results[fmt] = {
                        'success': True,
                        'length': len(content),
                        'is_empty': len(content) == 0,
                        'processing_time': time.time() - start_time
                    }
                else:
                    # 일반 파일 처리
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    results[fmt] = {
                        'success': True,
                        'length': len(content),
                        'has_korean': any(ord(c) > 127 for c in content[:100]),
                        'line_count': content.count('\n') + 1,
                        'processing_time': time.time() - start_time
                    }

                logger.info(f"{fmt}: {len(content)} 문자 읽기 성공")

            except Exception as e:
                results[fmt] = {
                    'success': False,
                    'error': str(e),
                    'processing_time': time.time() - start_time
                }
                logger.error(f"{fmt} 읽기 실패: {e}")

        return results

    def test_simple_chunking(self, files: Dict[str, Path]) -> Dict[str, Any]:
        """간단한 청킹 테스트"""
        logger.info("=== 간단한 청킹 테스트 ===")
        results = {}

        def simple_chunk(text: str, max_size: int = 500) -> List[str]:
            """간단한 청킹 함수"""
            if not text or len(text) <= max_size:
                return [text] if text else []

            chunks = []
            current_pos = 0

            while current_pos < len(text):
                end_pos = min(current_pos + max_size, len(text))

                # 단어 경계에서 자르기 시도
                if end_pos < len(text):
                    space_pos = text.rfind(' ', current_pos, end_pos)
                    if space_pos > current_pos:
                        end_pos = space_pos

                chunk = text[current_pos:end_pos].strip()
                if chunk:
                    chunks.append(chunk)

                current_pos = end_pos + 1

            return chunks

        for fmt, file_path in files.items():
            if fmt == 'empty':
                continue

            start_time = time.time()

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                chunks = simple_chunk(content)
                processing_time = time.time() - start_time

                results[fmt] = {
                    'success': True,
                    'original_length': len(content),
                    'chunk_count': len(chunks),
                    'chunk_sizes': [len(chunk) for chunk in chunks],
                    'avg_chunk_size': sum(len(chunk) for chunk in chunks) / len(chunks) if chunks else 0,
                    'processing_time': processing_time
                }

                logger.info(f"{fmt}: {len(chunks)}개 청크 생성")

            except Exception as e:
                results[fmt] = {
                    'success': False,
                    'error': str(e),
                    'processing_time': time.time() - start_time
                }
                logger.error(f"{fmt} 청킹 실패: {e}")

        return results

    def test_simple_pii_detection(self, files: Dict[str, Path]) -> Dict[str, Any]:
        """간단한 PII 탐지 테스트"""
        logger.info("=== 간단한 PII 탐지 테스트 ===")
        results = {}

        import re

        # 간단한 PII 패턴
        pii_patterns = {
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'phone': re.compile(r'\b(?:\d{2,3}-\d{3,4}-\d{4}|\d{10,11})\b'),
            'ssn': re.compile(r'\b\d{6}-[1-4]\d{6}\b'),  # 한국 주민등록번호
            'credit_card': re.compile(r'\b\d{4}-\d{4}-\d{4}-\d{4}\b')
        }

        for fmt, file_path in files.items():
            if fmt == 'empty':
                continue

            start_time = time.time()

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                detections = {}
                for pii_type, pattern in pii_patterns.items():
                    matches = pattern.findall(content)
                    detections[pii_type] = {
                        'count': len(matches),
                        'matches': matches
                    }

                total_detections = sum(d['count'] for d in detections.values())
                processing_time = time.time() - start_time

                results[fmt] = {
                    'success': True,
                    'total_detections': total_detections,
                    'detections_by_type': detections,
                    'processing_time': processing_time
                }

                logger.info(f"{fmt}: {total_detections}개 PII 탐지")

            except Exception as e:
                results[fmt] = {
                    'success': False,
                    'error': str(e),
                    'processing_time': time.time() - start_time
                }
                logger.error(f"{fmt} PII 탐지 실패: {e}")

        return results

    def test_html_parsing(self, files: Dict[str, Path]) -> Dict[str, Any]:
        """HTML 파싱 테스트 (BeautifulSoup 사용)"""
        logger.info("=== HTML 파싱 테스트 ===")
        results = {}

        try:
            from bs4 import BeautifulSoup

            html_file = files.get('html')
            if not html_file:
                return {'error': 'HTML 파일이 없습니다'}

            start_time = time.time()

            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()

            soup = BeautifulSoup(html_content, 'html.parser')

            # 스크립트와 스타일 제거
            for script in soup(["script", "style"]):
                script.decompose()

            # 텍스트 추출
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            clean_text = ' '.join(chunk for chunk in chunks if chunk)

            processing_time = time.time() - start_time

            results['html_parsing'] = {
                'success': True,
                'original_html_length': len(html_content),
                'extracted_text_length': len(clean_text),
                'title': soup.title.string if soup.title else None,
                'has_korean': any(ord(c) > 127 for c in clean_text[:100]),
                'processing_time': processing_time
            }

            logger.info(f"HTML 파싱 성공: {len(clean_text)} 문자 추출")

        except ImportError:
            results['html_parsing'] = {
                'success': False,
                'error': 'BeautifulSoup이 설치되지 않음'
            }
            logger.warning("BeautifulSoup이 설치되지 않아 HTML 파싱을 건너뜁니다")
        except Exception as e:
            results['html_parsing'] = {
                'success': False,
                'error': str(e),
                'processing_time': time.time() - start_time if 'start_time' in locals() else 0
            }
            logger.error(f"HTML 파싱 실패: {e}")

        return results

    def test_json_parsing(self, files: Dict[str, Path]) -> Dict[str, Any]:
        """JSON 파싱 테스트"""
        logger.info("=== JSON 파싱 테스트 ===")
        results = {}

        json_file = files.get('json')
        if not json_file:
            return {'error': 'JSON 파일이 없습니다'}

        start_time = time.time()

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # JSON 데이터를 텍스트로 변환
            def extract_text_from_json(obj, texts=None):
                if texts is None:
                    texts = []

                if isinstance(obj, dict):
                    for value in obj.values():
                        extract_text_from_json(value, texts)
                elif isinstance(obj, list):
                    for item in obj:
                        extract_text_from_json(item, texts)
                elif isinstance(obj, str):
                    texts.append(obj)

                return texts

            extracted_texts = extract_text_from_json(data)
            combined_text = ' '.join(extracted_texts)

            processing_time = time.time() - start_time

            results['json_parsing'] = {
                'success': True,
                'keys_count': len(data) if isinstance(data, dict) else 0,
                'extracted_texts_count': len(extracted_texts),
                'combined_text_length': len(combined_text),
                'has_korean': any(ord(c) > 127 for c in combined_text[:100]),
                'processing_time': processing_time
            }

            logger.info(f"JSON 파싱 성공: {len(extracted_texts)}개 텍스트 추출")

        except Exception as e:
            results['json_parsing'] = {
                'success': False,
                'error': str(e),
                'processing_time': time.time() - start_time
            }
            logger.error(f"JSON 파싱 실패: {e}")

        return results

    def test_performance_benchmark(self, files: Dict[str, Path]) -> Dict[str, Any]:
        """성능 벤치마크 테스트"""
        logger.info("=== 성능 벤치마크 테스트 ===")
        results = {}

        # 대용량 파일 성능 테스트
        large_file = files.get('large')
        if large_file:
            start_time = time.time()

            try:
                with open(large_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                read_time = time.time() - start_time

                # 처리 시간 측정
                process_start = time.time()

                # 간단한 처리 (단어 수 계산)
                word_count = len(content.split())
                char_count = len(content)
                line_count = content.count('\n')

                process_time = time.time() - process_start
                total_time = time.time() - start_time

                results['large_file_performance'] = {
                    'success': True,
                    'file_size_chars': char_count,
                    'word_count': word_count,
                    'line_count': line_count,
                    'read_time': read_time,
                    'process_time': process_time,
                    'total_time': total_time,
                    'chars_per_second': char_count / total_time if total_time > 0 else 0
                }

                logger.info(f"대용량 파일 처리: {char_count:,} 문자, {total_time:.3f}초")

            except Exception as e:
                results['large_file_performance'] = {
                    'success': False,
                    'error': str(e)
                }
                logger.error(f"대용량 파일 처리 실패: {e}")

        # 모든 파일 배치 처리 성능
        start_time = time.time()

        try:
            total_chars = 0
            total_files = 0

            for fmt, file_path in files.items():
                if fmt in ['empty', 'large']:
                    continue

                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    total_chars += len(content)
                    total_files += 1
                except:
                    continue

            batch_time = time.time() - start_time

            results['batch_performance'] = {
                'success': True,
                'total_files': total_files,
                'total_chars': total_chars,
                'batch_time': batch_time,
                'files_per_second': total_files / batch_time if batch_time > 0 else 0,
                'chars_per_second': total_chars / batch_time if batch_time > 0 else 0
            }

            logger.info(f"배치 처리: {total_files}개 파일, {total_chars:,} 문자, {batch_time:.3f}초")

        except Exception as e:
            results['batch_performance'] = {
                'success': False,
                'error': str(e)
            }
            logger.error(f"배치 처리 실패: {e}")

        return results

    def generate_summary_report(self) -> Dict[str, Any]:
        """요약 보고서 생성"""
        total_time = time.time() - self.start_time

        # 성공률 계산
        total_tests = 0
        successful_tests = 0

        for test_name, test_results in self.results.items():
            if isinstance(test_results, dict):
                for sub_test, result in test_results.items():
                    if isinstance(result, dict) and 'success' in result:
                        total_tests += 1
                        if result['success']:
                            successful_tests += 1

        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0

        return {
            'summary': {
                'total_test_time': total_time,
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'failed_tests': total_tests - successful_tests,
                'success_rate': success_rate
            },
            'detailed_results': self.results,
            'recommendations': self._generate_recommendations()
        }

    def _generate_recommendations(self) -> List[str]:
        """권장사항 생성"""
        recommendations = []

        # 기본 파일 읽기 결과 분석
        file_reading = self.results.get('basic_file_reading', {})
        failed_formats = [fmt for fmt, result in file_reading.items()
                         if isinstance(result, dict) and not result.get('success', True)]

        if failed_formats:
            recommendations.append(f"파일 읽기 실패 형식: {', '.join(failed_formats)}. 인코딩 또는 파서 문제를 확인하세요.")

        # PII 탐지 결과 분석
        pii_detection = self.results.get('simple_pii_detection', {})
        total_pii = sum(result.get('total_detections', 0) for result in pii_detection.values()
                       if isinstance(result, dict))

        if total_pii == 0:
            recommendations.append("PII가 탐지되지 않았습니다. PII 패턴이 올바른지 확인하세요.")
        elif total_pii > 50:
            recommendations.append(f"많은 PII가 탐지되었습니다 ({total_pii}개). 마스킹 전략을 검토하세요.")

        # 성능 분석
        performance = self.results.get('performance_benchmark', {})
        if 'large_file_performance' in performance:
            perf = performance['large_file_performance']
            if perf.get('success') and perf.get('chars_per_second', 0) < 10000:
                recommendations.append("대용량 파일 처리 속도가 느립니다. 스트리밍 처리를 고려하세요.")

        if not recommendations:
            recommendations.append("모든 테스트가 성공적으로 완료되었습니다.")

        return recommendations

    def run_all_tests(self) -> Dict[str, Any]:
        """모든 테스트 실행"""
        logger.info("🚀 간소화된 문서 파이프라인 테스트 시작")

        try:
            # 1. 테스트 파일 생성
            test_files = self.create_test_files()

            # 2. 기본 파일 읽기 테스트
            self.results['basic_file_reading'] = self.test_basic_file_reading(test_files)

            # 3. 청킹 테스트
            self.results['simple_chunking'] = self.test_simple_chunking(test_files)

            # 4. PII 탐지 테스트
            self.results['simple_pii_detection'] = self.test_simple_pii_detection(test_files)

            # 5. HTML 파싱 테스트
            self.results['html_parsing'] = self.test_html_parsing(test_files)

            # 6. JSON 파싱 테스트
            self.results['json_parsing'] = self.test_json_parsing(test_files)

            # 7. 성능 벤치마크
            self.results['performance_benchmark'] = self.test_performance_benchmark(test_files)

            logger.info("✅ 모든 테스트 완료")

        except Exception as e:
            logger.error(f"테스트 실행 중 오류: {e}")
            self.results['fatal_error'] = {
                'error': str(e),
                'traceback': traceback.format_exc()
            }

        return self.generate_summary_report()

def main():
    """메인 함수"""
    print("📋 간소화된 문서 수집 파이프라인 테스트")
    print("=" * 50)

    tester = SimpleDocumentTester()

    try:
        # 테스트 실행
        report = tester.run_all_tests()

        # 결과 저장
        report_file = Path("simple_pipeline_test_report.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        # 결과 출력
        print("\n📊 테스트 결과 요약")
        print("-" * 30)

        summary = report['summary']
        print(f"🕐 총 테스트 시간: {summary['total_test_time']:.2f}초")
        print(f"📝 총 테스트 수: {summary['total_tests']}개")
        print(f"✅ 성공: {summary['successful_tests']}개")
        print(f"❌ 실패: {summary['failed_tests']}개")
        print(f"📈 성공률: {summary['success_rate']:.1f}%")

        if report['recommendations']:
            print("\n💡 권장사항:")
            for i, rec in enumerate(report['recommendations'], 1):
                print(f"{i}. {rec}")

        print(f"\n📋 상세 보고서: {report_file.absolute()}")

        # 성공 여부 반환
        if summary['success_rate'] >= 80:
            print("\n🎉 테스트 성공!")
            return 0
        else:
            print("\n⚠️ 일부 테스트 실패")
            return 1

    except Exception as e:
        print(f"\n💥 테스트 실행 실패: {e}")
        return 2

    finally:
        # 정리
        if hasattr(tester, 'temp_dir') and tester.temp_dir.exists():
            shutil.rmtree(tester.temp_dir, ignore_errors=True)

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)