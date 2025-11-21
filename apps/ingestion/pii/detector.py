"""
PII detection and masking utilities.

@CODE:INGESTION-001
"""
import re
from typing import List, Tuple, Dict
from dataclasses import dataclass
from enum import Enum


class PIIType(str, Enum):
    RESIDENT_REGISTRATION_NUMBER = "resident_registration_number"
    PHONE_NUMBER = "phone_number"
    EMAIL = "email"
    CREDIT_CARD = "credit_card"
    BANK_ACCOUNT = "bank_account"


@dataclass
class PIIMatch:
    pii_type: PIIType
    original_text: str
    start_position: int
    end_position: int
    confidence: float


class PIIDetector:
    PATTERNS = {
        PIIType.RESIDENT_REGISTRATION_NUMBER: [
            r"\b\d{6}[-\s]?[1-4]\d{6}\b",
            r"\b\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])[-\s]?[1-4]\d{6}\b",
        ],
        PIIType.PHONE_NUMBER: [
            r"\b0(?:1[0-9]|2[0-9]|3[0-9]|4[0-9]|5[0-9]|6[0-9]|7[0-9])[-\s]?\d{3,4}[-\s]?\d{4}\b",
            r"\b(?:\+82|82)[-\s]?(?:1[0-9]|2[0-9]|3[0-9]|4[0-9]|5[0-9]|6[0-9]|7[0-9])[-\s]?\d{3,4}[-\s]?\d{4}\b",
        ],
        PIIType.EMAIL: [
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        ],
        PIIType.CREDIT_CARD: [
            r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|6(?:011|5[0-9]{2})[0-9]{12}|(?:2131|1800|35\d{3})\d{11})\b",
        ],
        PIIType.BANK_ACCOUNT: [
            r"\b\d{3,4}[-\s]?\d{2,6}[-\s]?\d{4,8}\b",
        ],
    }

    MASK_LABELS = {
        PIIType.RESIDENT_REGISTRATION_NUMBER: "[주민번호]",
        PIIType.PHONE_NUMBER: "[전화번호]",
        PIIType.EMAIL: "[이메일]",
        PIIType.CREDIT_CARD: "[카드번호]",
        PIIType.BANK_ACCOUNT: "[계좌번호]",
    }

    # @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
    def __init__(self) -> None:
        self.compiled_patterns: Dict[PIIType, List[re.Pattern]] = {}
        for pii_type, patterns in self.PATTERNS.items():
            self.compiled_patterns[pii_type] = [
                re.compile(pattern) for pattern in patterns
            ]

    def validate_resident_registration_number(self, rrn: str) -> bool:
        rrn_clean = re.sub(r"[-\s]", "", rrn)

        if len(rrn_clean) != 13:
            return False

        if not rrn_clean.isdigit():
            return False

        birth_part = rrn_clean[:6]
        gender_digit = int(rrn_clean[6])

        try:
            month = int(birth_part[2:4])
            day = int(birth_part[4:6])

            if month < 1 or month > 12:
                return False
            if day < 1 or day > 31:
                return False
            if gender_digit not in [1, 2, 3, 4]:
                return False

            return True
        except ValueError:
            return False

    def validate_luhn(self, card_number: str) -> bool:
        card_clean = re.sub(r"[-\s]", "", card_number)

        if not card_clean.isdigit():
            return False

        digits = [int(d) for d in card_clean]
        checksum = 0

        for i in range(len(digits) - 2, -1, -2):
            doubled = digits[i] * 2
            checksum += doubled if doubled < 10 else doubled - 9

        for i in range(len(digits) - 1, -1, -2):
            checksum += digits[i]

        return checksum % 10 == 0

    def detect_pii(self, text: str) -> List[PIIMatch]:
        matches: List[PIIMatch] = []
        matched_ranges: set[Tuple[int, int]] = set()

        priority_order = [
            PIIType.RESIDENT_REGISTRATION_NUMBER,
            PIIType.CREDIT_CARD,
            PIIType.PHONE_NUMBER,
            PIIType.EMAIL,
            PIIType.BANK_ACCOUNT,
        ]

        for pii_type in priority_order:
            compiled_patterns = self.compiled_patterns.get(pii_type, [])
            for pattern in compiled_patterns:
                for match in pattern.finditer(text):
                    original_text = match.group(0)
                    start_pos = match.start()
                    end_pos = match.end()

                    if any(
                        start_pos < r_end and end_pos > r_start
                        for r_start, r_end in matched_ranges
                    ):
                        continue

                    confidence = 1.0

                    if pii_type == PIIType.RESIDENT_REGISTRATION_NUMBER:
                        if not self.validate_resident_registration_number(
                            original_text
                        ):
                            continue
                    elif pii_type == PIIType.CREDIT_CARD:
                        if not self.validate_luhn(original_text):
                            continue

                    matches.append(
                        PIIMatch(
                            pii_type=pii_type,
                            original_text=original_text,
                            start_position=start_pos,
                            end_position=end_pos,
                            confidence=confidence,
                        )
                    )
                    matched_ranges.add((start_pos, end_pos))

        matches.sort(key=lambda m: m.start_position)

        return matches

    def mask_pii(self, text: str, matches: List[PIIMatch]) -> str:
        if not matches:
            return text

        masked_text = text
        offset = 0

        for match in matches:
            mask_label = self.MASK_LABELS[match.pii_type]

            start = match.start_position + offset
            end = match.end_position + offset

            masked_text = masked_text[:start] + mask_label + masked_text[end:]

            offset += len(mask_label) - (match.end_position - match.start_position)

        return masked_text

    def detect_and_mask(self, text: str) -> Tuple[str, List[PIIMatch]]:
        matches = self.detect_pii(text)
        masked_text = self.mask_pii(text, matches)
        return masked_text, matches

    def has_pii(self, text: str) -> bool:
        return len(self.detect_pii(text)) > 0

    def get_pii_types(self, text: str) -> List[str]:
        matches = self.detect_pii(text)
        pii_types = list(set([match.pii_type.value for match in matches]))
        return pii_types
