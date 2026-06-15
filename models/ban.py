from database import db


class Ban(db.Model):
    __tablename__ = 'ban'

    id = db.Column(db.Integer, primary_key=True)

    ten_ban = db.Column(
        db.String(50),
        nullable=False
    )

    khu_vuc_id = db.Column(
        db.Integer,
        db.ForeignKey('khu_vuc.id'),
        nullable=True
    )

    so_thu_tu = db.Column(
        db.Integer,
        default=0
    )

    so_ghe = db.Column(
        db.Integer,
        default=4
    )

    loai = db.Column(
        db.Enum(
            'THUONG',
            'VIP'
        )
    )

    trang_thai = db.Column(
        db.Enum(
            'TRONG',
            'DANG_PHUC_VU',
            'DAT_TRUOC'
        ),
        default='TRONG'
    )

    ghi_chu = db.Column(db.Text)

    chi_nhanh_id = db.Column(
        db.Integer,
        nullable=False
    )

    khu_vuc = db.relationship(
        'KhuVuc',
        back_populates='ban'
    )