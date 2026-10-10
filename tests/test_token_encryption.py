import crypto
import os
import json
from unittest.mock import patch, mock_open

def test_encrypt_decrypt_token():
    test_token = "my-secret-nightscout-token-123"
    key = "my-admin-password"

    encrypted = crypto.encrypt_token(test_token, key)
    assert encrypted != test_token
    decrypted = crypto.decrypt_token(encrypted, key)
    assert decrypted == test_token

def test_encrypt_decrypt_empty_token():
    key = "my-admin-password"
    assert crypto.encrypt_token("", key) == ""
    assert crypto.encrypt_token(None, key) == ""
    assert crypto.decrypt_token("", key) == ""
    assert crypto.decrypt_token(None, key) == ""

def test_decrypt_invalid_token():
    key = "my-admin-password"
    assert crypto.decrypt_token("invalid-base64-string!!", key) == ""

def test_save_load_config():
    url = "https://example.com"
    token = "secret123"
    key = "my-admin-password"

    with patch('builtins.open', mock_open()) as mocked_file:
        crypto.save_ns_config(url, token, key)
        mocked_file.assert_called_with("ns_config.json", "w")

    encrypted_token = crypto.encrypt_token(token, key)
    mock_json_content = f'{{"url": "{url}", "token": "{encrypted_token}"}}'
    with patch('builtins.open', mock_open(read_data=mock_json_content)):
        data = crypto.load_ns_config(key)
        assert data["url"] == url
        assert data["token"] == token

if __name__ == "__main__":
    test_encrypt_decrypt_token()
    test_encrypt_decrypt_empty_token()
    test_decrypt_invalid_token()
    test_save_load_config()
    print("All crypto tests passed.")
