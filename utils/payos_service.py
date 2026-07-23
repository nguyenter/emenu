import os
import time
from urllib.parse import quote

from database import db
from models.cau_hinh import CauHinh


PAYOS_CLIENT_ID = 'PAYOS_CLIENT_ID'
PAYOS_API_KEY = 'PAYOS_API_KEY'
PAYOS_CHECKSUM_KEY = 'PAYOS_CHECKSUM_KEY'


def dam_bao_bang_cau_hinh():
    CauHinh.__table__.create(db.engine, checkfirst=True)


def lay_cau_hinh(khoa, mac_dinh=''):
    dam_bao_bang_cau_hinh()
    row = CauHinh.query.filter_by(khoa=khoa).first()
    if row and row.gia_tri:
        return row.gia_tri.strip()
    return (os.getenv(khoa) or mac_dinh).strip()


def luu_cau_hinh(khoa, gia_tri):
    dam_bao_bang_cau_hinh()
    row = CauHinh.query.filter_by(khoa=khoa).first()
    if not row:
        row = CauHinh(khoa=khoa, gia_tri=gia_tri)
        db.session.add(row)
    else:
        row.gia_tri = gia_tri
    db.session.commit()


def lay_cau_hinh_payos():
    return {
        'client_id': lay_cau_hinh(PAYOS_CLIENT_ID),
        'api_key': lay_cau_hinh(PAYOS_API_KEY),
        'checksum_key': lay_cau_hinh(PAYOS_CHECKSUM_KEY),
    }


def da_cau_hinh_payos():
    cfg = lay_cau_hinh_payos()
    return bool(
        cfg['client_id']
        and cfg['api_key']
        and cfg['checksum_key']
    )


def _tao_client_payos():
    from payos import PayOS

    cfg = lay_cau_hinh_payos()
    if not (
        cfg['client_id']
        and cfg['api_key']
        and cfg['checksum_key']
    ):
        return None

    return PayOS(
        client_id=cfg['client_id'],
        api_key=cfg['api_key'],
        checksum_key=cfg['checksum_key'],
    )


def tao_order_code(hoa_don_id):
    """order_code duy nhất (int) cho PayOS."""
    return int(f'{hoa_don_id}{int(time.time()) % 1000000:06d}')


def tao_link_thanh_toan_payos(
    hoa_don,
    return_url,
    cancel_url,
):
    """
    Tạo payment link PayOS.
    Trả về (ok, data_or_error).
    data: checkout_url, qr_code, qr_image_url, order_code, payment_link_id
    """
    client = _tao_client_payos()
    if not client:
        return False, (
            'Chưa cấu hình PayOS '
            '(Client ID, API Key, Checksum Key).'
        )

    so_tien = int(round(float(hoa_don.tong_tien or 0)))
    if so_tien < 1000:
        return False, 'Số tiền tối thiểu thanh toán PayOS là 1.000 đ'

    from payos import APIError
    from payos.types import CreatePaymentLinkRequest

    order_code = tao_order_code(hoa_don.id)
    mo_ta = f'HD {hoa_don.ma_hoa_don}'[:25]

    try:
        response = client.payment_requests.create(
            payment_data=CreatePaymentLinkRequest(
                order_code=order_code,
                amount=so_tien,
                description=mo_ta,
                return_url=return_url,
                cancel_url=cancel_url,
            )
        )
    except APIError as e:
        msg = getattr(e, 'error_desc', None) or str(e)
        return False, f'PayOS lỗi: {msg}'
    except Exception as e:
        return False, f'Không tạo được link PayOS: {e}'

    checkout_url = getattr(response, 'checkout_url', None) or ''
    qr_code = getattr(response, 'qr_code', None) or ''
    payment_link_id = getattr(
        response, 'payment_link_id', None
    ) or getattr(response, 'id', None)

    qr_image_url = ''
    if qr_code:
        qr_image_url = (
            'https://api.qrserver.com/v1/create-qr-code/'
            f'?size=260x260&data={quote(qr_code)}'
        )
    elif checkout_url:
        qr_image_url = (
            'https://api.qrserver.com/v1/create-qr-code/'
            f'?size=260x260&data={quote(checkout_url)}'
        )

    return True, {
        'checkout_url': checkout_url,
        'qr_code': qr_code,
        'qr_image_url': qr_image_url,
        'order_code': order_code,
        'payment_link_id': payment_link_id,
    }


def kiem_tra_thanh_toan_payos(order_code):
    """Trả về True nếu đơn PayOS đã PAID."""
    client = _tao_client_payos()
    if not client or not order_code:
        return False

    try:
        info = client.payment_requests.get(id=int(order_code))
        status = (
            getattr(info, 'status', None)
            or ''
        )
        return str(status).upper() == 'PAID'
    except Exception:
        try:
            info = client.getPaymentLinkInformation(orderId=int(order_code))
            status = getattr(info, 'status', None) or ''
            return str(status).upper() == 'PAID'
        except Exception:
            return False
