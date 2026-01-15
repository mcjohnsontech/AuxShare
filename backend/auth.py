import os
import urllib.parse
import requests
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
REDIRECT_URI = "http://localhost:5173/callback" # Frontend callback
AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"

# Scopes needed for playlist creation
SCOPES = "playlist-modify-public playlist-modify-private user-read-private user-read-email"

class SpotifyAuth:
    @staticmethod
    def get_auth_url():
        """Generate the Spotify Login URL"""
        if not CLIENT_ID:
            raise Exception("Missing SPOTIFY_CLIENT_ID env variable")
            
        params = {
            'client_id': CLIENT_ID,
            'response_type': 'code',
            'redirect_uri': REDIRECT_URI,
            'scope': SCOPES,
            'show_dialog': 'true'
        }
        url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
        return url

    @staticmethod
    def exchange_code(code: str):
        """Exchange auth code for access token"""
        if not CLIENT_ID or not CLIENT_SECRET:
            raise Exception("Missing Spotify Credentials")
            
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': REDIRECT_URI,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
        }
        
        response = requests.post(TOKEN_URL, data=data)
        
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get token from Spotify")
            
        return response.json()
