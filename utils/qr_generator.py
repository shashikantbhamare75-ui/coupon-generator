import os
import qrcode
from config import Config


def generate_qr_code(data: str, filename: str) -> str:
    """
    Generates a QR code image for the given data and saves it to the QR folder.
    Returns the relative static path to the saved image.
    """
    os.makedirs(Config.QR_CODE_FOLDER, exist_ok=True)

    img = qrcode.make(data)
    filepath = os.path.join(Config.QR_CODE_FOLDER, filename)
    img.save(filepath)

    return f'qrcodes/{filename}'