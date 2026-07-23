import time
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    url_for,
    send_file,
    flash,
)
from functools import wraps
from config import Config
from database import db
from models.nguoi_dung import NguoiDung
from models.hang_hoa import HangHoa
from models.nhom_hang import NhomHang
from models.khu_vuc import KhuVuc
from models.ban import Ban
from models.chi_tiet_hoa_don import ChiTietHoaDon
from datetime import datetime
from models.khach_hang import KhachHang
from models.hoa_don import HoaDon
from models.chi_nhanh import ChiNhanh
from utils.gop_tach_ban import gop_ban, tach_ban
from utils.hoa_don_pdf import tao_hoa_don_pdf
from utils.nhap_hang_hoa_excel import (
    nhap_hang_hoa_tu_excel,
    tao_file_mau_excel,
)
from utils.xoa_an_toan import (
    dem_admin,
    xoa_chi_nhanh_an_toan,
    xoa_hang_hoa_an_toan,
    xoa_hoa_don_an_toan,
    xoa_khach_hang_an_toan,
    xoa_nguoi_dung_an_toan,
    xoa_nhom_hang_an_toan,
)

app = Flask(__name__)

app.config.from_object(Config)

db.init_app(app)


def _lay_user_dang_nhap():
    """Trả về NguoiDung từ session; nếu không còn trong DB thì xóa session."""
    user_id = session.get('user_id')
    if not user_id:
        return None

    user = db.session.get(NguoiDung, user_id)
    if not user or not user.trang_thai:
        session.clear()
        return None


    session['ho_ten'] = user.ho_ten
    session['vai_tro'] = user.vai_tro
    return user


def login_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):

        if not _lay_user_dang_nhap():
            return redirect(url_for('login'))

        return f(*args, **kwargs)

    return decorated_function


def manager_required(f):
    """Quản lý hoặc Admin."""

    @wraps(f)
    def decorated_function(*args, **kwargs):

        user = _lay_user_dang_nhap()
        if not user:
            return redirect(url_for('login'))

        if user.vai_tro not in ('QUAN_LY', 'ADMIN'):
            return redirect(url_for('cashier'))

        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    """Chỉ Admin — role cao nhất."""

    @wraps(f)
    def decorated_function(*args, **kwargs):

        user = _lay_user_dang_nhap()
        if not user:
            return redirect(url_for('login'))

        if user.vai_tro != 'ADMIN':
            return redirect(url_for('dashboard'))

        return f(*args, **kwargs)

    return decorated_function


@app.route('/')
def home():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    if session.get('vai_tro') in ('ADMIN', 'QUAN_LY'):
        return redirect(url_for('dashboard'))

    return redirect(url_for('cashier'))

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        ten_dang_nhap = request.form['ten_dang_nhap']
        mat_khau = request.form['mat_khau']

        user = NguoiDung.query.filter_by(
            ten_dang_nhap=ten_dang_nhap,
            mat_khau=mat_khau,
            trang_thai=True
        ).first()

        if user:

            session['user_id'] = user.id
            session['ho_ten'] = user.ho_ten
            session['vai_tro'] = user.vai_tro

            if user.vai_tro in ('ADMIN', 'QUAN_LY'):
                return redirect(url_for('dashboard'))

            return redirect(url_for('cashier'))

        return render_template(
            'login.html',
            error='Sai tên đăng nhập hoặc mật khẩu'
        )

    return render_template('login.html')

@app.route('/dashboard')
@manager_required
def dashboard():
    tong_hang_hoa = HangHoa.query.count()

    tong_khach_hang = KhachHang.query.count()

    tong_hoa_don = HoaDon.query.count()

    tong_nhom_hang = NhomHang.query.count()

    return render_template(
        'dashboard.html',
        ho_ten=session['ho_ten'],
        tong_hang_hoa=tong_hang_hoa,
        tong_khach_hang=tong_khach_hang,
        tong_hoa_don=tong_hoa_don,
        tong_nhom_hang=tong_nhom_hang
    )

@app.route('/cashier')
@login_required
def cashier():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    ds_khu_vuc = KhuVuc.query.order_by(
        KhuVuc.so_thu_tu
    ).all()

    return render_template(
        'cashier.html',
        ds_khu_vuc=ds_khu_vuc
    )


@app.route('/cashier/gop-ban', methods=['GET', 'POST'])
@login_required
def cashier_gop_ban():

    user = _lay_user_dang_nhap()
    if not user:
        return redirect(url_for('login'))


    ds_hoa_don = HoaDon.query.filter_by(
        trang_thai='DANG_PHUC_VU'
    ).all()

    ds_ban_phuc_vu = []
    for hd in ds_hoa_don:
        if not hd.ban:
            continue
        so_mon = ChiTietHoaDon.query.filter_by(
            hoa_don_id=hd.id
        ).count()
        ds_ban_phuc_vu.append({
            'ban': hd.ban,
            'hoa_don': hd,
            'so_mon': so_mon,
            'tong_tien': hd.tong_tien or 0,
        })

    if request.method == 'POST':
        ban_ids = request.form.getlist('ban_ids')
        ban_chinh_id = request.form.get('ban_chinh_id')

        if len(ban_ids) < 2:
            return render_template(
                'gop_ban.html',
                ds_ban_phuc_vu=ds_ban_phuc_vu,
                error='Chọn ít nhất 2 bàn để gộp'
            )

        if not ban_chinh_id or ban_chinh_id not in ban_ids:
            return render_template(
                'gop_ban.html',
                ds_ban_phuc_vu=ds_ban_phuc_vu,
                error='Chọn bàn chính trong các bàn đã chọn'
            )

        ok, result = gop_ban(
            ban_chinh_id,
            ban_ids,
            user.id
        )

        if not ok:
            return render_template(
                'gop_ban.html',
                ds_ban_phuc_vu=ds_ban_phuc_vu,
                error=result
            )

        return redirect(
            url_for('chi_tiet_hoa_don', hoa_don_id=result)
        )

    return render_template(
        'gop_ban.html',
        ds_ban_phuc_vu=ds_ban_phuc_vu
    )


