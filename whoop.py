import json
import time
import requests
import streamlit as st
from urllib.parse import urlencode
import secrets

# Path for the local token vault
TOKEN_FILE = "whoop_tokens.json"

# Load credentials from Streamlit secrets
# Ensure these keys are defined in your Streamlit Cloud "Secrets" panel
CLIENT_ID = st.secrets["WHOOP_CLIENT_ID"]
CLIENT_SECRET = st.secrets["WHOOP_CLIENT_SECRET"]
REDIRECT_URI = st.secrets["WHOOP_REDIRECT_URI"]

# V1/V2 Base URLs
AUTH_URL = "https://api.prod.whoop.com/oauth/oauth2/auth"
TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"

def get_authorization_url():
    """Generates the Whoop login URL for the OAuth2 handshake."""
    state_token = secrets.token_urlsafe(16)

    # Store the token in session state for validation on callback
    st.session_state.oauth_state = state_token

    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "offline read:recovery read:cycles read:sleep read:workout",
        "state": state_token
    }
    return f"{AUTH_URL}?{urlencode(params)}"

def get_access_token(auth_code):
    """Exchanges the temporary auth code for permanent access/refresh tokens."""
    data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
    }
    try:
        # Timeout added to prevent hanging during network lag
        response = requests.post(TOKEN_URL, data=data, timeout=10)
        return response.json()
    except Exception as e:
        st.error(f"Whoop Auth Error: {e}")
        return None

@st.cache_data(ttl=300) # Performance: Cache biometric data for 5 minutes
def fetch_whoop_recovery(token):
    """Pulls and merges V2 Cycle (Recovery/Strain) and Sleep into a single profile."""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # 1. Hit the new V2 consolidated endpoints with 10s timeout protection
        # V2 Cycle contains both Recovery and Strain metrics
        cycle_res = requests.get("https://api.prod.whoop.com/developer/v2/cycle", headers=headers, timeout=10)
        sleep_res = requests.get("https://api.prod.whoop.com/developer/v2/activity/sleep", headers=headers, timeout=10)

        if cycle_res.status_code == 200:
            cycle_data = cycle_res.json().get('records', [])
            sleep_data = sleep_res.json().get('records', []) if sleep_res.status_code == 200 else []

            # Grab the latest physiological records
            latest_cycle = cycle_data[0] if cycle_data else {}
            latest_sleep = sleep_data[0] if sleep_data else {}

            # Extraction logic for V2 nested dictionary structure
            recovery_obj = latest_cycle.get('recovery', {}).get('score', {}) 
            if not recovery_obj:
                # Fallback for flattened payloads or different API scopes
                recovery_obj = latest_cycle.get('score', {})

            strain_obj = latest_cycle.get('score', {})
            sleep_obj = latest_sleep.get('score', {})

            # Standardized mapping for app.py and logic.py consumption
            return {
                "score": {
                    "recovery_score": recovery_obj.get('recovery_score', 0),
                    "hrv_rmssd_milli_seconds": recovery_obj.get('hrv_rmssd_milli', 0.0),
                    "resting_heart_rate_beats_per_minute": recovery_obj.get('resting_heart_rate', 0),
                    "day_strain": strain_obj.get('strain', 0.0),
                    "sleep_performance_percentage": sleep_obj.get('sleep_performance_percentage', 0)
                }
            }
        else:
            return None
            
    except Exception:
        # Silent fail ensures the UI defaults gracefully to "Not Synced" states
        return None

def save_tokens(token_data):
    """Calculates expiration time and saves tokens to session state and local vault."""
    # Add an expiration timestamp (current time + expires_in seconds)
    token_data['expires_at'] = time.time() + token_data.get('expires_in', 3600)
    
    # Store the primary access token in the active Streamlit session
    st.session_state.whoop_token = token_data.get("access_token")
    
    try:
        # Persistent local storage for the refresh token
        with open(TOKEN_FILE, 'w') as f:
            json.dump(token_data, f)
    except Exception:
        # Local file write might fail in some cloud environments; session state is used as backup
        pass

def load_tokens():
    """Retrieves tokens from the local JSON vault."""
    try:
        with open(TOKEN_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
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
    except Exception:
        pass
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
    
    return tokens['access_token']