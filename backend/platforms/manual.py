# backend/platforms/manual.py
import csv
import io
import re
import urllib.parse
from typing import List, Dict, Optional, Any
from models.canonical import CanonicalTrack
from .base import MusicPlatform

class ManualImportPlatform(MusicPlatform):
    """
    Source adapter for manually imported playlists (raw text lines or CSV).
    Enables importing song lists without platform API tokens.
    """
    def __init__(self):
        super().__init__('manual')
    
    def extract_playlist_id(self, url: str) -> Optional[str]:
        if url.startswith("manual://"):
            return url.replace("manual://", "")
        if url.strip().startswith("manual:") or "text=" in url:
            return "manual_session"
        return None
    
    def get_playlist_tracks(self, playlist_id: str) -> List[Dict[str, Any]]:
        # In URL mode, content may be urlencoded in the ID
        try:
            decoded = urllib.parse.unquote(playlist_id)
            tracks = self.parse_text_lines(decoded)
            results = []
            for track in tracks:
                item = track.model_dump()
                # Provide the legacy display field alongside canonical artists.
                item['artist'] = (
                    ", ".join(track.primaryArtists or track.artists)
                    if (track.primaryArtists or track.artists)
                    else ""
                )
                results.append(item)
            return results
        except Exception:
            return []
    
    def search_by_isrc(self, isrc: str) -> Optional[Dict]:
        return None
        
    def search_by_metadata(self, title: str, artist: str) -> Optional[Dict]:
        return None
        
    def generate_playback_link(self, track_ids: List[str]) -> str:
        return ""

    def parse_text_lines(self, text: str) -> List[CanonicalTrack]:
        """
        Parse lines of text into CanonicalTrack objects.
        Supports common formats:
        - "Title - Artist"
        - "Artist - Title" (detectable or default "Title - Artist")
        - "1. Title - Artist" (numbered lists)
        - "Title by Artist"
        """
        tracks: List[CanonicalTrack] = []
        lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
        
        for idx, line in enumerate(lines, 1):
            # Strip leading list numbers like "1. ", "01 - ", "[1] "
            cleaned = re.sub(r'^(?:\[\d+\]|\d+[\.\-\)]\s*)\s*', '', line).strip()
            
            title = ""
            artist = ""
            
            # Check for "Title by Artist"
            if " by " in cleaned.lower():
                parts = re.split(r'\s+by\s+', cleaned, maxsplit=1, flags=re.IGNORECASE)
                title, artist = parts[0].strip(), parts[1].strip()
            elif " - " in cleaned:
                parts = cleaned.split(" - ", 1)
                title, artist = parts[0].strip(), parts[1].strip()
            elif "\t" in cleaned:
                parts = cleaned.split("\t", 1)
                title, artist = parts[0].strip(), parts[1].strip()
            elif "," in cleaned and not cleaned.startswith('"'):
                parts = cleaned.split(",", 1)
                title, artist = parts[0].strip(), parts[1].strip()
            else:
                title = cleaned
                artist = "Unknown Artist"
            
            track = CanonicalTrack(
                sourcePlatform="manual",
                sourceId=f"manual_{idx}",
                title=title,
                baseTitle=title,
                artists=[artist] if artist else [],
                primaryArtists=[artist] if artist else [],
                featuredArtists=[]
            )
            tracks.append(track)
            
        return tracks

    def parse_csv(self, csv_content: str) -> List[CanonicalTrack]:
        """
        Parse CSV formatted content with headers (e.g. title, artist, album, isrc).
        """
        tracks: List[CanonicalTrack] = []
        reader = csv.DictReader(io.StringIO(csv_content.strip()))
        
        for idx, row in enumerate(reader, 1):
            # Normalize field names to lower case
            normalized_row = {k.strip().lower(): (v.strip() if v else "") for k, v in row.items() if k}
            
            title = normalized_row.get('title') or normalized_row.get('track') or normalized_row.get('name') or f"Track {idx}"
            artist = normalized_row.get('artist') or normalized_row.get('artists') or "Unknown Artist"
            album = normalized_row.get('album') or None
            isrc = normalized_row.get('isrc') or None
            
            artists_list = [a.strip() for a in artist.split(',') if a.strip()] if ',' in artist else [artist]
            
            track = CanonicalTrack(
                sourcePlatform="manual",
                sourceId=f"manual_csv_{idx}",
                title=title,
                baseTitle=title,
                artists=artists_list,
                primaryArtists=[artists_list[0]] if artists_list else [],
                featuredArtists=artists_list[1:] if len(artists_list) > 1 else [],
                album=album,
                isrc=isrc
            )
            tracks.append(track)
            
        return tracks