@app.route('/cashier/tach-ban', methods=['GET', 'POST'])
@login_required
def cashier_tach_ban():

    user = _lay_user_dang_nhap()
    if not user:
        return redirect(url_for('login'))

    ds_hoa_don = HoaDon.query.filter_by(
        trang_thai='DANG_PHUC_VU'
    ).all()

    ds_ban_nguon = []
    for hd in ds_hoa_don:
        if not hd.ban:
            continue
        ds_ct = ChiTietHoaDon.query.filter_by(
            hoa_don_id=hd.id
        ).all()
        if not ds_ct:
            continue
        ds_ban_nguon.append({
            'ban': hd.ban,
            'hoa_don': hd,
            'ds_chi_tiet': ds_ct,
        })

    ds_ban_trong = Ban.query.filter_by(
        trang_thai='TRONG'
    ).order_by(Ban.so_thu_tu).all()

    ban_nguon_id = request.values.get('ban_nguon_id', type=int)
    ban_nguon_info = next(
        (x for x in ds_ban_nguon if x['ban'].id == ban_nguon_id),
        None
    )

    if request.method == 'POST' and request.form.get('buoc') == 'tach':
        ban_nguon_id = request.form.get('ban_nguon_id', type=int)
        ban_dich_id = request.form.get('ban_dich_id', type=int)

        ds_tach = []
        for key, value in request.form.items():
            if key.startswith('sl_'):
                ct_id = key.replace('sl_', '')
                try:
                    so_luong = int(value or 0)
                except ValueError:
                    so_luong = 0
                if so_luong > 0:
                    ds_tach.append({
                        'chi_tiet_id': ct_id,
                        'so_luong': so_luong,
                    })

        ok, result = tach_ban(
            ban_nguon_id,
            ban_dich_id,
            ds_tach,
            user.id
        )

        if not ok:
            return render_template(
                'tach_ban.html',
                ds_ban_nguon=ds_ban_nguon,
                ds_ban_trong=ds_ban_trong,
                ban_nguon_id=ban_nguon_id,
                ban_nguon_info=next(
                    (x for x in ds_ban_nguon if x['ban'].id == ban_nguon_id),
                    None
                ),
                error=result
            )

        return redirect(
            url_for('chi_tiet_hoa_don', hoa_don_id=result)
        )

    return render_template(
        'tach_ban.html',
        ds_ban_nguon=ds_ban_nguon,
        ds_ban_trong=ds_ban_trong,
        ban_nguon_id=ban_nguon_id,
        ban_nguon_info=ban_nguon_info
    )


@app.route('/logout')
def logout():

    session.clear()

    return redirect(url_for('login'))

@app.route('/hang-hoa')
@manager_required
def hang_hoa():

    ds_hang_hoa = HangHoa.query.all()

    return render_template(
        'hang_hoa.html',
        ds_hang_hoa=ds_hang_hoa
    )


@app.route('/hang-hoa/nhap-excel',
           methods=['GET', 'POST'])
@manager_required
def nhap_hang_hoa_excel():

    if request.method == 'POST':
        file = request.files.get('file_excel')

        if not file or not file.filename:
            flash('Vui lòng chọn file Excel', 'danger')
            return redirect(url_for('nhap_hang_hoa_excel'))

        ten_file = file.filename.lower()
        if not (
            ten_file.endswith('.xlsx')
            or ten_file.endswith('.xlsm')
        ):
            flash(
                'Chỉ hỗ trợ file .xlsx (Excel 2007+)',
                'danger'
            )
            return redirect(url_for('nhap_hang_hoa_excel'))

        user = _lay_user_dang_nhap()
        chi_nhanh_id = user.chi_nhanh_id if user else 1

        ket_qua = nhap_hang_hoa_tu_excel(
            file,
            chi_nhanh_id,
            db.session
        )

        if ket_qua['thanh_cong'] or ket_qua['cap_nhat']:
            flash(
                f"Nhập thành công: thêm {ket_qua['thanh_cong']}, "
                f"cập nhật {ket_qua['cap_nhat']}, "
                f"bỏ qua {ket_qua['bo_qua']}",
                'success'
            )
        elif ket_qua['loi']:
            flash(ket_qua['loi'][0], 'danger')
        else:
            flash('Không có dòng dữ liệu nào để nhập', 'warning')

        for loi in ket_qua['loi'][1:20]:
            flash(loi, 'warning')

        if ket_qua['thanh_cong'] or ket_qua['cap_nhat']:
            return redirect(url_for('hang_hoa'))

        return redirect(url_for('nhap_hang_hoa_excel'))

    return render_template('nhap_hang_hoa_excel.html')


@app.route('/hang-hoa/mau-excel')
@manager_required
def tai_mau_excel_hang_hoa():

    from io import BytesIO

    wb = tao_file_mau_excel()
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name='mau_nhap_hang_hoa.xlsx',
        mimetype=(
            'application/vnd.openxmlformats-'
            'officedocument.spreadsheetml.sheet'
        )
    )


@app.route('/hang-hoa/them',
           methods=['GET', 'POST'])
