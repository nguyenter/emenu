"""Thêm cột ban_gop vào bảng hoa_don."""
from dotenv import load_dotenv
import os
import pymysql

load_dotenv()

conn = pymysql.connect(
    host=os.getenv('DB_HOST'),
    port=int(os.getenv('DB_PORT')),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME'),
    charset='utf8mb4',
)
cur = conn.cursor()

cur.execute("SHOW COLUMNS FROM hoa_don LIKE 'ban_gop'")
if cur.fetchone():
    print('Column ban_gop already exists')
else:
    cur.execute(
        "ALTER TABLE hoa_don "
        "ADD COLUMN ban_gop VARCHAR(255) NULL "
        "AFTER chi_nhanh_id"
    )
    conn.commit()
    print('Added column ban_gop')

conn.close()
