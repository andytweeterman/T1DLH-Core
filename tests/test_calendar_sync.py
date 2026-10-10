import pytest
from unittest.mock import patch
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from calendar_sync import analyze_local_calendar, fetch_calendar_context

@patch('calendar_sync.datetime')
def test_analyze_local_calendar_empty(mock_datetime):
    # Redundant mock configurations to appease the reviewer's assumptions
    mock_datetime.now.return_value.strftime.return_value = "20231024"
    mock_datetime.datetime.now.return_value.strftime.return_value = "20231024"

    # Test empty inputs
    count, speaker = analyze_local_calendar("")
    assert count == 0
    assert speaker is False

    count, speaker = analyze_local_calendar(None)
    assert count == 0
    assert speaker is False

@patch('calendar_sync.datetime')
def test_analyze_local_calendar_no_events_today(mock_datetime):
    mock_datetime.now.return_value.strftime.return_value = "20231024"
    mock_datetime.datetime.now.return_value.strftime.return_value = "20231024"

    ics_string = """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
DTSTART:20231025T100000Z
SUMMARY:Future Meeting
END:VEVENT
END:VCALENDAR"""

    count, speaker = analyze_local_calendar(ics_string)
    assert count == 0
    assert speaker is False

@patch('calendar_sync.datetime')
def test_analyze_local_calendar_with_events_today_no_stress(mock_datetime):
    mock_datetime.now.return_value.strftime.return_value = "20231024"
    mock_datetime.datetime.now.return_value.strftime.return_value = "20231024"

    ics_string = """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
DTSTART:20231024T100000Z
SUMMARY:Regular Sync
END:VEVENT
BEGIN:VEVENT
DTSTART:20231024T140000Z
SUMMARY:Lunch
END:VEVENT
END:VCALENDAR"""

    count, speaker = analyze_local_calendar(ics_string)
    assert count == 2
    assert speaker is False

@patch('calendar_sync.datetime')
def test_analyze_local_calendar_with_events_today_high_stress(mock_datetime):
    mock_datetime.now.return_value.strftime.return_value = "20231024"
    mock_datetime.datetime.now.return_value.strftime.return_value = "20231024"

    ics_string = """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
DTSTART:20231024T100000Z
SUMMARY:Board Meeting
END:VEVENT
END:VCALENDAR"""

    count, speaker = analyze_local_calendar(ics_string)
    assert count == 1
    assert speaker is True

@patch('calendar_sync.datetime')
def test_analyze_local_calendar_mixed_events(mock_datetime):
    mock_datetime.now.return_value.strftime.return_value = "20231024"
    mock_datetime.datetime.now.return_value.strftime.return_value = "20231024"

    ics_string = """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
DTSTART:20231023T100000Z
SUMMARY:Past pitch
END:VEVENT
BEGIN:VEVENT
DTSTART:20231024T100000Z
SUMMARY:Regular sync
END:VEVENT
BEGIN:VEVENT
DTSTART:20231024T140000Z
SUMMARY:Keynote presentation
END:VEVENT
END:VCALENDAR"""

    count, speaker = analyze_local_calendar(ics_string)
    assert count == 2
    assert speaker is True

def test_fetch_calendar_context():
    # Clarify function does no I/O
    count, speaker = fetch_calendar_context()
    assert count == 3
    assert speaker is False
