<p align="center">
  <img src="static/images/emenu.png" alt="Logo eMenu" width="320">
</p>

<h1 align="center">eMenu</h1>

<p align="center">
  Hệ thống quản lý nhà hàng / thu ngân (POS)<br>
  viết bằng <strong>Flask + MySQL + Bootstrap</strong>
</p>

<p align="center">
  <a href="https://github.com/nguyenter/emenu">github.com/nguyenter/emenu</a>
</p>

## Logo

Logo **eMenu** đặt nền đen, chữ hiện đại sans-serif:

- Chữ **e** màu xanh cyan — gợi ý phần mềm / điện tử (*electronic*)
- Chữ **Menu** màu trắng — nhấn mạnh thực đơn và nghiệp vụ nhà hàng

File logo: [`static/images/emenu.png`](static/images/emenu.png)

Logo được dùng làm:

- Thương hiệu trên sidebar / navbar (trang quản lý & thu ngân)
- Trang đăng nhập
- **Favicon** trên tab trình duyệt

## Tính năng chính

### Vai trò

| Role | Mô tả |
|------|--------|
| **ADMIN** | Role cao nhất (chỉ 1 tài khoản): chi nhánh, người dùng, cấu hình PayOS, hàng hóa, nhóm hàng, phòng/bàn, khách hàng, hóa đơn, báo cáo, dashboard |
| **QUAN_LY** | Quản lý chi nhánh: hàng hóa, phòng/bàn, hóa đơn, khách hàng, báo cáo, dashboard; có thể vào màn bán hàng |
| **NHAN_VIEN** | Thu ngân: chọn bàn, gọi món, thanh toán |

> ADMIN **không** có mục “Bán hàng (Thu ngân)” trên menu quản lý. QUAN_LY thì có.

### Quản lý

- **Dashboard**: thống kê tổng quan + doanh thu **hôm nay** (biểu đồ tròn tiền mặt / chuyển khoản)
- Hàng hóa (thêm / sửa / xóa, nhập Excel, định dạng giá có dấu phân cách)
- Nhóm hàng, phòng/bàn, khu vực (**thêm bàn**, **xóa bàn**)
- Khách hàng, hóa đơn, chi nhánh, người dùng
- Báo cáo doanh thu theo **ngày / tuần / tháng / năm**
  - Biểu đồ tròn phương thức thanh toán
  - **Xuất Excel** theo kỳ đang chọn

### Thu ngân (Cashier)

- Giao diện tối ưu mobile (navbar thu gọn, lưới bàn / món 2 cột)
- Chọn bàn → gọi món (tab Món ăn / Đồ uống / Combo)
- Thêm / giảm / xóa món **không reload trang** (AJAX)
- Thêm khách hàng theo số điện thoại (nhận diện khách cũ / mới, mã `KHxxx` dùng chung)
- Thanh toán **Tiền mặt** hoặc **Chuyển khoản**
- **Chuyển khoản + PayOS**: hiển thị QR / link thanh toán; xác nhận thủ công hoặc quay về từ PayOS
- Xuất hóa đơn PDF sau thanh toán
- **Gộp bàn** / **Tách bàn**
- Quay lại bàn trống nếu hóa đơn chưa có món

### Cấu hình PayOS (ADMIN)

