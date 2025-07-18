# type: ignore
"""
간단한 텔레그램 세션 관리 프로그램 패키지
"""

__version__ = "1.0.0"
__author__ = "TGCC Team"
__description__ = "간단한 텔레그램 세션 생성 및 관리 도구"

# 패키지 레벨에서 주요 클래스들을 export
try:
    from .session_creator import SessionCreator
    from .session_manager import SessionManager

    __all__ = [
        "SessionCreator",
        "SessionManager"
    ]
except ImportError:
    # 개발 환경에서 직접 실행할 때는 import 오류 무시
    pass
