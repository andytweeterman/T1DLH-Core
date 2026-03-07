import json
import time
import requests
import streamlit as st
import secrets
import logging
import os
from urllib.parse import urlencode

# Configure logging for this module
logger = logging.getLogger(__name__)

TOKEN_FILE = "whoop_tokens.json"

# Load credentials from Streamlit secrets
CLIENT_ID = st.secrets["WHOOP_CLIENT_ID"]
CLIENT_SECRET = st.secrets["WHOOP_CLIENT_SECRET"]
REDIRECT_URI = st.secrets["WHOOP_REDIRECT_URI"]

AUTH_URL = "https://api.prod.whoop.com/oauth/oauth2/auth"
TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"

def get_authorization_url():
    """Generates the Whoop login URL with a dynamic state for CSRF protection."""
    if "oauth_state" not in st.session_state:
        st.session_state.oauth_state = secrets.token_urlsafe(16)
        
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "offline read:recovery read:cycles read:sleep read:workout",
        "state": st.session_state.oauth_state
    }
    return f"{AUTH_URL}?{urlencode(params)}"

def get_access_token(auth_code):
    """Exchanges auth code for tokens with a strict network timeout."""
    data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
    }
    try:
        response = requests.post(TOKEN_URL, data=data, timeout=10)
        return response.json()
    except Exception as e:
        logger.error(f"Token exchange failed: {e}")
        return None

@st.cache_data(ttl=300)
def fetch_whoop_recovery(token):
    """Pulls V2 Cycle and Sleep metrics with error handling and timeouts."""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        cycle_res = requests.get("https://api.prod.whoop.com/developer/v2/cycle", headers=headers, timeout=10)
        sleep_res = requests.get("https://api.prod.whoop.com/developer/v2/activity/sleep", headers=headers, timeout=10)

        if cycle_res.status_code == 200:
            cycle_recs = cycle_res.json().get('records', [])
            sleep_recs = sleep_res.json().get('records', []) if sleep_res.status_code == 200 else []

            latest_cycle = cycle_recs[0] if cycle_recs else {}
            latest_sleep = sleep_recs[0] if sleep_recs else {}

            recovery_obj = latest_cycle.get('recovery', {}).get('score', latest_cycle.get('score', {}))
            strain_obj = latest_cycle.get('score', {})
            sleep_obj = latest_sleep.get('score', {})

            return {
                "score": {
                    "recovery_score": recovery_obj.get('recovery_score', 0),
                    "hrv_rmssd_milli_seconds": recovery_obj.get('hrv_rmssd_milli', 0.0),
                    "resting_heart_rate_beats_per_minute": recovery_obj.get('resting_heart_rate', 0),
                    "day_strain": strain_obj.get('strain', 0.0),
                    "sleep_performance_percentage": sleep_obj.get('sleep_performance_percentage', 0)
                }
            }
        return None
    except Exception as e:
        logger.error(f"Whoop data fetch failed: {e}")
        return None

def save_tokens(token_data):
    """Calculates expiration time and saves tokens to session state and local vault."""
    token_data['expires_at'] = time.time() + token_data.get('expires_in', 3600)
    st.session_state.whoop_token = token_data.get("access_token")
    
    try:
        with open(TOKEN_FILE, 'w') as f:
            json.dump(token_data, f)
    except Exception as e:
        logger.error(f"Failed to save tokens locally: {e}")

def load_tokens():
    """Retrieves tokens from the local JSON vault."""
    try:
        with open(TOKEN_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return None

def refresh_access_token(refresh_token):
    """Trades a refresh token for a fresh access token if credentials are near expiry."""
    try:
        response = requests.post(TOKEN_URL, data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET
        }, timeout=10)
        
        if response.status_code == 200:
            new_tokens = response.json()
            save_tokens(new_tokens)
            return new_tokens['access_token']
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
    return None

def get_valid_access_token():
    """Master controller for retrieving a usable token, handling refresh if necessary."""
    # Priority 1: Current Session Memory
    if "whoop_token" in st.session_state and st.session_state.whoop_token:
        return st.session_state.whoop_token
        
    # Priority 2: Persistent Local Vault
    tokens = load_tokens()
    if not tokens:
        return None
    
    # Priority 3: Automatic Refresh (if expiring within the next 5 minutes)
    if time.time() > tokens.get('expires_at', 0) - 300:
        return refresh_access_token(tokens.get('refresh_token'))
    
    return tokens.get('access_token')