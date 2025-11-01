import hashlib
import hmac
import urllib.parse
from django.conf import settings

def check_telegram_data_integrity(init_data: str) -> bool:
    """
    Checks the hash of the Telegram initData to ensure its authenticity.
    See: https://core.telegram.org/bots/webapps#checking-authorization
    """
    if not init_data:
        return False

    # 1. Parse the query string data
    data_check_string = []
    # Sort data parameters by key
    for pair in sorted(init_data.split('&')):
        if pair.startswith('hash='):
            continue
        # Use urllib.parse.unquote to decode URL-encoded values
        data_check_string.append(urllib.parse.unquote(pair))

    # Join sorted and decoded parameters with '\n'
    data_check_string = '\n'.join(data_check_string)
    
    # 2. Extract the hash from init_data
    auth_hash = dict(urllib.parse.parse_qsl(init_data)).get('hash', '')

    # 3. Derive the secret key
    # Key is HMAC-SHA256 of the string 'WebAppData' using the Bot Token as the key
    secret_key = hmac.new(
        key='WebAppData'.encode(),
        msg=settings.TELEGRAM_BOT_TOKEN.encode(), # MAKE SURE THIS IS IN settings.py
        digestmod=hashlib.sha256
    ).digest()

    # 4. Calculate the hash of the data_check_string
    calculated_hash = hmac.new(
        key=secret_key,
        msg=data_check_string.encode(),
        digestmod=hashlib.sha256
    ).hexdigest()

    # 5. Compare
    return calculated_hash == auth_hash