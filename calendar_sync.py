import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta

def get_calendar_service():
    """Authenticates using the Service Account keys from Streamlit Secrets."""
    creds_info = st.secrets["gcp_service_account"]
    credentials = service_account.Credentials.from_service_account_info(creds_info)
    scoped_credentials = credentials.with_scopes(['https://www.googleapis.com/auth/calendar.readonly'])
    return build('calendar', 'v3', credentials=scoped_credentials)

def fetch_calendar_context():
    """
    Returns (meeting_count, speaker_mode_active)
    """
    try:
        service = get_calendar_service()
        calendar_id = st.secrets.get("CALENDAR_ID", "primary")
        
        now = datetime.utcnow().isoformat() + 'Z'
        # Scan next 8 hours for density, but only next 60 mins for Speaker Mode
        eight_hours_later = (datetime.utcnow() + timedelta(hours=8)).isoformat() + 'Z'
        one_hour_later = (datetime.utcnow() + timedelta(hours=1)).isoformat() + 'Z'

        events_result = service.events().list(
            calendarId=calendar_id, 
            timeMin=now,
            timeMax=eight_hours_later,
            singleEvents=True
        ).execute()
        
        events = events_result.get('items', [])
        
        # 1. Count meetings (next 8h)
        meeting_count = sum(1 for e in events if 'dateTime' in e['start'])
        
        # 2. Check for Speaker Mode (next 1h)
        speaker_events = [e for e in events if e['start'].get('dateTime', '') < one_hour_later]
        speaker_mode = logic.check_speaker_mode(speaker_events)
        
        return meeting_count, speaker_mode
    except:
        return 0, False