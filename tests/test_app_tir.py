import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
import sys
import datetime

# Standard way to mock Streamlit and prevent module level exceptions
mock_st = MagicMock()

# Mock attributes so __getattr__ acts correctly
class MockDict(dict):
    def __getattr__(self, key):
        if key in self:
            return self[key]
        return MagicMock()
    def __setattr__(self, key, value):
        self[key] = value

mock_st.session_state = MockDict()
mock_st.session_state.authenticated = True
mock_st.session_state.current_context = "Normal"
mock_st.session_state.muted_intercepts = {}
mock_st.session_state.event_log = []
mock_st.secrets = MockDict({
    "WHOOP_CLIENT_ID": "dummy",
    "WHOOP_CLIENT_SECRET": "dummy",
    "WHOOP_REDIRECT_URI": "dummy",
    "GEMINI_API_KEY": "dummy",
    "OWM_API_KEY": "dummy",
    "ANTHROPIC_API_KEY": "dummy",
    "APP_PASSWORD": "admin"
})

def mock_columns(x, **kwargs):
    if isinstance(x, list):
        return [MagicMock() for _ in x]
    return [MagicMock() for _ in range(x)]

mock_st.columns.side_effect = mock_columns

# Mock selectbox to return valid types
def mock_selectbox(label, options, *args, **kwargs):
    if "Duration" in label:
        return 1.0
    if "Force Context" in label:
        return "Normal"
    return options[0] if options else MagicMock()
mock_st.selectbox.side_effect = mock_selectbox


# IMPORTANT: we need to mock cache decorators BEFORE importing app
mock_st.cache_data = MagicMock()
mock_st.cache_data.return_value = lambda f: f
mock_st.cache_resource = MagicMock()
mock_st.cache_resource.return_value = lambda f: f

sys.modules['streamlit'] = mock_st
sys.modules['streamlit.components'] = MagicMock()
sys.modules['streamlit.components.v1'] = MagicMock()
sys.modules['plotly'] = MagicMock()
sys.modules['plotly.graph_objects'] = MagicMock()
sys.modules['anthropic'] = MagicMock()
sys.modules['openai'] = MagicMock()
sys.modules['yfinance'] = MagicMock()

mock_audio = MagicMock()
mock_audio.audio_recorder.return_value = None
sys.modules['audio_recorder_streamlit'] = mock_audio
sys.modules['googleapiclient'] = MagicMock()
sys.modules['googleapiclient.discovery'] = MagicMock()
sys.modules['requests'] = MagicMock()
sys.modules['google.oauth2.credentials'] = MagicMock()
sys.modules['google_auth_oauthlib.flow'] = MagicMock()
sys.modules['google.auth.transport.requests'] = MagicMock()

# Inject globals to builtins so that module-level execution succeeds
import builtins
builtins.full_data = pd.DataFrame({'Glucose_Value': [100, 100, 100, 100, 100, 100]})
builtins.latest_bg = {'Trend': 'Steady', 'Glucose_Value': 100}
builtins.w_strain = 10.0
builtins.c_dex = [MagicMock(), MagicMock(), MagicMock()]
builtins.w_rec = 100
builtins.w_sleep = 100
builtins.w_hrv = 100
builtins.w_rhr = 60

# In order to let app.py import successfully without hitting NameError on module-level variables
# We provide a mock exception that stops execution gracefully at st.stop()
mock_st.stop.side_effect = SystemExit

try:
    import app
except SystemExit:
    pass
except NameError as e:
    pass
except Exception as e:
    pass

import app

def test_calculate_tir_empty():
    df = pd.DataFrame(columns=['Glucose_Value'])
    assert app.calculate_tir(df) == 0.0

def test_calculate_tir_all_in_range():
    df = pd.DataFrame({'Glucose_Value': [70, 100, 150, 180]})
    assert app.calculate_tir(df) == 100.0

def test_calculate_tir_all_out_of_range():
    df = pd.DataFrame({'Glucose_Value': [69, 181, 200, 50]})
    assert app.calculate_tir(df) == 0.0

def test_calculate_tir_mixed():
    df = pd.DataFrame({'Glucose_Value': [60, 100, 150, 190]})
    assert app.calculate_tir(df) == 50.0

def test_calculate_tir_rounding():
    df = pd.DataFrame({'Glucose_Value': [100, 200, 200]})
    assert app.calculate_tir(df) == 33.3
