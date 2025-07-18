# type: ignore
"""
간단한 텔레그램 세션 생성기
세션 생성하고 문자열로 변환해주는 기능

Python 3.11.9
PEP8 준수
"""

import asyncio
from typing import Optional, Tuple

try:
    from telethon import TelegramClient
    from telethon.sessions import StringSession
    from telethon.errors import (
        SessionPasswordNeededError,
        PhoneCodeInvalidError,
        ApiIdInvalidError
    )
except ImportError as e:
    print(f"❌ 텔레그램 라이브러리가 없습니다: {e}")
    print("설치 명령어: pip install telethon")
    exit(1)


class SessionCreator:
    """세션 생성 클래스"""

    def __init__(self, api_id: int, api_hash: str) -> None:
        """
        세션 생성기 초기화

        Args:
            api_id: 텔레그램 API ID
            api_hash: 텔레그램 API Hash
        """
        self.api_id = api_id
        self.api_hash = api_hash

    async def create_session(self, phone: str) -> Optional[str]:
        """
        새 세션을 생성하고 문자열로 반환

        Args:
            phone: 전화번호 (+821012345678 형식)

        Returns:
            세션 문자열 (실패시 None)
        """
        client = None
        try:
            print(f"📱 {phone}로 세션 생성을 시작합니다...")

            # StringSession으로 클라이언트 생성
            client = TelegramClient(StringSession(), self.api_id, self.api_hash)

            # 텔레그램 연결
            print("🔗 텔레그램에 연결 중...")
            await client.connect()

            # 인증 코드 요청
            print("📲 인증 코드를 전송합니다...")
            await client.send_code_request(phone)

            # 인증 코드 입력
            code = input("✅ 받은 인증 코드를 입력하세요: ").strip()

            try:
                # 인증 코드로 로그인 시도
                await client.sign_in(phone, code)

            except SessionPasswordNeededError:
                # 2단계 인증이 필요한 경우
                print("🔐 2단계 인증이 설정되어 있습니다.")
                password = input("🔐 2단계 인증 비밀번호를 입력하세요: ")
                await client.sign_in(password=password)

            # 로그인 성공 확인
            me = await client.get_me()
            name = getattr(me, 'first_name', None) or getattr(me, 'username', None) or 'Unknown'
            print(f"✅ '{name}'님으로 로그인 성공!")

            # 세션 문자열 추출
            session_string = client.session.save()
            print("🎉 세션 문자열 생성 완료!")

            return session_string

        except PhoneCodeInvalidError:
            print("❌ 잘못된 인증 코드입니다.")
            return None

        except ApiIdInvalidError:
            print("❌ 잘못된 API ID 또는 Hash입니다.")
            return None

        except Exception as e:
            print(f"❌ 세션 생성 실패: {e}")
            return None

        finally:
            # 클라이언트 연결 해제
            if client:
                await client.disconnect()

    async def test_session(self, session_string: str) -> bool:
        """
        세션 문자열이 유효한지 테스트

        Args:
            session_string: 테스트할 세션 문자열

        Returns:
            세션 유효성 여부
        """
        client = None
        try:
            print("🔍 세션을 테스트합니다...")

            # 세션 문자열로 클라이언트 생성
            client = TelegramClient(
                StringSession(session_string),
                self.api_id,
                self.api_hash
            )

            # 연결 및 인증 확인
            await client.connect()

            if await client.is_user_authorized():
                me = await client.get_me()
                name = getattr(me, 'first_name', None) or getattr(me, 'username', None) or 'Unknown'
                print(f"✅ 세션이 유효합니다! ({name})")
                return True
            else:
                print("❌ 세션이 유효하지 않습니다.")
                return False

        except Exception as e:
            print(f"❌ 세션 테스트 실패: {e}")
            return False

        finally:
            if client:
                await client.disconnect()


def get_api_credentials() -> Tuple[int, str]:
    """API 인증 정보 입력받기"""
    print("📋 텔레그램 API 정보를 입력하세요:")
    print("   🌐 https://my.telegram.org에서 발급받으세요")

    while True:
        try:
            api_id = int(input("🔑 API ID: ").strip())
            api_hash = input("🔐 API Hash: ").strip()

            if len(api_hash) < 30:
                print("❌ API Hash가 너무 짧습니다.")
                continue

            return api_id, api_hash

        except ValueError:
            print("❌ API ID는 숫자여야 합니다.")
        except KeyboardInterrupt:
            print("\n👋 프로그램을 종료합니다.")
            exit(0)


def get_phone_number() -> str:
    """전화번호 입력받기"""
    while True:
        phone = input("📱 전화번호를 입력하세요 (+821012345678): ").strip()

        if phone.startswith('+') and len(phone) > 10:
            return phone

        print("❌ 올바른 전화번호 형식이 아닙니다.")


async def main() -> None:
    """메인 함수"""
    print("🤖 간단한 텔레그램 세션 생성기")
    print("=" * 40)

    # API 정보 입력
    api_id, api_hash = get_api_credentials()

    # 전화번호 입력
    phone = get_phone_number()

    # 세션 생성
    creator = SessionCreator(api_id, api_hash)
    session_string = await creator.create_session(phone)

    if session_string:
        print("\n" + "=" * 60)
        print("📄 세션 문자열:")
        print("-" * 60)
        print(session_string)
        print("-" * 60)
        print("✅ 이 문자열을 저장해두고 필요할 때 사용하세요!")

        # 세션 테스트
        test_choice = input("\n🔍 세션을 테스트해보시겠습니까? (y/n): ").strip().lower()
        if test_choice in ['y', 'yes', '예']:
            await creator.test_session(session_string)
    else:
        print("❌ 세션 생성에 실패했습니다.")

    print("\n✨ 프로그램을 종료합니다.")
    input("아무 키나 눌러서 종료...")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 사용자에 의해 종료되었습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        input("아무 키나 눌러서 종료...")
