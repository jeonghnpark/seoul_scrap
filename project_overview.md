# 서울시 공공서비스 예약 알림 봇: 프로젝트 구조 및 흐름

이 문서는 서울시 공공서비스 예약 알림 봇의 전체적인 구조와 데이터 흐름을 설명합니다. 각 구성 요소의 역할과 주요 코드 스니펫을 통해 애플리케이션의 작동 방식을 구체적으로 이해할 수 있습니다.

## 1. 프로젝트 개요

- **목표**: 서울시 공공서비스 예약 정보를 주기적으로 수집하고, 새로 올라온 예약 정보를 텔레그램으로 실시간에 가깝게 알림.
- **기술 스택**: Python 3.x, `requests`, `python-telegram-bot`, `schedule`, `python-dotenv`, SQLite.
- **실행 환경**: 로컬 PC (Windows 권장).

## 2. 프로젝트 구조

프로젝트는 다음과 같은 파일들로 구성되어 있습니다.

```
seoul_scrap/
├── .env                # API Key, Telegram Token 등 민감 정보 저장 (환경 변수)
├── main.py             # 메인 실행 파일 및 스케줄러 (전체 흐름 제어)
├── scraper.py          # 서울시 API 호출 및 예약 정보 수집/파싱
├── notifier.py         # 텔레그램 알림 메시지 전송
├── storage.py          # SQLite 데이터베이스 관리 (중복 알림 방지)
├── requirements.txt    # 의존성 패키지 목록
├── README.md           # 프로젝트 설명서 및 사용법
└── .gitignore          # Git 버전 관리에서 제외할 파일 목록
```

## 3. 전체 애플리케이션 흐름 (데이터 파이프라인)

서울시 공공서비스 예약 알림 봇의 핵심 흐름은 주기적인 데이터 수집, 중복 필터링, 그리고 알림 전송으로 구성됩니다. 이는 `main.py` 파일의 `job()` 함수 내에서 제어됩니다.

```mermaid
graph TD
    A[시작: `main.py` 실행] --> B(초기 설정: 로깅, 환경 변수 로드)
    B --> C{10분마다 `job()` 함수 실행}
    C --> D[1. 데이터 수집: `scraper.py` 호출]
    D --> E[2. 데이터 저장소 확인: `storage.py` 호출]
    E --> F{새로운 예약 정보인가?}
    F -- Yes --> G[3. 알림 전송: `notifier.py` 호출]
    G --> H[4. 데이터 저장: `storage.py`에 예약 ID 기록]
    F -- No --> C
    H --> C
```

### 상세 흐름 설명 및 주요 코드

#### 3.1. 환경 변수 로드 (`.env` 파일)

애플리케이션은 민감한 정보(API 키, 텔레그램 토큰, 채팅 ID)를 `.env` 파일에 저장하고 `python-dotenv` 라이브러리를 사용하여 로드합니다. 이는 코드를 직접 수정하지 않고도 설정을 변경할 수 있게 하며, 버전 관리 시스템에 민감 정보가 노출되는 것을 방지합니다.

```python:5:e:\dev\seoul_scrap\main.py
load_dotenv()
```

#### 3.2. 주기적인 작업 스케줄링 (`main.py`)

`main.py`는 `schedule` 라이브러리를 사용하여 `job()` 함수를 정해진 시간(예: 10분)마다 실행하도록 스케줄링합니다. `main()` 함수는 봇의 시작점이며, 무한 루프를 통해 스케줄러가 계속해서 작업을 확인할 수 있도록 합니다.

```python:100:e:\dev\seoul_scrap\main.py
    schedule.every(10).minutes.do(job)
    
    while True:
        schedule.run_pending()
        time.sleep(1)
```

#### 3.3. 데이터 수집 (`scraper.py`)

`Scraper` 클래스는 서울 열린데이터광장 API와 통신하여 공공서비스 예약 정보를 가져옵니다. 여러 서비스 유형(체육시설, 시설대관 등)에 대한 데이터를 순회하며 수집하고, 각 응답에서 필요한 필드(서비스 ID, 이름, 장소, URL 등)를 추출하여 표준화된 딕셔너리 형태로 반환합니다.

