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
            target_platform_name: Name of target platform
        
        Returns:
            Dict with matched tracks and statistics
        """
        # Step 1: Detect source platform
        source_platform_info = self.detector.detect_platform(source_url)
        if not source_platform_info:
            raise ValueError(f"Unsupported platform URL: {source_url}")
        
        # Step 2: Check if source platform can be extracted
        if not source_platform_info['can_extract']:
            raise ValueError(
                f"❌ {source_platform_info['display_name']} playlists cannot be used as source with free API.\n"
                f"💡 Supported sources: Spotify, YouTube Music\n"
                f"   You can still convert TO {source_platform_info['display_name']}!"
            )
        
        source_platform = source_platform_info['handler']
        
        # Step 3: Get target platform
        target_platform = self.detector.get_platform(target_platform_name)
        if not target_platform:
            raise ValueError(f"Unsupported target platform: {target_platform_name}")
        
        print(f"🔄 Converting from {source_platform_info['display_name']} to {target_platform.name}")
        
        # Step 4: Extract playlist from source
        playlist_id = source_platform.extract_playlist_id(source_url)
        if not playlist_id:
            raise ValueError("Could not extract playlist ID from URL")
        
        source_tracks = source_platform.get_playlist_tracks(playlist_id)
        print(f"📥 Found {len(source_tracks)} tracks")
        
        if not source_tracks:
            raise ValueError("Playlist is empty or could not be fetched")
        
        # Step 5: Match each track to target platform
        matched_tracks = []
        for i, track in enumerate(source_tracks, 1):
            print(f"  [{i}/{len(source_tracks)}] {track['title']} - {track['artist']}")
            
            target_match = target_platform.match_track(track)
            
            # Build result with all source data + target match
            result = {
                **track,  # Keep original data
                f'{target_platform.name}_id': target_match['id'] if target_match else None,
                f'{target_platform.name}_match_method': target_match.get('match_method') if target_match else None,
                f'{target_platform.name}_confidence': target_match.get('confidence', 0) if target_match else 0
            }
            
            # Add platform-specific fields if target match exists
            if target_match:
                # Determine the URL key for this platform
                url_key = f'{target_platform.name}_url'
                
                # Add URL based on platform
                if target_platform.name == 'apple_music':
                    if 'apple_music_url' in target_match:
                        result[url_key] = target_match['apple_music_url']
                    
                    # Add preview URL and artwork for Apple Music
                    if 'preview_url' in target_match:
                        result['preview_url'] = target_match['preview_url']
                    if 'artwork_url' in target_match:
                        result['artwork_url'] = target_match['artwork_url']
                
                elif target_platform.name == 'youtube_music':
                    # Generate YouTube Music URL from ID
                    result[url_key] = f"https://music.youtube.com/watch?v={target_match['id']}"
                
                elif target_platform.name == 'spotify':
                    # Generate Spotify URL from ID
                    result[url_key] = f"https://open.spotify.com/track/{target_match['id']}"
                
                # Add any other metadata from target match
                if 'album' in target_match and not result.get('album'):
                    result['album'] = target_match['album']
            
            matched_tracks.append(result)
        
        # Step 6: Calculate statistics
        stats = self._calculate_stats(matched_tracks, target_platform.name)
        
        return {
            'source_platform': source_platform_info['display_name'],
            'target_platform': target_platform.name,
            'tracks': matched_tracks,
            'stats': stats
        }
    
    def _calculate_stats(self, tracks: List[Dict], target_platform: str) -> Dict:
        """Calculate matching statistics"""
        total = len(tracks)
        id_key = f'{target_platform}_id'
        confidence_key = f'{target_platform}_confidence'
        
        matched = sum(1 for t in tracks if t.get(id_key))
        failed = total - matched
        
        avg_confidence = 0
        if matched > 0:
            confidences = [t[confidence_key] for t in tracks if t.get(id_key)]
            avg_confidence = sum(confidences) / len(confidences)
        
        # Additional stats - confidence breakdown
        high_confidence = sum(1 for t in tracks if t.get(confidence_key, 0) >= 0.9)
        medium_confidence = sum(1 for t in tracks if 0.7 <= t.get(confidence_key, 0) < 0.9)
        low_confidence = sum(1 for t in tracks if t.get(id_key) and t.get(confidence_key, 0) < 0.7)
        
        return {
            'total': total,
            'matched': matched,
            'failed': failed,
            'match_rate': matched / total if total > 0 else 0,
            'avg_confidence': avg_confidence,
            'high_confidence': high_confidence,  # >=90%
            'medium_confidence': medium_confidence,  # 70-89%
            'low_confidence': low_confidence  # <70%
        }


# Test it!
if __name__ == "__main__":
    print("🧪 Testing Universal Converter with Apple Music\n")
    
    converter = UniversalConverter()
    
    # Test: Spotify → Apple Music
    print("=" * 60)
    print("Test: Converting Spotify → Apple Music (FREE)")
    print("=" * 60 + "\n")
    
    try:
        result = converter.convert(
            source_url="https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M",
            target_platform_name="apple_music"
        )
        
        print(f"\n📊 Conversion Results:")
        print(f"Source: {result['source_platform']}")
        print(f"Target: {result['target_platform']}")
        print(f"\nStatistics:")
        print(f"  Total tracks: {result['stats']['total']}")
        print(f"  Matched: {result['stats']['matched']}")
        print(f"  Failed: {result['stats']['failed']}")
        print(f"  Match rate: {result['stats']['match_rate']:.1%}")
        print(f"  Avg confidence: {result['stats']['avg_confidence']:.1%}")
        print(f"\nConfidence breakdown:")
        print(f"  High (≥90%): {result['stats']['high_confidence']}")
        print(f"  Medium (70-89%): {result['stats']['medium_confidence']}")
        print(f"  Low (<70%): {result['stats']['low_confidence']}")
        
        # Show first 3 matches with URLs
        print(f"\n🎵 Sample matches (first 3):")
        for i, track in enumerate(result['tracks'][:3], 1):
            matched = "✅" if track.get('apple_music_id') else "❌"
            print(f"\n  {i}. {matched} {track['title']} - {track['artists']}")
            if track.get('apple_music_id'):
                print(f"     Confidence: {track['apple_music_confidence']:.1%}")
                print(f"     Apple Music URL: {track.get('apple_music_url', 'N/A')}")
                print(f"     Preview URL: {track.get('preview_url', 'N/A')[:60]}...")
                print(f"     Artwork URL: {track.get('artwork_url', 'N/A')[:60]}...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60 + "\n")
    
    # Test: Apple Music as source (should fail with helpful message)
    print("Test: Trying Apple Music as source (should fail gracefully)")
    print("=" * 60 + "\n")
    
    try:
        result = converter.convert(
            source_url="https://music.apple.com/us/playlist/todays-hits/pl.f4d106fed2bd41149aaacabb233eb5eb",
            target_platform_name="spotify"
        )
    except ValueError as e:
        print(f"Expected error message:\n{e}")
    
    print("\n" + "=" * 60 + "\n")
    
    # Test: Spotify → YouTube Music
    print("Test: Converting Spotify → YouTube Music")
    print("=" * 60 + "\n")
    
    try:
        result = converter.convert(
            source_url="https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M",
            target_platform_name="youtube_music"
        )
        
        print(f"\n📊 Conversion Results:")
        print(f"Source: {result['source_platform']}")
        print(f"Target: {result['target_platform']}")
        print(f"\nStatistics:")
        print(f"  Total tracks: {result['stats']['total']}")
        print(f"  Matched: {result['stats']['matched']}")
        print(f"  Match rate: {result['stats']['match_rate']:.1%}")
        
        # Show first match with URL
        print(f"\n🎵 Sample match:")
        if result['tracks']:
            track = result['tracks'][0]
            matched = "✅" if track.get('youtube_music_id') else "❌"
            print(f"  {matched} {track['title']} - {track['artists']}")
            if track.get('youtube_music_id'):
                print(f"     YouTube Music URL: {track.get('youtube_music_url', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Error: {e}")