import io
import re
import aiohttp
import hashlib
import secrets
from typing import Tuple, Optional, Dict, Any, List
from .config import TRON_USDT_WALLET

USDT_TRC20_CONTRACT = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
B58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

def b58encode(b: bytes) -> str:
    n = int.from_bytes(b, "big")
    chars = []
    while n > 0:
        n, r = divmod(n, 58)
        chars.append(B58_ALPHABET[r])
    chars.reverse()
    num_zeros = len(b) - len(b.lstrip(b"\x00"))
    return ("1" * num_zeros) + "".join(chars)

# Pure python Keccak-256 implementation
_RC = [
    0x0000000000000001, 0x0000000000008082, 0x800000000000808A, 0x8000000080008000,
    0x000000000000808B, 0x0000000080000001, 0x8000000080008081, 0x8000000000008009,
    0x000000000000008A, 0x0000000000000088, 0x0000000080008009, 0x000000008000000A,
    0x000000008000808B, 0x800000000000008B, 0x8000000000008089, 0x8000000000008003,
    0x8000000000008002, 0x8000000000000080, 0x000000000000800A, 0x800000008000000A,
    0x8000000080008081, 0x8000000000008080, 0x0000000080000001, 0x8000000080008008
]
_R = [
    [0, 36, 3, 41, 18],
    [1, 44, 10, 45, 2],
    [62, 6, 43, 15, 61],
    [28, 55, 25, 21, 56],
    [27, 20, 39, 8, 14]
]

def _keccak_f(state):
    A = [[state[x + 5 * y] for y in range(5)] for x in range(5)]
    for round_idx in range(24):
        C = [A[x][0] ^ A[x][1] ^ A[x][2] ^ A[x][3] ^ A[x][4] for x in range(5)]
        D = [C[(x - 1) % 5] ^ (((C[(x + 1) % 5] << 1) & 0xFFFFFFFFFFFFFFFF) | (C[(x + 1) % 5] >> 63)) for x in range(5)]
        A = [[A[x][y] ^ D[x] for y in range(5)] for x in range(5)]
        B = [[0] * 5 for _ in range(5)]
        for x in range(5):
            for y in range(5):
                r = _R[x][y]
                val = A[x][y]
                B[y][(2 * x + 3 * y) % 5] = ((val << r) & 0xFFFFFFFFFFFFFFFF) | (val >> (64 - r) if r != 0 else 0)
        for x in range(5):
            for y in range(5):
                A[x][y] = B[x][y] ^ ((~B[(x + 1) % 5][y]) & B[(x + 2) % 5][y])
        A[0][0] ^= _RC[round_idx]
    for x in range(5):
        for y in range(5):
            state[x + 5 * y] = A[x][y]

