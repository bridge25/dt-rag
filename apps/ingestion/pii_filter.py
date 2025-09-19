"""
PII Filter Module

개인정보 탐지 및 필터링 모듈
- 이메일 주소 탐지/마스킹
- 전화번호 탐지/마스킹 (한국/국제)
- 주민등록번호 탐지/마스킹
- 신용카드 번호 탐지/마스킹
- 주소 정보 탐지/마스킹
- 커스텀 PII 패턴 지원
- GDPR/CCPA/PIPA 규정 준수
"""

import re
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Any, Optional, Union, Callable
from dataclasses import dataclass
from enum import Enum
import hashlib
import secrets
from datetime import datetime

logger = logging.getLogger(__name__)

class PIIType(Enum):
    """PII 타입 열거형"""
    EMAIL = "email"
    PHONE = "phone"
    SSN_KR = "ssn_kr"  # 주민등록번호
    SSN_US = "ssn_us"  # 미국 SSN
    CREDIT_CARD = "credit_card"
    ADDRESS = "address"
    NAME = "name"
    CUSTOM = "custom"

class MaskingStrategy(Enum):
    """마스킹 전략 열거형"""
    REDACT = "redact"  # 완전 제거
    MASK = "mask"      # *** 로 마스킹
    PARTIAL = "partial"  # 부분 마스킹 (예: 12*-***-****)
    HASH = "hash"      # 해시값으로 대체
    TOKENIZE = "tokenize"  # 토큰으로 대체
    PRESERVE_FORMAT = "preserve_format"  # 형식 보존하며 마스킹

@dataclass
class PIIMatch:
    """PII 탐지 결과"""
    pii_type: PIIType
    text: str
    start: int
    end: int
    confidence: float
    metadata: Dict[str, Any]

@dataclass
class PIIFilterResult:
    """PII 필터링 결과"""
    filtered_text: str
    detected_pii: List[PIIMatch]
    masking_applied: Dict[PIIType, int]
    processing_time: float
    compliance_flags: Dict[str, bool]

class PIIDetector(ABC):
    """PII 탐지기 추상 기본 클래스"""

    @abstractmethod
    def detect(self, text: str) -> List[PIIMatch]:
        """PII 탐지"""
        pass

    @abstractmethod
    def get_pii_type(self) -> PIIType:
        """지원하는 PII 타입 반환"""
        pass

class EmailDetector(PIIDetector):
    """이메일 주소 탐지기"""

    def __init__(self, confidence_threshold: float = 0.9):
        self.confidence_threshold = confidence_threshold
        # 강화된 이메일 정규식
        self.email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            re.IGNORECASE
        )

    def detect(self, text: str) -> List[PIIMatch]:
        matches = []
        for match in self.email_pattern.finditer(text):
            email = match.group()
            confidence = self._calculate_email_confidence(email)

            if confidence >= self.confidence_threshold:
                pii_match = PIIMatch(
                    pii_type=PIIType.EMAIL,
                    text=email,
                    start=match.start(),
                    end=match.end(),
                    confidence=confidence,
                    metadata={
                        'domain': email.split('@')[1],
                        'local_part': email.split('@')[0]
                    }
                )
                matches.append(pii_match)

        return matches

    def _calculate_email_confidence(self, email: str) -> float:
        """이메일 신뢰도 계산"""
        confidence = 0.8  # 기본 신뢰도

        # 도메인 유효성 검사
        if '@' not in email:
            return 0.0

        domain = email.split('@')[1]

        # 일반적인 도메인 확장자
        common_tlds = ['.com', '.org', '.net', '.edu', '.gov', '.co.kr', '.kr']
        if any(domain.endswith(tld) for tld in common_tlds):
            confidence += 0.1

        # 도메인 길이 검사
        if 3 <= len(domain.split('.')[0]) <= 20:
            confidence += 0.1

        return min(1.0, confidence)

    def get_pii_type(self) -> PIIType:
        return PIIType.EMAIL

