# type: ignore
"""
간단한 텔레그램 세션 관리 프로그램
세션 생성, 저장, 불러오기 기능

Python 3.11.9
PEP8 준수
"""

import asyncio
from typing import Optional

# 로컬 모듈 import
try:
    from session_creator import SessionCreator, get_api_credentials, get_phone_number
    from session_manager import SessionManager, test_session_connection
except ImportError as e:
    print(f"❌ 모듈 import 오류: {e}")
    print("session_creator.py와 session_manager.py 파일이 같은 폴더에 있는지 확인하세요.")
    exit(1)


class SimpleTelegramSessionApp:
    """간단한 텔레그램 세션 앱"""

    def __init__(self) -> None:
        """앱 초기화"""
        self.session_manager = SessionManager()
        self.api_id: Optional[int] = None
        self.api_hash: Optional[str] = None

    def setup_api_credentials(self) -> None:
        """API 인증 정보 설정"""
        print("🔑 API 정보를 설정합니다.")
        self.api_id, self.api_hash = get_api_credentials()
        print("✅ API 정보가 설정되었습니다!")

    async def create_new_session(self) -> None:
        """새 세션 생성"""
        if not self.api_id or not self.api_hash:
            print("❌ API 정보를 먼저 설정하세요.")
            return

        print("\n📱 새 세션을 생성합니다.")

        # 전화번호 입력
        phone = get_phone_number()

        # 세션 생성
        creator = SessionCreator(self.api_id, self.api_hash)
        session_string = await creator.create_session(phone)

        if session_string:
            print("\n✅ 세션 생성 성공!")

            # 세션 저장 여부 확인
            save_choice = input("💾 이 세션을 저장하시겠습니까? (y/n): ").strip().lower()

            if save_choice in ['y', 'yes', '예']:
                # 세션 이름 입력
                name = input("📝 세션 이름을 입력하세요: ").strip()
                if not name:
                    name = f"Session_{phone.replace('+', '')}"

                # 메모 입력 (선택사항)
                notes = input("📄 메모 (선택사항): ").strip()
                if not notes:
                    notes = None

                # 세션 저장
                success = self.session_manager.save_session(
                    session_string=session_string,
                    name=name,
                    phone=phone,
                    notes=notes
                )

                if success:
                    print("💾 세션이 성공적으로 저장되었습니다!")
                else:
                    print("❌ 세션 저장에 실패했습니다.")

            # 세션 문자열 출력
            print("\n" + "=" * 60)
            print("📄 세션 문자열:")
            print("-" * 60)
            print(session_string)
            print("-" * 60)
            print("✅ 이 문자열을 복사해서 보관하세요!")

        else:
            print("❌ 세션 생성에 실패했습니다.")

    def view_saved_sessions(self) -> None:
        """저장된 세션 목록 보기"""
        print("\n📋 저장된 세션들:")
        self.session_manager.print_sessions_list()

    async def load_saved_session(self) -> None:
        """저장된 세션 불러오기"""
        sessions = self.session_manager.list_sessions()

        if not sessions:
            print("📭 저장된 세션이 없습니다.")
            return

        print("\n📋 사용 가능한 세션:")
        for i, session in enumerate(sessions, 1):
            phone = session.get('phone', 'Unknown')
            notes = session.get('notes', '')
            print(f"{i:2d}. {session['name']} ({phone})")
            if notes:
                print(f"     메모: {notes}")

        try:
            idx = int(input("\n📂 불러올 세션 번호를 선택하세요: ")) - 1

            if 0 <= idx < len(sessions):
                session_name = sessions[idx]["name"]
                session_string = self.session_manager.load_session(session_name)

                if session_string:
                    print("\n" + "=" * 60)
                    print("📄 세션 문자열:")
                    print("-" * 60)
                    print(session_string)
                    print("-" * 60)
                    print("✅ 이 문자열을 복사해서 사용하세요!")

                    # 세션 테스트 여부 확인
                    if self.api_id and self.api_hash:
                        test_choice = input(
                            "\n🔍 세션을 테스트해보시겠습니까? (y/n): "
                        ).strip().lower()
                        if test_choice in ['y', 'yes', '예']:
                            await test_session_connection(
                                session_string, self.api_id, self.api_hash
                            )

                else:
                    print("❌ 세션을 불러오는데 실패했습니다.")
            else:
                print("❌ 잘못된 번호입니다.")

        except ValueError:
            print("❌ 숫자를 입력하세요.")

    def delete_saved_session(self) -> None:
        """저장된 세션 삭제"""
        sessions = self.session_manager.list_sessions()

        if not sessions:
            print("📭 저장된 세션이 없습니다.")
            return

        print("\n📋 저장된 세션:")
        for i, session in enumerate(sessions, 1):
            phone = session.get('phone', 'Unknown')
            print(f"{i:2d}. {session['name']} ({phone})")

        try:
            idx = int(input("\n🗑️ 삭제할 세션 번호를 선택하세요: ")) - 1

            if 0 <= idx < len(sessions):
                session_name = sessions[idx]["name"]

                print(f"\n⚠️ 정말로 '{session_name}' 세션을 삭제하시겠습니까?")
                confirm = input("삭제하려면 'DELETE'를 입력하세요: ").strip()

                if confirm == "DELETE":
                    success = self.session_manager.delete_session(session_name)
                    if success:
                        print("✅ 세션이 삭제되었습니다.")
                    else:
                        print("❌ 세션 삭제에 실패했습니다.")
                else:
                    print("❌ 삭제가 취소되었습니다.")
            else:
                print("❌ 잘못된 번호입니다.")

        except ValueError:
            print("❌ 숫자를 입력하세요.")

    async def run(self) -> None:
        """메인 실행 루프"""
        print("🤖 간단한 텔레그램 세션 관리 프로그램")
        print("=" * 50)

        while True:
            print("\n📋 메뉴:")
            print("1. API 정보 설정")
            print("2. 새 세션 생성")
            print("3. 저장된 세션 목록 보기")
            print("4. 저장된 세션 불러오기")
            print("5. 저장된 세션 삭제")
            print("6. 프로그램 종료")

            # API 설정 상태 표시
            if self.api_id and self.api_hash:
                print(f"\n✅ API ID: {self.api_id}")
            else:
                print("\n❌ API 정보가 설정되지 않았습니다.")

            choice = input("\n선택하세요 (1-6): ").strip()

            try:
                if choice == "1":
                    self.setup_api_credentials()

                elif choice == "2":
                    await self.create_new_session()

                elif choice == "3":
                    self.view_saved_sessions()

                elif choice == "4":
                    await self.load_saved_session()

                elif choice == "5":
                    self.delete_saved_session()

                elif choice == "6":
                    print("👋 프로그램을 종료합니다.")
                    break

                else:
                    print("❌ 잘못된 선택입니다. 1-6 사이의 숫자를 입력하세요.")

            except (KeyboardInterrupt, EOFError):
                print("\n\n👋 사용자에 의해 프로그램이 종료되었습니다.")
                break
            except Exception as general_error:  # pylint: disable=broad-exception-caught
                print(f"\n❌ 오류 발생: {general_error}")
                input("아무 키나 눌러서 계속...")


async def main() -> None:
    """프로그램 진입점"""
    try:
        app = SimpleTelegramSessionApp()
        await app.run()

    except (KeyboardInterrupt, EOFError):
        print("\n👋 프로그램이 종료되었습니다.")
    except Exception as general_error:  # pylint: disable=broad-exception-caught
        print(f"\n❌ 예상치 못한 오류: {general_error}")
        input("아무 키나 눌러서 종료...")


if __name__ == "__main__":
    asyncio.run(main())
