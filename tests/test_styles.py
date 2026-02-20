import unittest
import os
import sys
import base64
import tempfile
import shutil
from unittest.mock import MagicMock, patch

# Mock streamlit and plotly
sys.modules['streamlit'] = MagicMock()
sys.modules['plotly'] = MagicMock()
sys.modules['plotly.graph_objects'] = MagicMock()

# Add parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import styles

class TestGetBase64Image(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for the test environment
        self.test_dir = tempfile.mkdtemp()

        # Determine what we want styles.__file__ to be
        # It should be a file inside this directory so that base_dir is self.test_dir
        self.mock_styles_file = os.path.join(self.test_dir, "styles.py")

        # Create a valid test image file in the test directory
        self.test_filename = "test_image.txt"
        self.test_filepath = os.path.join(self.test_dir, self.test_filename)
        with open(self.test_filepath, "wb") as f:
            f.write(b"test content")

        # Create a file outside the test directory (in tmp)
        self.outside_file = tempfile.NamedTemporaryFile(delete=False)
        self.outside_file.write(b"secret content")
        self.outside_file.close()

    def tearDown(self):
        shutil.rmtree(self.test_dir)
        if os.path.exists(self.outside_file.name):
            os.remove(self.outside_file.name)

    def test_valid_path(self):
        # Mock styles.__file__ to be our mock path
        with patch.object(styles, '__file__', self.mock_styles_file):
            result = styles.get_base64_image(self.test_filename)
            self.assertIsNotNone(result)
            expected = base64.b64encode(b"test content").decode()
            self.assertEqual(result, expected)

    def test_outside_file_absolute(self):
        # Attempt to access the outside file using absolute path
        # Should be blocked because it's not inside base_dir (self.test_dir)
        with patch.object(styles, '__file__', self.mock_styles_file):
            result = styles.get_base64_image(self.outside_file.name)
            self.assertIsNone(result)

    def test_path_traversal_relative(self):
        # Attempt to access outside file using relative path "../..."
        # We create a file in the parent directory of self.test_dir
        parent_dir = os.path.dirname(self.test_dir)
        sibling_filepath = None

        try:
            # Create a temp file in the parent directory
            with tempfile.NamedTemporaryFile(dir=parent_dir, delete=False) as f:
                 f.write(b"sibling secret")
                 sibling_filepath = f.name

            # Calculate relative path from test_dir to sibling_filepath
            filename = os.path.basename(sibling_filepath)
            rel_path = os.path.join("..", filename)

            with patch.object(styles, '__file__', self.mock_styles_file):
                result = styles.get_base64_image(rel_path)
                self.assertIsNone(result)
        finally:
             if sibling_filepath and os.path.exists(sibling_filepath):
                 os.remove(sibling_filepath)

    def test_non_existent_file(self):
        with patch.object(styles, '__file__', self.mock_styles_file):
            result = styles.get_base64_image("non_existent.txt")
            self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
