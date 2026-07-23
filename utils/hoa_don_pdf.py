import os
from io import BytesIO
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


_FONT_REGISTERED = False


def _dang_ky_font():
    global _FONT_REGISTERED
    if _FONT_REGISTERED:
        return

    font_dir = os.path.join(
        os.environ.get('WINDIR', r'C:\Windows'),
        'Fonts'
    )
    regular = os.path.join(font_dir, 'arial.ttf')
    bold = os.path.join(font_dir, 'arialbd.ttf')

    if not os.path.exists(regular):
        raise FileNotFoundError(
            'Không tìm thấy font Arial để xuất PDF tiếng Việt'
        )

    pdfmetrics.registerFont(TTFont('VNFont', regular))
    if os.path.exists(bold):
        pdfmetrics.registerFont(TTFont('VNFont-Bold', bold))
    else:
        pdfmetrics.registerFont(TTFont('VNFont-Bold', regular))

    _FONT_REGISTERED = True


def _format_tien(so_tien):
    try:
        return f'{float(so_tien):,.0f}'.replace(',', '.') + ' đ'
    except (TypeError, ValueError):
        return '0 đ'


def _ten_phuong_thuc(ma):
    mapping = {
        'TIEN_MAT': 'Tiền mặt',
        'CHUYEN_KHOAN': 'Chuyển khoản',
        'QR': 'QR',
    }
    return mapping.get(ma, ma or '—')


