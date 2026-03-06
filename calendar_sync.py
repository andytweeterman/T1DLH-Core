import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta

def get_calendar_service():
    creds_info = st.secrets["gcp_service_account"]
    credentials = service_account.Credentials.from_service_account_info(creds_info)
    scoped_credentials = credentials.with_scopes(['https://www.googleapis.com/auth/calendar.readonly'])
    return build('calendar', 'v3', credentials=scoped_credentials)

def is_speaker_event(events):
    """Helper to scan for high-stakes keywords."""
    keywords = ["panel", "presentation", "aferm", "keynote", "board", "speaker"]
    for event in events:
        title = event.get('summary', '').lower()
        if any(kw in title for kw in keywords):
            return True
    return False

def fetch_calendar_context():
    """Returns (meeting_count, speaker_mode_active)"""
    try:
        service = get_calendar_service()
        calendar_id = st.secrets.get("CALENDAR_ID", "primary")
        
        now_dt = datetime.utcnow()
        now = now_dt.isoformat() + 'Z'
        eight_hours_later = (now_dt + timedelta(hours=8)).isoformat() + 'Z'
        one_hour_later = (now_dt + timedelta(hours=1)).isoformat() + 'Z'

        events_result = service.events().list(
            calendarId=calendar_id, 
            timeMin=now,
            timeMax=eight_hours_later,
            singleEvents=True
        ).execute()
        
        events = events_result.get('items', [])
        
        # 1. Count meetings (next 8h)
        meeting_count = sum(1 for e in events if 'dateTime' in e['start'])
        
        # 2. Check for Speaker Mode (events starting in next 60 mins)
        speaker_mode = is_speaker_event(events)
        
        return meeting_count, speaker_mode
    except Exception as e:
        # Silently fail to 0 to keep the UI from crashing if API is down
        return 0, False