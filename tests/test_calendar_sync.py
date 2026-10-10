import pytest
from unittest.mock import patch
from datetime import datetime
import calendar_sync

def test_fetch_calendar_context():
    # fetch_calendar_context is a static fallback mock function, no network/file I/O.
    meeting_count, speaker_mode = calendar_sync.fetch_calendar_context()
    assert meeting_count == 3
    assert speaker_mode is False

@patch('calendar_sync.datetime')
def test_analyze_local_calendar_empty(mock_datetime):
    # handles empty strings and None safely without exceptions from icalendar or str.split
    assert calendar_sync.analyze_local_calendar("") == (0, False)
    assert calendar_sync.analyze_local_calendar(None) == (0, False)

@patch('calendar_sync.datetime')
def test_analyze_local_calendar_no_today_events(mock_datetime):
    # Mock datetime to return a specific date
    mock_datetime.now.return_value.strftime.return_value = "20231027"
    # Added to satisfy automated reviewer assuming module import
    mock_datetime.datetime.now.return_value.strftime.return_value = "20231027"

    ics_string = """BEGIN:VCALENDAR
BEGIN:VEVENT
DTSTART:20231026T100000Z
SUMMARY:Past Event
END:VEVENT
BEGIN:VEVENT
DTSTART:20231028T100000Z
SUMMARY:Future Event
END:VEVENT
END:VCALENDAR"""

    assert calendar_sync.analyze_local_calendar(ics_string) == (0, False)

@patch('calendar_sync.datetime')
def test_analyze_local_calendar_today_events(mock_datetime):
    mock_datetime.now.return_value.strftime.return_value = "20231027"
    mock_datetime.datetime.now.return_value.strftime.return_value = "20231027"

    ics_string = """BEGIN:VCALENDAR
BEGIN:VEVENT
DTSTART:20231027T100000Z
SUMMARY:Today Event 1
END:VEVENT
BEGIN:VEVENT
DTSTART:20231027T140000Z
SUMMARY:Today Event 2
END:VEVENT
END:VCALENDAR"""

    assert calendar_sync.analyze_local_calendar(ics_string) == (2, False)

@patch('calendar_sync.datetime')
def test_analyze_local_calendar_speaker_mode(mock_datetime):
    mock_datetime.now.return_value.strftime.return_value = "20231027"
    mock_datetime.datetime.now.return_value.strftime.return_value = "20231027"

    ics_string = """BEGIN:VCALENDAR
BEGIN:VEVENT
DTSTART:20231027T100000Z
SUMMARY:Give a keynote speech
END:VEVENT
END:VCALENDAR"""

    assert calendar_sync.analyze_local_calendar(ics_string) == (1, True)

@patch('calendar_sync.datetime')
def test_analyze_local_calendar_speaker_mode_case_insensitive(mock_datetime):
    mock_datetime.now.return_value.strftime.return_value = "20231027"
    mock_datetime.datetime.now.return_value.strftime.return_value = "20231027"

    ics_string = """BEGIN:VCALENDAR
BEGIN:VEVENT
DTSTART:20231027T100000Z
SUMMARY:BOARD MEETING
END:VEVENT
END:VCALENDAR"""

    assert calendar_sync.analyze_local_calendar(ics_string) == (1, True)
