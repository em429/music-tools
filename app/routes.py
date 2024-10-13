import math
import re
from flask import Blueprint, render_template, request, g, redirect, url_for, flash
from models import get_db, get_playlists, read_playlist, get_random_track

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
    playlist = read_playlist(playlist_name)
    page = request.args.get('page', 1, type=int)
    per_page = 15
    total_pages = math.ceil(len(playlist) / per_page)
    
    start = (page - 1) * per_page
    end = start + per_page
    
    playlist_page = playlist[start:end]
    
    return render_template('playlist.html', playlist_page=playlist_page, page=page, total_pages=total_pages, get_youtube_id=get_youtube_id, playlist_name=playlist_name, playlists=playlists)

@main.route('/remove_track/<playlist_name>/<int:track_id>', methods=['POST'])
def remove_track(playlist_name, track_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        DELETE FROM playlist_tracks
        WHERE track_id = ? AND playlist_id = (SELECT id FROM playlists WHERE title = ?)
    ''', (track_id, playlist_name))
    db.commit()
    flash(f'Track removed from playlist "{playlist_name}"')
    return redirect(url_for('main.playlist', playlist_name=playlist_name))

@main.route('/create_playlist', methods=['POST'])
def create_playlist():
    playlist_name = request.form.get('playlist_name')
    if playlist_name:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id FROM playlists WHERE title = ?", (playlist_name,))
        existing_playlist = cursor.fetchone()
        if existing_playlist:
            flash(f'Playlist "{playlist_name}" already exists')
        else:
            cursor.execute("INSERT INTO playlists (title) VALUES (?)", (playlist_name,))
            db.commit()
            flash(f'Playlist "{playlist_name}" created successfully')
    return redirect(url_for('main.index'))

@main.route('/remove_playlist/<playlist_name>', methods=['POST'])
def remove_playlist(playlist_name):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM playlist_tracks WHERE playlist_id = (SELECT id FROM playlists WHERE title = ?)", (playlist_name,))
    count = cursor.fetchone()[0]
    if count == 0:
        cursor.execute("DELETE FROM playlists WHERE title = ?", (playlist_name,))
        db.commit()
        flash(f'Playlist "{playlist_name}" removed successfully')
    else:
        flash(f'Cannot remove playlist "{playlist_name}". It is not empty.')
    return redirect(url_for('main.index'))

@main.route('/add_track', methods=['POST'])
def add_track():
    playlist_name = request.form.get('playlist_name')
    date = request.form.get('date')
    artist = request.form.get('artist')
    title = request.form.get('title')
    url = request.form.get('url')

    if playlist_name and date and artist and title and url:
        db = get_db()
        cursor = db.cursor()

        cursor.execute("SELECT id FROM tracks WHERE artist = ? AND title = ?", (artist, title))
        existing_track = cursor.fetchone()

        if existing_track:
            track_id = existing_track['id']
        else:
            cursor.execute("INSERT INTO tracks (date, artist, title, url) VALUES (?, ?, ?, ?)",
                           (date, artist, title, url))
            track_id = cursor.lastrowid

        cursor.execute('''
            SELECT 1 FROM playlist_tracks
            WHERE playlist_id = (SELECT id FROM playlists WHERE title = ?)
            AND track_id = ?
        ''', (playlist_name, track_id))
        
        if cursor.fetchone():
            flash(f'Track "{title}" by {artist} is already in the playlist "{playlist_name}"')
        else:
            cursor.execute('''
                INSERT INTO playlist_tracks (playlist_id, track_id)
                VALUES ((SELECT id FROM playlists WHERE title = ?), ?)
            ''', (playlist_name, track_id))
            db.commit()
            flash(f'Track "{title}" by {artist} added to playlist "{playlist_name}"')
    else:
        flash('All fields are required to add a track')

    return redirect(url_for('main.index'))
