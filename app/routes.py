import math
import re
from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import get_playlists, read_playlist, get_random_track, remove_track_from_playlist, create_playlist, remove_playlist, add_track_to_playlist

main = Blueprint('main', __name__)

def get_youtube_id(url):
    match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', url)
    return match.group(1) if match else None

@main.route('/')
def index():
    playlists = get_playlists()
    random_track = get_random_track()
    return render_template('index.html', random_track=random_track, get_youtube_id=get_youtube_id, playlists=playlists)

@main.route('/playlist/<playlist_name>')
def playlist(playlist_name):
    playlists = get_playlists()
    search_query = request.args.get('search', '')
    playlist = read_playlist(playlist_name, search_query)
    page = request.args.get('page', 1, type=int)
    per_page = 15
    total_pages = math.ceil(len(playlist) / per_page)
    
    start = (page - 1) * per_page
    end = start + per_page
    
    playlist_page = playlist[start:end]
    
    return render_template('playlist.html', playlist=playlist, playlist_page=playlist_page, page=page, total_pages=total_pages, get_youtube_id=get_youtube_id, playlist_name=playlist_name, playlists=playlists, search_query=search_query)

@main.route('/remove_track/<playlist_name>/<int:track_id>', methods=['POST'])
def remove_track(playlist_name, track_id):
    remove_track_from_playlist(track_id, playlist_name)
    flash(f'Track removed from playlist "{playlist_name}"')
    return redirect(url_for('main.playlist', playlist_name=playlist_name))

@main.route('/create_playlist', methods=['POST'])
def create_playlist_route():
    playlist_name = request.form.get('playlist_name')
    if playlist_name:
        if create_playlist(playlist_name):
            flash(f'Playlist "{playlist_name}" created successfully')
        else:
            flash(f'Playlist "{playlist_name}" already exists')
    return redirect(url_for('main.index'))

@main.route('/remove_playlist/<playlist_name>', methods=['POST'])
def remove_playlist_route(playlist_name):
    if remove_playlist(playlist_name):
        flash(f'Playlist "{playlist_name}" removed successfully')
        return redirect(url_for('main.index'))
    else:
        flash(f'Cannot remove playlist "{playlist_name}". It is not empty.')
        return redirect(url_for('main.playlist', playlist_name=playlist_name))

@main.route('/add_track', methods=['POST'])
def add_track():
    playlist_name = request.form.get('playlist_name')
    date = request.form.get('date')
    artist = request.form.get('artist')
    title = request.form.get('title')
    url = request.form.get('url')

    if playlist_name and date and artist and title and url:
        if add_track_to_playlist(playlist_name, date, artist, title, url):
            flash(f'Track "{title}" by {artist} added to playlist "{playlist_name}"')
        else:
            flash(f'Track "{title}" by {artist} is already in the playlist "{playlist_name}"')
    else:
        flash('All fields are required to add a track')

    return redirect(url_for('main.index'))
