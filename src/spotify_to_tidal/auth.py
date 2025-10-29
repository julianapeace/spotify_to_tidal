#!/usr/bin/env python3

import sys
import spotipy
import tidalapi
import webbrowser
import yaml

__all__ = [
    'open_spotify_session',
    'open_tidal_session'
]

SPOTIFY_SCOPES = 'playlist-read-private, user-library-read'

def open_spotify_session(config) -> spotipy.Spotify:
    credentials_manager = spotipy.SpotifyOAuth(username=config['username'],
       scope=SPOTIFY_SCOPES,
       client_id=config['client_id'],
       client_secret=config['client_secret'],
       redirect_uri=config['redirect_uri'],
       requests_timeout=10,
       open_browser=config.get('open_browser', True),
       cache_path=f".cache-{config['username']}")
    
    try:
        # Try to get cached token first
        token = credentials_manager.get_cached_token()
        if token:
            print(f"Using cached Spotify token for user: {config['username']}")
            return spotipy.Spotify(auth=token['access_token'])
        
        # If no cached token, get new one
        print(f"Getting new Spotify token for user: {config['username']}")
        token = credentials_manager.get_access_token(as_dict=False)
        return spotipy.Spotify(auth=token)
        
    except spotipy.SpotifyOauthError as e:
        print(f"Spotify OAuth Error: {e}")
        print(f"Please visit the following URL to authorize the app:")
        print(f"{credentials_manager.get_authorize_url()}")
        print(f"After authorization, paste the redirect URL here.")
        raise e
    except Exception as e:
        print(f"Error opening Spotify session: {e}")
        raise e

def open_tidal_session(config = None) -> tidalapi.Session:
    try:
        with open('.session.yml', 'r') as session_file:
            previous_session = yaml.safe_load(session_file)
    except OSError:
        previous_session = None

    if config:
        session = tidalapi.Session(config=config)
    else:
        session = tidalapi.Session()
    if previous_session:
        try:
            if session.load_oauth_session(token_type= previous_session['token_type'],
                                   access_token=previous_session['access_token'],
                                   refresh_token=previous_session['refresh_token'] ):
                return session
        except Exception as e:
            print("Error loading previous Tidal Session: \n" + str(e) )

    login, future = session.login_oauth()
    print('Login with the webbrowser: ' + login.verification_uri_complete)
    url = login.verification_uri_complete
    if not url.startswith('https://'):
        url = 'https://' + url
    webbrowser.open(url)
    future.result()
    with open('.session.yml', 'w') as f:
        yaml.dump( {'session_id': session.session_id,
                   'token_type': session.token_type,
                   'access_token': session.access_token,
                   'refresh_token': session.refresh_token}, f )
    return session

def get_tidal_login_url(config = None) -> tuple[tidalapi.Session, str]:
    """Get Tidal session and login URL for web authentication"""
    try:
        with open('.session.yml', 'r') as session_file:
            previous_session = yaml.safe_load(session_file)
    except OSError:
        previous_session = None

    if config:
        session = tidalapi.Session(config=config)
    else:
        session = tidalapi.Session()
    
    if previous_session:
        try:
            if session.load_oauth_session(token_type= previous_session['token_type'],
                                   access_token=previous_session['access_token'],
                                   refresh_token=previous_session['refresh_token'] ):
                return session, None  # Already authenticated
        except Exception as e:
            print("Error loading previous Tidal Session: \n" + str(e) )

    login, future = session.login_oauth()
    url = login.verification_uri_complete
    if not url.startswith('https://'):
        url = 'https://' + url
    
    # Store the future for later completion
    session._login_future = future
    session._login_data = login
    
    return session, url

def complete_tidal_login(session) -> tidalapi.Session:
    """Complete Tidal authentication after user visits the login URL"""
    try:
        # Wait for the authentication to complete
        session._login_future.result()
        
        # Save the session
        with open('.session.yml', 'w') as f:
            yaml.dump( {'session_id': session.session_id,
                       'token_type': session.token_type,
                       'access_token': session.access_token,
                       'refresh_token': session.refresh_token}, f )
        
        return session
    except Exception as e:
        raise Exception(f"Tidal authentication failed: {e}")


