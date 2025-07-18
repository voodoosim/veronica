# type: ignore
"""
간단한 세션 관리기
세션 문자열을 파일로 저장하고 불러오는 기능

Python 3.11.9
PEP8 준수
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any

try:
    from telethon import TelegramClient
    from telethon.sessions import StringSession
except ImportError as e:
    print(f"❌ 텔레그램 라이브러리가 없습니다: {e}")
    print("설치 명령어: pip install telethon")
    exit(1)


class SessionManager:
    """세션 저장/불러오기 관리 클래스"""

    def __init__(self, sessions_dir: str = "sessions") -> None:
        """
        세션 관리자 초기화

        Args:
            sessions_dir: 세션 파일들을 저장할 디렉토리
        """
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(exist_ok=True)

    def save_session(self, session_string: str, name: str,
                    phone: Optional[str] = None, notes: Optional[str] = None) -> bool:
        """
        세션 문자열을 파일로 저장

        Args:
            session_string: 저장할 세션 문자열
            name: 세션 이름 (파일명으로 사용)
            phone: 전화번호 (선택사항)
            notes: 메모 (선택사항)

        Returns:
            저장 성공 여부
        """
        try:
            # 파일명 정리 (특수문자 제거)
            safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
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

        except Exception as e:
            print(f"❌ 세션 저장 실패: {e}")
            return False

    def load_session(self, name: str) -> Optional[str]:
        """
        저장된 세션 문자열을 불러오기

        Args:
            name: 세션 이름 또는 파일명

        Returns:
            세션 문자열 (실패시 None)
        """
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

        except Exception as e:
            print(f"❌ 세션 불러오기 실패: {e}")
            return None

    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        저장된 모든 세션 목록 반환

        Returns:
            세션 정보 리스트
        """
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

                except Exception as e:
                    print(f"⚠️ 파일 읽기 실패 ({filepath.name}): {e}")
                    continue

        except Exception as e:
            print(f"❌ 세션 목록 조회 실패: {e}")

        # 생성 시간순 정렬
        sessions.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return sessions

    def delete_session(self, name: str) -> bool:
        """
        세션 파일 삭제

        Args:
            name: 세션 이름 또는 파일명

        Returns:
            삭제 성공 여부
        """
        try:
            filename = self._find_session_file(name)
            if not filename:
                print(f"❌ '{name}' 세션을 찾을 수 없습니다.")
                return False

            filepath = self.sessions_dir / filename
            filepath.unlink()

            print(f"🗑️ 세션이 삭제되었습니다: {filename}")
            return True

        except Exception as e:
            print(f"❌ 세션 삭제 실패: {e}")
            return False

    def _find_session_file(self, name: str) -> Optional[str]:
        """
        세션 이름으로 파일명 찾기

        Args:
            name: 세션 이름

        Returns:
            찾은 파일명 (없으면 None)
        """
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

            except Exception:
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
            except Exception:
                pass

            print(f"{i:2d}. 📱 {name}")
            print(f"     전화번호: {phone}")
            print(f"     파일명: {filename}")
            print(f"     생성일: {created}")
            print(f"     마지막 사용: {last_used}")

            if session.get("notes"):
                print(f"     메모: {session['notes']}")

            print("-" * 60)


async def test_session_connection(session_string: str, api_id: int, api_hash: str) -> bool:
    """
    세션 문자열로 텔레그램 연결 테스트

    Args:
        session_string: 테스트할 세션 문자열
        api_id: 텔레그램 API ID
        api_hash: 텔레그램 API Hash

    Returns:
        연결 성공 여부
    """
    client = None
    try:
        print("🔍 세션 연결을 테스트합니다...")

        client = TelegramClient(
            StringSession(session_string),
            api_id,
            api_hash
        )

        await client.connect()

        if await client.is_user_authorized():
            me = await client.get_me()
            name = getattr(me, 'first_name', None) or getattr(me, 'username', None) or 'Unknown'
            print(f"✅ 연결 성공! ({name})")
            return True
        else:
            print("❌ 세션이 만료되었거나 유효하지 않습니다.")
            return False

    except Exception as e:
        print(f"❌ 연결 테스트 실패: {e}")
        return False

    finally:
        if client:
            await client.disconnect()


def main() -> None:
    """간단한 CLI 인터페이스"""
    manager = SessionManager()

    while True:
        print("\n🤖 세션 관리자")
        print("=" * 30)
        print("1. 세션 목록 보기")
        print("2. 세션 불러오기")
        print("3. 세션 삭제")
        print("4. 종료")

        choice = input("\n선택하세요 (1-4): ").strip()

        if choice == "1":
            manager.print_sessions_list()

        elif choice == "2":
            sessions = manager.list_sessions()
            if not sessions:
                print("📭 저장된 세션이 없습니다.")
                continue

            print("\n📋 사용 가능한 세션:")
            for i, session in enumerate(sessions, 1):
                print(f"{i}. {session['name']} ({session.get('phone', 'Unknown')})")

            try:
                idx = int(input("\n세션 번호를 선택하세요: ")) - 1
                if 0 <= idx < len(sessions):
                    session_name = sessions[idx]["name"]
                    session_string = manager.load_session(session_name)

                    if session_string:
                        print("\n" + "=" * 60)
                        print("📄 세션 문자열:")
                        print("-" * 60)
                        print(session_string)
                        print("-" * 60)
                        print("✅ 이 문자열을 복사해서 사용하세요!")
                else:
                    print("❌ 잘못된 번호입니다.")
            except ValueError:
                print("❌ 숫자를 입력하세요.")

        elif choice == "3":
            sessions = manager.list_sessions()
            if not sessions:
                print("📭 저장된 세션이 없습니다.")
                continue

            print("\n📋 저장된 세션:")
            for i, session in enumerate(sessions, 1):
                print(f"{i}. {session['name']} ({session.get('phone', 'Unknown')})")

            try:
                idx = int(input("\n삭제할 세션 번호를 선택하세요: ")) - 1
                if 0 <= idx < len(sessions):
                    session_name = sessions[idx]["name"]
                    confirm = input(f"정말로 '{session_name}' 세션을 삭제하시겠습니까? (y/n): ").strip().lower()

                    if confirm in ['y', 'yes', '예']:
                        manager.delete_session(session_name)
                    else:
                        print("❌ 삭제가 취소되었습니다.")
                else:
                    print("❌ 잘못된 번호입니다.")
            except ValueError:
                print("❌ 숫자를 입력하세요.")

        elif choice == "4":
            print("👋 프로그램을 종료합니다.")
            break

        else:
            print("❌ 잘못된 선택입니다.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 사용자에 의해 종료되었습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