@manager_required
def them_hang_hoa():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    nhom_hang = NhomHang.query.all()

    if request.method == 'POST':

        hang_hoa = HangHoa(
            ma_hang=request.form['ma_hang'],
            ten_hang=request.form['ten_hang'],
            nhom_hang_id=request.form['nhom_hang_id'],
            don_vi_tinh=request.form['don_vi_tinh'],
            gia_ban=request.form['gia_ban'],
            loai_thuc_don=request.form['loai_thuc_don'],
            chi_nhanh_id=1
        )

        db.session.add(hang_hoa)

        db.session.commit()

        return redirect('/hang-hoa')

    return render_template(
        'them_hang_hoa.html',
        nhom_hang=nhom_hang
    )


@app.route('/hang-hoa/sua/<int:id>',
           methods=['GET', 'POST'])
@manager_required
def sua_hang_hoa(id):

    hang_hoa = HangHoa.query.get_or_404(id)
    nhom_hang = NhomHang.query.all()

    if request.method == 'POST':
        hang_hoa.ma_hang = request.form['ma_hang']
        hang_hoa.ten_hang = request.form['ten_hang']
        hang_hoa.nhom_hang_id = request.form['nhom_hang_id']
        hang_hoa.don_vi_tinh = request.form['don_vi_tinh']
        hang_hoa.gia_ban = request.form['gia_ban']
        hang_hoa.loai_thuc_don = request.form['loai_thuc_don']
        hang_hoa.trang_thai = (
            request.form.get('trang_thai', '1') == '1'
        )

        db.session.commit()
        return redirect('/hang-hoa')

    return render_template(
        'sua_hang_hoa.html',
        hang_hoa=hang_hoa,
        nhom_hang=nhom_hang
    )


@app.route('/hang-hoa/xoa/<int:id>')
@manager_required
def xoa_hang_hoa(id):

    hang_hoa = HangHoa.query.get_or_404(id)
    xoa_hang_hoa_an_toan(hang_hoa)
    db.session.commit()

    return redirect('/hang-hoa')


@app.route('/phong-ban')
@manager_required
def phong_ban():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    ds_khu_vuc = KhuVuc.query.order_by(
        KhuVuc.so_thu_tu
    ).all()

    return render_template(
        'phong_ban.html',
        ds_khu_vuc=ds_khu_vuc
    )

@app.route('/khu-vuc/them',
           methods=['GET', 'POST'])
@manager_required
def them_khu_vuc():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        user = _lay_user_dang_nhap()
        chi_nhanh_id = user.chi_nhanh_id if user else 1

        max_stt = db.session.query(
            db.func.coalesce(db.func.max(KhuVuc.so_thu_tu), 0)
        ).filter(
            KhuVuc.chi_nhanh_id == chi_nhanh_id
        ).scalar()

        khu_vuc = KhuVuc(
            ten_khu_vuc=request.form['ten_khu_vuc'],
            so_thu_tu=max_stt + 1,
            ghi_chu=request.form['ghi_chu'],
            chi_nhanh_id=chi_nhanh_id
        )

        db.session.add(khu_vuc)

        db.session.commit()

        return redirect('/phong-ban')

    return render_template('them_khu_vuc.html')

@app.route('/ban/them',
           methods=['GET', 'POST'])
@manager_required
def them_ban():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    ds_khu_vuc = KhuVuc.query.all()

    if request.method == 'POST':
        user = _lay_user_dang_nhap()
        khu_vuc_id = request.form['khu_vuc_id']

        max_stt = db.session.query(
            db.func.coalesce(db.func.max(Ban.so_thu_tu), 0)
        ).filter(
            Ban.khu_vuc_id == khu_vuc_id
        ).scalar()

        ban = Ban(
            ten_ban=request.form['ten_ban'],
            khu_vuc_id=khu_vuc_id,
            so_thu_tu=max_stt + 1,
            so_ghe=4,
            loai='THUONG',
            ghi_chu=request.form['ghi_chu'],
            chi_nhanh_id=user.chi_nhanh_id if user else 1
        )

        db.session.add(ban)

        db.session.commit()

        return redirect('/phong-ban')

    return render_template(
        'them_ban.html',
        ds_khu_vuc=ds_khu_vuc
    )

@app.route('/cashier/chon-ban/<int:ban_id>')
@login_required
def chon_ban(ban_id):

    user = _lay_user_dang_nhap()
    if not user:
        return redirect(url_for('login'))

    ban = db.session.get(Ban, ban_id)
    if not ban:
        return redirect(url_for('cashier'))

    hoa_don = HoaDon.query.filter_by(
        ban_id=ban_id,
        trang_thai='DANG_PHUC_VU'
    ).first()

    if not hoa_don:

        ma_hd = "HD" + datetime.now().strftime("%Y%m%d%H%M%S")

        hoa_don = HoaDon(
            ma_hoa_don=ma_hd,
            ban_id=ban_id,
            nguoi_dung_id=user.id,
            chi_nhanh_id=ban.chi_nhanh_id or user.chi_nhanh_id
        )

        db.session.add(hoa_don)

        db.session.commit()

    return redirect(
        url_for(
            'chi_tiet_hoa_don',
            hoa_don_id=hoa_don.id
        )
    )


def _cap_nhat_trang_thai_ban_theo_hoa_don(hoa_don):
    """Bàn = Đang phục vụ chỉ khi hóa đơn còn món và chưa thanh toán."""
    if not hoa_don or not hoa_don.ban_id:
        return

    ban = db.session.get(Ban, hoa_don.ban_id)
    if not ban:
        return

    if hoa_don.trang_thai != 'DANG_PHUC_VU':
        return

    co_mon = ChiTietHoaDon.query.filter_by(
        hoa_don_id=hoa_don.id
    ).count() > 0

    ban.trang_thai = 'DANG_PHUC_VU' if co_mon else 'TRONG'


