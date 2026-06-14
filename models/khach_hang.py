from database import db


class KhachHang(db.Model):
    __tablename__ = 'khach_hang'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    ma_khach_hang = db.Column(
        db.String(50),
        unique=True
    )

    ten_khach_hang = db.Column(
        db.String(100),
        nullable=False
    )

    dien_thoai = db.Column(
        db.String(20)
    )

    gioi_tinh = db.Column(
        db.Enum(
            'NAM',
            'NU',
            'KHAC'
        )
    )

    ngay_sinh = db.Column(
        db.Date
    )

    dia_chi = db.Column(
        db.String(255)
    )

    tinh_thanh = db.Column(
        db.String(100)
    )

    phuong_xa = db.Column(
        db.String(100)
    )

    ghi_chu = db.Column(
        db.Text
    )

    chi_nhanh_id = db.Column(
        db.Integer,
        nullable=False
    )