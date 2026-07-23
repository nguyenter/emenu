from database import db
from models.ban import Ban
from models.chi_tiet_hoa_don import ChiTietHoaDon
from models.hang_hoa import HangHoa
from models.hoa_don import HoaDon
from models.khach_hang import KhachHang
from models.khu_vuc import KhuVuc
from models.nguoi_dung import NguoiDung
from models.nhom_hang import NhomHang


def lay_admin():
    return NguoiDung.query.filter_by(vai_tro='ADMIN').first()


def dem_admin():
    return NguoiDung.query.filter_by(vai_tro='ADMIN').count()


def xoa_ban_an_toan(ban):
    """
    Xóa bàn an toàn.
    - Không xóa khi bàn đang phục vụ
    - Gỡ liên kết hóa đơn cũ rồi mới xóa bàn
    """
    if ban.trang_thai == 'DANG_PHUC_VU':
        return False, (
            f'Không thể xóa "{ban.ten_ban}" '
            'vì đang phục vụ'
        )

    dang_phuc_vu = HoaDon.query.filter_by(
        ban_id=ban.id,
        trang_thai='DANG_PHUC_VU'
    ).count()

    if dang_phuc_vu > 0:
        return False, (
            f'Không thể xóa "{ban.ten_ban}" '
            'vì còn hóa đơn đang phục vụ'
        )

    HoaDon.query.filter_by(ban_id=ban.id).update(
        {HoaDon.ban_id: None},
        synchronize_session=False
    )

    db.session.delete(ban)
    return True, None


def xoa_hoa_don_an_toan(hoa_don):
    """Xóa hóa đơn và chi tiết; mở lại bàn nếu đang phục vụ."""
    if hoa_don.ban_id and hoa_don.trang_thai == 'DANG_PHUC_VU':
        ban = db.session.get(Ban, hoa_don.ban_id)
        if ban:
            ban.trang_thai = 'TRONG'

    ChiTietHoaDon.query.filter_by(
        hoa_don_id=hoa_don.id
    ).delete(synchronize_session=False)

    db.session.delete(hoa_don)


def xoa_nguoi_dung_an_toan(nguoi_dung, current_user_id):
    """
    Xóa người dùng an toàn.
    - Không xóa chính mình
    - Không xóa ADMIN (chỉ có 1 admin)
    - Chuyển hóa đơn sang admin trước khi xóa
    """
    if nguoi_dung.id == current_user_id:
        return False, 'Không thể xóa tài khoản đang đăng nhập'

    if nguoi_dung.vai_tro == 'ADMIN':
        return False, 'Không thể xóa tài khoản ADMIN'

    admin = lay_admin()
    if not admin:
        return False, 'Chưa có tài khoản ADMIN để chuyển dữ liệu hóa đơn'

    HoaDon.query.filter_by(
        nguoi_dung_id=nguoi_dung.id
    ).update(
        {HoaDon.nguoi_dung_id: admin.id},
        synchronize_session=False
    )

    db.session.delete(nguoi_dung)
    return True, None


def xoa_khach_hang_an_toan(khach_hang):
    """Gỡ liên kết hóa đơn rồi xóa khách hàng."""
    HoaDon.query.filter_by(
        khach_hang_id=khach_hang.id
    ).update(
        {HoaDon.khach_hang_id: None},
        synchronize_session=False
    )
    db.session.delete(khach_hang)


def xoa_hang_hoa_an_toan(hang_hoa):
    """Xóa chi tiết hóa đơn liên quan rồi xóa hàng hóa."""
    ChiTietHoaDon.query.filter_by(
        hang_hoa_id=hang_hoa.id
    ).delete(synchronize_session=False)
    db.session.delete(hang_hoa)


