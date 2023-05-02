import os
import warnings


import spotipy
from spotipy.oauth2 import SpotifyOAuth


CLIENT_SECRET = os.environ['CLIENT_SECRET']
CLIENT_ID = os.environ['CLIENT_ID']
REDIRECT_URI = os.environ['REDIRECT_URI']
USERNAME = os.environ['USERNAME']
SCOPES = ['playlist-read-private', 'playlist-modify-private']


auth_manager = spotipy.SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=SCOPES
)

url = auth_manager.get_authorize_url()

print(f'1. Open the  link in your browser:\n\n{url}\n')

redirect_url = input(
    '2. Enter the URL that you\'ve gotten redirected to after accepting the authorization\n'
)
response_code = auth_manager.parse_response_code(redirect_url)
with warnings.catch_warnings():
    warnings.filterwarnings("ignore")
    access_token = auth_manager.get_access_token(response_code)

print(f'Your refresh token is:\n{access_token["refresh_token"]}\n')
