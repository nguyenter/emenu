"""Tạo bảng cau_hinh để lưu Client ID / API Key / Checksum Key PayOS."""

import os
import sys

from dotenv import load_dotenv
import pymysql

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
load_dotenv(os.path.join(ROOT, '.env'))


def main():
    conn = pymysql.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 3306)),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'emenu'),
        charset='utf8mb4',
    )
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS cau_hinh (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    khoa VARCHAR(100) NOT NULL UNIQUE,
                    gia_tri TEXT NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )
        conn.commit()
        print('OK: bang cau_hinh da san sang.')
    finally:
        conn.close()


if __name__ == '__main__':
    main()