def xoa_nhom_hang_an_toan(nhom_hang):
    """Xóa hàng hóa trong nhóm (và chi tiết HĐ) rồi xóa nhóm."""
    ds_hang = HangHoa.query.filter_by(
        nhom_hang_id=nhom_hang.id
    ).all()

    for hang in ds_hang:
        xoa_hang_hoa_an_toan(hang)

    db.session.delete(nhom_hang)


def xoa_chi_nhanh_an_toan(chi_nhanh):
    """
    Xóa toàn bộ dữ liệu thuộc chi nhánh rồi xóa chi nhánh.
    ADMIN thuộc chi nhánh này sẽ được chuyển sang chi nhánh khác (nếu có).
    """
    from models.chi_nhanh import ChiNhanh

    admin = lay_admin()
    chi_nhanh_khac = ChiNhanh.query.filter(
        ChiNhanh.id != chi_nhanh.id
    ).first()

    if admin and admin.chi_nhanh_id == chi_nhanh.id:
        if not chi_nhanh_khac:
            return False, (
                'Không thể xóa chi nhánh cuối cùng '
                'đang chứa tài khoản ADMIN'
            )
        admin.chi_nhanh_id = chi_nhanh_khac.id

    khu_vuc_ids = [
        kv.id for kv in KhuVuc.query.filter_by(
            chi_nhanh_id=chi_nhanh.id
        ).all()
    ]


    ban_query = Ban.query.filter(Ban.chi_nhanh_id == chi_nhanh.id)
    if khu_vuc_ids:
        ban_query = Ban.query.filter(
            db.or_(
                Ban.chi_nhanh_id == chi_nhanh.id,
                Ban.khu_vuc_id.in_(khu_vuc_ids),
            )
        )

    ban_ids = [b.id for b in ban_query.all()]


    if ban_ids:
        for hd in HoaDon.query.filter(
            HoaDon.ban_id.in_(ban_ids)
        ).all():
            xoa_hoa_don_an_toan(hd)


    for hd in HoaDon.query.filter_by(
        chi_nhanh_id=chi_nhanh.id
    ).all():
        xoa_hoa_don_an_toan(hd)


    ds_user = NguoiDung.query.filter_by(
        chi_nhanh_id=chi_nhanh.id
    ).all()

    for user in ds_user:
        if user.vai_tro == 'ADMIN':
            continue

        if admin:
            HoaDon.query.filter_by(
                nguoi_dung_id=user.id
            ).update(
                {HoaDon.nguoi_dung_id: admin.id},
                synchronize_session=False
            )

        for hd in HoaDon.query.filter_by(
            nguoi_dung_id=user.id
        ).all():
            xoa_hoa_don_an_toan(hd)

        db.session.delete(user)

    KhachHang.query.filter_by(
        chi_nhanh_id=chi_nhanh.id
    ).delete(synchronize_session=False)

    for hang in HangHoa.query.filter_by(
        chi_nhanh_id=chi_nhanh.id
    ).all():
        xoa_hang_hoa_an_toan(hang)

    NhomHang.query.filter_by(
        chi_nhanh_id=chi_nhanh.id
    ).delete(synchronize_session=False)


    ds_ban = []
    if ban_ids:
        ds_ban = Ban.query.filter(Ban.id.in_(ban_ids)).all()
    if khu_vuc_ids:
        ds_ban_kv = Ban.query.filter(
            Ban.khu_vuc_id.in_(khu_vuc_ids)
        ).all()
        seen = {b.id for b in ds_ban}
        for ban in ds_ban_kv:
            if ban.id not in seen:
                ds_ban.append(ban)

    for ban in ds_ban:
        for hd in HoaDon.query.filter_by(ban_id=ban.id).all():
            xoa_hoa_don_an_toan(hd)
        db.session.delete(ban)

    db.session.flush()

    for kv in KhuVuc.query.filter_by(
        chi_nhanh_id=chi_nhanh.id
    ).all():
        db.session.delete(kv)

    db.session.flush()

    db.session.delete(chi_nhanh)
    return True, None
