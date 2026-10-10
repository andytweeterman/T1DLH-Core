import base64
import json
import hashlib
from cryptography.fernet import Fernet
from cryptography.fernet import InvalidToken

def _get_fernet(key: str) -> Fernet:
    # Fernet requires a 32-byte url-safe base64-encoded key
    derived_key = hashlib.sha256(key.encode()).digest()
    b64_key = base64.urlsafe_b64encode(derived_key)
    return Fernet(b64_key)

def encrypt_token(token: str, key: str) -> str:
    if not token or not key: return token or ""
    f = _get_fernet(key)
    return f.encrypt(token.encode()).decode()

def decrypt_token(token: str, key: str) -> str:
    if not token: return ""
    if not key: return token

    try:
        f = _get_fernet(key)
        return f.decrypt(token.encode()).decode()
    except (InvalidToken, ValueError):
        return ""

def load_ns_config(key: str):
    try:
        with open("ns_config.json", "r") as f:
            data = json.load(f)
            if key and data.get("token"):
                data["token"] = decrypt_token(data["token"], key)
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        return {"url": "", "token": ""}

def save_ns_config(url, token, key: str):
    try:
        encrypted_token = encrypt_token(token, key) if key else token
        with open("ns_config.json", "w") as f:
            json.dump({"url": url, "token": encrypted_token}, f)
    except Exception as e:
        pass
