import sys
import math
from unittest.mock import MagicMock, patch

class MockPandas:
    @staticmethod
    def isna(val):
        return val is None or math.isnan(val)

def test_calculate_gmi():
    # Only mock inside the test to prevent global pollution
    mock_st = MagicMock()
    mock_st.columns.side_effect = lambda x, **kwargs: [MagicMock() for _ in x] if isinstance(x, list) else [MagicMock() for _ in range(x)]
    mock_st.stop.side_effect = SystemExit

    class MockSessionState(dict):
        def __getattr__(self, key):
            return self.get(key)
        def __setattr__(self, key, value):
            self[key] = value

    mock_st.session_state = MockSessionState()
    mock_st.session_state.authenticated = True
    mock_st.secrets = {"APP_PASSWORD": "admin"}
    mock_st.query_params = MagicMock()

    mock_whoop = MagicMock()
    mock_whoop.fetch_whoop_recovery.return_value = (100, 100, 10.0)

    mock_calendar = MagicMock()
    mock_calendar.analyze_local_calendar.return_value = (False, False)

    mock_logic = MagicMock()
    mock_logic.fetch_environmental_load.return_value = (1.0, "Normal")
    mock_logic.fetch_nightscout_data.return_value = []

    mocks = {
        'pandas': MockPandas(),
        'streamlit': mock_st,
        'plotly': MagicMock(),
        'plotly.graph_objects': MagicMock(),
        'anthropic': MagicMock(),
        'openai': MagicMock(),
        'audio_recorder_streamlit': MagicMock(),
        'numpy': MagicMock(),
        'requests': MagicMock(),
        'whoop': mock_whoop,
        'calendar_sync': mock_calendar,
        'logic': mock_logic
    }

    with patch.dict('sys.modules', mocks):
        from app import calculate_gmi
        assert calculate_gmi(150.0) == 6.9
        assert calculate_gmi(100.0) == 5.7
        assert calculate_gmi(200.0) == 8.1
        assert calculate_gmi(float('nan')) == 0.0
        assert calculate_gmi(None) == 0.0

if __name__ == "__main__":
    test_calculate_gmi()
    print("Tests passed")
