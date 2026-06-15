import time
from flask import Flask, render_template, request, redirect, session, url_for
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

app = Flask(__name__)

app.config.from_object(Config)

db.init_app(app)
def login_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):

        if 'user_id' not in session:
            return redirect(url_for('login'))

        return f(*args, **kwargs)

    return decorated_function


def manager_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):

        if 'user_id' not in session:
            return redirect(url_for('login'))

        if session.get('vai_tro') != 'QUAN_LY':
            return redirect(url_for('cashier'))

        return f(*args, **kwargs)

    return decorated_function


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
@manager_required
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if session['vai_tro'] != 'QUAN_LY':
        return redirect(url_for('cashier'))

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

    ds_hang_hoa = HangHoa.query.join(
        NhomHang,
        HangHoa.nhom_hang_id == NhomHang.id
    ).filter(
        HangHoa.trang_thai == True,
        NhomHang.trang_thai == True
    ).all()

    return render_template(
        'cashier.html',
        ds_khu_vuc=ds_khu_vuc
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
@manager_required
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
@login_required
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

    return render_template(
        'chi_tiet_hoa_don.html',
        hoa_don=hoa_don,
        ds_mon_an=ds_mon_an,
        ds_do_uong=ds_do_uong,
        ds_combo=ds_combo,
        ds_chi_tiet=ds_chi_tiet
    )

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

    db.session.commit()

    return redirect(
        url_for(
            'chi_tiet_hoa_don',
            hoa_don_id=hoa_don_id
        )
    )

@app.route('/cashier/giam-mon/<int:chi_tiet_id>')
@login_required
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
@login_required
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
@login_required
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
@login_required
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

@app.route('/khach-hang')
@manager_required
def khach_hang():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    if session['vai_tro'] != 'QUAN_LY':
        return redirect(url_for('cashier'))

    if 'user_id' not in session:
        return redirect(url_for('login'))

    keyword = request.args.get(
        'keyword',
        ''
    )

    gioi_tinh = request.args.get(
        'gioi_tinh',
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

    if gioi_tinh:

        query = query.filter(
            KhachHang.gioi_tinh == gioi_tinh
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

            gioi_tinh=request.form[
                'gioi_tinh'
            ],

            ngay_sinh=request.form[
                'ngay_sinh'
            ] or None,

            dia_chi=request.form[
                'dia_chi'
            ],

            tinh_thanh=request.form[
                'tinh_thanh'
            ],

            phuong_xa=request.form[
                'phuong_xa'
            ],

            ghi_chu=request.form[
                'ghi_chu'
            ],

            chi_nhanh_id=1

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

        khach_hang.gioi_tinh = request.form[
            'gioi_tinh'
        ]

        khach_hang.ngay_sinh = (
                request.form['ngay_sinh']
                or None
        )

        khach_hang.dia_chi = request.form[
            'dia_chi'
        ]

        khach_hang.tinh_thanh = request.form[
            'tinh_thanh'
        ]

        khach_hang.phuong_xa = request.form[
            'phuong_xa'
        ]

        khach_hang.ghi_chu = request.form[
            'ghi_chu'
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

    if 'user_id' not in session:
        return redirect(url_for('login'))

    khach_hang = KhachHang.query.get_or_404(id)

    db.session.delete(khach_hang)

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
@app.route('/bao-cao')
@manager_required
def bao_cao():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    tu_ngay = request.args.get('tu_ngay')
    den_ngay = request.args.get('den_ngay')

    query = HoaDon.query.filter(
        HoaDon.trang_thai == 'DA_THANH_TOAN'
    )

    if tu_ngay:
        query = query.filter(
            db.func.date(HoaDon.created_at) >= tu_ngay
        )

    if den_ngay:
        query = query.filter(
            db.func.date(HoaDon.created_at) <= den_ngay
        )

    ds_hoa_don = query.all()

    tong_doanh_thu = sum(
        hd.tong_tien
        for hd in ds_hoa_don
    )

    tong_hoa_don = len(ds_hoa_don)

    tien_mat = sum(
        hd.tong_tien
        for hd in ds_hoa_don
        if hd.phuong_thuc_thanh_toan == 'TIEN_MAT'
    )

    chuyen_khoan = sum(
        hd.tong_tien
        for hd in ds_hoa_don
        if hd.phuong_thuc_thanh_toan == 'CHUYEN_KHOAN'
    )

    qr = sum(
        hd.tong_tien
        for hd in ds_hoa_don
        if hd.phuong_thuc_thanh_toan == 'QR'
    )

    return render_template(
        'bao_cao.html',
        ds_hoa_don=ds_hoa_don,
        tong_doanh_thu=tong_doanh_thu,
        tong_hoa_don=tong_hoa_don,
        tien_mat=tien_mat,
        chuyen_khoan=chuyen_khoan,
        qr=qr
    )

@app.route('/chi-nhanh')
@manager_required
def chi_nhanh():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    ds_chi_nhanh = ChiNhanh.query.all()

    return render_template(
        'chi_nhanh.html',
        ds_chi_nhanh=ds_chi_nhanh
    )

@app.route('/chi-nhanh/them',
           methods=['GET', 'POST'])
@manager_required
def them_chi_nhanh():

    if 'user_id' not in session:
        return redirect(url_for('login'))

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
@manager_required
def sua_chi_nhanh(id):

    if 'user_id' not in session:
        return redirect(url_for('login'))

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
@manager_required
def xoa_chi_nhanh(id):

    if 'user_id' not in session:
        return redirect(url_for('login'))

    chi_nhanh = ChiNhanh.query.get_or_404(id)

    db.session.delete(chi_nhanh)

    db.session.commit()

    return redirect('/chi-nhanh')

@app.route('/nguoi-dung')
@manager_required
def nguoi_dung():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    ds_nguoi_dung = NguoiDung.query.all()

    return render_template(
        'nguoi_dung.html',
        ds_nguoi_dung=ds_nguoi_dung
    )

@app.route('/nguoi-dung/them',
           methods=['GET', 'POST'])
@manager_required
def them_nguoi_dung():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    ds_chi_nhanh = ChiNhanh.query.all()

    if request.method == 'POST':

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

            vai_tro=request.form[
                'vai_tro'
            ],

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
@manager_required
def sua_nguoi_dung(id):

    if 'user_id' not in session:
        return redirect(url_for('login'))

    nguoi_dung = NguoiDung.query.get_or_404(id)

    ds_chi_nhanh = ChiNhanh.query.all()

    if request.method == 'POST':

        nguoi_dung.ten_dang_nhap = request.form[
            'ten_dang_nhap'
        ]

        nguoi_dung.ho_ten = request.form[
            'ho_ten'
        ]

        nguoi_dung.vai_tro = request.form[
            'vai_tro'
        ]

        nguoi_dung.chi_nhanh_id = request.form[
            'chi_nhanh_id'
        ]

        nguoi_dung.trang_thai = (
            request.form['trang_thai'] == '1'
        )

        # Chỉ đổi mật khẩu nếu có nhập
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
@manager_required
def xoa_nguoi_dung(id):

    if 'user_id' not in session:
        return redirect(url_for('login'))

    nguoi_dung = NguoiDung.query.get_or_404(id)

    # Không cho phép xóa chính mình
    if nguoi_dung.id == session['user_id']:

        return "Không thể xóa tài khoản đang đăng nhập"

    db.session.delete(nguoi_dung)

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
        nhom_hang = NhomHang(
            ten_nhom=request.form['ten_nhom'],
            so_thu_tu=request.form['so_thu_tu'],
            trang_thai=True,
            chi_nhanh_id=1
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

        nhom.so_thu_tu = request.form['so_thu_tu']

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

    db.session.delete(nhom)

    db.session.commit()

    return redirect('/nhom-hang')

if __name__ == '__main__':
    app.run(debug=True)