```python:22:e:\dev\seoul_scrap\scraper.py
    def fetch_new_reservations(self):
        """
        서울시 공공서비스 예약 API에서 새로운 예약 정보를 가져옵니다.
        각 서비스 유형별로 최대 100건의 최신 데이터를 조회하며,
        API 호출 중 발생할 수 있는 네트워크 오류나 데이터 파싱 오류를 처리합니다.
        """
        all_reservations = []
        
        for service in self.SERVICES:
            try:
                url = f"{self.BASE_URL}/{self.api_key}/json/{service}/1/100/"
                response = requests.get(url)
                response.raise_for_status()
                
                data = response.json()
                
                if service in data and "row" in data[service]:
                    rows = data[service]["row"]
                    for row in rows:
                        reservation = self._parse_row(row, service)
                        all_reservations.append(reservation)
                        
            except requests.exceptions.RequestException as e:
                print(f"Error fetching {service}: {e}")
            except Exception as e:
                print(f"Unexpected error processing {service}: {e}")
                
        return all_reservations
```

#### 3.4. 데이터 중복 확인 및 저장 (`storage.py`)

`Storage` 클래스는 SQLite 데이터베이스를 관리하여 이전에 알림을 보낸 예약의 `svc_id`를 기록합니다. `is_seen()` 메서드를 통해 새로운 예약인지 확인하고, `add_seen()` 메서드를 통해 새로운 예약 ID를 데이터베이스에 추가하여 중복 알림을 방지합니다.

```python:24:e:\dev\seoul_scrap\storage.py
    def is_seen(self, svc_id):
        """
        특정 서비스 ID(`svc_id`)가 이미 데이터베이스의 `seen_reservations` 테이블에
        저장되어 있는지 확인합니다. 이 함수는 새로운 예약인지 판단하는 핵심 로직입니다.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM seen_reservations WHERE svc_id = ?', (svc_id,))
            return cursor.fetchone() is not None

    def add_seen(self, svc_id):
        """
        새로운 서비스 ID(`svc_id`)를 `seen_reservations` 테이블에 추가합니다.
        만약 동일한 `svc_id`가 이미 존재한다면 Primary Key 제약 조건 위반으로
        `sqlite3.IntegrityError`가 발생하며, 이는 중복 추가 시도를 방지합니다.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    'INSERT INTO seen_reservations (svc_id, created_at) VALUES (?, ?)',
                    (svc_id, datetime.now())
                )
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False
```

#### 3.5. 텔레그램 알림 전송 (`notifier.py`)

`Notifier` 클래스는 `python-telegram-bot` 라이브러리를 사용하여 텔레그램으로 메시지를 전송합니다. `format_message()` 메서드는 수집된 예약 정보를 가독성 좋은 텍스트 형식으로 변환하고, `send_message()` 메서드는 실제 메시지 전송을 담당합니다. 비동기(`asyncio`)로 구현되어 메시지 전송 중에도 다른 작업을 수행할 수 있도록 합니다.

```python:21:e:\dev\seoul_scrap\notifier.py
    async def send_message(self, message):
        """
        지정된 `chat_id`로 텔레그램 메시지를 비동기적으로 전송합니다.
        메시지 전송 실패 시 `TelegramError`를 처리하여 프로그램의 안정성을 높입니다.
        """
        try:
            await self.bot.send_message(chat_id=self.chat_id, text=message)
            return True
        except TelegramError as e:
            print(f"Failed to send message: {e}")
            return False

    def format_message(self, reservation):
        """
        주어진 예약 정보(딕셔너리)를 텔레그램 메시지에 적합하고 가독성 좋은 형식으로 포맷팅합니다.
        사용자에게 중요한 정보(제목, 장소, 접수 기간, 링크 등)를 명확하게 전달하는 데 중점을 둡니다.
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
```

## 4. 실행 방법

1.  **환경 변수 설정**: `.env` 파일에 `SEOUL_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`를 올바르게 설정합니다.
2.  **의존성 설치**: `pip install -r requirements.txt` 명령어로 필요한 라이브러리를 설치합니다.
3.  **봇 실행**: `python main.py` 명령어로 봇을 실행합니다.

이 문서를 통해 프로젝트의 전체적인 구조와 흐름을 이해하는 데 도움이 되기를 바랍니다. 궁금한 점이 있으시면 언제든지 질문해주세요.