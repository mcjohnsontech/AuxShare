# backend/apple_music_client.py

import os
import time
import jwt
import requests
from dotenv import load_dotenv

load_dotenv()

class AppleMusicClient:
    def __init__(self):
        """Initialize Apple Music client with JWT token"""
        self.base_url = "https://api.music.apple.com/v1"
        self.token = self._generate_token()
    
    def _generate_token(self):
        """Generate JWT token for Apple Music API"""
        # Read your private key file
        with open(os.getenv('APPLE_MUSIC_PRIVATE_KEY_PATH'), 'r') as f:
            private_key = f.read()
        
        # JWT payload
        payload = {
            'iss': os.getenv('APPLE_TEAM_ID'),  # Your Team ID
            'iat': int(time.time()),
            'exp': int(time.time()) + 15777000,  # 6 months
        }
        
        # JWT headers
        headers = {
            'alg': 'ES256',
            'kid': os.getenv('APPLE_KEY_ID')  # Your Key ID
        }
        
        token = jwt.encode(
            payload,
            private_key,
            algorithm='ES256',
            headers=headers
        )
        
        return token
    
    def search_by_isrc(self, isrc):
        """Search Apple Music catalog by ISRC code"""
        url = f"{self.base_url}/catalog/us/songs"
        params = {'filter[isrc]': isrc}
        headers = {'Authorization': f'Bearer {self.token}'}
        
        response = requests.get(url, params=params, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('data'):
                song = data['data'][0]
                return {
                    'apple_music_id': song['id'],
                    'title': song['attributes']['name'],
                    'artist': song['attributes']['artistName'],
                    'album': song['attributes']['albumName']
                }
        
        return None
    
    def search_by_title_artist(self, title, artist):
        """Fallback search by title and artist"""
        url = f"{self.base_url}/catalog/us/search"
        params = {
            'term': f"{title} {artist}",
            'types': 'songs',
            'limit': 5
        }
        headers = {'Authorization': f'Bearer {self.token}'}
        
        response = requests.get(url, params=params, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('results', {}).get('songs', {}).get('data'):
                # Return first result (we'll add fuzzy matching later)
                song = data['results']['songs']['data'][0]
                return {
                    'apple_music_id': song['id'],
                    'title': song['attributes']['name'],
                    'artist': song['attributes']['artistName'],
                    'album': song['attributes']['albumName']
                }
        
        return None

# Test it!
if __name__ == "__main__":
    client = AppleMusicClient()
    
    # Test with an ISRC
    test_isrc = "USUG11700517"  # "Shape of You" by Ed Sheeran
    result = client.search_by_isrc(test_isrc)
    
    if result:
        print(f"Found: {result['title']} - {result['artist']}")
        print(f"Apple Music ID: {result['apple_music_id']}")
    else:
        print("Not found")