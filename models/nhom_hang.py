from database import db


class NhomHang(db.Model):
    __tablename__ = 'nhom_hang'

    id = db.Column(db.Integer, primary_key=True)

    ten_nhom = db.Column(db.String(100),
                         nullable=False)

    so_thu_tu = db.Column(db.Integer,
                          default=0)

    chi_nhanh_id = db.Column(db.Integer,
                             nullable=False)