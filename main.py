import os
import requests
from flask import Flask, session, redirect, request, url_for
from decouple import config, Csv

from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import FlaskSessionCacheHandler


# Initialize the Flask application
app = Flask(__name__)
# Set a secret key for session management
app.config['SECRET_KEY'] = os.urandom(64)


# Load Spotify API credentials from environment variables
client_id = config("client_id")
client_secret = config("client_secret")
redirect_uri ='http://localhost:5000/callback'
scope ='user-library-read'


# Initialize the cache handler to manage session caching
cache_handler = FlaskSessionCacheHandler(session)

# Initialize Spotify OAuth object with credentials and cache handler
sp_Oauth = SpotifyOAuth(
    client_id = client_id,
    client_secret = client_secret,
    redirect_uri = redirect_uri,
    scope = scope,
    cache_handler = cache_handler,
    show_dialog = True
)
# Initialize the Spotify object using the OAuth manager
sp = Spotify(auth_manager=sp_Oauth)


# Home route - checks if there is a valid token, if not, redirects to the authorization URL
@app.route('/')
def home():
    if not sp_Oauth.validate_token(cache_handler.get_cached_token()):
        auth_url = sp_Oauth.get_authorize_url()
        return redirect(auth_url)
    return redirect(url_for('get_saved_songs'))


# Callback route - handles the redirect from Spotify after user authorization
@app.route('/callback')
def callback():
    sp_Oauth.get_access_token(request.args['code'])
    return redirect(url_for('get_saved_songs'))


# Route to get and display the user's saved songs
@app.route('/get_saved_songs')
def get_saved_songs():
    if not sp_Oauth.validate_token(cache_handler.get_cached_token()):
        auth_url = sp_Oauth.get_authorize_url()
        return redirect(auth_url)
    
    # Retrieve the cached token
    token_info = sp_Oauth.get_cached_token()

    # Re-initialize the Spotify object with the access token
    sp = Spotify(auth=token_info['access_token'])
    

    # Fetch the user's saved tracks
    results = sp.current_user_saved_tracks()

    # Create a list of strings containing track names and artist names
    saved_songs = [
        f"{item['track']['name']} by {', '.join(artist['name'] for artist in item['track']['artists'])}"
        for item in results['items']
    ]
    
    # Display the list of saved songs as an HTML response
    return "<br>".join(saved_songs)


# Route to log out the user by clearing the session
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# Runs the Flask application
if __name__ == '__main__':
    app.run(debug=True)