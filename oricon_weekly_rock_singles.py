import mechanicalsoup
import os
import spotipy
from datetime import datetime
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth


load_dotenv()
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
    redirect_uri="http://127.0.0.1:9090",
    scope="playlist-read-private playlist-modify-private"
))
ORICON_WEEKLY_ROCK_SINGLES_URL = 'https://www.oricon.co.jp/rank/rs/w/'
PLAYLIST_ID = os.getenv("SPOTIFY_PLAYLIST_ID")
SILENT_TRACK_ID = '5XSKC4d0y0DfcGbvDOiL93'


def get_oricon_url():
    # The default url should redirect to something like "https://www.oricon.co.jp/rank/rs/w/2021-02-15/"
    # Use the redirected url in rest of the code
    browser = mechanicalsoup.StatefulBrowser()
    browser.open(ORICON_WEEKLY_ROCK_SINGLES_URL)
    return browser.url


def get_songs(oricon_url):
    print('getting songs from oricon website...')
    browser = mechanicalsoup.StatefulBrowser()
    songs = []

    # Page 1 Songs #1-10
    browser.open(oricon_url)
    entries = browser.page.find_all("section", {"class": "box-rank-entry"})

    for entry in entries:
        songArtist = entry.findChild("p", {"class": "name"}).string
        songTitle = entry.findChild("h2", {"class": "title"}).string
        songs.append({"artist": songArtist, "track": songTitle})

    # Page 2 Songs #11-20
    browser.open(oricon_url + 'p/2/')
    entries = browser.page.find_all("section", {"class": "box-rank-entry"})

    for entry in entries:
        songArtist = entry.findChild("p", {"class": "name"}).string
        songTitle = entry.findChild("h2", {"class": "title"}).string
        songs.append({"artist": songArtist, "track": songTitle})

    print('songs gotten from oricon website')
    return songs


def clear_playlist():
    print('clearing playlist...')

    # Get current songs on playlist
    current_songs_on_playlist = []
    playlist_items = sp.playlist_items(PLAYLIST_ID, fields='items.track.id')
    for playlist_item in playlist_items['items']:
        current_songs_on_playlist.append(playlist_item['track']['id'])

    # Remove the songs from the playlist
    sp.playlist_remove_all_occurrences_of_items(
        PLAYLIST_ID, current_songs_on_playlist
    )

    print('playlist cleared')


def add_songs_to_playlist(songs):
    print('adding songs to playlist...')
    playlist_songs = []

    for song in songs:
        # If two artists Oricon uses " & ", Spotify doesn't understand that
        artist = song['artist'].split(' & ')[0]
        # Often track titles on Oricon have a "/" containing two tracks, Spotify doesn't understand that
        track = song['track'].split('/')[0]

        query = f"{artist} {track}"
        results = sp.search(q=query)

        if len(results['tracks']['items']) == 0:
            print(song)
            print(f'nothing found for this query: "{query}"')

            # Add Silent Track for songs that were not found
            playlist_songs.append(SILENT_TRACK_ID)

            # FIXME send email if a song is not found, manual action needed
            continue

        first_result = results['tracks']['items'][0]
        playlist_songs.append(first_result["id"])

    sp.playlist_add_items(PLAYLIST_ID, playlist_songs)

    print('songs added to playlist')


def update_playlist_description(oricon_url):
    print('updating playlist description')

    sp.playlist_change_details(
        playlist_id=PLAYLIST_ID,
        description=f'[Updated Weekly]  [Silent Track for unfound songs]  [Last Updated: {datetime.date(datetime.now())}]  [Retrieved From Oricon Japan: {oricon_url}] '
    )

    print('playlist description updated')


oricon_url = get_oricon_url()
songs = get_songs(oricon_url)
clear_playlist()
add_songs_to_playlist(songs)
update_playlist_description(oricon_url)
