"""Logic gộp bàn / tách bàn cho cashier."""
from datetime import datetime

from database import db
from models.ban import Ban
from models.chi_tiet_hoa_don import ChiTietHoaDon
from models.hoa_don import HoaDon


def _lay_hoa_don_dang_phuc_vu(ban_id):
    return HoaDon.query.filter_by(
        ban_id=ban_id,
        trang_thai='DANG_PHUC_VU'
    ).first()


def _tinh_lai_tong_tien(hoa_don_id):
    tong = sum(
        (ct.thanh_tien or 0)
        for ct in ChiTietHoaDon.query.filter_by(
            hoa_don_id=hoa_don_id
        ).all()
    )
    hoa_don = db.session.get(HoaDon, hoa_don_id)
    if hoa_don:
        hoa_don.tong_tien = tong
    return tong


def _gop_chi_tiet_vao_hoa_don(hoa_don_dich, hoa_don_nguon):
    """Chuyển toàn bộ món từ hóa đơn nguồn sang đích (cộng dồn nếu trùng món)."""
    ds_ct = ChiTietHoaDon.query.filter_by(
        hoa_don_id=hoa_don_nguon.id
    ).all()

    for ct in ds_ct:
        ct_dich = ChiTietHoaDon.query.filter_by(
            hoa_don_id=hoa_don_dich.id,
            hang_hoa_id=ct.hang_hoa_id
        ).first()

        if ct_dich:
            ct_dich.so_luong += ct.so_luong
            ct_dich.thanh_tien = (
                ct_dich.so_luong * ct_dich.don_gia
            )
            db.session.delete(ct)
        else:
            ct.hoa_don_id = hoa_don_dich.id


def gop_ban(ban_chinh_id, ds_ban_gop_id, nguoi_dung_id):
    """
    Gộp nhiều bàn vào bàn chính.
    - Hóa đơn giữ ở bàn chính
    - Món từ các bàn khác chuyển hết sang
    - Các bàn phụ về trạng thái trống
    """
    ban_chinh_id = int(ban_chinh_id)
    ds_ban_gop_id = [int(x) for x in ds_ban_gop_id if int(x) != ban_chinh_id]

    if not ds_ban_gop_id:
        return False, 'Cần chọn ít nhất 2 bàn để gộp'

    ban_chinh = db.session.get(Ban, ban_chinh_id)
    if not ban_chinh:
        return False, 'Không tìm thấy bàn chính'

    hoa_don_chinh = _lay_hoa_don_dang_phuc_vu(ban_chinh_id)
    if not hoa_don_chinh:
        # Tạo hóa đơn trống nếu bàn chính chưa có
        hoa_don_chinh = HoaDon(
            ma_hoa_don='HD' + datetime.now().strftime('%Y%m%d%H%M%S'),
            ban_id=ban_chinh_id,
            nguoi_dung_id=nguoi_dung_id,
            chi_nhanh_id=ban_chinh.chi_nhanh_id,
            trang_thai='DANG_PHUC_VU',
            tong_tien=0,
        )
        db.session.add(hoa_don_chinh)
        db.session.flush()

    ten_ban_gop = []
    for ban_id in ds_ban_gop_id:
        ban = db.session.get(Ban, ban_id)
        if not ban:
            return False, f'Không tìm thấy bàn id={ban_id}'

        hoa_don_phu = _lay_hoa_don_dang_phuc_vu(ban_id)
        if not hoa_don_phu:
            return False, f'Bàn {ban.ten_ban} không có hóa đơn đang phục vụ'

        _gop_chi_tiet_vao_hoa_don(hoa_don_chinh, hoa_don_phu)

        # Giữ khách hàng nếu bàn chính chưa có
        if not hoa_don_chinh.khach_hang_id and hoa_don_phu.khach_hang_id:
            hoa_don_chinh.khach_hang_id = hoa_don_phu.khach_hang_id

        ten_ban_gop.append(ban.ten_ban)

        # Xóa hóa đơn phụ
        db.session.delete(hoa_don_phu)
        ban.trang_thai = 'TRONG'

    _tinh_lai_tong_tien(hoa_don_chinh.id)

    # Cập nhật ghi chú bàn gộp để hiển thị
    cu = (hoa_don_chinh.ban_gop or '').strip()
    moi = ', '.join(ten_ban_gop)
    if cu:
        hoa_don_chinh.ban_gop = f'{cu}, {moi}'
    else:
        hoa_don_chinh.ban_gop = moi

    ban_chinh.trang_thai = 'DANG_PHUC_VU'
    db.session.commit()

    return True, hoa_don_chinh.id


