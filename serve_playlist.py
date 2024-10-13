#!/usr/bin/env python3

import os
import math
import re
import random
import sqlite3
from flask import Flask, render_template_string, request, g

app = Flask(__name__)

DATABASE = 'playlists.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
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
             title TEXT)
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
        SELECT t.date, t.artist, t.title, t.url
        FROM tracks t
        JOIN playlist_tracks pt ON t.id = pt.track_id
        JOIN playlists p ON p.id = pt.playlist_id
        WHERE p.title = ?
    ''', (playlist_name,))
    return cursor.fetchall()

def get_youtube_id(url):
    # Extract YouTube video ID from URL
    match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', url)
    return match.group(1) if match else None

def get_random_track():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT date, artist, title, url FROM tracks ORDER BY RANDOM() LIMIT 1")
    return cursor.fetchone()

@app.route('/')
def index():
    playlists = get_playlists()
    random_track = get_random_track()
    return render_template_string(BASE_TEMPLATE, playlists=playlists, content=render_template_string(INDEX_TEMPLATE, random_track=random_track, get_youtube_id=get_youtube_id), get_youtube_id=get_youtube_id)

@app.route('/playlist/<playlist_name>')
def playlist(playlist_name):
    playlists = get_playlists()
    playlist = read_playlist(playlist_name)
    page = request.args.get('page', 1, type=int)
    per_page = 15
    total_pages = math.ceil(len(playlist) / per_page)
    
    start = (page - 1) * per_page
    end = start + per_page
    
    playlist_page = playlist[start:end]
    
    return render_template_string(BASE_TEMPLATE, playlists=playlists, content=render_template_string(PLAYLIST_TEMPLATE, playlist_page=playlist_page, page=page, total_pages=total_pages, get_youtube_id=get_youtube_id, playlist_name=playlist_name), get_youtube_id=get_youtube_id)

BASE_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Playlist Viewer</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://www.youtube.com/iframe_api"></script>
</head>
<body class="bg-slate-100 min-h-screen">
    <nav class="bg-sky-800 p-4">
        <div class="container mx-auto space-x-3 flex justify-center text-white">
            <a href="/" class="hover:underline">home</a>
            {% for playlist in playlists %}
            <a href="{{ url_for('playlist', playlist_name=playlist) }}" class="hover:underline">{{ playlist }}</a>
            {% endfor %}
        </div>
    </nav>
    <div class="container mx-auto px-4 py-8">
        {{ content | safe }}
    </div>
    <script>
    let players = {};
    
    function onYouTubeIframeAPIReady() {
        // The API is ready, but we'll create players on demand
    }
    
    function playAudio(videoId, imgElement) {
        if (!players[videoId]) {
            players[videoId] = new YT.Player('player-' + videoId, {
                height: '0',
                width: '0',
                videoId: videoId,
                playerVars: {
                    'autoplay': 1,
                    'controls': 0,
                },
                events: {
                    'onReady': function(event) {
                        event.target.playVideo();
                        imgElement.style.opacity = '0.5';
                        updateProgressBar(videoId);
                    },
                    'onStateChange': function(event) {
                        if (event.data == YT.PlayerState.PLAYING) {
                            updateProgressBar(videoId);
                        } else {
                            clearInterval(players[videoId].progressInterval);
                        }
                    }
                }
            });
        } else {
            if (players[videoId].getPlayerState() === YT.PlayerState.PLAYING) {
                players[videoId].pauseVideo();
                imgElement.style.opacity = '1';
                clearInterval(players[videoId].progressInterval);
            } else {
                players[videoId].playVideo();
                imgElement.style.opacity = '0.5';
                updateProgressBar(videoId);
            }
        }
    }

    function updateProgressBar(videoId) {
        clearInterval(players[videoId].progressInterval);
        players[videoId].progressInterval = setInterval(() => {
            const player = players[videoId];
            const duration = player.getDuration();
            const currentTime = player.getCurrentTime();
            const progress = (currentTime / duration) * 100;
            const progressBar = document.getElementById('progress-' + videoId);
            if (progressBar) {
                progressBar.style.width = progress + '%';
            }
        }, 1000);
    }
    </script>
</body>
</html>
'''

INDEX_TEMPLATE = '''
<div class="text-center">
    <h2 class="text-2xl font-semibold mb-4">Random Track</h2>
    {% if random_track %}
    <div class="max-w-2xl mx-auto bg-white rounded-lg shadow-md overflow-hidden">
        <div class="aspect-w-16 aspect-h-9 relative">
            <img src="https://img.youtube.com/vi/{{ get_youtube_id(random_track['url']) }}/0.jpg" 
                 alt="{{ random_track['title'] }}" 
                 class="w-full h-full object-cover cursor-pointer"
                 onclick="playAudio('{{ get_youtube_id(random_track['url']) }}', this)">
            <div id="player-{{ get_youtube_id(random_track['url']) }}" class="absolute inset-0 hidden"></div>
            <div class="absolute bottom-0 left-0 right-0 h-1 bg-slate-200">
                <div id="progress-{{ get_youtube_id(random_track['url']) }}" class="h-full bg-red-500 w-0"></div>
            </div>
        </div>
        <div class="p-4">
            <a href="{{random_track['url']}}" class="hover:underline" target="_blank">
                <h2 class="text-xl font-semibold mb-2 text-slate-800">{{ random_track['title'] }}</h2>
            </a>
            <p class="text-slate-600 mb-2">{{ random_track['artist'] }}</p>
            <p class="text-sm text-slate-500">{{ random_track['date'] }}</p>
        </div>
    </div>
    {% else %}
    <p>No videos available.</p>
    {% endif %}
</div>
'''

PLAYLIST_TEMPLATE = '''
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
    {% for track in playlist_page %}
    <div class="bg-white rounded-lg shadow-md overflow-hidden">
        <div class="aspect-w-16 aspect-h-9 relative">
            <img src="https://img.youtube.com/vi/{{ get_youtube_id(track['url']) }}/0.jpg" 
                 alt="{{ track['title'] }}" 
                 class="w-full h-full object-cover cursor-pointer"
                 onclick="playAudio('{{ get_youtube_id(track['url']) }}', this)">
            <div id="player-{{ get_youtube_id(track['url']) }}" class="absolute inset-0 hidden"></div>
            <div class="absolute bottom-0 left-0 right-0 h-1 bg-slate-200">
                <div id="progress-{{ get_youtube_id(track['url']) }}" class="h-full bg-red-500 w-0"></div>
            </div>
        </div>
        <div class="p-4">
            <a href="{{track['url']}}" class="hover:underline" target="_blank">
                <h2 class="font-semibold mb-2 text-slate-800 truncate">{{ track['title'] }}</h2>
            </a>
            <p class="text-sm text-slate-600 mb-2">{{ track['artist'] }}</p>
            <p class="place-item-bottom text-xs text-slate-500">{{ track['date'] }}</p>
        </div>
    </div>
    {% endfor %}
</div>
<div class="mt-8 flex justify-center">
    {% if page > 1 %}
        <a href="{{ url_for('playlist', playlist_name=playlist_name, page=page-1) }}" class="bg-sky-800 hover:bg-sky-700 text-white font-bold py-2 px-4 rounded-l">
            Previous
        </a>
    {% endif %}
    {% if page < total_pages %}
        <a href="{{ url_for('playlist', playlist_name=playlist_name, page=page+1) }}" class="bg-sky-800 hover:bg-sky-700 text-white font-bold py-2 px-4 rounded-r">
            Next
        </a>
    {% endif %}
</div>
'''

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5001)
