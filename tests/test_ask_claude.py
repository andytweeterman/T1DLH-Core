import pytest
from unittest.mock import patch, MagicMock
import sys
import builtins
import pandas as pd
import json

@pytest.fixture(autouse=True)
def setup_module_mocks():
    """Safely patch sys.modules without polluting global test state."""

    # ---------------------------------------------------------
    # Mock streamlit before importing app.py
    # ---------------------------------------------------------
    mock_st = MagicMock()
    mock_st.secrets = {
        "ANTHROPIC_API_KEY": "dummy",
        "OPENAI_API_KEY": "dummy",
        "WHOOP_CLIENT_ID": "dummy",
        "WHOOP_CLIENT_SECRET": "dummy",
        "WHOOP_REDIRECT_URI": "dummy",
        "GEMINI_API_KEY": "dummy"
    }
    mock_st.columns.side_effect = lambda x, **kwargs: [MagicMock() for _ in x] if isinstance(x, list) else [MagicMock() for _ in range(x)]

    # Create a mock cache_data function that has a clear attribute
    def mock_cache_data(*args, **kwargs):
        def decorator(f):
            return f
        return decorator
    mock_cache_data.clear = MagicMock()

    mock_st.cache_data = mock_cache_data
    mock_st.cache_resource = mock_cache_data

    class SessionStateMock(dict):
        def __getattr__(self, name):
            if name in self:
                return self[name]
            return None
        def __setattr__(self, name, value):
            self[name] = value

    mock_session_state = SessionStateMock()
    mock_session_state.authenticated = True
    mock_session_state.current_context = "Normal"
    mock_session_state.muted_intercepts = {}
    mock_session_state.event_log = []
    mock_session_state.ns_url = "dummy"
    mock_session_state.ns_token = "dummy"
    mock_session_state.whoop_token = "dummy"

    mock_st.session_state = mock_session_state
    mock_st.stop = MagicMock()
    mock_st.rerun = MagicMock()
    mock_st.file_uploader.return_value = None

    def selectbox_side_effect(label, options, *args, **kwargs):
        if label == "Type":
            return "🍽️ Meal"
        if label == "Force Context Mode:":
            return "Normal"
        if label == "Duration:":
            return 1.0
        return options[0]

    mock_st.selectbox.side_effect = selectbox_side_effect

    mock_components = MagicMock()
    mock_components_v1 = MagicMock()

    mock_audio = MagicMock()
    mock_audio.audio_recorder.return_value = None

    mock_whoop = MagicMock()
    mock_whoop.fetch_whoop_recovery.return_value = {'score': {'strain': 10.0}}

    mock_logic = MagicMock()
    df = pd.DataFrame({'Glucose_Value': [100]*6, 'Trend': ['Flat']*6, 'Timestamp': [pd.Timestamp.now()]*6})
    mock_logic.fetch_health_data.return_value = df
    mock_logic.calc_glycemic_risk.return_value = (df, 'OK', '#000', 'reason')

    mock_calendar = MagicMock()

    mocks = {
        'streamlit': mock_st,
        'streamlit.components': mock_components,
        'streamlit.components.v1': mock_components_v1,
        'audio_recorder_streamlit': mock_audio,
        'whoop': mock_whoop,
        'logic': mock_logic,
        'calendar_sync': mock_calendar
    }

    with patch.dict('sys.modules', mocks):
        import app
        yield app

# ---------------------------------------------------------
# Test Cases
# ---------------------------------------------------------

def test_ask_claude_json_parsing(setup_module_mocks):
    app = setup_module_mocks
    app.client = MagicMock()
    app.client.messages.create.return_value.content = [MagicMock(text='```json\n{"test": "value"}\n```')]

    result = app.ask_claude("sys", [{"role": "user", "content": "msg"}], parse_json=True)
    assert result == {"test": "value"}

    app.client.messages.create.assert_called_once()
    kwargs = app.client.messages.create.call_args.kwargs
    assert kwargs['system'].startswith("sys\n\n")

def test_ask_claude_no_json_parsing(setup_module_mocks):
    app = setup_module_mocks
    app.client = MagicMock()
    app.client.messages.create.return_value.content = [MagicMock(text='Just a response string.')]

    result = app.ask_claude("sys", [{"role": "user", "content": "msg"}], parse_json=False)
    assert result == 'Just a response string.'

def test_ask_claude_api_error_account_locked(setup_module_mocks):
    app = setup_module_mocks
    app.client = MagicMock()
    app.client.messages.create.side_effect = Exception("404 not_found_error")

    with pytest.raises(Exception) as excinfo:
        app.ask_claude("sys", [], parse_json=False)

    assert "API Account Locked" in str(excinfo.value)

def test_ask_claude_other_api_error(setup_module_mocks):
    app = setup_module_mocks
    app.client = MagicMock()
    app.client.messages.create.side_effect = Exception("Some other error")

    with pytest.raises(Exception) as excinfo:
        app.ask_claude("sys", [], parse_json=False)

    assert "Some other error" in str(excinfo.value)

def test_ask_claude_json_parsing_no_match(setup_module_mocks):
    app = setup_module_mocks
    app.client = MagicMock()
    app.client.messages.create.return_value.content = [MagicMock(text='"just a string"')]

    result = app.ask_claude("sys", [], parse_json=True)
    assert result == "just a string"

def test_ask_claude_json_parsing_with_json_block_and_surrounding_text(setup_module_mocks):
    app = setup_module_mocks
    app.client = MagicMock()
    app.client.messages.create.return_value.content = [MagicMock(text='Here is the JSON:\n```json\n{"data": 123}\n```\nHope it helps!')]

    result = app.ask_claude("sys", [], parse_json=True)
    assert result == {"data": 123}
