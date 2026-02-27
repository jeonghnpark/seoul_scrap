import schedule
import time
import asyncio
import logging
from datetime import datetime

from scraper import Scraper
from storage import Storage
from notifier import Notifier

# 로깅 설정
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def job():
    logger.info("Starting job...")
    try:
        # 1. 초기화
        scraper = Scraper()
        storage = Storage()
        notifier = Notifier()

        # 2. 데이터 수집
        reservations = scraper.fetch_new_reservations()
        logger.info(f"Fetched {len(reservations)} reservations.")

        new_count = 0
        
        # 3. 필터링 및 알림 전송
        # 비동기 작업을 위한 이벤트 루프 실행
        async def process_reservations():
            nonlocal new_count
            for reservation in reservations:
                svc_id = reservation['svc_id']
                
                if not storage.is_seen(svc_id):
                    # 새로운 예약 발견
                    logger.info(f"New reservation found: {reservation['svc_name']}")
                    
                    # 메시지 포맷팅
                    message = notifier.format_message(reservation)
                    
                    # 알림 전송
                    if await notifier.send_message(message):
                        # 전송 성공 시 DB에 저장
                        storage.add_seen(svc_id)
                        new_count += 1
                        # 텔레그램 API 제한 고려하여 잠시 대기
                        await asyncio.sleep(1)
                    else:
                        logger.error(f"Failed to send notification for {svc_id}")

        asyncio.run(process_reservations())
        
        if new_count > 0:
            logger.info(f"Job finished. Sent {new_count} new notifications.")
        else:
            logger.info("Job finished. No new notifications.")

    except Exception as e:
        logger.error(f"Job failed: {e}")

def main():
    logger.info("Seoul Reservation Bot started.")
    
    # 첫 실행 시 바로 한 번 실행 (선택 사항)
    job()
    
    # 10분마다 실행
    schedule.every(10).minutes.do(job)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