def tach_ban(ban_nguon_id, ban_dich_id, ds_tach, nguoi_dung_id):
    """
    Tách món từ bàn nguồn sang bàn đích (bàn trống).
    ds_tach: list[{chi_tiet_id, so_luong}]
    """
    ban_nguon_id = int(ban_nguon_id)
    ban_dich_id = int(ban_dich_id)

    if ban_nguon_id == ban_dich_id:
        return False, 'Bàn nguồn và bàn đích phải khác nhau'

    ban_nguon = db.session.get(Ban, ban_nguon_id)
    ban_dich = db.session.get(Ban, ban_dich_id)

    if not ban_nguon or not ban_dich:
        return False, 'Không tìm thấy bàn'

    if ban_dich.trang_thai != 'TRONG':
        return False, f'Bàn {ban_dich.ten_ban} phải đang trống'

    hoa_don_nguon = _lay_hoa_don_dang_phuc_vu(ban_nguon_id)
    if not hoa_don_nguon:
        return False, f'Bàn {ban_nguon.ten_ban} không có hóa đơn đang phục vụ'

    # Lọc các dòng tách hợp lệ
    mon_tach = []
    for item in ds_tach:
        ct_id = int(item.get('chi_tiet_id', 0))
        so_luong = int(item.get('so_luong', 0) or 0)
        if so_luong <= 0:
            continue

        ct = db.session.get(ChiTietHoaDon, ct_id)
        if not ct or ct.hoa_don_id != hoa_don_nguon.id:
            return False, 'Chi tiết món không hợp lệ'

        if so_luong > ct.so_luong:
            return False, (
                f'Số lượng tách vượt quá số lượng hiện có '
                f'({ct.hang_hoa.ten_hang})'
            )

        mon_tach.append((ct, so_luong))

    if not mon_tach:
        return False, 'Chọn ít nhất 1 món với số lượng > 0 để tách'

    hoa_don_dich = HoaDon(
        ma_hoa_don='HD' + datetime.now().strftime('%Y%m%d%H%M%S'),
        ban_id=ban_dich_id,
        nguoi_dung_id=nguoi_dung_id,
        chi_nhanh_id=ban_dich.chi_nhanh_id,
        trang_thai='DANG_PHUC_VU',
        tong_tien=0,
    )
    db.session.add(hoa_don_dich)
    db.session.flush()

    for ct, so_luong in mon_tach:
        thanh_tien = so_luong * ct.don_gia

        ct_moi = ChiTietHoaDon(
            hoa_don_id=hoa_don_dich.id,
            hang_hoa_id=ct.hang_hoa_id,
            so_luong=so_luong,
            don_gia=ct.don_gia,
            thanh_tien=thanh_tien,
        )
        db.session.add(ct_moi)

        ct.so_luong -= so_luong
        if ct.so_luong <= 0:
            db.session.delete(ct)
        else:
            ct.thanh_tien = ct.so_luong * ct.don_gia

    _tinh_lai_tong_tien(hoa_don_nguon.id)
    _tinh_lai_tong_tien(hoa_don_dich.id)

    ban_dich.trang_thai = 'DANG_PHUC_VU'

    # Nếu bàn nguồn hết món → về trống và hủy hóa đơn trống
    so_mon_con = ChiTietHoaDon.query.filter_by(
        hoa_don_id=hoa_don_nguon.id
    ).count()

    if so_mon_con == 0:
        ban_nguon.trang_thai = 'TRONG'
        db.session.delete(hoa_don_nguon)
    else:
        ban_nguon.trang_thai = 'DANG_PHUC_VU'
        # Xóa tên bàn đích khỏi ban_gop nếu có
        if hoa_don_nguon.ban_gop:
            parts = [
                p.strip()
                for p in hoa_don_nguon.ban_gop.split(',')
                if p.strip() and p.strip() != ban_dich.ten_ban
            ]
            hoa_don_nguon.ban_gop = ', '.join(parts) or None

    db.session.commit()
    return True, hoa_don_dich.id
