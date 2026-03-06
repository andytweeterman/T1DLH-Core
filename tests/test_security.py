import unittest
from unittest.mock import patch, MagicMock
import sys

class TestSecurity(unittest.TestCase):
    @patch('google.generativeai.GenerativeModel')
    def test_system_instruction_used_for_prompt_injection_prevention(self, mock_model):
        """
        Ensures that model_json uses system_instruction to prevent
        prompt injection vulnerabilities, rather than concatenating
        instructions with untrusted user input.
        """
        # Save old modules to restore later if needed
        old_st = sys.modules.get('streamlit')
        old_app = sys.modules.get('app')
        old_logic = sys.modules.get('logic')

        # Remove modules if they exist to force reload
        for mod in ['app', 'logic', 'streamlit']:
            if mod in sys.modules:
                del sys.modules[mod]

        # Mock Streamlit completely to avoid UI rendering and cache issues during the test
        mock_st = MagicMock()
        mock_st.secrets = {
            "GEMINI_API_KEY": "dummy",
            "WHOOP_CLIENT_ID": "dummy",
            "WHOOP_CLIENT_SECRET": "dummy",
            "WHOOP_REDIRECT_URI": "dummy"
        }
        mock_st.session_state = MagicMock()
        mock_st.query_params = {}
        mock_st.columns.return_value = [MagicMock() for _ in range(4)]
        sys.modules['streamlit'] = mock_st

        # Import app to trigger the module level GenerativeModel initialization
        import app

        found_call = False
        for call in mock_model.call_args_list:
            args, kwargs = call
            if kwargs.get('generation_config', {}).get('response_mime_type') == 'application/json':
                self.assertEqual(
                    kwargs.get('system_instruction'),
                    "Analyze this life download and return JSON with reply, summary, tags, scores (bio, cog, emo), and impact_prediction."
                )
                found_call = True
                break

        self.assertTrue(found_call, "GenerativeModel was not initialized with the required system_instruction for JSON model")
