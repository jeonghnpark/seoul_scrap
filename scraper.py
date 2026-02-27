import requests
import os
from dotenv import load_dotenv

load_dotenv()

class Scraper:
    BASE_URL = "http://openAPI.seoul.go.kr:8088"
    SERVICES = [
        "ListPublicReservationSport",       # 체육시설
        "ListPublicReservationInstitution", # 시설대관
        "ListPublicReservationEducation",   # 교육강좌
        "ListPublicReservationCulture",     # 문화행사
        "ListPublicReservationMedical"      # 진료복지
    ]

    def __init__(self):
        self.api_key = os.getenv("SEOUL_API_KEY")
        if not self.api_key:
            raise ValueError("SEOUL_API_KEY is not set in .env file")

    def fetch_new_reservations(self):
        all_reservations = []
        
        for service in self.SERVICES:
            try:
                # 1부터 100까지 조회 (최신순으로 정렬되어 있다고 가정하거나, 전체를 가져와서 필터링)
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

    def _parse_row(self, row, service_type):
        """
        API 응답 row에서 필요한 정보만 추출
        """
        return {
            "svc_id": row.get("SVCID"),
            "svc_name": row.get("SVCNM"),
            "place_name": row.get("PLACENM"),
            "service_type": service_type,
            "category": row.get("MINCLASSNM"),
            "url": row.get("SVCURL"),
            "rcpt_bgndt": row.get("RCPTBGNDT"),
            "rcpt_enddt": row.get("RCPTENDDT"),
            "use_bgndt": row.get("USEBGNDT"),
            "use_enddt": row.get("USEENDDT"),
            "state": row.get("SVCSTATNM") # 접수중, 접수종료, 안내중 등
        }

if __name__ == "__main__":
    # 테스트 코드
    try:
        scraper = Scraper()
        reservations = scraper.fetch_new_reservations()
        print(f"Fetched {len(reservations)} reservations.")
        if reservations:
            print("Sample:", reservations[0])
    except Exception as e:
        print(f"Setup error: {e}")
