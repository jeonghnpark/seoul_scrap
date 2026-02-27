import sqlite3
import os
from datetime import datetime

class Storage:
    def __init__(self, db_path='reservations.db'):
        # SQLite 데이터베이스 파일 경로를 설정합니다. 이 파일은 중복 알림을 방지하기 위해
        # 이미 텔레그램으로 전송된 예약 정보의 ID를 저장하는 데 사용됩니다.
        self.db_path = db_path
        # Storage 객체 초기화 시 데이터베이스 테이블이 존재하지 않으면 생성합니다.
        self.create_table()

    def get_connection(self):
        """
        SQLite 데이터베이스 연결 객체를 반환합니다.
        이 메서드는 데이터베이스 작업 시마다 호출되어 연결을 얻습니다.
        """
        return sqlite3.connect(self.db_path)

    def create_table(self):
        """
        'seen_reservations' 테이블을 생성합니다. 만약 테이블이 이미 존재한다면
        이 작업은 무시됩니다 (IF NOT EXISTS 절 사용). 이는 스크립트 재실행 시
        데이터 손실을 방지하고 안정성을 높입니다.
        
        - `svc_id`: 서비스 고유 ID. Primary Key로 설정되어 중복 저장을 자동으로 방지합니다.
        - `created_at`: 해당 예약 정보가 데이터베이스에 추가된 일시를 기록합니다.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS seen_reservations (
                    svc_id TEXT PRIMARY KEY,    -- 서비스 고유 ID (중복 방지를 위한 기본 키)
                    created_at DATETIME         -- 데이터가 저장된 시간 기록
                )
            ''')
            conn.commit() # 데이터베이스에 대한 변경사항을 영구적으로 저장합니다.

    def is_seen(self, svc_id):
        """
        특정 서비스 ID(`svc_id`)가 이미 데이터베이스의 `seen_reservations` 테이블에
        저장되어 있는지 확인합니다. 이 함수는 새로운 예약인지 판단하는 핵심 로직입니다.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # `svc_id`를 기준으로 레코드가 존재하는지 효율적으로 조회합니다.
            # `SELECT 1`은 특정 값을 가져오는 대신 단순히 레코드 존재 여부만 확인하여 성능상 이점이 있습니다.
            cursor.execute('SELECT 1 FROM seen_reservations WHERE svc_id = ?', (svc_id,))
            # `fetchone()` 결과가 `None`이 아니라면, 해당 `svc_id`가 이미 존재함을 의미합니다.
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
                # 서비스 ID와 현재 시간을 데이터베이스에 삽입합니다.
                # `datetime.now()`는 현재 시각을 기록하여 언제 데이터가 추가되었는지 알 수 있게 합니다.
                cursor.execute(
                    'INSERT INTO seen_reservations (svc_id, created_at) VALUES (?, ?)',
                    (svc_id, datetime.now())
                )
                conn.commit() # 변경사항을 데이터베이스에 반영합니다.
                return True # 추가 성공 시 True 반환
            except sqlite3.IntegrityError:
                # Primary Key 제약 조건 위반 (중복) 시 False 반환. 오류가 아니므로 메시지는 출력하지 않습니다.
                return False