@app.route('/cashier/quay-lai/<int:hoa_don_id>')
@login_required
def quay_lai_hoa_don(hoa_don_id):

    hoa_don = HoaDon.query.get_or_404(hoa_don_id)

    if hoa_don.trang_thai == 'DANG_PHUC_VU':
        so_mon = ChiTietHoaDon.query.filter_by(
            hoa_don_id=hoa_don.id
        ).count()

        if so_mon == 0:

            ban = db.session.get(Ban, hoa_don.ban_id)
            if ban:
                ban.trang_thai = 'TRONG'

            db.session.delete(hoa_don)
            db.session.commit()
        else:

            _cap_nhat_trang_thai_ban_theo_hoa_don(hoa_don)
            db.session.commit()

    return redirect(url_for('cashier'))


@app.route('/cashier/hoa-don/<int:hoa_don_id>')
@login_required
def chi_tiet_hoa_don(hoa_don_id):

    hoa_don = HoaDon.query.get_or_404(
        hoa_don_id
    )

    ds_mon_an = HangHoa.query.join(
        NhomHang,
        HangHoa.nhom_hang_id == NhomHang.id
    ).filter(
        HangHoa.trang_thai == True,
        NhomHang.trang_thai == True,
        HangHoa.loai_thuc_don == 'MON_AN'
    ).all()


    ds_do_uong = HangHoa.query.join(
        NhomHang,
        HangHoa.nhom_hang_id == NhomHang.id
    ).filter(
        HangHoa.trang_thai == True,
        NhomHang.trang_thai == True,
        HangHoa.loai_thuc_don == 'DO_UONG'
    ).all()


    ds_combo = HangHoa.query.join(
        NhomHang,
        HangHoa.nhom_hang_id == NhomHang.id
    ).filter(
        HangHoa.trang_thai == True,
        NhomHang.trang_thai == True,
        HangHoa.loai_thuc_don == 'COMBO'
    ).all()

    ds_chi_tiet = ChiTietHoaDon.query.filter_by(
        hoa_don_id=hoa_don_id
    ).all()

    tab = request.args.get('tab', 'mon-an')
    if tab not in ('mon-an', 'do-uong', 'combo'):
        tab = 'mon-an'

    return render_template(
        'chi_tiet_hoa_don.html',
        hoa_don=hoa_don,
        ds_mon_an=ds_mon_an,
        ds_do_uong=ds_do_uong,
        ds_combo=ds_combo,
        ds_chi_tiet=ds_chi_tiet,
        active_tab=tab
    )

def _tab_tu_loai_thuc_don(loai_thuc_don):
    mapping = {
        'MON_AN': 'mon-an',
        'DO_UONG': 'do-uong',
        'COMBO': 'combo',
    }
    return mapping.get(loai_thuc_don, 'mon-an')


@app.route('/cashier/them-mon/<int:hoa_don_id>/<int:hang_hoa_id>')
@login_required
def them_mon(hoa_don_id, hang_hoa_id):

    chi_tiet = ChiTietHoaDon.query.filter_by(
        hoa_don_id=hoa_don_id,
        hang_hoa_id=hang_hoa_id
    ).first()

    hang_hoa = HangHoa.query.get(hang_hoa_id)

    if chi_tiet:

        chi_tiet.so_luong += 1

        chi_tiet.thanh_tien = (
            chi_tiet.so_luong *
            chi_tiet.don_gia
        )

    else:

        chi_tiet = ChiTietHoaDon(

            hoa_don_id=hoa_don_id,

            hang_hoa_id=hang_hoa_id,

            so_luong=1,

            don_gia=hang_hoa.gia_ban,

            thanh_tien=hang_hoa.gia_ban
        )

        db.session.add(chi_tiet)

    hoa_don = HoaDon.query.get(hoa_don_id)

    hoa_don.tong_tien = sum(
        ct.thanh_tien
        for ct in ChiTietHoaDon.query.filter_by(
            hoa_don_id=hoa_don_id
        ).all()
    )

    _cap_nhat_trang_thai_ban_theo_hoa_don(hoa_don)

    db.session.commit()

    tab = request.args.get(
        'tab',
        _tab_tu_loai_thuc_don(hang_hoa.loai_thuc_don)
    )

    return redirect(
        url_for(
            'chi_tiet_hoa_don',
            hoa_don_id=hoa_don_id,
            tab=tab
        )
    )

@app.route('/cashier/giam-mon/<int:chi_tiet_id>')
@login_required
def giam_mon(chi_tiet_id):

    ct = ChiTietHoaDon.query.get_or_404(
        chi_tiet_id
    )

    hoa_don_id = ct.hoa_don_id
    tab = request.args.get(
        'tab',
        _tab_tu_loai_thuc_don(ct.hang_hoa.loai_thuc_don)
    )

    ct.so_luong -= 1

    if ct.so_luong <= 0:

        db.session.delete(ct)

    else:

        ct.thanh_tien = (
            ct.so_luong *
            ct.don_gia
        )

    hoa_don = HoaDon.query.get(
        hoa_don_id
    )

    hoa_don.tong_tien = sum(
        item.thanh_tien
        for item in ChiTietHoaDon.query.filter_by(
            hoa_don_id=hoa_don_id
        )
    )

    _cap_nhat_trang_thai_ban_theo_hoa_don(hoa_don)

    db.session.commit()

    return redirect(
        url_for(
            'chi_tiet_hoa_don',
            hoa_don_id=hoa_don_id,
            tab=tab
        )
    )

