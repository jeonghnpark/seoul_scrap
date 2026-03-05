import schedule
import time
import asyncio
import logging
from datetime import datetime
from scraper import Scraper
from storage import Storage
from notifier import Notifier

# 로깅 설정을 통해 애플리케이션의 동작 상태를 콘솔에 출력하고, 문제 발생 시 디버깅 정보를 제공합니다.
# `format`은 로그 메시지의 형식을 지정하며, `level=logging.INFO`는 정보 수준 이상의 로그를 출력하도록 설정합니다.
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def job(fetch_limit=500, notify_limit=30):
    """
    주기적으로 실행될 메인 작업 함수입니다. 이 함수는 서울시 공공서비스 예약 정보를 스크랩하고,
    이미 알림을 보낸 중복 예약을 필터링한 후, 새로운 예약 정보를 텔레그램으로 전송하는 일련의 과정을 담당합니다.
    
    Args:
        fetch_limit (int): API에서 가져올 최대 공고 수 (기본값: 500)
        notify_limit (int): 텔레그램으로 알림을 보낼 최대 공고 수 (기본값: 30)
    """
    logger.info("Starting job...")  # 작업 시작을 알리는 로그 메시지
    try:
        # 1. 각 모듈의 인스턴스를 초기화합니다.
        # `Scraper`: 서울시 API로부터 데이터를 가져오는 역할
        # `Storage`: SQLite 데이터베이스에 예약 ID를 저장하고 중복을 확인하는 역할
        # `Notifier`: 텔레그램으로 알림 메시지를 전송하는 역할
        scraper = Scraper()
        storage = Storage()
        notifier = Notifier()

        # 2. Scraper를 사용하여 서울시 공공서비스 예약 API로부터 최신 예약 정보를 가져옵니다.
        # 이 과정에서 네트워크 요청과 JSON 데이터 파싱이 이루어집니다.
        reservations = scraper.fetch_new_reservations(fetch_limit=fetch_limit)
        logger.info(
            f"Fetched {len(reservations)} reservations."
        )  # 가져온 예약 정보의 개수 로깅

        new_count = 0  # 새로 발견되어 알림을 보낸 예약의 개수를 세기 위한 카운터
        
        # 3. 가져온 예약 정보를 비동기적으로 처리하고, 필터링하여 텔레그램 알림을 전송하는 함수입니다.
        # `async def`를 사용하여 비동기 작업을 정의하고, `asyncio.run`으로 실행합니다.
        async def process_reservations():
            nonlocal new_count  # 중첩 함수에서 외부 함수의 `new_count` 변수를 수정하기 위해 필요
            
            # 오늘 날짜를 가져옵니다.
            today = datetime.now().strftime("%Y-%m-%d")
            
            # 접수 시작일이 있는 데이터만 필터링합니다.
            valid_reservations = [r for r in reservations if r.get('rcpt_bgndt')]
            
            # 사용자의 요구사항:
            # "오늘을 기준으로 접수 시작일이 가까운 순서대로 notify해줘."
            # "오늘 이후로 접수가 시작되는 건에 대해서 보여주고, 이후에는 접수일이 이미 지난 건에 대한 순서로 받아줘."
            # "텔레그램에 보낼때는 마찬가지로 우선순위가 높은 건을 마지막으로 notify해줘."
            
            # 즉, 전송 순서(처리 순서)는 다음과 같아야 합니다:
            # 1. 우선순위가 낮은 것 (이미 지난 것, 먼 미래인 것)
            # 2. 우선순위가 높은 것 (오늘, 내일 등 접수 임박한 것)
            
            # 이를 위해 데이터를 두 그룹으로 나눕니다.
            future_reservations = []  # 오늘 포함 이후 접수 시작
            past_reservations = []    # 오늘 이전 접수 시작
            
            for r in valid_reservations:
                # 날짜 비교를 위해 문자열 앞 10자리(YYYY-MM-DD)만 사용
                rcpt_date = r.get('rcpt_bgndt', '')[:10]
                if rcpt_date >= today:
                    future_reservations.append(r)
                else:
                    past_reservations.append(r)
            
            # 정렬 로직:
            # past_reservations: 오름차순 정렬 (오래된 과거 -> 최근 과거)
            past_reservations.sort(key=lambda x: x.get('rcpt_bgndt', ''))
            
            # future_reservations: 내림차순 정렬 (먼 미래 -> 가까운 미래)
            # 접수일이 가까운 것(오늘/내일)이 가장 중요하므로 가장 마지막에 전송되어야 함
            future_reservations.sort(key=lambda x: x.get('rcpt_bgndt', ''), reverse=True)
            
            # 최종 처리 순서 리스트: [과거 데이터] + [미래 데이터]
            sorted_reservations = past_reservations + future_reservations
            
            # notify_limit 개수만큼만 추출합니다.
            # sorted_reservations는 [과거 -> 미래] 순서이므로, 
            # 가장 중요한(마지막에 전송될) 미래 데이터가 리스트의 뒤쪽에 있습니다.
            # 따라서 뒤에서부터 notify_limit 개수를 가져와야 가장 우선순위 높은 것들이 포함됩니다.
            if len(sorted_reservations) > notify_limit:
                sorted_reservations = sorted_reservations[-notify_limit:]
            
            # 수집된 각 예약 정보에 대해 반복합니다.
            for reservation in sorted_reservations:
                svc_id = reservation["svc_id"]  # 예약 고유 ID 추출

                # `storage.is_seen()`을 통해 해당 예약이 이전에 알림이 발송되었는지 확인합니다.
                # `False`를 반환하면 새로운 예약임을 의미합니다.
                if not storage.is_seen(svc_id):
                    # 새로운 예약이 발견되었음을 로그로 기록합니다.
                    logger.info(f"New reservation found: {reservation['svc_name']}")

                    # Notifier를 사용하여 예약 정보를 텔레그램 메시지 형식으로 포맷팅합니다.
                    message = notifier.format_message(reservation)

                    # 포맷팅된 메시지를 텔레그램으로 비동기적으로 전송합니다.
                    if await notifier.send_message(message):
                        # 메시지 전송에 성공하면, 해당 예약의 ID를 데이터베이스에 저장하여
                        # 다음에 다시 알림을 보내지 않도록 합니다.
                        storage.add_seen(svc_id)
                        new_count += 1  # 새로운 알림 개수 증가
                        # 텔레그램 API의 Rate Limit (초당 요청 수 제한)을 준수하기 위해
                        # 메시지 전송 후 1초간 잠시 대기합니다. 이는 너무 많은 요청으로 인해
                        # API 호출이 차단되는 것을 방지하기 위함입니다.
                        await asyncio.sleep(1)
                    else:
                        # 알림 전송 실패 시 에러 로그를 기록하여 문제 파악에 도움을 줍니다.
                        logger.error(f"Failed to send notification for {svc_id}")

        # 비동기 예약 처리 함수를 실행합니다.
        asyncio.run(process_reservations())

        # 모든 예약 처리 후, 새로 보낸 알림의 총 개수를 로그로 출력합니다.
        if new_count > 0:
            logger.info(f"Job finished. Sent {new_count} new notifications.")
        else:
            logger.info("Job finished. No new notifications.")

    except Exception as e:
        # `job` 함수 실행 중 발생할 수 있는 모든 예외를 catch하여 로그로 기록하고
        # 프로그램이 비정상적으로 종료되는 것을 방지합니다. 이는 스케줄러가 계속 동작하도록 합니다.
        logger.error(f"Job failed: {e}")


