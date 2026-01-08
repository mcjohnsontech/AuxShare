from ytmusicapi import YTMusic
import sys

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')

def test_playlist_fetch():
    yt = YTMusic()
    playlist_id = "PLJXrkAcGPApEEK5UrnN_ku_s-zxWILGk_"
    print(f"Testing fetch for playlist: {playlist_id}")
    
    try:
        # Try to get playlist
        playlist = yt.get_playlist(playlist_id)
        print("✅ Successfully fetched playlist")
        print(f"Title: {playlist.get('title')}")
        print(f"Tracks: {len(playlist.get('tracks', []))}")
            
    except Exception as e:
        print(f"❌ Failed to fetch playlist: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_playlist_fetch()
