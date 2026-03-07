import pytest
from unittest.mock import patch, MagicMock
import sys

@patch('google.generativeai.GenerativeModel')
def test_prompt_injection_fix(mock_generative_model):
    """
    Test that GenAI calls use system_instruction parameter to prevent prompt injection.
    """
    # Verify the code structure directly by reading app.py
    with open('app.py', 'r') as f:
        content = f.read()

    # Assert that system_instruction is used for GenerativeModel instantiation
    assert "system_instruction=sys_inst" in content
    assert "response = local_model.generate_content([audio_part])" in content
    assert "response = local_model.generate_content(\"Generate daily briefing.\")" in content
    assert "response = local_model.generate_content(text_input)" in content

    # Assert that we removed user input interpolation from prompt
    assert 'The user just reported the following subjective state: "{text_input}"' not in content
