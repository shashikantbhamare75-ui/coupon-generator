import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader

from config import Config


def generate_coupons_pdf(session, coupons, output_filename):
    """
    Generates a printable PDF with a grid of coupons (3 columns x 4 rows per page),
    each showing session info, coupon ID, and its QR code.
    Returns the full filepath of the generated PDF.
    """
    os.makedirs(Config.PDF_FOLDER, exist_ok=True)
    filepath = os.path.join(Config.PDF_FOLDER, output_filename)

    page_width, page_height = A4
    c = canvas.Canvas(filepath, pagesize=A4)

    cols, rows = 3, 4
    margin = 10 * mm
    cell_width = (page_width - 2 * margin) / cols
    cell_height = (page_height - 2 * margin) / rows

    for index, coupon in enumerate(coupons):
        pos_in_page = index % (cols * rows)
        if index > 0 and pos_in_page == 0:
            c.showPage()

        col = pos_in_page % cols
        row = pos_in_page // cols

        x = margin + col * cell_width
        y = page_height - margin - (row + 1) * cell_height

        # Cell border
        c.rect(x + 2, y + 2, cell_width - 4, cell_height - 4)

        # Header
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(x + cell_width / 2, y + cell_height - 14, "FOOD COUPON")

        c.setFont("Helvetica", 8)
        c.drawCentredString(x + cell_width / 2, y + cell_height - 26, session.session_name[:28])
        c.drawCentredString(x + cell_width / 2, y + cell_height - 36, session.session_date.strftime('%d-%m-%Y'))
        if session.food_item:
            c.drawCentredString(x + cell_width / 2, y + cell_height - 46, session.food_item[:28])

        # QR code image
        qr_path = os.path.join(Config.QR_CODE_FOLDER, f"{coupon.secure_token}.png")
        qr_size = min(cell_width, cell_height) * 0.5
        qr_x = x + (cell_width - qr_size) / 2
        qr_y = y + 16
        if os.path.exists(qr_path):
            c.drawImage(ImageReader(qr_path), qr_x, qr_y, width=qr_size, height=qr_size)

        # Coupon ID + status
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(x + cell_width / 2, y + 8, coupon.coupon_code)

    c.save()
    return filepath