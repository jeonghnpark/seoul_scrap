import os
import asyncio
from telegram import Bot
from telegram.error import TelegramError
from dotenv import load_dotenv

load_dotenv()

class Notifier:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN is not set in .env file")
        if not self.chat_id:
            raise ValueError("TELEGRAM_CHAT_ID is not set in .env file")
            
        self.bot = Bot(token=self.token)

    async def send_message(self, message):
        try:
            await self.bot.send_message(chat_id=self.chat_id, text=message)
            return True
        except TelegramError as e:
            print(f"Failed to send message: {e}")
            return False

    def format_message(self, reservation):
        """
        예약 정보를 보기 좋은 메시지 포맷으로 변환
        """
        title = reservation.get('svc_name', '제목 없음')
        place = reservation.get('place_name', '장소 미정')
        category = reservation.get('category', '기타')
        state = reservation.get('state', '상태 미정')
        url = reservation.get('url', '#')
        
        rcpt_bgndt = reservation.get('rcpt_bgndt', '')
        rcpt_enddt = reservation.get('rcpt_enddt', '')
        
        message = (
            f"📢 [신규 예약 알림]\n\n"
            f"🏷️ {category} | {state}\n"
            f"📌 {title}\n"
            f"📍 {place}\n"
            f"📅 접수: {rcpt_bgndt} ~ {rcpt_enddt}\n\n"
            f"🔗 바로가기: {url}"
        )
        return message

if __name__ == "__main__":
    # 테스트 코드
    async def test():
        try:
            notifier = Notifier()
            await notifier.send_message("테스트 메시지입니다.")
            print("Message sent successfully")
        except Exception as e:
            print(f"Setup error: {e}")

    asyncio.run(test())
