from database import db


class ChiTietHoaDon(db.Model):
    __tablename__ = 'chi_tiet_hoa_don'

    id = db.Column(db.Integer, primary_key=True)

    hoa_don_id = db.Column(
        db.Integer,
        db.ForeignKey('hoa_don.id'),
        nullable=False
    )

    hang_hoa_id = db.Column(
        db.Integer,
        db.ForeignKey('hang_hoa.id'),
        nullable=False
    )

    so_luong = db.Column(
        db.Integer,
        nullable=False
    )

    don_gia = db.Column(
        db.Numeric(15, 2),
        nullable=False
    )

    thanh_tien = db.Column(
        db.Numeric(15, 2),
        nullable=False
    )

    hang_hoa = db.relationship(
        'HangHoa'
    )
