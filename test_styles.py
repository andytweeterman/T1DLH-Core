import unittest
import os
import styles
import base64
import shutil

class TestStyles(unittest.TestCase):
    def setUp(self):
        self.test_filename = "test_image.png"
        self.test_content = b"test_image_content"
        with open(self.test_filename, "wb") as f:
            f.write(self.test_content)

    def tearDown(self):
        if os.path.exists(self.test_filename):
            os.remove(self.test_filename)

    def test_get_base64_image_valid(self):
        b64_str = styles.get_base64_image(self.test_filename)
        self.assertIsNotNone(b64_str)
        decoded = base64.b64decode(b64_str)
        self.assertEqual(decoded, self.test_content)

    def test_get_base64_image_invalid_path(self):
        b64_str = styles.get_base64_image("non_existent_file.png")
        self.assertIsNone(b64_str)

    def test_get_base64_image_security(self):
        # Create a file outside the allowed directory structure if possible,
        # but since we are running in the repo root, let's try '..'
        # The function enforces paths to be within base_dir (where styles.py is located)

        b64_str = styles.get_base64_image("../styles.py")
        self.assertIsNone(b64_str)

        # Let's just test relative path that tries to escape
        self.assertIsNone(styles.get_base64_image("../outside.png"))

if __name__ == '__main__':
    unittest.main()
