import sys
from unittest.mock import MagicMock, patch
import unittest

# Mock Streamlit to prevent secrets loading issues during module import
mock_st = MagicMock()
mock_st.secrets = {
    "WHOOP_CLIENT_ID": "test_client_id",
    "WHOOP_CLIENT_SECRET": "test_client_secret",
    "WHOOP_REDIRECT_URI": "test_redirect_uri"
}

sys.modules['streamlit'] = mock_st
import whoop

class TestWhoop(unittest.TestCase):

    @classmethod
    def tearDownClass(cls):
        # Clean up the mocked sys.modules so it doesn't leak into other tests
        if 'streamlit' in sys.modules and sys.modules['streamlit'] == mock_st:
            del sys.modules['streamlit']

    def test_get_authorization_url(self):
        url = whoop.get_authorization_url()
        self.assertIn("client_id=test_client_id", url)
        self.assertIn("redirect_uri=test_redirect_uri", url)
        self.assertIn("response_type=code", url)
        self.assertTrue(url.startswith("https://api.prod.whoop.com/oauth/oauth2/auth"))

    @patch('whoop.requests.post')
    def test_get_access_token(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"access_token": "test_token"}
        mock_post.return_value = mock_response

        res = whoop.get_access_token("test_auth_code")

        self.assertEqual(res, {"access_token": "test_token"})
        mock_post.assert_called_once_with(
            "https://api.prod.whoop.com/oauth/oauth2/token",
            data={
                "grant_type": "authorization_code",
                "code": "test_auth_code",
                "client_id": "test_client_id",
                "client_secret": "test_client_secret",
                "redirect_uri": "test_redirect_uri",
            }
        )

    @patch('whoop.requests.get')
    def test_fetch_whoop_recovery_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"recovery_score": 95}]
        mock_get.return_value = mock_response

        res = whoop.fetch_whoop_recovery("test_token")

        self.assertEqual(res, {"recovery_score": 95})
        mock_get.assert_called_once_with(
            "https://api.prod.whoop.com/developer/v1/recovery",
            headers={"Authorization": "Bearer test_token"}
        )

    @patch('whoop.requests.get')
    def test_fetch_whoop_recovery_success_empty(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        res = whoop.fetch_whoop_recovery("test_token")

        self.assertIsNone(res)

    @patch('whoop.requests.get')
    def test_fetch_whoop_recovery_failure(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        res = whoop.fetch_whoop_recovery("test_token")

        self.assertIsNone(res)

if __name__ == '__main__':
    unittest.main()
