import os
import sys
import time
import logging
import datetime
import traceback


import spotipy
from spotipy.oauth2 import SpotifyOAuth

DATE_FORMAT = '%Y%m%d_%HM%%S'

CONSOLE_LOG_FORMAT = '%(levelname)-12s %(name)-20s %(message)s'
FILE_LOG_FORMAT = '%(asctime)-23s %(levelname)-20s %(name)-12s %(message)s'

CLIENT_SECRET = os.environ['CLIENT_SECRET']
CLIENT_ID = os.environ['CLIENT_ID']
REFRESH_TOKEN = os.environ['REFRESH_TOKEN']
REDIRECT_URI = os.environ['REDIRECT_URI']
USERNAME = os.environ['USERNAME']
SCOPES = ['playlist-read-private', 'playlist-modify-private']


def get_discover_weekly_playlist_id(client):
    discover_weekly_playlist_id = None

    results = client.search(q='Discover Weekly', type='playlist')
    for result in results['playlists']['items']:
        if result['name'] == 'Discover Weekly':
            discover_weekly_playlist_id = result['id']
    return discover_weekly_playlist_id


def parse_current_week(client, discover_weekly_playlist_id):
    discover_weekly_items = client.playlist(discover_weekly_playlist_id)
    playlist_created = datetime.datetime.strptime(
        discover_weekly_items['tracks']['items'][0]['added_at'], '%Y-%m-%dT%H:%M:%SZ'
    )
    
    discover_weekly_uris = [track['track']['uri'] for track in discover_weekly_items['tracks']['items']]
    playlist_date = playlist_created.strftime('%Y-%m-%d')
    return playlist_date, discover_weekly_uris


def add_to_permanent_playlist(client, username, playlist_date, discover_weekly_uris, logger):
    current_week_playlist = f'Discover Weekly from {playlist_date}'

    playlists = client.user_playlists(username)
    for playlist in playlists['items']:
        if playlist['name'] == current_week_playlist:
            playlist_id = playlist['id']
            break
    else:
        # Create a new playlist
        logger.info(f'Creating this week\'s discover playlist: {current_week_playlist}')
        saved_playlist = client.user_playlist_create(
            username, current_week_playlist, public=False
        )
        playlist_id = saved_playlist['id']

    # Get the tracks in the permanent playlist
    permanent_tracks = []
    permanent_tracks_response = client.playlist_tracks(playlist_id, offset=0, limit=50)
    permanent_tracks.extend(permanent_tracks_response['items'])
    while permanent_tracks_response['next']:
        permanent_tracks_response = client.next(permanent_tracks_response)
        permanent_tracks.extend(permanent_tracks_response['items'])
    
    # Check if any of the tracks in the discovery weekly playlist are already in the permanent playlist
    new_tracks = []
    for uri in discover_weekly_uris:
        if uri not in [track['track']['uri'] for track in permanent_tracks]:
            new_tracks.append(uri)
    # Add the new tracks to the permanent playlist
    if new_tracks:
        client.playlist_add_items(playlist_id, new_tracks)
        logger.info('Done creating this week\'s archive playlist.')
    else:
        logger.info(
            'This script has already been run for this week.'
            'Skipping add to a permanent playlist.'
        )
        return


def setup_logging(log_file, verbose):
    logging_level = logging.INFO
    if verbose:
        logging_level = logging.DEBUG

    logger = logging.getLogger('main')
    logger.setLevel(logging_level)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging_level)
    stream_handler.setFormatter(logging.Formatter(CONSOLE_LOG_FORMAT))
    logger.addHandler(stream_handler)

    if log_file is not None:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging_level)
        file_handler.setFormatter(logging.Formatter(FILE_LOG_FORMAT))
        logger.addHandler(file_handler)
    
    return logger


def main():
    logger = setup_logging('status.log', False)

    start_time = time.perf_counter()
    logger.info('Script started discover weekly archiving!')

    try:
        auth_manager = SpotifyOAuth(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
            scope=SCOPES,
        )
        auth_manager.refresh_access_token(REFRESH_TOKEN)

        client = spotipy.Spotify(
            auth_manager=auth_manager
        )
    except Exception as e:
        logger.error('Error while authenticating the spotify client: {0}'.format(e))
        logger.error(traceback.format_exc())

    playlist_date, discover_weekly_uris = parse_current_week(
        client, get_discover_weekly_playlist_id(client)
    )
    logger.info(f'Found this week\'s playlist for {playlist_date}')
    
    logger.info('Adding to the weekly archive')
    try:
        add_to_permanent_playlist(
            client=client,
            username=USERNAME, 
            playlist_date=playlist_date, 
            discover_weekly_uris=discover_weekly_uris, 
            logger=logger,
        )
    except Exception as e:
        logger.error('Error while discovering: {0}'.format(e))
        logger.error(traceback.format_exc())

    logger.info('Done discover weekly archiving')
    logger.info('discover weekly archiving script has finished in {0} seconds'.format(round(time.perf_counter() - start_time, 3)))


if __name__ == '__main__':
    main()



