from database import db


class CauHinh(db.Model):
    __tablename__ = 'cau_hinh'

    id = db.Column(db.Integer, primary_key=True)

    khoa = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    gia_tri = db.Column(
        db.Text,
        nullable=True
    )
