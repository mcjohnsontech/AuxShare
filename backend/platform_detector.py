# backend/platform_detector.py (ADD Apple Music support)

import re
from typing import Optional, Dict, List
from platforms.base import MusicPlatform
from platforms.spotify import SpotifyPlatform
from platforms.youtube_music import YouTubeMusicPlatform
from platforms.apple_music import AppleMusicPlatform  # NEW!

class PlatformDetector:
    """Detect and retrieve the appropriate platform handler"""
    
    def __init__(self):
        # Registry of all supported platforms
        self.platforms = {
            'spotify': {
                'handler': SpotifyPlatform(),
                'patterns': [
                    r'open\.spotify\.com/(playlist|album|track)',
                    r'spotify:(playlist|album|track):'
                ],
                'display_name': 'Spotify',
                'can_extract': True,  # Can use as source
                'icon': '🟢'
            },
            'youtube_music': {
                'handler': YouTubeMusicPlatform(),
                'patterns': [
                    r'music\.youtube\.com/(playlist|watch)',
                ],
                'display_name': 'YouTube Music',
                'can_extract': True,
                'icon': '🔴'
            },
            'apple_music': {
                'handler': AppleMusicPlatform(),
                'patterns': [
                    r'music\.apple\.com/.+/(playlist|album|song)',
                ],
                'display_name': 'Apple Music',
                'can_extract': False,  # FREE version can't extract
                'icon': '🎵'
            }
        }
    
    def detect_platform(self, url: str) -> Optional[Dict]:
        """
        Detect which platform a URL belongs to
        
        Returns:
            Dict with 'name', 'handler', 'display_name', 'can_extract' or None
        """
        for name, config in self.platforms.items():
            for pattern in config['patterns']:
                if re.search(pattern, url):
                    return {
                        'name': name,
                        'handler': config['handler'],
                        'display_name': config['display_name'],
                        'can_extract': config['can_extract'],
                        'icon': config['icon']
                    }
        return None
    
    def get_platform(self, name: str) -> Optional[MusicPlatform]:
        """Get a platform handler by name"""
        config = self.platforms.get(name)
        return config['handler'] if config else None
    
    def get_supported_platforms(self) -> List[Dict]:
        """Get list of all supported platforms"""
        return [
            {
                'name': name,
                'display_name': config['display_name'],
                'can_extract': config['can_extract'],
                'icon': config['icon']
            }
            for name, config in self.platforms.items()
        ]
    
    def get_supported_sources(self) -> List[Dict]:
        """Get platforms that can be used as source"""
        return [
            {
                'name': name,
                'display_name': config['display_name'],
                'icon': config['icon']
            }
            for name, config in self.platforms.items()
            if config['can_extract']
        ]
    
    def get_supported_targets(self) -> List[Dict]:
        """Get all platforms (all can be targets)"""
        return self.get_supported_platforms()


# Test it!
if __name__ == "__main__":
    detector = PlatformDetector()
    
    print("🎯 Supported Platforms:\n")
    
    for platform in detector.get_supported_platforms():
        extract_status = "✅ Can extract" if platform['can_extract'] else "❌ Target only"
        print(f"{platform['icon']} {platform['display_name']}: {extract_status}")
    
    print("\n" + "="*60 + "\n")
    
    test_urls = [
        "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M",
        "https://music.youtube.com/playlist?list=RDCLAK5uy_kmPRjHDECIcuVwnKsx",
        "https://music.apple.com/us/playlist/todays-hits/pl.f4d106fed2bd41149aaacabb233eb5eb"
    ]
    
    print("🔍 Testing URL Detection:\n")
    
    for url in test_urls:
        platform = detector.detect_platform(url)
        if platform:
            print(f"{platform['icon']} {url[:50]}...")
            print(f"   Platform: {platform['display_name']}")
            print(f"   Can use as source: {platform['can_extract']}")
        else:
            print(f"❌ {url} - Unknown platform")
        print()