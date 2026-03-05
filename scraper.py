import requests
import os
from dotenv import load_dotenv

# .env 파일에서 환경 변수를 로드합니다.
# 이 함수를 호출하여 API 키와 같은 민감한 정보들을 코드에 직접 노출시키지 않고
# 환경 변수에서 안전하게 가져올 수 있도록 합니다.
load_dotenv()


class Scraper:
    # 서울시 공공서비스 예약 API의 기본 URL을 정의합니다.
    BASE_URL = "http://openAPI.seoul.go.kr:8088"
    # 조회할 공공서비스 유형 목록을 정의합니다.
    # 각 문자열은 API 엔드포인트의 서비스명에 해당합니다.
    SERVICES = [
        "ListPublicReservationSport",  # 체육시설 예약 정보 조회
        "ListPublicReservationInstitution",  # 시설대관 예약 정보 조회
        "ListPublicReservationEducation",  # 교육강좌 예약 정보 조회
        "ListPublicReservationCulture",  # 문화행사 예약 정보 조회
        "ListPublicReservationMedical",  # 진료복지 예약 정보 조회
    ]

    # 각 서비스 유형별로 선택적으로 가져올 카테고리 목록을 정의합니다.
    # 이 딕셔너리를 수정하여 원하는 카테고리만 필터링할 수 있습니다.
    # 모든 카테고리를 가져오려면 해당 서비스 유형을 딕셔너리에서 제거하거나 빈 리스트로 설정하세요.
    SELECTED_CATEGORIES = {
        "ListPublicReservationCulture": [
            "문화행사",
            "전시/관람",
        ],  # 문화행사 서비스에서 선택
        "ListPublicReservationEducation": [
            "공예/취미",
            "자연/과학",
        ],  # 교육강좌 서비스에서 선택
    }

    def __init__(self):
        # .env 파일에서 서울시 API 키를 가져옵니다.
        # 이 키는 서울 열린데이터광장에서 발급받은 개인 인증키입니다.
        self.api_key = os.getenv("SEOUL_API_KEY")
        # API 키가 환경 변수에 설정되지 않았다면 명확한 에러 메시지를 발생시킵니다.
        # 이는 `.env` 파일 설정이 누락되었을 때 조기에 문제를 파악하는 데 도움을 줍니다.
        if not self.api_key:
            raise ValueError("SEOUL_API_KEY is not set in .env file")

    def fetch_new_reservations(self, fetch_limit=100):
        """
        서울시 공공서비스 예약 API에서 새로운 예약 정보를 가져옵니다.
        각 서비스 유형별로 최대 fetch_limit 건의 최신 데이터를 조회하며,
        API 호출 중 발생할 수 있는 네트워크 오류나 데이터 파싱 오류를 처리합니다.
        """
        all_reservations = []  # 모든 서비스 유형에서 가져온 예약 정보를 저장할 리스트

        # 정의된 모든 서비스 유형(체육시설, 시설대관 등)에 대해 반복합니다.
        for service in self.SERVICES:
            try:
                # API 요청 URL을 구성합니다.
                # {KEY}는 발급받은 API 키, {SERVICE}는 각 서비스 유형 이름,
                # 1/fetch_limit은 시작 인덱스와 끝 인덱스로, 보통 최신 fetch_limit 건을 의미합니다.
                # API 문서에 따라 이 숫자는 달라질 수 있습니다.
                url = f"{self.BASE_URL}/{self.api_key}/json/{service}/1/{fetch_limit}/"
                # 구성된 URL로 서울시 API에 GET 요청을 보냅니다.
                response = requests.get(url)
                # HTTP 요청이 성공했는지 (상태 코드 200번대) 확인하고,
                # 실패 시 `requests.exceptions.HTTPError` 예외를 발생시킵니다.
                response.raise_for_status()

                # API 응답(JSON 형식)을 Python 딕셔너리로 파싱합니다.
                data = response.json()

                # 응답 데이터에 현재 서비스명(예: ListPublicReservationSport) 키가 있고,
                # 그 안에 실제 데이터 목록을 포함하는 "row" 키가 있는지 확인합니다.
                # API 응답 구조가 특정 서비스에서 다를 수 있으므로 안전하게 접근합니다.
                if service in data and "row" in data[service]:
                    rows = data[service]["row"]  # 실제 예약 정보 리스트를 가져옵니다.
                    # 각 예약 정보(row)를 파싱하여 `all_reservations` 리스트에 추가합니다.
                    for row in rows:
                        reservation = self._parse_row(
                            row, service
                        )  # 헬퍼 함수로 데이터 정제

                        # 특정 서비스 유형에 대해 카테고리 필터링 적용
                        if reservation.get("state") != "예약마감":
                            if service in self.SELECTED_CATEGORIES:
                                # 해당 서비스 유형에 대한 선택 카테고리 목록이 있고,
                                # 현재 예약의 카테고리가 해당 목록에 포함될 경우에만 추가합니다.
                                if (
                                    reservation.get("category")
                                    in self.SELECTED_CATEGORIES[service]
                                ):
                                    all_reservations.append(reservation)
                            # else:  # 체육시설 카테고리 문제제
                            #     # SELECTED_CATEGORIES에 없는 서비스 유형은 모든 카테고리를 가져옵니다.
                            #     all_reservations.append(reservation)

            except requests.exceptions.RequestException as e:
                # 네트워크 연결 문제, 타임아웃 등 `requests` 라이브러리 관련 예외 처리
                # 어떤 서비스에서 오류가 발생했는지 명시하여 디버깅에 도움을 줍니다.
                print(f"Error fetching {service}: {e}")
            except Exception as e:
                # JSON 파싱 오류나 기타 예상치 못한 오류에 대한 일반적인 예외 처리
                print(f"Unexpected error processing {service}: {e}")

        return all_reservations  # 모든 서비스에서 수집된 예약 정보 리스트 반환

    def _parse_row(self, row, service_type):
        """
        API 응답의 단일 row(딕셔너리)에서 필요한 정보만 추출하여
        표준화된 딕셔너리 형태로 반환합니다.
        `row.get(key, default_value)`를 사용하여 키가 없을 경우 `None` 대신 기본값을 반환하여
        `KeyError`를 방지하고 코드 안정성을 높입니다.
        """
        return {
            "svc_id": row.get("SVCID"),  # 서비스 고유 ID (예: S220310172740589179)
            "svc_name": row.get("SVCNM"),  # 서비스 명칭 (예: 테니스장1(평일)-2026년)
            "place_name": row.get(
                "PLACENM"
            ),  # 서비스 제공 장소 (예: 응봉공원(대현산배수지))
            "service_type": service_type,
            "category": row.get("MINCLASSNM"),  # 서비스 소분류 카테고리 (예: 테니스)
            "url": row.get("SVCURL"),  # 서비스 바로가기 URL
            "rcpt_bgndt": row.get("RCPTBGNDT"),  # 접수 시작 일시 (예: 2026-02-01 09:00)
            "rcpt_enddt": row.get("RCPTENDDT"),  # 접수 종료 일시 (예: 2026-02-28 18:00)
            "use_bgndt": row.get("USEBGNDT"),  # 이용 시작 일시
            "use_enddt": row.get("USEENDDT"),  # 이용 종료 일시
            "state": row.get("SVCSTATNM"),  # 서비스 상태 (예: 접수중, 접수종료, 안내중)
        }


if __name__ == "__main__":
    # 이 스크립트가 직접 실행될 때만 동작하는 테스트 코드 블록입니다.
    # Scraper 클래스의 기능을 개별적으로 검증할 때 유용합니다.
    try:
        scraper = Scraper()  # Scraper 객체 생성
        reservations = scraper.fetch_new_reservations()  # 예약 정보 가져오기
        print(f"Fetched {len(reservations)} reservations.")  # 가져온 예약 개수 출력
        if reservations:  # 예약 정보가 있다면 첫 번째 샘플을 출력합니다.
            print("Sample:", reservations[0])
    except Exception as e:
        print(f"Setup error: {e}")  # 설정 오류 발생 시 에러 메시지 출력
