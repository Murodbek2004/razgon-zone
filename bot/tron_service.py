import io
import qrcode
import re
from typing import Tuple, Optional
from .config import TRON_USDT_WALLET

def validate_tron_address(address: str) -> bool:
    """Validate TRON (TRC-20) address format (Starts with T, 34 alphanumeric chars)"""
    if not address or len(address) != 34:
        return False
    return bool(re.match(r"^T[1-9A-HJ-NP-za-km-z]{33}$", address))

def validate_tron_tx_hash(tx_hash: str) -> bool:
    """Validate 64-hex Tron transaction hash"""
    clean = tx_hash.strip()
    return bool(re.match(r"^[0-9a-fA-F]{64}$", clean))

def generate_qr_code(text: str) -> io.BytesIO:
    """Generate QR code PNG in-memory stream for telegram photo sending"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#00FFA3", back_color="#0A0E17")
    bio = io.BytesIO()
    bio.name = "qr_usdt_trc20.png"
    img.save(bio, "PNG")
    bio.seek(0)
    return bio

def get_deposit_info(user_id: int) -> Tuple[str, str]:
    """Return deposit address and formatted text"""
    addr = TRON_USDT_WALLET
    msg = (
        "💎 <b>Пополнение баланса | USDT (TRC-20)</b>\n\n"
        f"📍 <b>Адрес для перевода:</b>\n<code>{addr}</code>\n\n"
        "⚠️ <b>Важные правила:</b>\n"
        "• Сеть: <b>TRON (TRC-20)</b>\n"
        "• Валюта: <b>Tether USD (USDT)</b>\n"
        "• Минимальный депозит: <b>10 USDT</b>\n"
        "• Отправка любой другой валюты приведет к потере средств.\n\n"
        "После перевода нажмите <b>«Подтвердить транзакцию»</b> и отправьте TxID (хеш перевода)."
    )
    return addr, msg
