"""
Author: Alex Hedges
"""

import argparse
import os
from os.path import join
from os.path import split
import plistlib
import re
import shutil
from urllib.parse import unquote

LIBRARY_FILE_NAME = r'D:\Alex\Music\iTunes\iTunes Library.xml'

def get_playlist(library: dict, name: str) -> list:
    """Gets sorted list of a playlist's song IDs from library ."""
    playlists = [playlist for playlist in library['Playlists'] if playlist['Name'] == name]
    if not playlists:
        return None
    playlist = playlists[0]
    tracks = playlist['Playlist Items']
    track_ids = [track['Track ID'] for track in tracks]
    return sorted(track_ids)

def get_song(library: dict, track_id: int) -> (str, str, str, str):
    """Gets song information from library and transform it to proper format."""
    song = library['Tracks'][str(track_id)]
    name = song['Name']
    if 'Compilation' in song and song['Compilation']:
        artist = 'Compilations'
    else:
        artist = song['Artist']
    if 'Album' not in song:
        album = 'Unknown Album'
    else:
        album = song['Album']
    location = unquote(song['Location'].replace('file://localhost/', ''))

    return name, artist, album, location

def normalize_name(text: str) -> str:
    """Converts string into a version safer for file paths by:
        - Replacing characters not permitted in Windows file paths with underscores.
        - Truncating the string to 40 characters (to stay within the Windows file path limit).
        - Removing trailing and leading whitespace for convenience.
    """
    return re.sub(r'[<>:"/\|?*]+', '_', text)[:40].strip()

def write_m3u(playlist_songs: list, playlist_name: str, destination_dir: str):
    """Writes songs to .m3u file ordered by album, then song"""
    playlist_file_name = join(destination_dir, f'{normalize_name(playlist_name)}.m3u')
    songs = [(album, split(location_source)[1], artist)
        for name, artist, album, location_source in playlist_songs]
    songs.sort()
    with open(playlist_file_name, 'w', encoding='utf8') as playlist_file:
        for album, file_name, artist in songs:
            playlist_file.write('/storage/emulated/0/Music/'
                               f'{normalize_name(artist)}/{normalize_name(album)}/{file_name}\n')

def main():
    """Exports songs from a playlist (and the playlist itself) to another directory."""
    parser = argparse.ArgumentParser(
        description='Exports songs from a playlist (and the playlist itself) to another directory.')
    parser.add_argument('playlist', help='Name of playlist to export')
    parser.add_argument('destination_dir', help='Local directory to export to.')
    args = vars(parser.parse_args())
    playlist_name = args['playlist']
    destination_dir = args['destination_dir']
    if not os.path.isfile(LIBRARY_FILE_NAME):
        raise RuntimeError(f'The iTunes library file "{LIBRARY_FILE_NAME}" does not exist!')
    if not os.path.isdir(destination_dir):
        raise RuntimeError(f'The destination directory "{destination_dir}" does not exist!')

    with open(LIBRARY_FILE_NAME, mode='rb') as library_file:
        library_text = library_file.read()
    library = plistlib.loads(library_text)

    print(f'Reading playlist "{playlist_name}"')
    playlist = get_playlist(library, playlist_name)
    playlist_songs = []

    for song in playlist:
        name, artist, album, location_source = get_song(library, song)
        playlist_songs.append((name, artist, album, location_source))
        location_destination = join(destination_dir, normalize_name(artist), normalize_name(album),
            split(location_source)[1])
        if os.path.isfile(location_destination):
            continue
        if not os.path.isdir(split(location_destination)[0]):
            os.makedirs(split(location_destination)[0])
        print(f'Copying "{name}" from {album}')
        shutil.copyfile(location_source, location_destination)

    print(f'Writing playlist "{playlist_name}"')
    write_m3u(playlist_songs, playlist_name, destination_dir)


if __name__ == '__main__':
    main()