class PhoneDetector(PIIDetector):
    """전화번호 탐지기 (한국/국제)"""

    def __init__(self, include_international: bool = True):
        self.include_international = include_international

        # 한국 전화번호 패턴
        self.kr_patterns = [
            re.compile(r'\b010[-\s]?\d{4}[-\s]?\d{4}\b'),  # 휴대폰
            re.compile(r'\b01[1|6|7|8|9][-\s]?\d{3,4}[-\s]?\d{4}\b'),  # 기타 휴대폰
            re.compile(r'\b0\d{1,2}[-\s]?\d{3,4}[-\s]?\d{4}\b'),  # 지역번호
            re.compile(r'\b\d{3}[-\s]?\d{4}[-\s]?\d{4}\b'),  # 일반 형식
        ]

        # 국제 전화번호 패턴
        self.intl_patterns = [
            re.compile(r'\+\d{1,3}[-\s]?\d{1,4}[-\s]?\d{1,4}[-\s]?\d{1,9}'),
            re.compile(r'\b\d{3}[-\s]?\d{3}[-\s]?\d{4}\b'),  # 미국 형식
        ]

    def detect(self, text: str) -> List[PIIMatch]:
        matches = []

        # 한국 전화번호 탐지
        for pattern in self.kr_patterns:
            for match in pattern.finditer(text):
                phone = match.group()
                if self._is_valid_korean_phone(phone):
                    pii_match = PIIMatch(
                        pii_type=PIIType.PHONE,
                        text=phone,
                        start=match.start(),
                        end=match.end(),
                        confidence=0.95,
                        metadata={'country': 'KR', 'type': 'korean'}
                    )
                    matches.append(pii_match)

        # 국제 전화번호 탐지
        if self.include_international:
            for pattern in self.intl_patterns:
                for match in pattern.finditer(text):
                    phone = match.group()
                    if self._is_valid_international_phone(phone):
                        pii_match = PIIMatch(
                            pii_type=PIIType.PHONE,
                            text=phone,
                            start=match.start(),
                            end=match.end(),
                            confidence=0.8,
                            metadata={'country': 'INTL', 'type': 'international'}
                        )
                        matches.append(pii_match)

        return self._remove_overlapping_matches(matches)

    def _is_valid_korean_phone(self, phone: str) -> bool:
        """한국 전화번호 유효성 검사"""
        digits = re.sub(r'[^\d]', '', phone)

        # 길이 검사
        if len(digits) < 10 or len(digits) > 11:
            return False

        # 휴대폰 번호 검사
        if digits.startswith('010') and len(digits) == 11:
            return True

        # 지역번호 검사
        if digits.startswith('0') and len(digits) in [10, 11]:
            return True

        return False

    def _is_valid_international_phone(self, phone: str) -> bool:
        """국제 전화번호 유효성 검사"""
        digits = re.sub(r'[^\d]', '', phone)

        # 기본 길이 검사
        if len(digits) < 10 or len(digits) > 15:
            return False

        # 너무 단순한 패턴 제외
        if len(set(digits)) < 3:
            return False

        return True

    def _remove_overlapping_matches(self, matches: List[PIIMatch]) -> List[PIIMatch]:
        """중복 매치 제거"""
        if not matches:
            return matches

        # 시작 위치로 정렬
        sorted_matches = sorted(matches, key=lambda x: x.start)
        filtered = []

        for match in sorted_matches:
            # 기존 매치와 겹치는지 확인
            overlapping = False
            for existing in filtered:
                if (match.start < existing.end and match.end > existing.start):
                    # 더 높은 신뢰도를 가진 매치 유지
                    if match.confidence > existing.confidence:
                        filtered.remove(existing)
                    else:
                        overlapping = True
                    break

            if not overlapping:
                filtered.append(match)

        return filtered

    def get_pii_type(self) -> PIIType:
        return PIIType.PHONE

