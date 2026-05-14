import sqlite3
from datetime import datetime

db_path = "reservations.db"
today = datetime.now().strftime("%Y-%m-%d")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 오늘 저장된 데이터 삭제
cursor.execute("DELETE FROM seen_reservations WHERE DATE(created_at) = ?", (today,))

deleted_count = cursor.rowcount
conn.commit()
conn.close()

print(f"✓ {deleted_count}개의 오늘 데이터 삭제 완료")