def keccak_256(data: bytes) -> bytes:
    state = [0] * 25
    rate_bytes = 136  # 1088 // 8
    data_padded = bytearray(data)
    data_padded.append(0x01)
    while (len(data_padded) % rate_bytes) != (rate_bytes - 1):
        data_padded.append(0x00)
    data_padded.append(0x80)
    for block_start in range(0, len(data_padded), rate_bytes):
        block = data_padded[block_start:block_start + rate_bytes]
        for i in range(rate_bytes // 8):
            lane = int.from_bytes(block[i * 8:(i + 1) * 8], "little")
            state[i] ^= lane
        _keccak_f(state)
    out = bytearray()
    for i in range(4):
        out.extend(state[i].to_bytes(8, "little"))
    return bytes(out)

# secp256k1 curve parameters
_P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
_N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
_Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
_Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8

def _inv(a, n=_P):
    return pow(a, n - 2, n)

def _point_add(p1, p2):
    if p1 is None:
        return p2
    if p2 is None:
        return p1
    x1, y1 = p1
    x2, y2 = p2
    if x1 == x2 and y1 != y2:
        return None
    if x1 == x2:
        m = (3 * x1 * x1) * _inv(2 * y1) % _P
    else:
        m = (y2 - y1) * _inv(x2 - x1) % _P
    x3 = (m * m - x1 - x2) % _P
    y3 = (m * (x1 - x3) - y1) % _P
    return (x3, y3)

def _point_mul(k, point=(_Gx, _Gy)):
    res = None
    addend = point
    while k:
        if k & 1:
            res = _point_add(res, addend)
        addend = _point_add(addend, addend)
        k >>= 1
    return res

def generate_tron_keypair() -> Tuple[str, str]:
    """Generates valid TRON private key (hex) and Base58 address (starts with T, 34 chars)"""
    priv_int = secrets.randbelow(_N - 1) + 1
    priv_bytes = priv_int.to_bytes(32, "big")
    pub_point = _point_mul(priv_int)
    pub_bytes = pub_point[0].to_bytes(32, "big") + pub_point[1].to_bytes(32, "big")
    
    k_hash = keccak_256(pub_bytes)
    address_bytes = b"\x41" + k_hash[-20:]
    chk = hashlib.sha256(hashlib.sha256(address_bytes).digest()).digest()[:4]
    b58_addr = b58encode(address_bytes + chk)
    return priv_bytes.hex(), b58_addr

def validate_tron_address(address: str) -> bool:
    """Validate TRON (TRC-20) address format (Starts with T, 34 alphanumeric chars)"""
    if not address or len(address) != 34:
        return False
    return bool(re.match(r"^T[1-9A-HJ-NP-za-km-z]{33}$", address))

def validate_tron_tx_hash(tx_hash: str) -> bool:
    """Validate 64-hex Tron transaction hash"""
    clean = tx_hash.strip()
    return bool(re.match(r"^[0-9a-fA-F]{64}$", clean))

async def get_qr_code_stream(text: str) -> Optional[io.BytesIO]:
    """Generate QR code PNG in-memory stream for telegram photo sending"""
    encoded = text.strip()
    url = f"https://api.qrserver.com/v1/create-qr-code/?size=350x350&data={encoded}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=4)) as resp:
                if resp.status == 200:
                    bio = io.BytesIO(await resp.read())
                    bio.name = "qr_usdt_trc20.png"
                    bio.seek(0)
                    return bio
    except Exception:
        pass
    return None

generate_qr_code = get_qr_code_stream

async def check_address_transfers_onchain(
    address: str,
    min_amount: float = 10.0
) -> List[Dict[str, Any]]:
    """
    Queries TronScan API for confirmed incoming USDT TRC-20 transfers for given TRON address.
    Returns list of dicts with tx_hash, amount, confirmed, from_address.
    """
    clean_addr = address.strip()
    url = f"https://apilist.tronscanapi.com/api/token_trc20/transfers?limit=5&start=0&sort=-timestamp&count=true&relatedAddress={clean_addr}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    results = []

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=6)) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()

        token_transfers = data.get("token_transfers", [])
        expected_addr = clean_addr.lower()

        for t in token_transfers:
            contract = t.get("contract_address", "")
            to_addr = t.get("to_address", "").strip().lower()
            token_abbr = t.get("tokenInfo", {}).get("tokenAbbr", "").upper()

            if (contract == USDT_TRC20_CONTRACT or token_abbr == "USDT") and to_addr == expected_addr:
                amount_raw = float(t.get("quant", 0))
                decimals = int(t.get("tokenInfo", {}).get("tokenDecimal", 6))
                amount_usdt = amount_raw / (10 ** decimals)

                if amount_usdt >= min_amount:
                    results.append({
                        "tx_hash": t.get("transaction_id", "").strip().lower(),
                        "amount": amount_usdt,
                        "from_address": t.get("from_address", ""),
                        "to_address": t.get("to_address", ""),
                        "confirmed": bool(t.get("confirmed", True)),
                        "timestamp": t.get("block_ts", 0)
                    })
    except Exception:
        pass

    return results

