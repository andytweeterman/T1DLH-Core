import json
import time
import requests
import streamlit as st
from urllib.parse import urlencode  # <-- THE FIX

TOKEN_FILE = "whoop_tokens.json"

# Load credentials from Streamlit secrets
CLIENT_ID = st.secrets["WHOOP_CLIENT_ID"]
CLIENT_SECRET = st.secrets["WHOOP_CLIENT_SECRET"]
REDIRECT_URI = st.secrets["WHOOP_REDIRECT_URI"]
AUTH_URL = "https://api.prod.whoop.com/oauth/oauth2/auth"
TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"

def get_authorization_url():
    """Generates the Whoop login URL."""
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "offline read:recovery read:cycles read:sleep read:workout",
        "state": "tldh_auth_state"
    }
    return f"{AUTH_URL}?{urlencode(params)}"

def get_access_token(auth_code):
    """Exchanges the auth code for a real access token."""
    data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
    }
    response = requests.post(TOKEN_URL, data=data)
    return response.json()

def fetch_whoop_recovery(token):
    """Pulls and merges V2 Cycle (Recovery & Strain) and Sleep into a single profile."""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # 1. Hit the new V2 endpoints
        cycle_res = requests.get("https://api.prod.whoop.com/developer/v2/cycle", headers=headers)
        sleep_res = requests.get("https://api.prod.whoop.com/developer/v2/activity/sleep", headers=headers)

        if cycle_res.status_code == 200:
            cycle_data = cycle_res.json().get('records', [])
            sleep_data = sleep_res.json().get('records', []) if sleep_res.status_code == 200 else []

            latest_cycle = cycle_data[0] if cycle_data else {}
            latest_sleep = sleep_data[0] if sleep_data else {}

            # In V2, Recovery is nested inside the Cycle object. 
            # We use robust .get() chains to catch the data regardless of exact nesting.
            recovery_obj = latest_cycle.get('recovery', {}).get('score', {}) 
            if not recovery_obj:
                # Fallback if Whoop flattens the dictionary
                recovery_obj = latest_cycle.get('score', {})

            strain_obj = latest_cycle.get('score', {})
            sleep_obj = latest_sleep.get('score', {})

            # Map the V2 keys back to the exact format your app.py is expecting
            return {
                "score": {
                    "recovery_score": recovery_obj.get('recovery_score', 0),
                    # V2 drops the "_seconds" and "_beats_per_minute" suffixes, so we map them here
                    "hrv_rmssd_milli_seconds": recovery_obj.get('hrv_rmssd_milli', 0.0),
                    "resting_heart_rate_beats_per_minute": recovery_obj.get('resting_heart_rate', 0),
                    "day_strain": strain_obj.get('strain', 0.0),
                    "sleep_performance_percentage": sleep_obj.get('sleep_performance_percentage', 0)
                }
            }
        else:
            st.error(f"Whoop API Error: {cycle_res.status_code}. Whoop may be down or tokens expired.")
            return None
            
    except Exception as e:
        st.error(f"Whoop Connection Error: {e}")
        return None

def save_tokens(token_data):
    """Calculates expiration time and saves to a local JSON vault."""
    # Add an expiration timestamp (current time + expires_in seconds)
    token_data['expires_at'] = time.time() + token_data.get('expires_in', 3600)
    with open(TOKEN_FILE, 'w') as f:
        json.dump(token_data, f)

def load_tokens():
    """Loads tokens from the vault."""
    try:
        with open(TOKEN_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def refresh_access_token(refresh_token):
    """Silently trades the refresh token for a fresh access token."""
    client_id = st.secrets["WHOOP_CLIENT_ID"]
    client_secret = st.secrets["WHOOP_CLIENT_SECRET"]
    
    response = requests.post("https://api.prod.whoop.com/oauth/oauth2/token", data={
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret
    })
    
    if response.status_code == 200:
        new_tokens = response.json()
        save_tokens(new_tokens)
        return new_tokens['access_token']
    else:
        return None

def get_valid_access_token():
    """The Master Auth Function: Gets a token, refreshing it if necessary."""
    tokens = load_tokens()
    if not tokens:
        return None
    
    # If the token expires in the next 5 minutes, refresh it now
    if time.time() > tokens.get('expires_at', 0) - 300:
        return refresh_access_token(tokens.get('refresh_token'))
    
    return tokens['access_token']