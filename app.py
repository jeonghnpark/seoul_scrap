import asyncio
import logging
import webbrowser
import threading
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS

from scraper import Scraper
from storage import Storage
from notifier import Notifier

# 로깅 설정
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Flask 애플리케이션 생성
app = Flask(__name__)
CORS(app)  # CORS 허용


class ReservationBot:
    """서울시 예약 알림 봇의 핵심 로직을 담은 클래스"""
    
    def __init__(self):
        self.scraper = Scraper()
        self.storage = Storage()
        self.notifier = Notifier()
    
    async def send_notifications(self, fetch_limit=500, notify_limit=30):
        """
        예약 정보를 가져와서 텔레그램으로 알림을 전송하는 메인 로직
        
        Args:
            fetch_limit (int): API에서 가져올 최대 공고 수
            notify_limit (int): 텔레그램으로 알림을 보낼 최대 공고 수
            
        Returns:
            dict: 실행 결과 정보
        """
        try:
            logger.info("Starting notification job...")
            
            # 1. 서울시 API에서 예약 정보 가져오기
            reservations = self.scraper.fetch_new_reservations(fetch_limit=fetch_limit)
            logger.info(f"Fetched {len(reservations)} reservations.")
            
            if not reservations:
                return {
                    'success': True,
                    'message': '가져온 예약 정보가 없습니다.',
                    'total_fetched': 0,
                    'new_notifications': 0
                }
            
            # 2. 예약 정보 처리 및 알림 전송
            new_count = await self._process_reservations(reservations, notify_limit)
            
            result = {
                'success': True,
                'message': f'성공적으로 완료되었습니다. 새로운 알림 {new_count}개를 전송했습니다.',
                'total_fetched': len(reservations),
                'new_notifications': new_count
            }
            
            logger.info(f"Job completed. Sent {new_count} new notifications.")
            return result
            
        except Exception as e:
            error_msg = f"알림 전송 중 오류가 발생했습니다: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'message': error_msg,
                'total_fetched': 0,
                'new_notifications': 0
            }
    
    async def _process_reservations(self, reservations, notify_limit):
        """예약 정보를 처리하고 텔레그램 알림을 전송"""
        new_count = 0
        today = datetime.now().strftime("%Y-%m-%d")
        
        # 접수 시작일이 있는 데이터만 필터링
        valid_reservations = [r for r in reservations if r.get('rcpt_bgndt')]
        logger.info(f"유효한 예약: {len(valid_reservations)}개")
        
        # 데이터를 과거/미래로 분류
        future_reservations = []  # 오늘 포함 이후 접수 시작
        past_reservations = []    # 오늘 이전 접수 시작
        
        for r in valid_reservations:
            rcpt_date = r.get('rcpt_bgndt', '')[:10]
            if rcpt_date >= today:
                future_reservations.append(r)
            else:
                past_reservations.append(r)
        
        logger.info(f"과거 예약: {len(past_reservations)}개, 미래 예약: {len(future_reservations)}개")
        
        # 정렬: 과거는 오름차순, 미래는 내림차순
        past_reservations.sort(key=lambda x: x.get('rcpt_bgndt', ''))
        future_reservations.sort(key=lambda x: x.get('rcpt_bgndt', ''), reverse=True)
        
        # 최종 처리 순서: [과거] + [미래]
        sorted_reservations = past_reservations + future_reservations
        
        # notify_limit 개수만큼만 추출 (우선순위 높은 것들)
        if len(sorted_reservations) > notify_limit:
            sorted_reservations = sorted_reservations[-notify_limit:]
        
        logger.info(f"처리할 예약: {len(sorted_reservations)}개")
        
        # 각 예약 정보에 대해 알림 전송
        for idx, reservation in enumerate(sorted_reservations, 1):
            svc_id = reservation["svc_id"]
            svc_name = reservation.get("svc_name", "알 수 없음")
            
            logger.debug(f"[{idx}/{len(sorted_reservations)}] 처리 중: {svc_name} (ID: {svc_id})")
            
            if not self.storage.is_seen(svc_id):
                logger.info(f"새 예약 발견: {svc_name}")
                
                try:
                    message = self.notifier.format_message(reservation)
                    logger.debug(f"메시지 포맷팅 완료")
                    
                    if await self.notifier.send_message(message):
                        self.storage.add_seen(svc_id)
                        new_count += 1
                        logger.info(f"✓ [{new_count}] {svc_name} 알림 전송 성공")
                        await asyncio.sleep(1)  # Rate limiting
                    else:
                        logger.error(f"✗ {svc_name} 알림 전송 실패")
                except Exception as e:
                    logger.error(f"메시지 처리 중 오류 - {svc_name}: {type(e).__name__} - {str(e)}")
            else:
                logger.debug(f"이미 본 예약: {svc_name}")
        
        return new_count


# 전역 봇 인스턴스
bot = ReservationBot()


@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')


@app.route('/api/send-notifications', methods=['POST'])
def send_notifications():
    """텔레그램 알림 전송 API"""
    try:
        # 요청에서 파라미터 가져오기
        data = request.get_json() or {}
        fetch_limit = data.get('fetch_limit', 500)
        notify_limit = data.get('notify_limit', 30)
        
        # 비동기 함수를 동기적으로 실행
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            bot.send_notifications(fetch_limit=fetch_limit, notify_limit=notify_limit)
        )
        loop.close()
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"API error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'서버 오류가 발생했습니다: {str(e)}',
            'total_fetched': 0,
            'new_notifications': 0
        }), 500


@app.route('/api/status')
def status():
    """서버 상태 확인 API"""
    return jsonify({
        'status': 'running',
        'timestamp': datetime.now().isoformat()
    })


def open_browser():
    """브라우저를 자동으로 열기"""
    webbrowser.open('http://localhost:5000')


if __name__ == '__main__':
    print("서울시 예약 알림 봇 웹 서버를 시작합니다...")
    print("브라우저가 자동으로 열립니다. 열리지 않으면 http://localhost:5000 으로 접속하세요.")
    
    # 1초 후에 브라우저 열기
    threading.Timer(1.0, open_browser).start()
    
    # Flask 서버 실행
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)