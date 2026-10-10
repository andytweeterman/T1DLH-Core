import pytest
from unittest.mock import patch, mock_open
import sys

# Import app normally; tests use patch on builtins.open
import app

def test_load_ns_config_success():
    """Verify that configuration is correctly loaded from a valid JSON file."""
    mock_data = '{"url": "http://test", "token": "test_token"}'
    with patch("builtins.open", mock_open(read_data=mock_data)):
        result = app.load_ns_config()
    assert result == {"url": "http://test", "token": "test_token"}

def test_load_ns_config_file_not_found():
    """Verify that default config is returned when file is missing."""
    with patch("builtins.open", side_effect=FileNotFoundError):
        result = app.load_ns_config()
    assert result == {"url": "", "token": ""}

def test_load_ns_config_json_decode_error():
    """Verify that default config is returned when file contains invalid JSON."""
    mock_data = 'invalid json'
    with patch("builtins.open", mock_open(read_data=mock_data)):
        result = app.load_ns_config()
    assert result == {"url": "", "token": ""}