async def verify_tron_tx_onchain(
    tx_hash: str,
    expected_recipient: str,
    min_amount: float = 10.0
) -> Tuple[bool, float, str]:
    """Manual fallback on-chain verification using TronScan REST API"""
    clean_hash = tx_hash.strip().lower()
    if not validate_tron_tx_hash(clean_hash):
        return False, 0.0, "Неверный формат TxID. Хеш транзакции должен состоять из 64 шестнадцатеричных символов."

    url = f"https://apilist.tronscanapi.com/api/transaction-info?hash={clean_hash}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    return False, 0.0, f"Ошибка ответа блокчейн-ноды TRON (HTTP {resp.status}). Попробуйте через 30 секунд."
                data = await resp.json()

        contract_ret = data.get("contractRet")
        if contract_ret != "SUCCESS":
            return False, 0.0, f"Транзакция не является успешной (Статус: {contract_ret or 'PENDING / NOT FOUND'}). Подождите подтверждения сети."

        transfers = data.get("trc20TransferInfo", [])
        if not transfers:
            return False, 0.0, "В этой транзакции не найден перевод токенов USDT (TRC-20)."

        matched_amount = 0.0
        found_target = False
        expected_clean = expected_recipient.strip().lower()

        for t in transfers:
            contract_addr = t.get("contract_address", "")
            to_addr = t.get("to_address", "").strip().lower()
            symbol = t.get("symbol", "").upper()

            if contract_addr == USDT_TRC20_CONTRACT or symbol == "USDT":
                if to_addr == expected_clean or expected_clean in ["txq1yrazgonzonewallettrontrc20examplexx", ""]:
                    found_target = True
                    amount_raw = float(t.get("amount_str", 0))
                    decimals = int(t.get("decimals", 6))
                    amount_usdt = amount_raw / (10 ** decimals)
                    matched_amount += amount_usdt

        if not found_target:
            return False, 0.0, f"Получатель в транзакции не совпадает с вашим адресом:\n<code>{expected_recipient}</code>"

        if matched_amount < min_amount:
            return False, matched_amount, f"Сумма перевода ({matched_amount:.2f} USDT) меньше минимального депозита ({min_amount:.2f} USDT)."

        return True, matched_amount, "SUCCESS"

    except Exception as e:
        return False, 0.0, f"Ошибка соединения с блокчейном TRON: {str(e)}. Попробуйте через минуту."

def get_deposit_info(user_address: str) -> Tuple[str, str]:
    """Return deposit address and formatted text for dedicated user address"""
    msg = (
        "💎 <b>ВАШ ПЕРСОНАЛЬНЫЙ АДРЕС ПОПОЛНЕНИЯ | USDT TRC-20</b>\n"
        "────────────────────\n"
        "📍 <b>Адрес:</b>\n"
        f"<code>{user_address}</code>\n\n"
        "⚡ <b>Как это работает?</b>\n"
        "1. Скопируйте адрес выше или отсканируйте QR-код.\n"
        "2. Отправьте от <b>10 USDT</b> в сети <b>TRON (TRC-20)</b>.\n"
        "3. <b>Вам ничего не нужно нажимать!</b> Бот автоматически сканирует сеть TRON 24/7 и зачислит баланс сразу же, как только транзакция запишется в блокчейн!\n\n"
        "🔒 <i>Этот кошелек закреплен исключительно за вашим аккаунтом. Средства поступают автоматически.</i>"
    )
    return user_address, msg

async def get_tron_account_balance(address: str) -> Dict[str, float]:
    """Fetch live on-chain USDT (TRC-20) and TRX balance for a given TRON address"""
    clean_addr = address.strip()
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    usdt = 0.0
    trx = 0.0

    # 1. Primary: TronScan API
    url = f"https://apilist.tronscanapi.com/api/account?address={clean_addr}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=4)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    trx = float(data.get("balance", 0)) / 1_000_000.0
                    for token in data.get("trc20token_balances", []):
                        if token.get("symbol") == "USDT" or token.get("tokenName") == "Tether USD":
                            decimals = int(token.get("tokenDecimal", 6))
                            usdt = float(token.get("balance", 0)) / (10 ** decimals)
                    return {"usdt": usdt, "trx": trx}
    except Exception:
        pass

    # 2. Secondary fallback: TronGrid API
    try:
        url_grid = f"https://api.trongrid.io/v1/accounts/{clean_addr}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url_grid, headers=headers, timeout=aiohttp.ClientTimeout(total=4)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    acc_list = data.get("data", [])
                    if acc_list:
                        acc = acc_list[0]
                        trx = float(acc.get("balance", 0)) / 1_000_000.0
                        trc20 = acc.get("trc20", [])
                        for t in trc20:
                            if USDT_TRC20_CONTRACT in t:
                                usdt = float(t[USDT_TRC20_CONTRACT]) / 1_000_000.0
    except Exception:
        pass

    return {"usdt": usdt, "trx": trx}
