import math
import re
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models import get_playlists, read_playlist, get_random_track, remove_track_from_playlist, create_playlist, remove_playlist, add_track_to_playlist, move_track_between_playlists, increment_play_count

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
    sort_by = request.args.get('sort', 'date')  # Default sort by date
    sort_direction = request.args.get('direction', 'ASC')  # Default sort direction is ascending
    playlist = read_playlist(playlist_name, search_query, sort_by, sort_direction)
    page = request.args.get('page', 1, type=int)
    per_page = 15
    total_pages = math.ceil(len(playlist) / per_page)
    
    start = (page - 1) * per_page
    end = start + per_page
    
    playlist_page = playlist[start:end]
    
    return render_template('playlist.html', playlist=playlist, playlist_page=playlist_page, page=page, total_pages=total_pages, get_youtube_id=get_youtube_id, playlist_name=playlist_name, playlists=playlists, search_query=search_query, sort_by=sort_by, sort_direction=sort_direction)

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

@main.route('/move_track/<int:track_id>', methods=['POST'])
def move_track(track_id):
    from_playlist = request.form.get('from_playlist')
    to_playlist = request.form.get('to_playlist')
    
    if from_playlist and to_playlist:
        if move_track_between_playlists(track_id, from_playlist, to_playlist):
            flash(f'Track moved from "{from_playlist}" to "{to_playlist}"')
        else:
            flash(f'Failed to move track. It may already exist in the destination playlist.')
    else:
        flash('Both source and destination playlists are required to move a track')
    
    return redirect(url_for('main.playlist', playlist_name=from_playlist))

@main.route('/increment_play_count/<int:track_id>', methods=['POST'])
def increment_play_count_route(track_id):
    increment_play_count(track_id)
    return jsonify(success=True)
