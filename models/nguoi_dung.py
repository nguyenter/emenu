from database import db


class NguoiDung(db.Model):
    __tablename__ = 'nguoi_dung'

    id = db.Column(db.Integer, primary_key=True)

    ten_dang_nhap = db.Column(db.String(50),
                              unique=True,
                              nullable=False)

    mat_khau = db.Column(db.String(255),
                         nullable=False)

    ho_ten = db.Column(db.String(100),
                       nullable=False)

    vai_tro = db.Column(db.Enum('ADMIN',
                                'QUAN_LY',
                                'NHAN_VIEN'),
                        nullable=False)

    chi_nhanh_id = db.Column(
        db.Integer,
        db.ForeignKey('chi_nhanh.id'),
        nullable=False
    )

    chi_nhanh = db.relationship(
        'ChiNhanh'
    )

    trang_thai = db.Column(db.Boolean,
                           default=True)

    def __repr__(self):
        return f'<NguoiDung {self.ten_dang_nhap}>'
