# 서울시 공공서비스 예약 알림 봇

서울시 공공서비스 예약 정보를 주기적으로 확인하여 새로운 예약이 올라오면 텔레그램으로 알림을 보내는 봇입니다.

## 설치 및 실행

1. 필요한 라이브러리 설치
   ```bash
   pip install -r requirements.txt
   ```

2. `.env` 파일 설정
   - `SEOUL_API_KEY`: 서울 열린데이터광장 API 키
   - `TELEGRAM_BOT_TOKEN`: 텔레그램 봇 토큰
   - `TELEGRAM_CHAT_ID`: 알림 받을 채팅방 ID

3. 실행
   ```bash
   python main.py
   ```
