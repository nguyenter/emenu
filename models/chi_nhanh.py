from database import db


class ChiNhanh(db.Model):
    __tablename__ = 'chi_nhanh'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    ten_chi_nhanh = db.Column(
        db.String(100),
        nullable=False
    )

    dia_chi = db.Column(
        db.String(255)
    )

    dien_thoai = db.Column(
        db.String(20)
    )

    trang_thai = db.Column(
        db.Boolean,
        default=True
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )