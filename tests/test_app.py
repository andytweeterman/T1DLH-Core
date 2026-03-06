import sys
import unittest
from unittest.mock import MagicMock

class TestAppGeminiFallback(unittest.TestCase):
    def setUp(self):
        # Clean up modules that might be cached to ensure app.py runs fresh
        modules_to_remove = ['app', 'streamlit', 'google.generativeai', 'plotly.graph_objects', 'whoop', 'logic', 'styles', 'calendar_sync']
        for mod in list(sys.modules.keys()):
            if mod in modules_to_remove:
                del sys.modules[mod]

    def _setup_mocks(self):
        # Mock streamlit
        mock_st = MagicMock()
        mock_st.secrets = {
            "GEMINI_API_KEY": "fake_key",
            "WHOOP_CLIENT_ID": "fake_id",
            "WHOOP_CLIENT_SECRET": "fake_secret",
            "WHOOP_REDIRECT_URI": "fake_uri"
        }
        mock_st.session_state = MagicMock()
        mock_st.columns.return_value = [MagicMock() for _ in range(4)]

        # Exception classes that Streamlit defines
        class StopException(Exception): pass
        mock_st.stop.side_effect = StopException("st.stop called")
        sys.modules['streamlit'] = mock_st

        # Mock plotly.graph_objects
        sys.modules['plotly.graph_objects'] = MagicMock()

        # Mock google.generativeai
        mock_genai = MagicMock()
        sys.modules['google.generativeai'] = mock_genai

        return mock_st, mock_genai

    def test_gemini_success(self):
        mock_st, mock_genai = self._setup_mocks()

        def generative_model_side_effect(model_name, *args, **kwargs):
            mock_model = MagicMock()
            return mock_model

        mock_genai.GenerativeModel.side_effect = generative_model_side_effect

        # Import app, triggering top-level code
        import app

        self.assertEqual(app.active_model_name, 'gemini-3-flash-preview')
        self.assertEqual(app.model_status, "✨ GEMINI 3.0 FLASH (PREVIEW) ONLINE")

        # Verify configure was called with the key
        mock_genai.configure.assert_called_with(api_key="fake_key")

    def test_gemini_fallback(self):
        mock_st, mock_genai = self._setup_mocks()

        def generative_model_side_effect(model_name, *args, **kwargs):
            mock_model = MagicMock()
            if model_name == 'gemini-3-flash-preview':
                mock_model.generate_content.side_effect = Exception("API Error")
            return mock_model

        mock_genai.GenerativeModel.side_effect = generative_model_side_effect

        # Import app
        import app

        self.assertEqual(app.active_model_name, 'gemini-1.5-flash')
        self.assertEqual(app.model_status, "⚠️ LEGACY FALLBACK: GEMINI 1.5 FLASH")

    def test_gemini_critical_failure(self):
        mock_st, mock_genai = self._setup_mocks()

        # Force configure to throw an error, hitting the outer except block
        mock_genai.configure.side_effect = Exception("Critical Config Error")

        # Catch the st.stop exception so the test can finish
        with self.assertRaises(Exception) as context:
            import app

        self.assertEqual(str(context.exception), "st.stop called")

        # Verify st.error was called with the exception message
        mock_st.error.assert_called_once()
        self.assertIn("Critical Config Error", mock_st.error.call_args[0][0])

if __name__ == '__main__':
    unittest.main()
