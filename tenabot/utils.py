import hashlib
import hmac
import urllib.parse
from django.conf import settings

def check_telegram_data_integrity(init_data: str) -> bool:
    """
    Verifies Telegram WebApp initData integrity according to Telegram spec.
    """
    if not init_data:
        return False

    # 1. Parse and prepare data_check_string
    data_check_arr = []
    parsed_data = urllib.parse.parse_qsl(init_data)
    for key, value in sorted(parsed_data):
        if key == 'hash':
            continue
        data_check_arr.append(f"{key}={value}")
    data_check_string = "\n".join(data_check_arr)

    # 2. Extract the hash from init_data
    auth_hash = dict(parsed_data).get('hash', '')

    # 3. Correct secret key derivation (reversed in your code)
    secret_key = hmac.new(
        settings.TELEGRAM_BOT_TOKEN.encode(),
        b"WebAppData",
        hashlib.sha256
    ).digest()

    # 4. Calculate the hash of the data_check_string
    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()

    # 5. Compare
    return calculated_hash == auth_hash