1. Đăng nhập ADMIN → menu **Cấu hình PayOS**
2. Nhập **Client ID**, **API Key**, **Checksum Key** (từ [my.payos.vn](https://my.payos.vn))
3. Các ô nhập hiện dạng mật khẩu (dấu chấm / sao)
4. Thu ngân chọn **Thanh toán → Chuyển khoản** → hệ thống tạo QR / link PayOS

Có thể cấu hình qua `.env` (`PAYOS_*`). Giá trị lưu trên giao diện (bảng `cau_hinh`) được ưu tiên hơn.

> **Không commit** Client ID / API Key / Checksum Key. File `.env` đã nằm trong `.gitignore`.

## Công nghệ

| Thành phần | Thư viện |
|------------|----------|
| Web | Flask, Jinja2, Bootstrap 5 |
| ORM / DB | Flask-SQLAlchemy, PyMySQL, MySQL |
| Excel | openpyxl (nhập hàng hóa, xuất báo cáo) |
| PDF | reportlab |
| Thanh toán | payos (SDK chính thức) |
| Biểu đồ | Chart.js |
| Cấu hình | python-dotenv |

Python **3.11+** khuyến nghị.

## Yêu cầu

- Python 3.11+
- MySQL đang chạy
- Database `emenu` (các bảng tương ứng models)
- (Tuỳ chọn) Tài khoản PayOS nếu dùng thanh toán chuyển khoản QR

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

# Tuỳ chọn — hoặc cấu hình trên giao diện ADMIN
PAYOS_CLIENT_ID=
PAYOS_API_KEY=
PAYOS_CHECKSUM_KEY=
```

### Migration (nếu cần)

Chạy lần lượt (an toàn nếu đã chạy trước đó):

```bash
python scripts/migrate_admin_role.py
python scripts/migrate_ban_gop.py
python scripts/migrate_cau_hinh.py
```

| Script | Mục đích |
|--------|----------|
| `migrate_admin_role.py` | Thêm enum `ADMIN` + tạo tài khoản admin mẫu (nếu chưa có) |
| `migrate_ban_gop.py` | Cột `ban_gop` cho gộp bàn |
| `migrate_cau_hinh.py` | Bảng `cau_hinh` lưu cấu hình PayOS |

## Chạy ứng dụng

```bash
python app.py
```

Mở trình duyệt: http://127.0.0.1:5000

## Đăng nhập mẫu (sau khi chạy migrate admin)

| Tài khoản | Mật khẩu | Role |
|-----------|----------|------|
| superadmin | 123456 | ADMIN |

> Đổi mật khẩu ngay sau khi cài đặt. Tài khoản quản lý / nhân viên tạo trong mục **Người dùng** (ADMIN).

## Cấu trúc thư mục

```text
emenu/
├── app.py                      # Routes chính
├── config.py                   # Cấu hình từ .env
├── database.py
├── requirements.txt
├── .env.example                # Mẫu biến môi trường (không chứa secret thật)
├── models/                     # SQLAlchemy models
│   ├── cau_hinh.py             # Cấu hình PayOS (key-value)
│   ├── hoa_don.py, ban.py, ...
├── templates/                  # Jinja2 + Bootstrap
│   ├── layout.html             # Layout quản lý (sidebar / mobile offcanvas)
│   ├── layout_cashier.html     # Layout thu ngân
│   ├── cau_hinh_payos.html
│   ├── chi_tiet_hoa_don.html   # Gọi món (AJAX)
│   └── ...
├── utils/
│   ├── payos_service.py        # Tạo link / kiểm tra thanh toán PayOS
│   ├── xuat_bao_cao_excel.py   # Xuất báo cáo doanh thu
│   ├── nhap_hang_hoa_excel.py
│   ├── hoa_don_pdf.py
│   ├── gop_tach_ban.py
│   └── xoa_an_toan.py          # Xóa có xử lý ràng buộc FK
└── scripts/                    # Migration scripts
```

## Nhập hàng hóa Excel

Cột bắt buộc (dòng 1 là tiêu đề):

- Mã hàng, Tên hàng, Nhóm hàng, Đơn vị tính, Giá bán, Loại thực đơn

Loại thực đơn: `MON_AN` / `DO_UONG` / `COMBO` (hoặc Món ăn / Đồ uống / Combo).

Tải file mẫu tại trang Hàng hóa → **Tải file mẫu**.

## Xuất báo cáo doanh thu

1. Vào **Báo cáo** → chọn kỳ (ngày / tuần / tháng / năm)
2. Bấm **Xuất Excel**
3. File gồm tổng hợp (doanh thu, số HĐ, tiền mặt, CK/QR) và danh sách hóa đơn chi tiết

## Ghi chú bảo mật

- Mật khẩu người dùng hiện lưu **plain text** (phù hợp demo; nên hash khi đưa lên production)
- **Không commit** file `.env` và không đẩy Client ID / API Key / Checksum Key lên Git
- Khóa PayOS trên form cấu hình được ẩn bằng `type="password"`
- Xóa dữ liệu (người dùng, chi nhánh, bàn, hàng hóa, …) dùng luồng xóa an toàn để tránh lỗi khóa ngoại

## Liên kết hữu ích

- Repo: https://github.com/nguyenter/emenu
- PayOS merchant: https://my.payos.vn
- PayOS Python SDK: https://github.com/payOSHQ/payos-lib-python