@app.route('/cashier/xoa-mon/<int:chi_tiet_id>')
@login_required
def xoa_mon(chi_tiet_id):

    ct = ChiTietHoaDon.query.get_or_404(
        chi_tiet_id
    )

    hoa_don_id = ct.hoa_don_id
    tab = request.args.get(
        'tab',
        _tab_tu_loai_thuc_don(ct.hang_hoa.loai_thuc_don)
    )

    db.session.delete(ct)

    hoa_don = HoaDon.query.get(
        hoa_don_id
    )

    db.session.flush()

    hoa_don.tong_tien = sum(
        item.thanh_tien
        for item in ChiTietHoaDon.query.filter_by(
            hoa_don_id=hoa_don_id
        )
    )

    _cap_nhat_trang_thai_ban_theo_hoa_don(hoa_don)

    db.session.commit()

    return redirect(
        url_for(
            'chi_tiet_hoa_don',
            hoa_don_id=hoa_don_id,
            tab=tab
        )
    )

@app.route('/cashier/thanh-toan/<int:hoa_don_id>')
@login_required
def thanh_toan(hoa_don_id):

    hoa_don = HoaDon.query.get_or_404(
        hoa_don_id
    )

    if hoa_don.trang_thai != 'DANG_PHUC_VU':
        return redirect(url_for('cashier'))

    hoa_don.trang_thai = 'DA_THANH_TOAN'

    hoa_don.phuong_thuc_thanh_toan = 'TIEN_MAT'

    ban = Ban.query.get(
        hoa_don.ban_id
    )

    ban.trang_thai = 'TRONG'

    db.session.commit()

    return redirect(
        url_for(
            'thanh_toan_thanh_cong',
            hoa_don_id=hoa_don_id
        )
    )


@app.route('/cashier/thanh-toan-chuyen-khoan/<int:hoa_don_id>')
@login_required
def thanh_toan_chuyen_khoan(hoa_don_id):

    hoa_don = HoaDon.query.get_or_404(
        hoa_don_id
    )

    if hoa_don.trang_thai != 'DANG_PHUC_VU':
        return redirect(url_for('cashier'))

    ds_chi_tiet = ChiTietHoaDon.query.filter_by(
        hoa_don_id=hoa_don_id
    ).all()

    return render_template(
        'thanh_toan_chuyen_khoan.html',
        hoa_don=hoa_don,
        ds_chi_tiet=ds_chi_tiet
    )


@app.route(
    '/cashier/xac-nhan-chuyen-khoan/<int:hoa_don_id>',
    methods=['POST']
)
@login_required
def xac_nhan_chuyen_khoan(hoa_don_id):

    hoa_don = HoaDon.query.get_or_404(
        hoa_don_id
    )

    if hoa_don.trang_thai != 'DANG_PHUC_VU':
        return redirect(url_for('cashier'))


    hoa_don.trang_thai = 'DA_THANH_TOAN'
    hoa_don.phuong_thuc_thanh_toan = 'CHUYEN_KHOAN'

    ban = Ban.query.get(
        hoa_don.ban_id
    )

    ban.trang_thai = 'TRONG'

    db.session.commit()

    return redirect(
        url_for(
            'thanh_toan_thanh_cong',
            hoa_don_id=hoa_don_id
        )
    )


@app.route('/cashier/thanh-toan-thanh-cong/<int:hoa_don_id>')
@login_required
def thanh_toan_thanh_cong(hoa_don_id):

    hoa_don = HoaDon.query.get_or_404(
        hoa_don_id
    )

    if hoa_don.trang_thai != 'DA_THANH_TOAN':
        return redirect(url_for('cashier'))

    return render_template(
        'thanh_toan_thanh_cong.html',
        hoa_don=hoa_don
    )


@app.route('/cashier/hoa-don/<int:hoa_don_id>/pdf')
@login_required
def xuat_hoa_don_pdf(hoa_don_id):

    hoa_don = HoaDon.query.get_or_404(
        hoa_don_id
    )

    if hoa_don.trang_thai != 'DA_THANH_TOAN':
        return redirect(
            url_for(
                'chi_tiet_hoa_don',
                hoa_don_id=hoa_don_id
            )
        )

    ds_chi_tiet = ChiTietHoaDon.query.filter_by(
        hoa_don_id=hoa_don_id
    ).all()

    chi_nhanh = ChiNhanh.query.get(
        hoa_don.chi_nhanh_id
    )

    pdf_buffer = tao_hoa_don_pdf(
        hoa_don,
        ds_chi_tiet,
        chi_nhanh=chi_nhanh
    )

    ten_file = f'hoa_don_{hoa_don.ma_hoa_don}.pdf'

    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=ten_file
    )

@app.route('/cashier/them-khach-hang/<int:hoa_don_id>',
           methods=['GET', 'POST'])