class SSNKoreanDetector(PIIDetector):
    """한국 주민등록번호 탐지기"""

    def __init__(self):
        # 주민등록번호 패턴 (6자리-7자리)
        self.ssn_pattern = re.compile(
            r'\b\d{6}[-\s]?\d{7}\b'
        )

    def detect(self, text: str) -> List[PIIMatch]:
        matches = []

        for match in self.ssn_pattern.finditer(text):
            ssn = match.group()
            if self._is_valid_korean_ssn(ssn):
                pii_match = PIIMatch(
                    pii_type=PIIType.SSN_KR,
                    text=ssn,
                    start=match.start(),
                    end=match.end(),
                    confidence=0.98,
                    metadata={
                        'country': 'KR',
                        'type': 'resident_registration'
                    }
                )
                matches.append(pii_match)

        return matches

    def _is_valid_korean_ssn(self, ssn: str) -> bool:
        """한국 주민등록번호 유효성 검사"""
        digits = re.sub(r'[^\d]', '', ssn)

        if len(digits) != 13:
            return False

        # 생년월일 검사
        birth_year = int(digits[:2])
        birth_month = int(digits[2:4])
        birth_day = int(digits[4:6])

        if birth_month < 1 or birth_month > 12:
            return False

        if birth_day < 1 or birth_day > 31:
            return False

        # 성별 코드 검사
        gender_code = int(digits[6])
        if gender_code not in [1, 2, 3, 4, 9, 0]:
            return False

        # 검증 번호 확인 (간소화된 버전)
        weights = [2, 3, 4, 5, 6, 7, 8, 9, 2, 3, 4, 5]
        total = sum(int(digits[i]) * weights[i] for i in range(12))
        check_digit = (11 - (total % 11)) % 10

        return check_digit == int(digits[12])

    def get_pii_type(self) -> PIIType:
        return PIIType.SSN_KR

class CreditCardDetector(PIIDetector):
    """신용카드 번호 탐지기"""

    def __init__(self):
        # 신용카드 번호 패턴 (여러 형식)
        self.cc_patterns = [
            re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'),
            re.compile(r'\b\d{4}[-\s]?\d{6}[-\s]?\d{5}\b'),  # Amex
        ]

    def detect(self, text: str) -> List[PIIMatch]:
        matches = []

        for pattern in self.cc_patterns:
            for match in pattern.finditer(text):
                cc_number = match.group()
                if self._is_valid_credit_card(cc_number):
                    card_type = self._identify_card_type(cc_number)

                    pii_match = PIIMatch(
                        pii_type=PIIType.CREDIT_CARD,
                        text=cc_number,
                        start=match.start(),
                        end=match.end(),
                        confidence=0.95,
                        metadata={
                            'card_type': card_type,
                            'masked_number': self._mask_cc_number(cc_number)
                        }
                    )
                    matches.append(pii_match)

        return matches

    def _is_valid_credit_card(self, cc_number: str) -> bool:
        """Luhn 알고리즘을 사용한 신용카드 번호 검증"""
        digits = re.sub(r'[^\d]', '', cc_number)

        if len(digits) < 13 or len(digits) > 19:
            return False

        # Luhn 알고리즘
        total = 0
        reverse_digits = digits[::-1]

        for i, digit in enumerate(reverse_digits):
            n = int(digit)
            if i % 2 == 1:
                n *= 2
                if n > 9:
                    n = n // 10 + n % 10
            total += n

        return total % 10 == 0

    def _identify_card_type(self, cc_number: str) -> str:
        """신용카드 타입 식별"""
        digits = re.sub(r'[^\d]', '', cc_number)

        if digits.startswith('4'):
            return 'Visa'
        elif digits.startswith(('51', '52', '53', '54', '55')):
            return 'MasterCard'
        elif digits.startswith(('34', '37')):
            return 'American Express'
        elif digits.startswith('6011'):
            return 'Discover'
        else:
            return 'Unknown'

    def _mask_cc_number(self, cc_number: str) -> str:
        """신용카드 번호 마스킹"""
        digits = re.sub(r'[^\d]', '', cc_number)
        if len(digits) >= 4:
            return '**** **** **** ' + digits[-4:]
        return '**** **** **** ****'

    def get_pii_type(self) -> PIIType:
        return PIIType.CREDIT_CARD

