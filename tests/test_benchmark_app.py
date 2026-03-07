import pytest
import time
from unittest.mock import patch, MagicMock
import sys

# We should probably not pollute the global `sys.modules` for other tests
# But since pytest runs tests in order and we import it globally...
import streamlit as st

mock_st = MagicMock()
mock_st.secrets = {"GEMINI_API_KEY": "dummy", "WHOOP_CLIENT_ID": "dummy", "WHOOP_CLIENT_SECRET": "dummy", "WHOOP_REDIRECT_URI": "dummy"}
mock_st.columns.side_effect = lambda x, **kwargs: [MagicMock() for _ in x] if isinstance(x, list) else [MagicMock() for _ in range(x)]
mock_st.cache_data = st.cache_data  # DO NOT mock cache_data, let it use the real one so logic works!
mock_st.cache_resource = st.cache_resource
sys.modules['streamlit'] = mock_st
sys.modules['streamlit.components'] = MagicMock()
mock_components_v1 = MagicMock()
mock_components_v1.declare_component.return_value = lambda **kwargs: None
sys.modules['streamlit.components.v1'] = mock_components_v1

sys.modules['audio_recorder_streamlit'] = MagicMock()
mock_audio = MagicMock()
mock_audio.audio_recorder.return_value = None
sys.modules['audio_recorder_streamlit'] = mock_audio

import whoop
import logic
import calendar_sync

def setup_mock_functions(mocker):
    # Ensure logic is reloaded in case other tests mock it
    import importlib
    import logic
    importlib.reload(logic)
    # Mock network/API calls with an artificial delay to simulate real-world latency
    mocker.patch('whoop.requests.get', side_effect=lambda *args, **kwargs: time.sleep(0.5) or MagicMock(status_code=200, json=lambda: {'records': [{'recovery': {'score': {'recovery_score': 85}}, 'score': {'strain': 12.0, 'sleep_performance_percentage': 90}}]}))

    # calendar_sync uses Google Calendar API
    mock_events = MagicMock()
    mock_events.list().execute.return_value = {'items': []}
    mock_service = MagicMock()
    mock_service.events.return_value = mock_events
    mocker.patch('calendar_sync.get_calendar_service', side_effect=lambda *args, **kwargs: time.sleep(0.5) or mock_service)

import app

def test_benchmark_data_loading(benchmark, mocker):
    setup_mock_functions(mocker)

    whoop_token = "dummy_token"
    current_context = "Normal"

    def run_block():
        if hasattr(whoop.fetch_whoop_recovery, 'clear'):
            whoop.fetch_whoop_recovery.clear()
        if hasattr(logic.fetch_health_data, 'clear'):
            logic.fetch_health_data.clear()
        if hasattr(logic.calc_glycemic_risk, 'clear'):
            logic.calc_glycemic_risk.clear()

        # We DO NOT clear the cache for app.load_all_data!
        # This will show the performance of hitting the Streamlit cache decorator.
        if hasattr(app, 'load_all_data'):
            return app.load_all_data(whoop_token, current_context)
        else:
            whoop_metrics = whoop.fetch_whoop_recovery(whoop_token)
            meeting_count, speaker_mode = calendar_sync.fetch_calendar_context()
            raw_data = logic.fetch_health_data()
            return logic.calc_glycemic_risk(
                raw_data,
                current_context,
                whoop_data=whoop_metrics,
                meeting_count=meeting_count,
                speaker_mode=speaker_mode
            )

    benchmark(run_block)
