"""Cập nhật enum vai_tro + tạo 1 tài khoản ADMIN nếu chưa có."""
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

cur.execute(
    "ALTER TABLE nguoi_dung "
    "MODIFY COLUMN vai_tro ENUM('ADMIN','QUAN_LY','NHAN_VIEN') NOT NULL"
)
conn.commit()
print('Updated vai_tro enum')

cur.execute("SELECT COUNT(*) FROM nguoi_dung WHERE vai_tro='ADMIN'")
count = cur.fetchone()[0]

if count == 0:
    cur.execute('SELECT id FROM chi_nhanh ORDER BY id LIMIT 1')
    row = cur.fetchone()
    cn_id = row[0] if row else 1

    cur.execute(
        "SELECT id FROM nguoi_dung WHERE ten_dang_nhap=%s",
        ('superadmin',),
    )
    exists = cur.fetchone()

    if exists:
        cur.execute(
            "UPDATE nguoi_dung SET vai_tro='ADMIN', trang_thai=1 WHERE id=%s",
            (exists[0],),
        )
        print('Updated existing superadmin -> ADMIN')
    else:
        cur.execute(
            "INSERT INTO nguoi_dung "
            "(ten_dang_nhap, mat_khau, ho_ten, vai_tro, chi_nhanh_id, trang_thai) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            ('superadmin', '123456', 'Administrator', 'ADMIN', cn_id, 1),
        )
        print('Created ADMIN: superadmin / 123456')
    conn.commit()
else:
    print(f'ADMIN already exists: {count}')

cur.execute('SELECT id, ten_dang_nhap, vai_tro FROM nguoi_dung')
for row in cur.fetchall():
    print(row)

conn.close()
