# backend/evaluation/record_live_fixtures.py
import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

def record_live():
    fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")
    os.makedirs(fixtures_dir, exist_ok=True)
    
    # 1. Spotify Live Recording
    client_id = os.getenv("SPOTIPY_CLIENT_ID")
    client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
    
    spotify_live = {}
    if client_id and client_secret:
        sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret
        ))
        
        isrc_queries = [
            "isrc:USUG11904206", # Blinding Lights
            "isrc:USSM12200612", # As It Was
            "isrc:USUM71900764", # bad guy
            "isrc:GBAHT2000570", # Levitating
            "isrc:GBAYE0601498", # Hey Jude
            "isrc:GBAHT1100140", # Comfortably Numb
            "isrc:USSM12209777", # Flowers
            "isrc:USUG12304987", # vampire
            "isrc:USUG11901472", # Cruel Summer
            "isrc:NGA552200001", # Calm Down
            "isrc:QZHN62369809"  # Daylight
        ]
        
        for q in isrc_queries:
            try:
                res = sp.search(q=q, type="track", limit=1)
                spotify_live[q] = {
                    "source": "live_recorded",
                    "tracks": res.get("tracks", {})
                }
                print(f"Recorded Spotify live: {q}")
            except Exception as e:
                print(f"Failed Spotify {q}: {e}")
                
        meta_queries = [
            "track:Blinding Lights artist:The Weeknd",
            "track:Yellow artist:Coldplay",
            "track:Another One Bites the Dust artist:Queen",
            "track:Don't Start Now artist:Dua Lipa",
            "track:Easy On Me artist:Adele",
            "track:Believer artist:Imagine Dragons"
        ]
        for q in meta_queries:
            try:
                res = sp.search(q=q, type="track", limit=1)
                spotify_live[q] = {
                    "source": "live_recorded",
                    "tracks": res.get("tracks", {})
                }
                print(f"Recorded Spotify meta live: {q}")
            except Exception as e:
                print(f"Failed Spotify {q}: {e}")

    # 2. iTunes Live Recording
    itunes_live = {}
    itunes_terms = [
        "Blinding Lights The Weeknd",
        "As It Was Harry Styles",
        "Flowers Miley Cyrus",
        "vampire Olivia Rodrigo",
        "Cruel Summer Taylor Swift",
        "Calm Down Rema",
        "Daylight David Kushner",
        "Hey Jude The Beatles",
        "Comfortably Numb Pink Floyd",
        "Hotel California Eagles"
    ]
    for term in itunes_terms:
        try:
            resp = requests.get(
                "https://itunes.apple.com/search",
                params={"term": term, "media": "music", "entity": "song", "limit": 5},
                timeout=10
            )
            if resp.status_code == 200:
                itunes_live[term] = {
                    "source": "live_recorded",
                    "data": resp.json()
                }
                print(f"Recorded iTunes live: {term}")
        except Exception as e:
            print(f"Failed iTunes {term}: {e}")

    out_path = os.path.join(fixtures_dir, "live_recorded_fixtures.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "spotify": spotify_live,
            "itunes": itunes_live
        }, f, indent=2)
    print(f"\nLive recordings saved to {out_path}")

if __name__ == "__main__":
    record_live()

