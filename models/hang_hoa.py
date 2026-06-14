from database import db


class HangHoa(db.Model):
    __tablename__ = 'hang_hoa'

    id = db.Column(db.Integer, primary_key=True)

    ma_hang = db.Column(db.String(50),
                        unique=True,
                        nullable=False)

    ten_hang = db.Column(db.String(150),
                         nullable=False)

    hinh_anh = db.Column(db.String(255))

    nhom_hang_id = db.Column(db.Integer,
                             nullable=True)

    don_vi_tinh = db.Column(db.String(50))

    gia_ban = db.Column(db.Numeric(15, 2),
                        nullable=False)

    loai_thuc_don = db.Column(
        db.Enum('MON_AN',
                'DO_UONG',
                'COMBO')
    )

    trang_thai = db.Column(db.Boolean,
                           default=True)

    chi_nhanh_id = db.Column(db.Integer,
                             nullable=False)