class CustomPIIDetector(PIIDetector):
    """커스텀 PII 탐지기"""

    def __init__(self, patterns: Dict[str, str], pii_type_name: str = "custom"):
        self.patterns = {name: re.compile(pattern, re.IGNORECASE)
                        for name, pattern in patterns.items()}
        self.pii_type_name = pii_type_name

    def detect(self, text: str) -> List[PIIMatch]:
        matches = []

        for pattern_name, pattern in self.patterns.items():
            for match in pattern.finditer(text):
                pii_match = PIIMatch(
                    pii_type=PIIType.CUSTOM,
                    text=match.group(),
                    start=match.start(),
                    end=match.end(),
                    confidence=0.9,
                    metadata={
                        'pattern_name': pattern_name,
                        'custom_type': self.pii_type_name
                    }
                )
                matches.append(pii_match)

        return matches

    def get_pii_type(self) -> PIIType:
        return PIIType.CUSTOM

class PIIMasker:
    """PII 마스킹 처리기"""

    def __init__(self):
        self.masking_strategies = {
            MaskingStrategy.REDACT: self._redact,
            MaskingStrategy.MASK: self._mask,
            MaskingStrategy.PARTIAL: self._partial_mask,
            MaskingStrategy.HASH: self._hash,
            MaskingStrategy.TOKENIZE: self._tokenize,
            MaskingStrategy.PRESERVE_FORMAT: self._preserve_format
        }
        self._token_map = {}  # 토큰화를 위한 매핑

    def mask_pii(
        self,
        text: str,
        pii_matches: List[PIIMatch],
        strategy_map: Dict[PIIType, MaskingStrategy]
    ) -> str:
        """PII 마스킹 적용"""
        if not pii_matches:
            return text

        # 위치 역순으로 정렬 (뒤에서부터 교체)
        sorted_matches = sorted(pii_matches, key=lambda x: x.start, reverse=True)

        masked_text = text
        for match in sorted_matches:
            strategy = strategy_map.get(match.pii_type, MaskingStrategy.MASK)
            masking_func = self.masking_strategies[strategy]

            masked_value = masking_func(match.text, match.pii_type, match.metadata)
            masked_text = (
                masked_text[:match.start] +
                masked_value +
                masked_text[match.end:]
            )

        return masked_text

    def _redact(self, text: str, pii_type: PIIType, metadata: Dict) -> str:
        """완전 제거"""
        return f"[{pii_type.value.upper()}_REDACTED]"

    def _mask(self, text: str, pii_type: PIIType, metadata: Dict) -> str:
        """완전 마스킹"""
        return "*" * min(len(text), 8)

    def _partial_mask(self, text: str, pii_type: PIIType, metadata: Dict) -> str:
        """부분 마스킹"""
        if pii_type == PIIType.EMAIL:
            parts = text.split('@')
            if len(parts) == 2:
                local = parts[0]
                domain = parts[1]
                masked_local = local[0] + "*" * (len(local) - 2) + local[-1] if len(local) > 2 else "*"
                return f"{masked_local}@{domain}"

        elif pii_type == PIIType.PHONE:
            digits = re.sub(r'[^\d]', '', text)
            if len(digits) >= 4:
                return text[:3] + "*" * (len(text) - 6) + text[-3:]

        elif pii_type == PIIType.SSN_KR:
            return text[:6] + "-" + "*" * 7

        elif pii_type == PIIType.CREDIT_CARD:
            digits = re.sub(r'[^\d]', '', text)
            if len(digits) >= 4:
                return "**** **** **** " + digits[-4:]

        # 기본 부분 마스킹
        if len(text) <= 4:
            return "*" * len(text)
        else:
            return text[:2] + "*" * (len(text) - 4) + text[-2:]

    def _hash(self, text: str, pii_type: PIIType, metadata: Dict) -> str:
        """해시값으로 대체"""
        hash_value = hashlib.sha256(text.encode()).hexdigest()[:8]
        return f"[{pii_type.value.upper()}_HASH_{hash_value}]"

    def _tokenize(self, text: str, pii_type: PIIType, metadata: Dict) -> str:
        """토큰으로 대체"""
        if text not in self._token_map:
            token = f"{pii_type.value.upper()}_TOKEN_{len(self._token_map) + 1:04d}"
            self._token_map[text] = token

        return f"[{self._token_map[text]}]"

    def _preserve_format(self, text: str, pii_type: PIIType, metadata: Dict) -> str:
        """형식 보존 마스킹"""
        result = ""
        for char in text:
            if char.isdigit():
                result += "*"
            elif char.isalpha():
                result += "X"
            else:
                result += char
        return result