@login_required
def them_khach_hang_nhanh(hoa_don_id):

    hoa_don = HoaDon.query.get_or_404(
        hoa_don_id
    )

    if request.method == 'GET':
        return render_template(
            'them_khach_hang_nhanh.html',
            hoa_don=hoa_don,
            buoc='nhap_sdt'
        )

    buoc = request.form.get('buoc', 'kiem_tra')
    dien_thoai = (
        request.form.get('dien_thoai', '')
        .strip()
        .replace(' ', '')
    )

    if not dien_thoai:
        return render_template(
            'them_khach_hang_nhanh.html',
            hoa_don=hoa_don,
            buoc='nhap_sdt',
            error='Vui lòng nhập số điện thoại'
        )


    khach_hang = KhachHang.query.filter(
        db.func.replace(KhachHang.dien_thoai, ' ', '') == dien_thoai
    ).first()

    if not khach_hang:

        khach_hang = KhachHang.query.filter_by(
            dien_thoai=dien_thoai
        ).first()

    if buoc == 'kiem_tra':
        if khach_hang:
            return render_template(
                'them_khach_hang_nhanh.html',
                hoa_don=hoa_don,
                buoc='khach_cu',
                khach_hang=khach_hang
            )

        return render_template(
            'them_khach_hang_nhanh.html',
            hoa_don=hoa_don,
            buoc='khach_moi',
            dien_thoai=dien_thoai
        )


    if khach_hang:

        hoa_don.khach_hang_id = khach_hang.id
        db.session.commit()

        return redirect(
            url_for(
                'chi_tiet_hoa_don',
                hoa_don_id=hoa_don.id
            )
        )

    ten_khach_hang = request.form.get(
        'ten_khach_hang',
        ''
    ).strip()

    if not ten_khach_hang:
        return render_template(
            'them_khach_hang_nhanh.html',
            hoa_don=hoa_don,
            buoc='khach_moi',
            dien_thoai=dien_thoai,
            error='Vui lòng nhập tên khách hàng'
        )

    user = _lay_user_dang_nhap()

    khach_hang = KhachHang(
        ten_khach_hang=ten_khach_hang,
        dien_thoai=dien_thoai,
        chi_nhanh_id=user.chi_nhanh_id if user else 1
    )

    db.session.add(khach_hang)
    db.session.flush()


    khach_hang.ma_khach_hang = f"KH{khach_hang.id:03d}"

    hoa_don.khach_hang_id = khach_hang.id
    db.session.commit()

    return redirect(
        url_for(
            'chi_tiet_hoa_don',
            hoa_don_id=hoa_don.id
        )
    )

@app.route('/khach-hang')
@manager_required
def khach_hang():

    keyword = request.args.get(
        'keyword',
        ''
    )

    query = KhachHang.query

    if keyword:

        query = query.filter(
            db.or_(
                KhachHang.ten_khach_hang.like(
                    f'%{keyword}%'
                ),
                KhachHang.ma_khach_hang.like(
                    f'%{keyword}%'
                ),
                KhachHang.dien_thoai.like(
                    f'%{keyword}%'
                )
            )
        )

    ds_khach_hang = query.all()

    return render_template(
        'khach_hang.html',
        ds_khach_hang=ds_khach_hang
    )

@app.route('/khach-hang/them',
           methods=['GET', 'POST'])
@manager_required
def them_khach_hang():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        user = _lay_user_dang_nhap()

        khach_hang = KhachHang(

            ma_khach_hang=request.form[
                'ma_khach_hang'
            ],

            ten_khach_hang=request.form[
                'ten_khach_hang'
            ],

            dien_thoai=request.form[
                'dien_thoai'
            ],

            chi_nhanh_id=user.chi_nhanh_id if user else 1

        )

        db.session.add(
            khach_hang
        )

        db.session.commit()

        return redirect(
            '/khach-hang'
        )

    return render_template(
        'them_khach_hang.html'
    )


@app.route('/khach-hang/sua/<int:id>',
           methods=['GET', 'POST'])
@manager_required
def sua_khach_hang(id):

    if 'user_id' not in session:
        return redirect(url_for('login'))

    khach_hang = KhachHang.query.get_or_404(id)

    if request.method == 'POST':
        khach_hang.ma_khach_hang = request.form[
            'ma_khach_hang'
        ]

        khach_hang.ten_khach_hang = request.form[
            'ten_khach_hang'
        ]

        khach_hang.dien_thoai = request.form[
            'dien_thoai'
        ]

        db.session.commit()

        return redirect('/khach-hang')

    return render_template(
        'sua_khach_hang.html',
        khach_hang=khach_hang
    )

@app.route('/khach-hang/xoa/<int:id>')
@manager_required
def xoa_khach_hang(id):

    khach_hang = KhachHang.query.get_or_404(id)

    xoa_khach_hang_an_toan(khach_hang)

    db.session.commit()

    return redirect('/khach-hang')

@app.route('/hoa-don')
@manager_required
def hoa_don():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    keyword = request.args.get(
        'keyword',
        ''
    )

    ngay = request.args.get(
        'ngay',
        ''
    )

    phuong_thuc = request.args.get(
        'phuong_thuc',
        ''
    )

    query = HoaDon.query

    if keyword:

        query = query.filter(
            HoaDon.ma_hoa_don.like(
                f'%{keyword}%'
            )
        )

    if ngay:

        query = query.filter(
            db.func.date(
                HoaDon.created_at
            ) == ngay
        )

    if phuong_thuc:

        query = query.filter(
            HoaDon.phuong_thuc_thanh_toan
            == phuong_thuc
        )

    ds_hoa_don = query.order_by(
        HoaDon.id.desc()
    ).all()

    return render_template(
        'hoa_don.html',
        ds_hoa_don=ds_hoa_don
    )

@app.route('/hoa-don/<int:id>')
@manager_required
def chi_tiet_hoa_don_quan_ly(id):

    if 'user_id' not in session:
        return redirect(url_for('login'))

    hoa_don = HoaDon.query.get_or_404(id)

    ds_chi_tiet = ChiTietHoaDon.query.filter_by(
        hoa_don_id=id
    ).all()

    return render_template(
        'chi_tiet_hoa_don_quan_ly.html',
        hoa_don=hoa_don,
        ds_chi_tiet=ds_chi_tiet
    )


@app.route('/hoa-don/xoa/<int:id>')
@manager_required
def xoa_hoa_don(id):

    hoa_don = HoaDon.query.get_or_404(id)
    xoa_hoa_don_an_toan(hoa_don)
    db.session.commit()

    return redirect('/hoa-don')