def main(fetch_limit: int = 500, notify_limit: int = 30):
    """
    봇의 메인 실행 함수입니다. 봇 시작을 알리고, 스케줄러를 설정하여 `job` 함수를 주기적으로 실행합니다.
    무한 루프를 통해 스케줄러가 항상 대기 상태로 있도록 합니다.
    """
    logger.info("Seoul Reservation Bot started.")  # 봇 시작을 알리는 초기 로그 메시지

    # 봇이 시작될 때 첫 번째 작업을 즉시 실행합니다. 이는 초기 데이터 동기화에 유용합니다.
    job(fetch_limit=fetch_limit, notify_limit=notify_limit)
    
    # `schedule` 라이브러리를 사용하여 `job` 함수를 10분마다 실행하도록 설정합니다.
    # 이 설정은 `schedule.run_pending()`이 호출될 때마다 확인됩니다.
    schedule.every(10).minutes.do(job, fetch_limit=fetch_limit, notify_limit=notify_limit)

    # 무한 루프를 실행하여 스케줄러가 등록된 작업을 지속적으로 확인하고 실행하도록 합니다.
    while True:
        schedule.run_pending()  # 스케줄에 따라 대기 중인 작업을 실행합니다.
        time.sleep(1)  # CPU 과부하를 방지하기 위해 1초간 대기합니다.


if __name__ == "__main__":
    # `argparse` 모듈을 사용하여 명령줄 인자를 파싱합니다.
    import argparse

    parser = argparse.ArgumentParser(description="서울시 공공서비스 예약 알림 봇")
    parser.add_argument(
        "--fetch_limit",
        type=int,
        default=500,
        help="API에서 가져올 최대 공고 수 (기본값: 500)",
    )
    parser.add_argument(
        "--notify_limit",
        type=int,
        default=30,
        help="텔레그램으로 알림을 보낼 최대 공고 수 (기본값: 30)",
    )
    args = parser.parse_args()

    # main 함수를 호출할 때 파싱된 인자 값을 전달합니다.
    main(fetch_limit=args.fetch_limit, notify_limit=args.notify_limit)
