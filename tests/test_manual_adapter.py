# tests/test_manual_adapter.py
from platforms.manual import ManualImportPlatform

def test_parse_text_lines():
    platform = ManualImportPlatform()
    text = """
    1. Blinding Lights - The Weeknd
    2. As It Was by Harry Styles
    3. bad guy - Billie Eilish
    Another One Bites the Dust - Queen
    """
    tracks = platform.parse_text_lines(text)
    assert len(tracks) == 4
    
    assert tracks[0].title == "Blinding Lights"
    assert tracks[0].primaryArtists == ["The Weeknd"]
    
    assert tracks[1].title == "As It Was"
    assert tracks[1].primaryArtists == ["Harry Styles"]
    
    assert tracks[2].title == "bad guy"
    assert tracks[2].primaryArtists == ["Billie Eilish"]
    
    assert tracks[3].title == "Another One Bites the Dust"
    assert tracks[3].primaryArtists == ["Queen"]

def test_parse_csv():
    platform = ManualImportPlatform()
    csv_data = """title,artist,album,isrc
Flowers,Miley Cyrus,Endless Summer Vacation,USSM12209777
vampire,Olivia Rodrigo,GUTS,USUG12304987
"""
    tracks = platform.parse_csv(csv_data)
    assert len(tracks) == 2
    assert tracks[0].title == "Flowers"
    assert tracks[0].artists == ["Miley Cyrus"]
    assert tracks[0].isrc == "USSM12209777"
    assert tracks[0].album == "Endless Summer Vacation"
    assert tracks[1].title == "vampire"
    assert tracks[1].isrc == "USUG12304987"

