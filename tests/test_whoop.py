import unittest
from unittest.mock import patch
import sys

# Mock streamlit before importing whoop
class MockSecrets(dict):
    pass

class MockStreamlit:
    secrets = MockSecrets({
        "WHOOP_CLIENT_ID": "mock_client_id",
        "WHOOP_CLIENT_SECRET": "mock_client_secret",
        "WHOOP_REDIRECT_URI": "mock_redirect_uri"
    })

sys.modules['streamlit'] = MockStreamlit()

import whoop

class TestWhoop(unittest.TestCase):

    @patch('whoop.requests.post')
    def test_get_access_token_timeout(self, mock_post):
        # Setup mock response
        mock_post.return_value.json.return_value = {"access_token": "mock_token"}

        # Call function
        result = whoop.get_access_token("mock_auth_code")

        # Verify the result
        self.assertEqual(result, {"access_token": "mock_token"})

        # Verify that post was called with timeout=10
        mock_post.assert_called_once()
        _, kwargs = mock_post.call_args
        self.assertIn('timeout', kwargs)
        self.assertEqual(kwargs['timeout'], 10)

    @patch('whoop.requests.get')
    def test_fetch_whoop_recovery_timeout(self, mock_get):
        # Setup mock response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [{"recovery_score": 100}]

        # Call function
        result = whoop.fetch_whoop_recovery("mock_token")

        # Verify the result
        self.assertEqual(result, {"recovery_score": 100})

        # Verify that get was called with timeout=10
        mock_get.assert_called_once()
        _, kwargs = mock_get.call_args
        self.assertIn('timeout', kwargs)
        self.assertEqual(kwargs['timeout'], 10)

if __name__ == '__main__':
    unittest.main()
