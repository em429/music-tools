import sqlite3
from flask import g

DATABASE = 'playlists.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def close_db(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db(app):
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tracks
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
             date TEXT,
             artist TEXT,
             title TEXT,
             url TEXT)
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS playlists
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
             title TEXT UNIQUE)
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS playlist_tracks
            (playlist_id INTEGER,
             track_id INTEGER,
             FOREIGN KEY(playlist_id) REFERENCES playlists(id),
             FOREIGN KEY(track_id) REFERENCES tracks(id),
             PRIMARY KEY(playlist_id, track_id))
        ''')
        db.commit()

def get_playlists():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT title FROM playlists")
    return [row['title'] for row in cursor.fetchall()]

def read_playlist(playlist_name):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT t.id, t.date, t.artist, t.title, t.url
        FROM tracks t
        JOIN playlist_tracks pt ON t.id = pt.track_id
        JOIN playlists p ON p.id = pt.playlist_id
        WHERE p.title = ?
    ''', (playlist_name,))
    return cursor.fetchall()

def get_random_track():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT date, artist, title, url FROM tracks ORDER BY RANDOM() LIMIT 1")
    return cursor.fetchone()
