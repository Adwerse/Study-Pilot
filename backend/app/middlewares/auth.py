import hashlib
import hmac
import json
from urllib.parse import parse_qs

from fastapi import HTTPException, status


def validate_init_data(init_data: str, bot_token: str) -> dict:
    parsed = parse_qs(init_data, keep_blank_values=True)
    data: dict[str, object] = {
        key: values[0] for key, values in parsed.items() if values
    }

    received_hash = data.pop("hash", None)
    if not isinstance(received_hash, str) or not received_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid initData"
        )

    data_check_string = "\n".join(f"{key}={data[key]}" for key in sorted(data.keys()))

    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    calculated_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid initData"
        )

    if "user" in data:
        try:
            data["user"] = json.loads(str(data["user"]))
        except (json.JSONDecodeError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid initData"
            )

    return data


def get_telegram_user(init_data: str, bot_token: str) -> dict:
    data = validate_init_data(init_data, bot_token)
    user = data.get("user")
    if not isinstance(user, dict):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid initData"
        )
    return user
