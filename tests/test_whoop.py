import sys
import unittest
from unittest.mock import patch, MagicMock, mock_open
import time
import json
import os
import requests

class SessionState(dict):
    def __getattr__(self, key):
        if key in self:
            return self[key]
        raise AttributeError(f"st.session_state has no attribute '{key}'")
    def __setattr__(self, key, value):
        self[key] = value

# Create a mock streamlit module
import streamlit as real_st
mock_st = MagicMock()
mock_st.secrets = {
    "WHOOP_CLIENT_ID": "mock_client_id",
    "WHOOP_CLIENT_SECRET": "mock_client_secret",
    "WHOOP_REDIRECT_URI": "http://mock_redirect_uri"
}
mock_st.session_state = SessionState()
mock_st.cache_data = real_st.cache_data
mock_st.cache_resource = real_st.cache_resource
mock_st.error = MagicMock()

# Inject into sys.modules BEFORE importing whoop
sys.modules['streamlit'] = mock_st

import whoop

class TestWhoop(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        # Cleanup injected mock
        if 'streamlit' in sys.modules and sys.modules['streamlit'] == mock_st:
            del sys.modules['streamlit']

    def setUp(self):
        # Reset session state and clear caches
        mock_st.session_state.clear()
        mock_st.error.reset_mock()
        if hasattr(whoop.fetch_whoop_recovery, 'clear'):
            whoop.fetch_whoop_recovery.clear()

    def test_get_authorization_url(self):
        url = whoop.get_authorization_url()
        self.assertIn("client_id=mock_client_id", url)
        self.assertIn("redirect_uri=http%3A%2F%2Fmock_redirect_uri", url)
        self.assertIn("response_type=code", url)

    @patch('whoop.requests.post')
    def test_get_access_token_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"access_token": "token123", "expires_in": 3600}
        mock_post.return_value = mock_response

        result = whoop.get_access_token("auth_code_xyz")

        mock_post.assert_called_once()
        self.assertEqual(result, {"access_token": "token123", "expires_in": 3600})

    @patch('whoop.requests.post')
    def test_get_access_token_error(self, mock_post):
        mock_post.side_effect = Exception("Network Error")

        result = whoop.get_access_token("auth_code_xyz")

        self.assertIsNone(result)
        mock_st.error.assert_called_once()

    @patch('whoop.requests.get')
    def test_fetch_whoop_recovery_success(self, mock_get):
        mock_cycle_response = MagicMock()
        mock_cycle_response.status_code = 200
        mock_cycle_response.json.return_value = {
            "records": [{
                "recovery": {"score": {"recovery_score": 85, "hrv_rmssd_milli": 60.5, "resting_heart_rate": 50}},
                "score": {"strain": 12.5}
            }]
        }

        mock_sleep_response = MagicMock()
        mock_sleep_response.status_code = 200
        mock_sleep_response.json.return_value = {
            "records": [{
                "score": {"sleep_performance_percentage": 95}
            }]
        }

        mock_get.side_effect = [mock_cycle_response, mock_sleep_response]

        result = whoop.fetch_whoop_recovery("fake_token")

        self.assertIsNotNone(result)
        self.assertEqual(result["score"]["recovery_score"], 85)
        self.assertEqual(result["score"]["hrv_rmssd_milli_seconds"], 60.5)
        self.assertEqual(result["score"]["resting_heart_rate_beats_per_minute"], 50)
        self.assertEqual(result["score"]["day_strain"], 12.5)
        self.assertEqual(result["score"]["sleep_performance_percentage"], 95)

    @patch('whoop.requests.get')
    def test_fetch_whoop_recovery_missing_recovery_score(self, mock_get):
        mock_cycle_response = MagicMock()
        mock_cycle_response.status_code = 200
        mock_cycle_response.json.return_value = {
            "records": [{
                "score": {"recovery_score": 75, "hrv_rmssd_milli": 55.5, "resting_heart_rate": 52, "strain": 10.0}
            }]
        }

        mock_sleep_response = MagicMock()
        mock_sleep_response.status_code = 200
        mock_sleep_response.json.return_value = {
            "records": [{
                "score": {"sleep_performance_percentage": 90}
            }]
        }

        mock_get.side_effect = [mock_cycle_response, mock_sleep_response]

        result = whoop.fetch_whoop_recovery("fake_token")

        self.assertIsNotNone(result)
        self.assertEqual(result["score"]["recovery_score"], 75)
        self.assertEqual(result["score"]["hrv_rmssd_milli_seconds"], 55.5)

    @patch('whoop.requests.get')
    def test_fetch_whoop_recovery_api_error(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        result = whoop.fetch_whoop_recovery("fake_token")
        self.assertIsNone(result)

    @patch('whoop.requests.get')
    def test_fetch_whoop_recovery_exception(self, mock_get):
        mock_get.side_effect = requests.exceptions.Timeout("Timeout")

        result = whoop.fetch_whoop_recovery("fake_token")

        self.assertIsNone(result)

    @patch('whoop.open', new_callable=mock_open)
    @patch('whoop.time.time', return_value=1000)
    def test_save_tokens(self, mock_time, mock_file):
        token_data = {"access_token": "my_token", "expires_in": 3600}
        whoop.save_tokens(token_data)

        self.assertEqual(mock_st.session_state.whoop_token, "my_token")
        self.assertEqual(token_data['expires_at'], 4600)
        mock_file.assert_called_once_with(whoop.TOKEN_FILE, 'w')

    @patch('whoop.open', side_effect=PermissionError)
    @patch('whoop.time.time', return_value=1000)
    def test_save_tokens_exception(self, mock_time, mock_file):
        token_data = {"access_token": "my_token", "expires_in": 3600}
        whoop.save_tokens(token_data)
        self.assertEqual(mock_st.session_state.whoop_token, "my_token")

    @patch('whoop.open', new_callable=mock_open, read_data='{"access_token": "loaded_token"}')
    def test_load_tokens_success(self, mock_file):
        result = whoop.load_tokens()
        self.assertEqual(result, {"access_token": "loaded_token"})

    @patch('whoop.open', side_effect=FileNotFoundError)
    def test_load_tokens_not_found(self, mock_file):
        result = whoop.load_tokens()
        self.assertIsNone(result)

    @patch('whoop.requests.post')
    @patch('whoop.save_tokens')
    def test_refresh_access_token_success(self, mock_save, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"access_token": "new_token"}
        mock_post.return_value = mock_response

        result = whoop.refresh_access_token("old_refresh")
        self.assertEqual(result, "new_token")
        mock_save.assert_called_once_with({"access_token": "new_token"})

    @patch('whoop.requests.post')
    def test_refresh_access_token_error(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_post.return_value = mock_response

        result = whoop.refresh_access_token("old_refresh")
        self.assertIsNone(result)

    @patch('whoop.requests.post')
    def test_refresh_access_token_exception(self, mock_post):
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection Error")
        result = whoop.refresh_access_token("old_refresh")
        self.assertIsNone(result)

    @patch('whoop.load_tokens')
    def test_get_valid_access_token_from_session(self, mock_load):
        mock_st.session_state.whoop_token = "session_token"
        result = whoop.get_valid_access_token()
        self.assertEqual(result, "session_token")
        mock_load.assert_not_called()

    @patch('whoop.load_tokens')
    @patch('whoop.time.time')
    @patch('whoop.refresh_access_token')
    def test_get_valid_access_token_from_vault_valid(self, mock_refresh, mock_time, mock_load):
        mock_st.session_state.clear()
        mock_time.return_value = 1000
        mock_load.return_value = {"access_token": "vault_token", "expires_at": 2000, "refresh_token": "refresh"}

        result = whoop.get_valid_access_token()
        self.assertEqual(result, "vault_token")
        mock_refresh.assert_not_called()

    @patch('whoop.load_tokens')
    @patch('whoop.time.time')
    @patch('whoop.refresh_access_token')
    def test_get_valid_access_token_from_vault_expired(self, mock_refresh, mock_time, mock_load):
        mock_st.session_state.clear()
        mock_time.return_value = 1000
        mock_load.return_value = {"access_token": "vault_token", "expires_at": 1100, "refresh_token": "refresh"}
        mock_refresh.return_value = "new_refreshed_token"

        result = whoop.get_valid_access_token()
        self.assertEqual(result, "new_refreshed_token")
        mock_refresh.assert_called_once_with("refresh")

    @patch('whoop.load_tokens')
    def test_get_valid_access_token_no_vault(self, mock_load):
        mock_st.session_state.clear()
        mock_load.return_value = None
        result = whoop.get_valid_access_token()
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
