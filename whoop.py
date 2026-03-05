import streamlit as st
import requests
import base64
from urllib.parse import urlencode

# Load credentials from Streamlit secrets
CLIENT_ID = st.secrets["085221b6-b196-4512-b3e8-f3356a010a56"]
CLIENT_SECRET = st.secrets["ff84d1fa1a7b04090be8cad68ab818c2296a6cd30317767864dc4bf4eda521a4"]
REDIRECT_URI = st.secrets["https://t1dlhagentic.streamlit.app/"]
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
    """Pulls the latest recovery metrics (HRV, RHR, Score)."""
    headers = {"Authorization": f"Bearer {token}"}
    # Pulling the latest recovery entry
    url = "https://api.prod.whoop.com/developer/v1/recovery"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data[0] if data else None
    return None