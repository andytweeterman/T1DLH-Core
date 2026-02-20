import unittest
import sys
import os

# Add parent directory to path so we can import styles
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import styles

class TestStyles(unittest.TestCase):
    def test_render_sub_header(self):
        text = "Test Header"
        expected = '<div class="steel-sub-header"><span class="steel-text-main" style="font-size: 20px !important;">Test Header</span></div>'
        # Check if the function exists first (for TDD, it won't yet)
        if hasattr(styles, 'render_sub_header'):
            result = styles.render_sub_header(text)
            self.assertEqual(result, expected)
        else:
            self.fail("render_sub_header not implemented in styles.py")

if __name__ == '__main__':
    unittest.main()