@app.route('/bao-cao')
@manager_required
def bao_cao():

    from datetime import date
    from calendar import monthrange

    today = date.today()
    loai = request.args.get('loai', 'ngay')
    if loai not in ('ngay', 'tuan', 'thang', 'nam'):
        loai = 'ngay'

    ngay = request.args.get('ngay') or today.isoformat()
    tuan = request.args.get('tuan') or today.strftime('%G-W%V')
    thang = request.args.get('thang') or today.strftime('%Y-%m')
    nam = request.args.get('nam') or str(today.year)

    nhan_ky = ''
    try:
        if loai == 'ngay':
            d = date.fromisoformat(ngay)
            tu_ngay = den_ngay = d
            nhan_ky = f'Ngày {d.strftime("%d/%m/%Y")}'

        elif loai == 'tuan':

            year_str, week_str = tuan.split('-W')
            year_i, week_i = int(year_str), int(week_str)
            tu_ngay = date.fromisocalendar(year_i, week_i, 1)
            den_ngay = date.fromisocalendar(year_i, week_i, 7)
            nhan_ky = (
                f'Tuần {week_i}/{year_i} '
                f'({tu_ngay.strftime("%d/%m")} - '
                f'{den_ngay.strftime("%d/%m/%Y")})'
            )

        elif loai == 'thang':
            year_i, month_i = map(int, thang.split('-'))
            tu_ngay = date(year_i, month_i, 1)
            den_ngay = date(
                year_i,
                month_i,
                monthrange(year_i, month_i)[1]
            )
            nhan_ky = f'Tháng {month_i:02d}/{year_i}'

        else:
            year_i = int(nam)
            tu_ngay = date(year_i, 1, 1)
            den_ngay = date(year_i, 12, 31)
            nhan_ky = f'Năm {year_i}'

    except (ValueError, TypeError):
        tu_ngay = den_ngay = today
        loai = 'ngay'
        ngay = today.isoformat()
        nhan_ky = f'Ngày {today.strftime("%d/%m/%Y")}'

    query = HoaDon.query.filter(
        HoaDon.trang_thai == 'DA_THANH_TOAN',
        db.func.date(HoaDon.created_at) >= tu_ngay.isoformat(),
        db.func.date(HoaDon.created_at) <= den_ngay.isoformat(),
    )

    ds_hoa_don = query.order_by(HoaDon.created_at.desc()).all()

    tong_doanh_thu = sum(
        hd.tong_tien or 0
        for hd in ds_hoa_don
    )

    tong_hoa_don = len(ds_hoa_don)

    tien_mat = sum(
        hd.tong_tien or 0
        for hd in ds_hoa_don
        if hd.phuong_thuc_thanh_toan == 'TIEN_MAT'
    )

    chuyen_khoan_qr = sum(
        hd.tong_tien or 0
        for hd in ds_hoa_don
        if hd.phuong_thuc_thanh_toan in ('CHUYEN_KHOAN', 'QR')
    )

    ds_nam = list(range(today.year, today.year - 6, -1))

    return render_template(
        'bao_cao.html',
        ds_hoa_don=ds_hoa_don,
        tong_doanh_thu=float(tong_doanh_thu or 0),
        tong_hoa_don=tong_hoa_don,
        tien_mat=float(tien_mat or 0),
        chuyen_khoan_qr=float(chuyen_khoan_qr or 0),
        loai=loai,
        ngay=ngay,
        tuan=tuan,
        thang=thang,
        nam=str(nam),
        nhan_ky=nhan_ky,
        ds_nam=ds_nam,
    )

@app.route('/chi-nhanh')
@admin_required
def chi_nhanh():

    ds_chi_nhanh = ChiNhanh.query.all()

    return render_template(
        'chi_nhanh.html',
        ds_chi_nhanh=ds_chi_nhanh
    )

@app.route('/chi-nhanh/them',
           methods=['GET', 'POST'])
@admin_required
def them_chi_nhanh():

    if request.method == 'POST':

        chi_nhanh = ChiNhanh(

            ten_chi_nhanh=request.form[
                'ten_chi_nhanh'
            ],

            dia_chi=request.form[
                'dia_chi'
            ],

            dien_thoai=request.form[
                'dien_thoai'
            ]

        )

        db.session.add(
            chi_nhanh
        )

        db.session.commit()

        return redirect(
            '/chi-nhanh'
        )

    return render_template(
        'them_chi_nhanh.html'
    )

@app.route('/chi-nhanh/sua/<int:id>',
           methods=['GET', 'POST'])
@admin_required
def sua_chi_nhanh(id):

    chi_nhanh = ChiNhanh.query.get_or_404(id)

    if request.method == 'POST':

        chi_nhanh.ten_chi_nhanh = request.form[
            'ten_chi_nhanh'
        ]

        chi_nhanh.dia_chi = request.form[
            'dia_chi'
        ]

        chi_nhanh.dien_thoai = request.form[
            'dien_thoai'
        ]

        chi_nhanh.trang_thai = (
            request.form['trang_thai'] == '1'
        )

        db.session.commit()

        return redirect('/chi-nhanh')

    return render_template(
        'sua_chi_nhanh.html',
        chi_nhanh=chi_nhanh
    )

@app.route('/chi-nhanh/xoa/<int:id>')
@admin_required
def xoa_chi_nhanh(id):

    chi_nhanh = ChiNhanh.query.get_or_404(id)

    ok, message = xoa_chi_nhanh_an_toan(chi_nhanh)

    if not ok:
        return message

    db.session.commit()

    return redirect('/chi-nhanh')

@app.route('/nguoi-dung')
@admin_required
def nguoi_dung():

    ds_nguoi_dung = NguoiDung.query.all()

    return render_template(
        'nguoi_dung.html',
        ds_nguoi_dung=ds_nguoi_dung
    )

