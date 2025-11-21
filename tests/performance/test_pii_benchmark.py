"""
PII Detection Performance Benchmarks

Tests performance metrics for PII detector:
- Resident registration number detection
- Phone number detection accuracy
- Email pattern detection
- Performance under various text loads

@TEST:PERFORMANCE-001
"""

import pytest
from apps.ingestion.pii.detector import PIIDetector, PIIType


class TestPIIDetectionBenchmark:
    def setup_method(self):
        self.detector = PIIDetector()

    def test_resident_registration_number_true_positives(self):
        valid_samples = [
            "901231-1234567",
            "850615-2876543",
            "700101-1234567",
            "951225-2345678",
        ]

        tp = 0
        fp = 0

        for sample in valid_samples:
            text = f"주민번호: {sample}"
            matches = self.detector.detect_pii(text)

            rrn_matches = [
                m for m in matches if m.pii_type == PIIType.RESIDENT_REGISTRATION_NUMBER
            ]

            if len(rrn_matches) > 0:
                tp += 1
            else:
                fp += 1

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0

        print(f"\nResident Registration Number (Valid):")
        print(f"  TP: {tp}, FP: {fp}")
        print(f"  Precision: {precision * 100:.2f}%")
        print(f"  Target: >99%")
        print(f"  Status: {'PASS' if precision > 0.99 else 'FAIL'}")

        assert precision > 0.99, f"Precision {precision * 100:.2f}% below target 99%"

    def test_resident_registration_number_false_positive_prevention(self):
        invalid_samples = [
            "991331-1234567",
            "900001-1234567",
            "901232-1234567",
            "901231-5234567",
        ]

        fp = 0
        tn = 0

        for sample in invalid_samples:
            text = f"번호: {sample}"
            matches = self.detector.detect_pii(text)

            rrn_matches = [
                m for m in matches if m.pii_type == PIIType.RESIDENT_REGISTRATION_NUMBER
            ]

            if len(rrn_matches) > 0:
                fp += 1
            else:
                tn += 1

        fp_rate = fp / (tn + fp) if (tn + fp) > 0 else 0.0
        status = "PASS" if fp_rate < 0.01 else "FAIL"

        print(f"\nResident Registration Number (Invalid - False Positive Prevention):")
        print(f"  TN: {tn}, FP: {fp}")
        print(f"  FP Rate: {fp_rate * 100:.2f}%")
        print(f"  Target FP Rate: <1%")
        print(f"  Status: {status}")

        assert fp == 0, f"False positives detected: {fp}"

    def test_phone_number_true_positives(self):
        valid_samples = [
            "010-1234-5678",
            "010-9876-5432",
            "031-456-7890",
            "051-123-4567",
        ]

        tp = 0
        fp = 0

        for sample in valid_samples:
            text = f"연락처: {sample}"
            matches = self.detector.detect_pii(text)

            phone_matches = [m for m in matches if m.pii_type == PIIType.PHONE_NUMBER]

            if len(phone_matches) > 0:
                tp += 1
            else:
                fp += 1

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0

        print(f"\nPhone Number:")
        print(f"  TP: {tp}, FP: {fp}")
        print(f"  Precision: {precision * 100:.2f}%")
        print(f"  Target: >99%")
        print(f"  Status: {'PASS' if precision > 0.99 else 'FAIL'}")

        assert precision > 0.99, f"Precision {precision * 100:.2f}% below target 99%"

    def test_email_true_positives(self):
        valid_samples = [
            "test@example.com",
            "user.name@domain.co.kr",
            "admin@company.org",
            "support@service.net",
        ]

        tp = 0
        fp = 0

        for sample in valid_samples:
            text = f"이메일: {sample}"
            matches = self.detector.detect_pii(text)

            email_matches = [m for m in matches if m.pii_type == PIIType.EMAIL]

            if len(email_matches) > 0:
                tp += 1
            else:
                fp += 1

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0

        print(f"\nEmail:")
        print(f"  TP: {tp}, FP: {fp}")
        print(f"  Precision: {precision * 100:.2f}%")
        print(f"  Target: >99%")
        print(f"  Status: {'PASS' if precision > 0.99 else 'FAIL'}")

        assert precision > 0.99, f"Precision {precision * 100:.2f}% below target 99%"

    def test_credit_card_true_positives(self):
        valid_samples = [
            "4532015112830366",
            "5425233430109903",
            "374245455400126",
        ]

        tp = 0
        fp = 0

        for sample in valid_samples:
            text = f"카드번호: {sample}"
            matches = self.detector.detect_pii(text)

            card_matches = [m for m in matches if m.pii_type == PIIType.CREDIT_CARD]

            if len(card_matches) > 0:
                tp += 1
            else:
                fp += 1

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0

        print(f"\nCredit Card:")
        print(f"  TP: {tp}, FP: {fp}")
        print(f"  Precision: {precision * 100:.2f}%")
        print(f"  Target: >99%")
        print(f"  Status: {'PASS' if precision > 0.99 else 'FAIL'}")

        assert precision > 0.99, f"Precision {precision * 100:.2f}% below target 99%"

    def test_credit_card_false_positive_prevention(self):
        invalid_samples = [
            "1234567812345670",
            "1111222233334444",
            "9999888877776666",
        ]

        fp = 0
        tn = 0

        for sample in invalid_samples:
            text = f"번호: {sample}"
            matches = self.detector.detect_pii(text)

            card_matches = [m for m in matches if m.pii_type == PIIType.CREDIT_CARD]

            if len(card_matches) > 0:
                fp += 1
            else:
                tn += 1

        fp_rate = fp / (tn + fp) if (tn + fp) > 0 else 0.0
        status = "PASS" if fp_rate < 0.01 else "FAIL"

        print(f"\nCredit Card (Invalid - Luhn Check):")
        print(f"  TN: {tn}, FP: {fp}")
        print(f"  FP Rate: {fp_rate * 100:.2f}%")
        print(f"  Target FP Rate: <1%")
        print(f"  Status: {status}")

        assert fp == 0, f"False positives detected: {fp}"

    def test_summary_table(self):
        test_cases = [
            (
                "Resident Number (Valid)",
                [
                    "901231-1234567",
                    "850615-2876543",
                    "700101-1234567",
                    "951225-2345678",
                ],
                PIIType.RESIDENT_REGISTRATION_NUMBER,
            ),
            (
                "Phone Number",
                [
                    "010-1234-5678",
                    "010-9876-5432",
                    "031-456-7890",
                    "051-123-4567",
                ],
                PIIType.PHONE_NUMBER,
            ),
            (
                "Email",
                [
                    "test@example.com",
                    "user.name@domain.co.kr",
                    "admin@company.org",
                    "support@service.net",
                ],
                PIIType.EMAIL,
            ),
            (
                "Credit Card (Valid)",
                [
                    "4532015112830366",
                    "5425233430109903",
                    "374245455400126",
                ],
                PIIType.CREDIT_CARD,
            ),
        ]

        print("\n\n=== PII Detection Precision Summary ===")
        print(
            f"{'PII Type':<25} | {'TP':<5} | {'FP':<5} | {'Precision':<12} | {'Target':<8} | {'Status':<8}"
        )
        print("-" * 85)

        for name, samples, pii_type in test_cases:
            tp = 0
            fp = 0

            for sample in samples:
                text = f"Data: {sample}"
                matches = self.detector.detect_pii(text)

                type_matches = [m for m in matches if m.pii_type == pii_type]

                if len(type_matches) > 0:
                    tp += 1
                else:
                    fp += 1

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            status = "PASS" if precision > 0.99 else "FAIL"

            print(
                f"{name:<25} | {tp:<5} | {fp:<5} | {precision * 100:.2f}%{'':<6} | {'>99%':<8} | {status:<8}"
            )

        print("\n=== False Positive Prevention Tests ===")
        print(
            f"{'Test Case':<30} | {'TN':<5} | {'FP':<5} | {'FP Rate':<10} | {'Status':<8}"
        )
        print("-" * 75)

        fp_tests = [
            (
                "RRN Invalid Dates",
                [
                    "991331-1234567",
                    "900001-1234567",
                    "901232-1234567",
                ],
                PIIType.RESIDENT_REGISTRATION_NUMBER,
            ),
            (
                "Card Invalid Luhn",
                [
                    "1234567812345670",
                    "1111222233334444",
                    "9999888877776666",
                ],
                PIIType.CREDIT_CARD,
            ),
        ]

        for name, samples, pii_type in fp_tests:
            fp = 0
            tn = 0

            for sample in samples:
                text = f"번호: {sample}"
                matches = self.detector.detect_pii(text)

                type_matches = [m for m in matches if m.pii_type == pii_type]

                if len(type_matches) > 0:
                    fp += 1
                else:
                    tn += 1

            fp_rate = fp / (tn + fp) if (tn + fp) > 0 else 0.0
            status = "PASS" if fp_rate < 0.01 else "FAIL"

            print(
                f"{name:<30} | {tn:<5} | {fp:<5} | {fp_rate * 100:.2f}%{'':<4} | {status:<8}"
            )
