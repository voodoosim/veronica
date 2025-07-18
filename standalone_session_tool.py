#!/usr/bin/env python3
# type: ignore
"""
독립 실행 가능한 텔레그램 세션 생성 도구
모든 기능이 하나의 파일에 포함되어 있어 import 오류 없이 실행 가능

Python 3.11.9
PEP8 준수
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple, List, Dict, Any

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
        except (KeyboardInterrupt, EOFError):
            print("\n👋 프로그램을 종료합니다.")
            exit(0)


def get_phone_number() -> str:
    """전화번호 입력받기"""
    while True:
        phone = input("📱 전화번호를 입력하세요 (+821012345678): ").strip()

        if phone.startswith('+') and len(phone) > 10:
            return phone

        print("❌ 올바른 전화번호 형식이 아닙니다.")


class StandaloneSessionManager:
    """독립 실행형 세션 관리자"""

    def __init__(self, sessions_dir: str = "sessions") -> None:
        """세션 관리자 초기화"""
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(exist_ok=True)
        self.api_id: Optional[int] = None
        self.api_hash: Optional[str] = None

    def setup_api_credentials(self) -> None:
        """API 인증 정보 설정"""
        print("🔑 API 정보를 설정합니다.")
        self.api_id, self.api_hash = get_api_credentials()
        print("✅ API 정보가 설정되었습니다!")

    async def create_session(self, phone: str) -> Optional[str]:
        """새 세션을 생성하고 문자열로 반환"""
        if not self.api_id or not self.api_hash:
            print("❌ API 정보를 먼저 설정하세요.")
            return None

        client = None
        try:
            print(f"📱 {phone}로 세션 생성을 시작합니다...")

            # StringSession으로 클라이언트 생성
            client = TelegramClient(
                StringSession(), self.api_id, self.api_hash
            )

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
            name = (getattr(me, 'first_name', None) or
                   getattr(me, 'username', None) or 'Unknown')
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

        except Exception as general_error:  # pylint: disable=broad-exception-caught
            print(f"❌ 세션 생성 실패: {general_error}")
            return None

        finally:
            # 클라이언트 연결 해제
            if client:
                await client.disconnect()

    def save_session(self, session_string: str, name: str,
                    phone: Optional[str] = None,
                    notes: Optional[str] = None) -> bool:
        """세션 문자열을 파일로 저장"""
        try:
            # 파일명 정리 (특수문자 제거)
            safe_name = "".join(
                c for c in name
                if c.isalnum() or c in (' ', '-', '_')
            ).strip()

            if not safe_name:
                safe_name = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            filename = f"{safe_name}.json"
            filepath = self.sessions_dir / filename

            # 세션 정보 구성
            session_data = {
                "name": name,
                "session_string": session_string,
                "phone": phone,
                "notes": notes,
                "created_at": datetime.now().isoformat(),
                "last_used": None
            }

            # JSON 파일로 저장
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)

            print(f"💾 세션이 저장되었습니다: {filepath}")
            return True

        except (OSError, IOError, ValueError) as e:
            print(f"❌ 세션 저장 실패: {e}")
            return False

    def load_session(self, name: str) -> Optional[str]:
        """저장된 세션 문자열을 불러오기"""
        try:
            # 파일명 찾기
            filename = self._find_session_file(name)
            if not filename:
                print(f"❌ '{name}' 세션을 찾을 수 없습니다.")
                return None

            filepath = self.sessions_dir / filename

            # JSON 파일 읽기
            with open(filepath, 'r', encoding='utf-8') as f:
                session_data = json.load(f)

            # 마지막 사용 시간 업데이트
            session_data["last_used"] = datetime.now().isoformat()

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)

            session_string = session_data["session_string"]
            print(f"📂 세션을 불러왔습니다: {session_data['name']}")

            return session_string

        except (OSError, IOError, ValueError, KeyError) as e:
            print(f"❌ 세션 불러오기 실패: {e}")
            return None

    def list_sessions(self) -> List[Dict[str, Any]]:
        """저장된 모든 세션 목록 반환"""
        sessions = []

        try:
            for filepath in self.sessions_dir.glob("*.json"):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)

                    # 파일 정보 추가
                    session_data["filename"] = filepath.name
                    session_data["file_size"] = filepath.stat().st_size

                    sessions.append(session_data)

                except (OSError, IOError, ValueError) as e:
                    print(f"⚠️ 파일 읽기 실패 ({filepath.name}): {e}")
                    continue

        except Exception as general_error:  # pylint: disable=broad-exception-caught
            print(f"❌ 세션 목록 조회 실패: {general_error}")

        # 생성 시간순 정렬
        sessions.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return sessions

    def delete_session(self, name: str) -> bool:
        """세션 파일 삭제"""
        try:
            filename = self._find_session_file(name)
            if not filename:
                print(f"❌ '{name}' 세션을 찾을 수 없습니다.")
                return False

            filepath = self.sessions_dir / filename
            filepath.unlink()

            print(f"🗑️ 세션이 삭제되었습니다: {filename}")
            return True

        except (OSError, IOError) as e:
            print(f"❌ 세션 삭제 실패: {e}")
            return False

    def _find_session_file(self, name: str) -> Optional[str]:
        """세션 이름으로 파일명 찾기"""
        # 정확한 파일명인 경우
        if name.endswith('.json'):
            filepath = self.sessions_dir / name
            if filepath.exists():
                return name

        # 확장자 없는 파일명인 경우
        filename_with_ext = f"{name}.json"
        filepath = self.sessions_dir / filename_with_ext
        if filepath.exists():
            return filename_with_ext

        # 세션 이름으로 검색
        for filepath in self.sessions_dir.glob("*.json"):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)

                if session_data.get("name") == name:
                    return filepath.name

            except (OSError, IOError, ValueError):
                continue

        return None

    def print_sessions_list(self) -> None:
        """저장된 세션 목록을 예쁘게 출력"""
        sessions = self.list_sessions()

        if not sessions:
            print("📭 저장된 세션이 없습니다.")
            return

        print(f"\n📋 저장된 세션 목록 ({len(sessions)}개):")
        print("=" * 60)

        for i, session in enumerate(sessions, 1):
            name = session.get("name", "Unknown")
            phone = session.get("phone", "Unknown")
            created = session.get("created_at", "Unknown")
            last_used = session.get("last_used", "Never")
            filename = session.get("filename", "Unknown")

            # 날짜 포맷팅
            try:
                if created != "Unknown":
                    created_dt = datetime.fromisoformat(created)
                    created = created_dt.strftime("%Y-%m-%d %H:%M")

                if last_used != "Never" and last_used:
                    last_used_dt = datetime.fromisoformat(last_used)
                    last_used = last_used_dt.strftime("%Y-%m-%d %H:%M")
            except (ValueError, TypeError):
                pass

            print(f"{i:2d}. 📱 {name}")
            print(f"     전화번호: {phone}")
            print(f"     파일명: {filename}")
            print(f"     생성일: {created}")
            print(f"     마지막 사용: {last_used}")

            if session.get("notes"):
                print(f"     메모: {session['notes']}")

            print("-" * 60)

    async def test_session(self, session_string: str) -> bool:
        """세션 문자열이 유효한지 테스트"""
        if not self.api_id or not self.api_hash:
            print("❌ API 정보를 먼저 설정하세요.")
            return False

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
                name = (getattr(me, 'first_name', None) or
                       getattr(me, 'username', None) or 'Unknown')
                print(f"✅ 세션이 유효합니다! ({name})")
                return True
            else:
                print("❌ 세션이 유효하지 않습니다.")
                return False

        except Exception as general_error:  # pylint: disable=broad-exception-caught
            print(f"❌ 세션 테스트 실패: {general_error}")
            return False

        finally:
            if client:
                await client.disconnect()

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
                    await self._handle_create_session()

                elif choice == "3":
                    self.print_sessions_list()

                elif choice == "4":
                    await self._handle_load_session()

                elif choice == "5":
                    self._handle_delete_session()

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

    async def _handle_create_session(self) -> None:
        """새 세션 생성 처리"""
        if not self.api_id or not self.api_hash:
            print("❌ API 정보를 먼저 설정하세요.")
            return

        print("\n📱 새 세션을 생성합니다.")

        # 전화번호 입력
        phone = get_phone_number()

        # 세션 생성
        session_string = await self.create_session(phone)

        if session_string:
            print("\n✅ 세션 생성 성공!")

            # 세션 저장 여부 확인
            save_choice = input(
                "💾 이 세션을 저장하시겠습니까? (y/n): "
            ).strip().lower()

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
                success = self.save_session(
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

    async def _handle_load_session(self) -> None:
        """저장된 세션 불러오기 처리"""
        sessions = self.list_sessions()

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
                session_string = self.load_session(session_name)

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
                            await self.test_session(session_string)

                else:
                    print("❌ 세션을 불러오는데 실패했습니다.")
            else:
                print("❌ 잘못된 번호입니다.")

        except ValueError:
            print("❌ 숫자를 입력하세요.")

    def _handle_delete_session(self) -> None:
        """저장된 세션 삭제 처리"""
        sessions = self.list_sessions()

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
                    success = self.delete_session(session_name)
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


async def main() -> None:
    """프로그램 진입점"""
    try:
        manager = StandaloneSessionManager()
        await manager.run()

    except (KeyboardInterrupt, EOFError):
        print("\n👋 프로그램이 종료되었습니다.")
    except Exception as general_error:  # pylint: disable=broad-exception-caught
        print(f"\n❌ 예상치 못한 오류: {general_error}")
        input("아무 키나 눌러서 종료...")


if __name__ == "__main__":
    asyncio.run(main())
