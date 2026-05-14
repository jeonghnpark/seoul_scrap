import os
import asyncio
import logging
from telegram import Bot
from telegram.error import TelegramError
from dotenv import load_dotenv
import html

# 로깅 설정
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG
)
logger = logging.getLogger(__name__)

# .env 파일에서 환경 변수를 로드합니다.
# 이를 통해 텔레그램 봇 토큰이나 채팅 ID와 같은 민감한 정보들을 안전하게 관리할 수 있습니다.
load_dotenv()


class Notifier:
    def __init__(self):
        # .env 파일에서 텔레그램 봇 토큰과 메시지를 보낼 채팅 ID를 가져옵니다.
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")

        logger.info(f"🔍 Notifier 초기화 시작")
        logger.debug(f"Token exists: {bool(self.token)}")
        logger.debug(f"Chat ID: {self.chat_id}")

        # 토큰이 설정되지 않았다면 명확한 에러를 발생시켜 초기 설정을 유도합니다.
        if not self.token:
            error_msg = "TELEGRAM_BOT_TOKEN is not set in .env file"
            logger.error(f"❌ {error_msg}")
            raise ValueError(error_msg)
        # 채팅 ID가 설정되지 않았다면 명확한 에러를 발생시켜 초기 설정을 유도합니다.
        if not self.chat_id:
            error_msg = "TELEGRAM_CHAT_ID is not set in .env file"
            logger.error(f"❌ {error_msg}")
            raise ValueError(error_msg)

        # 텔레그램 봇 객체를 생성합니다. 이 객체를 통해 텔레그램 API와 상호작용합니다.
        self.bot = Bot(token=self.token)
        logger.info(f"✓ Telegram Bot 객체 생성 완료")

    async def send_message(self, message):
        """
        지정된 `chat_id`로 텔레그램 메시지를 비동기적으로 전송합니다.
        메시지 전송 실패 시 `TelegramError`를 처리하여 프로그램의 안정성을 높입니다.
        """
        try:
            logger.debug(f"📤 메시지 전송 시도 - Chat ID: {self.chat_id}")
            logger.debug(f"Message content: {message[:100]}...")  # 처음 100자만 로그
            
            # `bot.send_message` 메서드를 사용하여 실제 메시지를 보냅니다.
            # `chat_id`는 메시지를 받을 대상(개인 또는 그룹 채팅방)을 식별합니다.
            result = await self.bot.send_message(
                chat_id=self.chat_id, text=message, parse_mode="HTML"
            )
            
            logger.info(f"✓ 메시지 전송 성공 - Message ID: {result.message_id}")
            return True  # 메시지 전송 성공 시 True 반환
            
        except TelegramError as e:
            # 텔레그램 API 관련 오류(예: 잘못된 토큰, 존재하지 않는 채팅방 ID) 발생 시
            # 오류 메시지를 출력하고 False를 반환하여 호출자에게 실패를 알립니다.
            logger.error(f"❌ 텔레그램 전송 실패: {type(e).__name__} - {str(e)}")
            return False
        except Exception as e:
            logger.error(f"❌ 예기치 않은 오류: {type(e).__name__} - {str(e)}")
            return False

    def format_message(self, reservation):
        """
        주어진 예약 정보(딕셔너리)를 텔레그램 메시지에 적합하고 가독성 좋은 형식으로 포맷팅합니다.
        사용자에게 중요한 정보(제목, 장소, 접수 기간, 링크 등)를 명확하게 전달하는 데 중점을 둡니다.
        """
        # 예약 정보 딕셔너리에서 각 필드의 값을 안전하게 가져옵니다.
        # `.get(key, default_value)`를 사용하여 키가 없을 경우 기본값을 반환함으로써
        # `KeyError`를 방지하고 메시지 형식을 일관되게 유지합니다.
        url = reservation.get("url", "#")

        title = html.escape(reservation.get("svc_name", "제목 없음"))
        place = html.escape(reservation.get("place_name", "장소 미정"))
        category = html.escape(reservation.get("category", "기타"))
        state = html.escape(reservation.get("state", "상태 미정"))
        url = html.escape(
            reservation.get("url", "#")
        )  # URL이 없는 경우 임시 링크로 처리

        rcpt_bgndt = html.escape(reservation.get("rcpt_bgndt", ""))  # 접수 시작 일시
        rcpt_enddt = html.escape(reservation.get("rcpt_enddt", ""))  # 접수 종료 일시

        # f-string을 사용하여 메시지 내용을 구성합니다.
        # 이모지와 줄 바꿈 문자(`\n`)를 사용하여 시각적으로 구분되고 읽기 쉽게 만듭니다.
        message = (
            # f"📢 [신규 예약 알림]\n"
            f"🏷️ {category} | {state}\n"
            f"📌 {title}\n"
            # f"📍 {place}\n"
            # f"📅 접수: {rcpt_bgndt} ~ {rcpt_enddt}\n\n"
            f"🔗 <a href = '{url}'>바로가기</a>"
        )
        return message


if __name__ == "__main__":
    # 이 스크립트가 직접 실행될 때만 동작하는 테스트 코드 블록입니다.
    # Notifier 클래스의 기능을 개별적으로 검증할 때 유용합니다.
    async def test():
        try:
            notifier = Notifier()  # Notifier 객체 생성
            # 테스트 메시지를 텔레그램으로 보냅니다.
            await notifier.send_message(
                "테스트 메시지입니다. 이 메시지가 텔레그램으로 전송됩니다."
            )
            print("Message sent successfully")
        except Exception as e:
            print(f"Setup error: {e}")  # 설정 오류 발생 시 에러 메시지 출력

    # 비동기 함수 `test()`를 실행합니다.
    asyncio.run(test())