@app.route('/nguoi-dung/them',
           methods=['GET', 'POST'])
@admin_required
def them_nguoi_dung():

    ds_chi_nhanh = ChiNhanh.query.all()

    if request.method == 'POST':

        vai_tro = request.form['vai_tro']

        if vai_tro == 'ADMIN' and dem_admin() >= 1:
            return render_template(
                'them_nguoi_dung.html',
                ds_chi_nhanh=ds_chi_nhanh,
                error='Chỉ được phép có 1 tài khoản ADMIN'
            )

        nguoi_dung = NguoiDung(

            ten_dang_nhap=request.form[
                'ten_dang_nhap'
            ],

            mat_khau=request.form[
                'mat_khau'
            ],

            ho_ten=request.form[
                'ho_ten'
            ],

            vai_tro=vai_tro,

            chi_nhanh_id=request.form[
                'chi_nhanh_id'
            ],

            trang_thai=True

        )

        db.session.add(
            nguoi_dung
        )

        db.session.commit()

        return redirect(
            '/nguoi-dung'
        )

    return render_template(
        'them_nguoi_dung.html',
        ds_chi_nhanh=ds_chi_nhanh
    )

@app.route('/nguoi-dung/sua/<int:id>',
           methods=['GET', 'POST'])
@admin_required
def sua_nguoi_dung(id):

    nguoi_dung = NguoiDung.query.get_or_404(id)

    ds_chi_nhanh = ChiNhanh.query.all()

    if request.method == 'POST':

        vai_tro_moi = request.form['vai_tro']

        if (
            vai_tro_moi == 'ADMIN'
            and nguoi_dung.vai_tro != 'ADMIN'
            and dem_admin() >= 1
        ):
            return render_template(
                'sua_nguoi_dung.html',
                nguoi_dung=nguoi_dung,
                ds_chi_nhanh=ds_chi_nhanh,
                error='Chỉ được phép có 1 tài khoản ADMIN'
            )

        if (
            nguoi_dung.vai_tro == 'ADMIN'
            and vai_tro_moi != 'ADMIN'
        ):
            return render_template(
                'sua_nguoi_dung.html',
                nguoi_dung=nguoi_dung,
                ds_chi_nhanh=ds_chi_nhanh,
                error='Không thể hạ quyền tài khoản ADMIN duy nhất'
            )

        nguoi_dung.ten_dang_nhap = request.form[
            'ten_dang_nhap'
        ]

        nguoi_dung.ho_ten = request.form[
            'ho_ten'
        ]

        nguoi_dung.vai_tro = vai_tro_moi

        nguoi_dung.chi_nhanh_id = request.form[
            'chi_nhanh_id'
        ]

        nguoi_dung.trang_thai = (
            request.form['trang_thai'] == '1'
        )


        if request.form['mat_khau']:

            nguoi_dung.mat_khau = request.form[
                'mat_khau'
            ]

        db.session.commit()

        return redirect('/nguoi-dung')

    return render_template(
        'sua_nguoi_dung.html',
        nguoi_dung=nguoi_dung,
        ds_chi_nhanh=ds_chi_nhanh
    )

@app.route('/nguoi-dung/xoa/<int:id>')
@admin_required
def xoa_nguoi_dung(id):

    nguoi_dung = NguoiDung.query.get_or_404(id)

    ok, message = xoa_nguoi_dung_an_toan(
        nguoi_dung,
        session['user_id']
    )

    if not ok:
        return message

    db.session.commit()

    return redirect('/nguoi-dung')

@app.route('/nhom-hang')
@manager_required
def nhom_hang():

    ds_nhom_hang = NhomHang.query.all()

    return render_template(
        'nhom_hang.html',
        ds_nhom_hang=ds_nhom_hang
    )

@app.route('/nhom-hang/them',
           methods=['GET', 'POST'])
@manager_required
def them_nhom_hang():

    if request.method == 'POST':
        user = _lay_user_dang_nhap()
        chi_nhanh_id = user.chi_nhanh_id if user else 1

        max_stt = db.session.query(
            db.func.coalesce(db.func.max(NhomHang.so_thu_tu), 0)
        ).filter(
            NhomHang.chi_nhanh_id == chi_nhanh_id
        ).scalar()

        nhom_hang = NhomHang(
            ten_nhom=request.form['ten_nhom'],
            so_thu_tu=max_stt + 1,
            trang_thai=True,
            chi_nhanh_id=chi_nhanh_id
        )

        db.session.add(nhom_hang)

        db.session.flush()

        nhom_hang.ma_nhom = (
            f"NH{nhom_hang.id:03d}"
        )

        db.session.commit()

        return redirect('/nhom-hang')

    return render_template(
        'them_nhom_hang.html'
    )

@app.route('/nhom-hang/sua/<int:id>',
           methods=['GET', 'POST'])
@manager_required
def sua_nhom_hang(id):


    nhom = NhomHang.query.get_or_404(id)

    if request.method == 'POST':

        nhom.ten_nhom = request.form['ten_nhom']

        nhom.trang_thai = (
                request.form['trang_thai'] == '1'
        )

        db.session.commit()

        return redirect('/nhom-hang')

    return render_template(
        'sua_nhom_hang.html',
        nhom=nhom
    )

@app.route('/nhom-hang/xoa/<int:id>')
@manager_required
def xoa_nhom_hang(id):

    nhom = NhomHang.query.get_or_404(id)

    xoa_nhom_hang_an_toan(nhom)

    db.session.commit()

    return redirect('/nhom-hang')

if __name__ == '__main__':
    app.run(debug=True)