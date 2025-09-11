"""
CI/CD 워크플로우의 실패 처리 테스트용 파일

이 파일은 의도적으로 테스트를 실패시켜서 AI 프롬프트 생성 기능을 테스트합니다.
"""

def test_that_always_fails():
    """이 테스트는 의도적으로 실패합니다."""
    assert False, "이 테스트는 CI/CD 실패 처리를 테스트하기 위해 의도적으로 실패시킵니다"

def test_syntax_error():
    """이 함수는 의도적인 구문 오류를 포함합니다."""
    # 의도적인 구문 오류
    print("Hello World"  # 괄호가 닫히지 않음

def failing_function():
    """이 함수는 런타임 에러를 발생시킵니다."""
    return 1 / 0  # ZeroDivisionError

if __name__ == "__main__":
    test_that_always_fails()
    test_syntax_error()
    failing_function()