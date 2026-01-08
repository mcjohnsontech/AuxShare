# backend/universal_converter.py

from typing import List, Dict
from platform_detector import PlatformDetector
from platforms.base import MusicPlatform

class UniversalConverter:
    """Convert playlists between any supported platforms"""
    
    def __init__(self):
        self.detector = PlatformDetector()
    
    def convert(
        self,
        source_url: str,
        target_platform_name: str
    ) -> Dict:
        """
        Convert a playlist from one platform to another
        
        Args:
            source_url: URL of the source playlist
            target_platform_name: Name of target platform (e.g., 'youtube_music')
        
        Returns:
            Dict with matched tracks and statistics
        """
        # Step 1: Detect source platform
        source_platform_info = self.detector.detect_platform(source_url)
        if not source_platform_info:
            raise ValueError(f"Unsupported platform URL: {source_url}")
        
        source_platform = source_platform_info['handler']
        
        # Step 2: Get target platform
        target_platform = self.detector.get_platform(target_platform_name)
        if not target_platform:
            raise ValueError(f"Unsupported target platform: {target_platform_name}")
        
        print(f"🔄 Converting from {source_platform_info['display_name']} to {target_platform.name}")
        
        # Step 3: Extract playlist from source
        playlist_id = source_platform.extract_playlist_id(source_url)
        if not playlist_id:
            raise ValueError("Could not extract playlist ID from URL")
        
        source_tracks = source_platform.get_playlist_tracks(playlist_id)
        print(f"📥 Found {len(source_tracks)} tracks")
        
        # Step 4: Match each track to target platform
        matched_tracks = []
        for i, track in enumerate(source_tracks, 1):
            print(f"  [{i}/{len(source_tracks)}] {track['title']} - {track['artists']}")
            
            target_match = target_platform.match_track(track)
            
            matched_tracks.append({
                **track,  # Keep original data
                f'{target_platform.name}_id': target_match['id'] if target_match else None,
                f'{target_platform.name}_match_method': target_match.get('match_method') if target_match else None,
                f'{target_platform.name}_confidence': target_match.get('confidence', 0) if target_match else 0
            })
        
        # Step 5: Calculate statistics
        stats = self._calculate_stats(matched_tracks, target_platform.name)
        
        return {
            'source_platform': source_platform_info['display_name'],
            'target_platform': target_platform.name,
            'tracks': matched_tracks,
            'stats': stats
        }
    
    # def _calculate_stats(self, tracks: List[Dict], target_platform: str) -> Dict:
    #     """Calculate matching statistics"""
    #     total = len(tracks)
    #     id_key = f'{target_platform}_id'
    #     confidence_key = f'{target_platform}_confidence'
        
    #     matched = sum(1 for t in tracks if t.get(id_key))
        
    #     avg_confidence = 0
    #     if matched > 0:
    #         confidences = [t[confidence_key] for t in tracks if t.get(id_key)]
    #         avg_confidence = sum(confidences) / len(confidences)
        
    #     return {
    #         'total': total,
    #         'matched': matched,
    #         'failed': total - matched,
    #         'match_rate': matched / total if total > 0 else 0,
    #         'avg_confidence': avg_confidence
    #     }


    def _calculate_stats(self, tracks: List[Dict], target_platform: str) -> Dict:
        """Calculate matching statistics including confidence buckets"""
        total = len(tracks)
        id_key = f'{target_platform}_id'
        confidence_key = f'{target_platform}_confidence'
        
        matched = sum(1 for t in tracks if t.get(id_key))
        
        # Initialize confidence counters
        high_conf = 0
        med_conf = 0
        low_conf = 0
        
        confidences = []
        for t in tracks:
            if t.get(id_key):
                conf = t.get(confidence_key, 0)
                confidences.append(conf)
                
                # Categorize confidence levels
                if conf >= 0.8:
                    high_conf += 1
                elif conf >= 0.5:
                    med_conf += 1
                else:
                    low_conf += 1
        
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        return {
            'total': total,
            'matched': matched,
            'failed': total - matched,
            'match_rate': matched / total if total > 0 else 0,
            'avg_confidence': avg_confidence,
            # These fields are required by your Pydantic MatchStats model:
            'high_confidence': high_conf,
            'medium_confidence': med_conf,
            'low_confidence': low_conf
        }

# Test it!
if __name__ == "__main__":
    converter = UniversalConverter()
    
    # Convert Spotify → YouTube Music
    result = converter.convert(
        source_url="https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M",
        target_platform_name="youtube_music"
    )
    
    print(f"\n📊 Results:")
    print(f"Source: {result['source_platform']}")
    print(f"Target: {result['target_platform']}")
    print(f"Match rate: {result['stats']['match_rate']:.1%}")
    print(f"Avg confidence: {result['stats']['avg_confidence']:.1%}")