class PIIFilter:
    """통합 PII 필터"""

    def __init__(self, compliance_mode: str = "strict"):
        self.compliance_mode = compliance_mode
        self.detectors: List[PIIDetector] = []
        self.masker = PIIMasker()

        # 기본 탐지기 등록
        self._register_default_detectors()

        # 준수 모드별 기본 전략
        self.default_strategies = self._get_compliance_strategies(compliance_mode)

    def _register_default_detectors(self):
        """기본 PII 탐지기 등록"""
        self.detectors.extend([
            EmailDetector(),
            PhoneDetector(),
            SSNKoreanDetector(),
            CreditCardDetector()
        ])

    def _get_compliance_strategies(self, mode: str) -> Dict[PIIType, MaskingStrategy]:
        """준수 모드별 기본 마스킹 전략"""
        if mode == "strict":  # GDPR/CCPA 엄격 모드
            return {
                PIIType.EMAIL: MaskingStrategy.HASH,
                PIIType.PHONE: MaskingStrategy.REDACT,
                PIIType.SSN_KR: MaskingStrategy.REDACT,
                PIIType.SSN_US: MaskingStrategy.REDACT,
                PIIType.CREDIT_CARD: MaskingStrategy.REDACT,
                PIIType.CUSTOM: MaskingStrategy.HASH
            }
        elif mode == "balanced":  # 균형 모드
            return {
                PIIType.EMAIL: MaskingStrategy.PARTIAL,
                PIIType.PHONE: MaskingStrategy.PARTIAL,
                PIIType.SSN_KR: MaskingStrategy.HASH,
                PIIType.SSN_US: MaskingStrategy.HASH,
                PIIType.CREDIT_CARD: MaskingStrategy.PARTIAL,
                PIIType.CUSTOM: MaskingStrategy.MASK
            }
        else:  # lenient 관대 모드
            return {
                PIIType.EMAIL: MaskingStrategy.MASK,
                PIIType.PHONE: MaskingStrategy.MASK,
                PIIType.SSN_KR: MaskingStrategy.PARTIAL,
                PIIType.SSN_US: MaskingStrategy.PARTIAL,
                PIIType.CREDIT_CARD: MaskingStrategy.MASK,
                PIIType.CUSTOM: MaskingStrategy.MASK
            }

    def add_detector(self, detector: PIIDetector):
        """커스텀 탐지기 추가"""
        self.detectors.append(detector)

    def add_custom_patterns(self, patterns: Dict[str, str], type_name: str = "custom"):
        """커스텀 패턴 추가"""
        custom_detector = CustomPIIDetector(patterns, type_name)
        self.add_detector(custom_detector)

    async def filter_text(
        self,
        text: str,
        custom_strategies: Optional[Dict[PIIType, MaskingStrategy]] = None,
        confidence_threshold: float = 0.8
    ) -> PIIFilterResult:
        """텍스트 PII 필터링"""
        start_time = datetime.utcnow()

        # PII 탐지
        all_matches = []
        for detector in self.detectors:
            try:
                matches = detector.detect(text)
                # 신뢰도 필터링
                filtered_matches = [m for m in matches if m.confidence >= confidence_threshold]
                all_matches.extend(filtered_matches)
            except Exception as e:
                logger.warning(f"PII 탐지 오류 ({detector.__class__.__name__}): {e}")

        # 중복 제거
        unique_matches = self._remove_duplicate_matches(all_matches)

        # 마스킹 전략 결정
        strategies = custom_strategies or self.default_strategies

        # 마스킹 적용
        filtered_text = self.masker.mask_pii(text, unique_matches, strategies)

        # 통계 수집
        masking_stats = {}
        for match in unique_matches:
            pii_type = match.pii_type
            masking_stats[pii_type] = masking_stats.get(pii_type, 0) + 1

        # 처리 시간 계산
        processing_time = (datetime.utcnow() - start_time).total_seconds()

        # 준수 플래그
        compliance_flags = {
            "gdpr_compliant": self._check_gdpr_compliance(unique_matches, strategies),
            "ccpa_compliant": self._check_ccpa_compliance(unique_matches, strategies),
            "pipa_compliant": self._check_pipa_compliance(unique_matches, strategies)
        }

        return PIIFilterResult(
            filtered_text=filtered_text,
            detected_pii=unique_matches,
            masking_applied=masking_stats,
            processing_time=processing_time,
            compliance_flags=compliance_flags
        )

    def _remove_duplicate_matches(self, matches: List[PIIMatch]) -> List[PIIMatch]:
        """중복 매치 제거"""
        if not matches:
            return matches

        # 위치와 텍스트로 중복 제거
        seen = set()
        unique_matches = []

        for match in matches:
            key = (match.start, match.end, match.text)
            if key not in seen:
                seen.add(key)
                unique_matches.append(match)

        return unique_matches

    def _check_gdpr_compliance(
        self,
        matches: List[PIIMatch],
        strategies: Dict[PIIType, MaskingStrategy]
    ) -> bool:
        """GDPR 준수 검사"""
        # GDPR Article 25: 데이터 보호 by design
        sensitive_types = [PIIType.SSN_KR, PIIType.SSN_US, PIIType.CREDIT_CARD]

        for match in matches:
            if match.pii_type in sensitive_types:
                strategy = strategies.get(match.pii_type, MaskingStrategy.MASK)
                if strategy not in [MaskingStrategy.REDACT, MaskingStrategy.HASH]:
                    return False

        return True

    def _check_ccpa_compliance(
        self,
        matches: List[PIIMatch],
        strategies: Dict[PIIType, MaskingStrategy]
    ) -> bool:
        """CCPA 준수 검사"""
        # CCPA 개인정보 범위 확인
        personal_info_types = [PIIType.EMAIL, PIIType.PHONE, PIIType.SSN_US]

        for match in matches:
            if match.pii_type in personal_info_types:
                strategy = strategies.get(match.pii_type, MaskingStrategy.MASK)
                if strategy == MaskingStrategy.PRESERVE_FORMAT:
                    return False

        return True

    def _check_pipa_compliance(
        self,
        matches: List[PIIMatch],
        strategies: Dict[PIIType, MaskingStrategy]
    ) -> bool:
        """한국 개인정보보호법(PIPA) 준수 검사"""
        # 주민등록번호는 반드시 안전하게 처리
        for match in matches:
            if match.pii_type == PIIType.SSN_KR:
                strategy = strategies.get(match.pii_type, MaskingStrategy.MASK)
                if strategy not in [MaskingStrategy.REDACT, MaskingStrategy.HASH]:
                    return False

        return True

    def get_filter_statistics(self) -> Dict[str, Any]:
        """필터 통계 정보"""
        return {
            "registered_detectors": len(self.detectors),
            "detector_types": [d.__class__.__name__ for d in self.detectors],
            "compliance_mode": self.compliance_mode,
            "supported_pii_types": [d.get_pii_type().value for d in self.detectors],
            "masking_strategies": list(MaskingStrategy),
            "compliance_standards": ["GDPR", "CCPA", "PIPA"]
        }

# 기본 PII 필터 인스턴스
default_pii_filter = PIIFilter(compliance_mode="balanced")