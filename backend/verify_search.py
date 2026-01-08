from ytmusicapi import YTMusic
import sys

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')

def test_search():
    yt = YTMusic()
    print("Testing search...")
    try:
        results = yt.search("Blinding Lights The Weeknd", filter='songs')
        if results:
            print("✅ Search successful")
            print(f"First result: {results[0]['title']} - {results[0]['artists'][0]['name']}")
        else:
            print("❌ Search returned no results")
            
    except Exception as e:
        print(f"❌ Search failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_search()
