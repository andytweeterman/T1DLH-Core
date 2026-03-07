import sys
import unittest
from unittest.mock import MagicMock

# mock google.generativeai
mock_genai = MagicMock()
sys.modules["google.generativeai"] = mock_genai

import app

class TestGenAI(unittest.TestCase):
    def test_assistant_call(self):
        print(app.active_model_name)

if __name__ == "__main__":
    unittest.main()
