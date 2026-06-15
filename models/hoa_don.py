from database import db


class HoaDon(db.Model):
    __tablename__ = 'hoa_don'

    id = db.Column(db.Integer, primary_key=True)

    ma_hoa_don = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    ban_id = db.Column(
        db.Integer,
        db.ForeignKey('ban.id')
    )

    khach_hang_id = db.Column(
        db.Integer,
        db.ForeignKey('khach_hang.id')
    )

    nguoi_dung_id = db.Column(
        db.Integer,
        db.ForeignKey('nguoi_dung.id'),
        nullable=False
    )

    tong_tien = db.Column(
        db.Numeric(15, 2),
        default=0
    )

    phuong_thuc_thanh_toan = db.Column(
        db.Enum(
            'TIEN_MAT',
            'CHUYEN_KHOAN',
            'QR'
        )
    )

    trang_thai = db.Column(
        db.Enum(
            'DANG_PHUC_VU',
            'DA_THANH_TOAN',
            'HUY'
        ),
        default='DANG_PHUC_VU'
    )

    chi_nhanh_id = db.Column(
        db.Integer,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    khach_hang = db.relationship(
        'KhachHang'
    )

    ban = db.relationship(
        'Ban'
    )

    nguoi_dung = db.relationship(
        'NguoiDung'
    )