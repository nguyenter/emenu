# eMenu

Hệ thống quản lý nhà hàng / thu ngân (POS) viết bằng **Flask + MySQL + Bootstrap**.

Repository: https://github.com/nguyenter/emenu

## Tính năng chính

### Vai trò
| Role | Mô tả |
|------|--------|
| **ADMIN** | Role cao nhất (chỉ 1 tài khoản): chi nhánh, người dùng, hàng hóa, nhóm hàng, khách hàng, hóa đơn, báo cáo |
| **QUAN_LY** | Quản lý chi nhánh: hàng hóa, phòng/bàn, hóa đơn, khách hàng, báo cáo; có thể vào màn bán hàng |
| **NHAN_VIEN** | Thu ngân: chọn bàn, gọi món, thanh toán |

### Quản lý
- Hàng hóa (thêm/sửa/xóa, nhập Excel)
- Nhóm hàng, phòng/bàn, khu vực
- Khách hàng, hóa đơn, chi nhánh, người dùng
- Báo cáo doanh thu theo ngày / tuần / tháng / năm + biểu đồ tròn

### Thu ngân (Cashier)
- Chọn bàn, gọi món (giữ tab Món ăn / Đồ uống / Combo)
- Thêm khách hàng theo số điện thoại (nhận diện khách cũ/mới)
- Thanh toán **Tiền mặt** hoặc **Chuyển khoản** (PayOS: QR / link thanh toán)
- Xuất hóa đơn PDF sau thanh toán
- **Gộp bàn** / **Tách bàn**

### Cấu hình PayOS (ADMIN)
- Menu **Cấu hình PayOS**: nhập Client ID, API Key, Checksum Key
- Khi thu ngân chọn **Chuyển khoản**, hệ thống tạo QR / link PayOS
## Công nghệ

- Python 3.11+
- Flask, Flask-SQLAlchemy, Jinja2
- MySQL (PyMySQL)
- Bootstrap 5, Chart.js
- openpyxl (nhập Excel), reportlab (PDF)

## Yêu cầu

- Python 3.11+
- MySQL đang chạy
- Database `emenu` (các bảng tương ứng models)

## Cài đặt

```bash
git clone https://github.com/nguyenter/emenu.git
cd emenu
pip install -r requirements.txt
```

Tạo file `.env` từ mẫu:

```bash
copy .env.example .env
```

Chỉnh `.env`:

```env
SECRET_KEY=your_secret_key_here
DB_HOST=localhost
DB_PORT=3306
DB_NAME=emenu
DB_USER=root
DB_PASSWORD=your_password_here
PAYOS_CLIENT_ID=
PAYOS_API_KEY=
PAYOS_CHECKSUM_KEY=
```

> PayOS cũng có thể cấu hình trên giao diện ADMIN → **Cấu hình PayOS** (ưu tiên hơn `.env`).

### Migration (nếu cần)

```bash
python scripts/migrate_admin_role.py
python scripts/migrate_ban_gop.py
python scripts/migrate_cau_hinh.py
```

- `migrate_admin_role.py`: thêm enum `ADMIN` + tạo tài khoản admin mẫu (nếu chưa có)
- `migrate_ban_gop.py`: thêm cột `ban_gop` cho tính năng gộp bàn
- `migrate_cau_hinh.py`: bảng lưu cấu hình PayOS

## Chạy ứng dụng

```bash
python app.py
```

Mở trình duyệt: http://127.0.0.1:5000

## Đăng nhập mẫu (sau khi chạy migrate admin)

| Tài khoản | Mật khẩu | Role |
|-----------|----------|------|
| superadmin | 123456 | ADMIN |

> Đổi mật khẩu ngay sau khi cài đặt. Tài khoản quản lý / nhân viên tạo trong mục Người dùng (ADMIN).

## Cấu trúc thư mục

```text
emenu/
├── app.py                 # Routes chính
├── config.py              # Cấu hình từ .env
├── database.py
├── requirements.txt
├── .env.example
├── models/                # SQLAlchemy models
├── templates/             # Jinja2 + Bootstrap
├── utils/                 # PDF, Excel, gộp/tách bàn, xóa an toàn
└── scripts/               # Migration scripts
```

## Nhập hàng hóa Excel

Cột bắt buộc (dòng 1 là tiêu đề):

- Mã hàng, Tên hàng, Nhóm hàng, Đơn vị tính, Giá bán, Loại thực đơn

Loại thực đơn: `MON_AN` / `DO_UONG` / `COMBO` (hoặc Món ăn / Đồ uống / Combo).

Tải file mẫu tại trang Hàng hóa → **Tải file mẫu**.

## Ghi chú

- Mật khẩu hiện lưu plain text (phù hợp demo; nên hash khi đưa lên production)
- Không commit file `.env` (đã có trong `.gitignore`)
