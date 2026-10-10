import pytest
from unittest.mock import mock_open, patch
import calendar_sync

def test_fetch_calendar_context_error_path():
    """
    Test that fetch_calendar_context returns [] when a file read error occurs.
    """
    with patch('builtins.open', side_effect=Exception('File read error')):
        result = calendar_sync.fetch_calendar_context()
        assert result == []