def tao_hoa_don_pdf(hoa_don, ds_chi_tiet, chi_nhanh=None):
    """Tạo file PDF hóa đơn, trả về BytesIO."""
    _dang_ky_font()

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    styles = getSampleStyleSheet()
    style_title = ParagraphStyle(
        'TitleVN',
        parent=styles['Title'],
        fontName='VNFont-Bold',
        fontSize=18,
        alignment=TA_CENTER,
        spaceAfter=6,
    )
    style_center = ParagraphStyle(
        'CenterVN',
        parent=styles['Normal'],
        fontName='VNFont',
        fontSize=10,
        alignment=TA_CENTER,
        spaceAfter=3,
    )
    style_normal = ParagraphStyle(
        'NormalVN',
        parent=styles['Normal'],
        fontName='VNFont',
        fontSize=10,
        alignment=TA_LEFT,
        spaceAfter=3,
    )
    style_bold = ParagraphStyle(
        'BoldVN',
        parent=styles['Normal'],
        fontName='VNFont-Bold',
        fontSize=10,
        alignment=TA_LEFT,
        spaceAfter=3,
    )
    style_right = ParagraphStyle(
        'RightVN',
        parent=styles['Normal'],
        fontName='VNFont-Bold',
        fontSize=11,
        alignment=TA_RIGHT,
    )
    style_cell = ParagraphStyle(
        'CellVN',
        parent=styles['Normal'],
        fontName='VNFont',
        fontSize=9,
        leading=12,
    )
    style_cell_bold = ParagraphStyle(
        'CellBoldVN',
        parent=styles['Normal'],
        fontName='VNFont-Bold',
        fontSize=9,
        leading=12,
    )

    ten_cua_hang = (
        chi_nhanh.ten_chi_nhanh
        if chi_nhanh and chi_nhanh.ten_chi_nhanh
        else 'eMenu'
    )

    dia_chi = (
        chi_nhanh.dia_chi
        if chi_nhanh and chi_nhanh.dia_chi
        else ''
    )
    sdt_cua_hang = (
        chi_nhanh.dien_thoai
        if chi_nhanh and chi_nhanh.dien_thoai
        else ''
    )

    thoi_gian_xuat = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

    ten_khach = '—'
    sdt_khach = '—'
    if hoa_don.khach_hang:
        ten_khach = hoa_don.khach_hang.ten_khach_hang or '—'
        sdt_khach = hoa_don.khach_hang.dien_thoai or '—'

    ten_ban = hoa_don.ban.ten_ban if hoa_don.ban else '—'
    nhan_vien = (
        hoa_don.nguoi_dung.ho_ten
        if hoa_don.nguoi_dung
        else '—'
    )

    story = []
    story.append(Paragraph('HÓA ĐƠN THANH TOÁN', style_title))
    story.append(Paragraph(ten_cua_hang, style_center))
    story.append(
        Paragraph(
            f'Địa chỉ cửa hàng: {dia_chi or "................................"}',
            style_center,
        )
    )
    if sdt_cua_hang:
        story.append(
            Paragraph(f'Điện thoại: {sdt_cua_hang}', style_center)
        )
    story.append(Spacer(1, 8))

    info_rows = [
        [
            Paragraph(
                f'<b>Mã hóa đơn:</b> {hoa_don.ma_hoa_don}',
                style_normal,
            ),
            Paragraph(
                f'<b>Thời gian xuất:</b> {thoi_gian_xuat}',
                style_normal,
            ),
        ],
        [
            Paragraph(f'<b>Bàn:</b> {ten_ban}', style_normal),
            Paragraph(
                f'<b>Nhân viên:</b> {nhan_vien}',
                style_normal,
            ),
        ],
        [
            Paragraph(
                f'<b>Khách hàng:</b> {ten_khach}',
                style_normal,
            ),
            Paragraph(
                f'<b>SĐT khách:</b> {sdt_khach}',
                style_normal,
            ),
        ],
    ]

    info_table = Table(info_rows, colWidths=[90 * mm, 80 * mm])
    info_table.setStyle(
        TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ])
    )
    story.append(info_table)
    story.append(Spacer(1, 10))
    story.append(Paragraph('Chi tiết món', style_bold))
    story.append(Spacer(1, 4))

    table_data = [[
        Paragraph('STT', style_cell_bold),
        Paragraph('Tên món', style_cell_bold),
        Paragraph('Đơn giá', style_cell_bold),
        Paragraph('SL', style_cell_bold),
        Paragraph('Thành tiền', style_cell_bold),
    ]]

    for i, ct in enumerate(ds_chi_tiet, start=1):
        ten_mon = ct.hang_hoa.ten_hang if ct.hang_hoa else '—'
        table_data.append([
            Paragraph(str(i), style_cell),
            Paragraph(ten_mon, style_cell),
            Paragraph(_format_tien(ct.don_gia), style_cell),
            Paragraph(str(ct.so_luong), style_cell),
            Paragraph(_format_tien(ct.thanh_tien), style_cell),
        ])

    if len(table_data) == 1:
        table_data.append([
            Paragraph('', style_cell),
            Paragraph('Không có món', style_cell),
            Paragraph('', style_cell),
            Paragraph('', style_cell),
            Paragraph('', style_cell),
        ])

    mon_table = Table(
        table_data,
        colWidths=[12 * mm, 70 * mm, 35 * mm, 15 * mm, 38 * mm],
    )
    mon_table.setStyle(
        TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f0f0f0')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (2, 1), (4, -1), 'RIGHT'),
            ('ALIGN', (3, 0), (3, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ])
    )
    story.append(mon_table)
    story.append(Spacer(1, 12))

    story.append(
        Paragraph(
            f'Tổng tiền: {_format_tien(hoa_don.tong_tien)}',
            style_right,
        )
    )
    story.append(Spacer(1, 6))
    story.append(
        Paragraph(
            f'Phương thức thanh toán: '
            f'{_ten_phuong_thuc(hoa_don.phuong_thuc_thanh_toan)}',
            style_normal,
        )
    )
    story.append(
        Paragraph(
            'Trạng thái: Đã thanh toán',
            style_normal,
        )
    )
    story.append(Spacer(1, 20))
    story.append(
        Paragraph(
            'Cảm ơn quý khách và hẹn gặp lại!',
            style_center,
        )
    )

    doc.build(story)
    buffer.seek(0)
    return buffer
