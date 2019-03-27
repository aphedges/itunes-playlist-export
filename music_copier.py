"""
Author: Alex Hedges
Written for Python 3.6.4.
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

def get_playlist(root, name):
	playlists = [playlist for playlist in root['Playlists'] if playlist['Name'] == name]
	if not playlists:
		return None
	else:
		playlist = playlists[0]
	tracks = playlist['Playlist Items']
	track_ids = [track['Track ID'] for track in tracks]
	return sorted(track_ids)

def get_song(root, track_id):
	song = root['Tracks'][str(track_id)]
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

def normalize_name(text):
	return re.sub(r'[<>:"/\|?*]', '_', text)[:40].strip()

def main():
	"""Extracts the text of animal pages on Wikipedia."""
	parser = argparse.ArgumentParser(description='Extracts text of animal pages on Wikipedia.')
	parser.add_argument('playlist', help='Redownload and reextract all files')
	parser.add_argument('destination_dir', help='Redownload and reextract all files')
	args = vars(parser.parse_args())
	playlist_name = args['playlist']
	destination_dir = args['destination_dir']
	if not os.path.isfile(LIBRARY_FILE_NAME):
		raise RuntimeError('The iTunes library file "{}" does not exist!'.format(LIBRARY_FILE_NAME))
	if not os.path.isdir(destination_dir):
		raise RuntimeError('The destination directory "{}" does not exist!'.format(destination_dir))

	library_text = open(LIBRARY_FILE_NAME, mode='rb').read()
	root = plistlib.loads(library_text)
	print('Reading playlist "{}"'.format(playlist_name))
	playlist = get_playlist(root, playlist_name)
	for song in playlist:
		name, artist, album, location_source = get_song(root, song)
		open('{}.m3u'.format(playlist_name), 'ab').write(f'/storage/emulated/0/Music/{normalize_name(artist)}/{normalize_name(album)}/{split(location_source)[1]}\n'.encode('utf8'))
		location_destination = join(destination_dir, normalize_name(artist), normalize_name(album),
			split(location_source)[1])
		if os.path.isfile(location_destination):
			continue
		if not os.path.isdir(split(location_destination)[0]):
			os.makedirs(split(location_destination)[0])
		print('Copying "{}" from {}'.format(name, album), flush=True)
		shutil.copyfile(location_source, location_destination)

if __name__ == '__main__':
	main()
