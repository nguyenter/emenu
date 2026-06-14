from database import db


class KhuVuc(db.Model):
    __tablename__ = 'khu_vuc'

    id = db.Column(db.Integer, primary_key=True)

    ten_khu_vuc = db.Column(
        db.String(100),
        nullable=False
    )

    so_thu_tu = db.Column(
        db.Integer,
        default=0
    )

    ghi_chu = db.Column(db.Text)

    chi_nhanh_id = db.Column(
        db.Integer,
        nullable=False
    )