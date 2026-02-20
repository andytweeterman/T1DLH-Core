import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add the root directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestStyles(unittest.TestCase):
    def setUp(self):
        # Create mocks
        self.mock_st = MagicMock()
        self.mock_st.session_state = {}
        self.mock_plotly = MagicMock()

        # Patch sys.modules to mock external dependencies
        self.modules_patcher = patch.dict(sys.modules, {
            'streamlit': self.mock_st,
            'plotly': self.mock_plotly,
            'plotly.graph_objects': self.mock_plotly.graph_objects
        })
        self.modules_patcher.start()

        # Now import styles
        # If styles was already imported (e.g. by another test), reload it
        if 'styles' in sys.modules:
            del sys.modules['styles']
        import styles
        self.styles = styles

    def tearDown(self):
        self.modules_patcher.stop()
        if 'styles' in sys.modules:
            del sys.modules['styles']

    def test_apply_theme_default(self):
        # Setup session state
        self.mock_st.session_state = {}

        # Call the function
        theme = self.styles.apply_theme()

        # Verify theme is returned
        self.assertIsInstance(theme, dict)
        self.assertEqual(theme['BG_COLOR'], "#ffffff") # Default light mode

        # Verify st.markdown was called
        self.assertTrue(self.mock_st.markdown.called)
        args, kwargs = self.mock_st.markdown.call_args
        css_content = args[0]

        # Verify CSS content structure
        self.assertIn('<style>', css_content)
        self.assertIn(':root {', css_content)
        self.assertIn('--bg-color: #ffffff;', css_content)
        self.assertIn('.stApp { background-color: var(--bg-color) !important;', css_content)
        self.assertEqual(kwargs.get('unsafe_allow_html'), True)

    def test_apply_theme_dark_mode(self):
        # Setup session state for dark mode
        self.mock_st.session_state = {'dark_mode': True}

        # Call the function
        theme = self.styles.apply_theme()

        # Verify theme
        self.assertEqual(theme['BG_COLOR'], "#0e1117")

        # Verify st.markdown call
        # st.markdown is called once
        self.assertTrue(self.mock_st.markdown.called)
        args, kwargs = self.mock_st.markdown.call_args
        css_content = args[0]

        # Verify CSS content uses dark mode color
        self.assertIn('--bg-color: #0e1117;', css_content)

if __name__ == '__main__':
    unittest.main()
