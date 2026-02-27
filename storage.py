import sqlite3
import os
from datetime import datetime

class Storage:
    def __init__(self, db_path='reservations.db'):
        self.db_path = db_path
        self.create_table()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def create_table(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS seen_reservations (
                    svc_id TEXT PRIMARY KEY,
                    created_at DATETIME
                )
            ''')
            conn.commit()

    def is_seen(self, svc_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM seen_reservations WHERE svc_id = ?', (svc_id,))
            return cursor.fetchone() is not None

    def add_seen(self, svc_id):
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
