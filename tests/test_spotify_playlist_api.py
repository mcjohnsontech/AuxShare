from unittest.mock import Mock, patch

from platforms.spotify import SpotifyPlatform


def response(payload, status=200):
    result = Mock(status_code=status)
    result.json.return_value = payload
    return result


def test_create_uses_current_user_endpoint_and_private_playlist():
    platform = SpotifyPlatform.__new__(SpotifyPlatform)
    with patch('requests.post', return_value=response({'id': 'new-playlist'}, 201)) as post:
        assert platform.create_playlist('token', 'AuxShare test') == 'new-playlist'
    assert post.call_args.args[0] == 'https://api.spotify.com/v1/me/playlists'
    assert post.call_args.kwargs['json']['public'] is False


def test_add_tracks_uses_items_endpoint_and_batches_in_order():
    platform = SpotifyPlatform.__new__(SpotifyPlatform)
    uris = [f'spotify:track:{i}' for i in range(101)]
    with patch('requests.post', return_value=response({}, 201)) as post:
        platform.add_tracks_to_playlist('token', 'playlist', uris, position=2)
    assert post.call_count == 2
    assert all(call.args[0].endswith('/playlists/playlist/items') for call in post.call_args_list)
    assert post.call_args_list[0].kwargs['json'] == {'uris': uris[:100], 'position': 2}
    assert post.call_args_list[1].kwargs['json'] == {'uris': uris[100:], 'position': 102}


def test_read_tracks_handles_new_item_field_and_pagination():
    platform = SpotifyPlatform.__new__(SpotifyPlatform)
    pages = [response({'items': [{'item': {'uri': 'spotify:track:a'}}], 'next': 'https://api.spotify.com/v1/next'}),
             response({'items': [{'track': {'uri': 'spotify:track:b'}}], 'next': None})]
    with patch('requests.get', side_effect=pages) as get:
        assert platform.get_playlist_track_uris('token', 'playlist') == ['spotify:track:a', 'spotify:track:b']
    assert '/playlists/playlist/items?' in get.call_args_list[0].args[0]


def test_count_reads_items_total_and_distinguishes_deleted_playlists():
    platform = SpotifyPlatform.__new__(SpotifyPlatform)
    with patch('requests.get', return_value=response({'total': 3})) as get:
        assert platform.get_playlist_track_count('token', 'playlist') == 3
    assert '/playlists/playlist/items?' in get.call_args.args[0]
    with patch('requests.get', return_value=response({}, 404)):
        assert platform.get_playlist_track_count('token', 'deleted') is None
