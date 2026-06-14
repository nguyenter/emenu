import time
from flask import Flask, render_template, request, redirect, session, url_for
from config import Config
from database import db
from models.nguoi_dung import NguoiDung
from models.hang_hoa import HangHoa
from models.nhom_hang import NhomHang
from models.khu_vuc import KhuVuc
from models.ban import Ban
from models.hoa_don import HoaDon
from models.chi_tiet_hoa_don import ChiTietHoaDon
from datetime import datetime
from models.khach_hang import KhachHang
from models.hoa_don import HoaDon

app = Flask(__name__)

app.config.from_object(Config)

db.init_app(app)


@app.route('/')
def home():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    return f"Xin chào {session['ho_ten']}"

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

            if user.vai_tro == 'QUAN_LY':
                return redirect(url_for('dashboard'))

            return redirect(url_for('cashier'))

        return render_template(
            'login.html',
            error='Sai tên đăng nhập hoặc mật khẩu'
        )

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    if session['vai_tro'] != 'QUAN_LY':
        return "Bạn không có quyền truy cập"

    return render_template(
        'dashboard.html',
        ho_ten=session['ho_ten']
    )

@app.route('/cashier')
def cashier():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    ds_ban = Ban.query.order_by(Ban.so_thu_tu).all()

    ds_hang_hoa = HangHoa.query.filter_by(
        trang_thai=True
    ).all()

    return render_template(
        'cashier.html',
        ds_ban=ds_ban,
        ds_hang_hoa=ds_hang_hoa
    )

@app.route('/logout')
def logout():

    session.clear()

    return redirect(url_for('login'))

@app.route('/hang-hoa')
def hang_hoa():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    ds_hang_hoa = HangHoa.query.all()

    return render_template(
        'hang_hoa.html',
        ds_hang_hoa=ds_hang_hoa
    )

@app.route('/hang-hoa/them',
           methods=['GET', 'POST'])
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

@app.route('/phong-ban')
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
def them_khu_vuc():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':

        khu_vuc = KhuVuc(
            ten_khu_vuc=request.form['ten_khu_vuc'],
            so_thu_tu=request.form['so_thu_tu'],
            ghi_chu=request.form['ghi_chu'],
            chi_nhanh_id=1
        )

        db.session.add(khu_vuc)

        db.session.commit()

        return redirect('/phong-ban')

    return render_template('them_khu_vuc.html')

@app.route('/ban/them',
           methods=['GET', 'POST'])
def them_ban():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    ds_khu_vuc = KhuVuc.query.all()

    if request.method == 'POST':

        ban = Ban(
            ten_ban=request.form['ten_ban'],
            khu_vuc_id=request.form['khu_vuc_id'],
            so_thu_tu=request.form['so_thu_tu'],
            so_ghe=request.form['so_ghe'],
            loai=request.form['loai'],
            ghi_chu=request.form['ghi_chu'],
            chi_nhanh_id=1
        )

        db.session.add(ban)

        db.session.commit()

        return redirect('/phong-ban')

    return render_template(
        'them_ban.html',
        ds_khu_vuc=ds_khu_vuc
    )

@app.route('/cashier/chon-ban/<int:ban_id>')
def chon_ban(ban_id):

    if 'user_id' not in session:
        return redirect(url_for('login'))

    hoa_don = HoaDon.query.filter_by(
        ban_id=ban_id,
        trang_thai='DANG_PHUC_VU'
    ).first()

    if not hoa_don:

        ma_hd = "HD" + datetime.now().strftime("%Y%m%d%H%M%S")

        hoa_don = HoaDon(
            ma_hoa_don=ma_hd,
            ban_id=ban_id,
            nguoi_dung_id=session['user_id'],
            chi_nhanh_id=1
        )

        db.session.add(hoa_don)

        ban = Ban.query.get(ban_id)

        ban.trang_thai = 'DANG_PHUC_VU'

        db.session.commit()

    return redirect(
        url_for(
            'chi_tiet_hoa_don',
            hoa_don_id=hoa_don.id
        )
    )

@app.route('/cashier/hoa-don/<int:hoa_don_id>')
def chi_tiet_hoa_don(hoa_don_id):

    hoa_don = HoaDon.query.get_or_404(
        hoa_don_id
    )

    ds_mon = HangHoa.query.filter_by(
        trang_thai=True
    ).all()

    ds_chi_tiet = ChiTietHoaDon.query.filter_by(
        hoa_don_id=hoa_don_id
    ).all()

    return render_template(
        'chi_tiet_hoa_don.html',
        hoa_don=hoa_don,
        ds_mon=ds_mon,
        ds_chi_tiet=ds_chi_tiet
    )

@app.route('/cashier/them-mon/<int:hoa_don_id>/<int:hang_hoa_id>')
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

    db.session.commit()

    return redirect(
        url_for(
            'chi_tiet_hoa_don',
            hoa_don_id=hoa_don_id
        )
    )

@app.route('/cashier/giam-mon/<int:chi_tiet_id>')
def giam_mon(chi_tiet_id):

    ct = ChiTietHoaDon.query.get_or_404(
        chi_tiet_id
    )

    hoa_don_id = ct.hoa_don_id

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

    db.session.commit()

    return redirect(
        url_for(
            'chi_tiet_hoa_don',
            hoa_don_id=hoa_don_id
        )
    )

@app.route('/cashier/xoa-mon/<int:chi_tiet_id>')
def xoa_mon(chi_tiet_id):

    ct = ChiTietHoaDon.query.get_or_404(
        chi_tiet_id
    )

    hoa_don_id = ct.hoa_don_id

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

    db.session.commit()

    return redirect(
        url_for(
            'chi_tiet_hoa_don',
            hoa_don_id=hoa_don_id
        )
    )

@app.route('/cashier/thanh-toan/<int:hoa_don_id>')
def thanh_toan(hoa_don_id):

    hoa_don = HoaDon.query.get_or_404(
        hoa_don_id
    )

    hoa_don.trang_thai = 'DA_THANH_TOAN'

    hoa_don.phuong_thuc_thanh_toan = 'TIEN_MAT'

    ban = Ban.query.get(
        hoa_don.ban_id
    )

    ban.trang_thai = 'TRONG'

    db.session.commit()

    return redirect(
        url_for('cashier')
    )

@app.route('/cashier/them-khach-hang/<int:hoa_don_id>',
           methods=['GET', 'POST'])
def them_khach_hang_nhanh(hoa_don_id):

    hoa_don = HoaDon.query.get_or_404(
        hoa_don_id
    )

    if request.method == 'POST':

        dien_thoai = request.form['dien_thoai']

        khach_hang = None

        if dien_thoai:

            khach_hang = KhachHang.query.filter_by(
                dien_thoai=dien_thoai
            ).first()

        if not khach_hang:

            khach_hang = KhachHang(

                ma_khach_hang=f"KH{int(time.time())}",

                ten_khach_hang=request.form[
                    'ten_khach_hang'
                ],

                dien_thoai=dien_thoai,

                chi_nhanh_id=1

            )

            db.session.add(
                khach_hang
            )

            db.session.flush()

        hoa_don.khach_hang_id = khach_hang.id

        db.session.commit()

        return redirect(
            url_for(
                'chi_tiet_hoa_don',
                hoa_don_id=hoa_don.id
            )
        )

    return render_template(
        'them_khach_hang_nhanh.html',
        hoa_don=hoa_don
    )

if __name__ == '__main__':
    app.run(debug=True)