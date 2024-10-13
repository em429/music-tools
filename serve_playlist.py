#!/usr/bin/env python3

import sys
import math
import re

import pandas as pd
from flask import Flask, render_template_string, request

app = Flask(__name__)

def read_playlist():
    return pd.read_csv(sys.argv[1], header=None, names=['date', 'artist', 'title', 'url'])

def get_youtube_id(url):
    # Extract YouTube video ID from URL
    match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', url)
    return match.group(1) if match else None

@app.route('/')
def index():
    playlist = read_playlist()
    page = request.args.get('page', 1, type=int)
    per_page = 9
    total_pages = math.ceil(len(playlist) / per_page)
    
    start = (page - 1) * per_page
    end = start + per_page
    
    playlist_page = playlist.iloc[start:end]
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Playlist Viewer</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://www.youtube.com/iframe_api"></script>
    </head>
    <body class="bg-gray-100 min-h-screen py-8">
        <div class="container mx-auto px-4">
            <h1 class="text-4xl font-bold mb-8 text-center text-gray-800">Playlist Viewer</h1>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {% for _, track in playlist_page.iterrows() %}
                <div class="bg-white rounded-lg shadow-md overflow-hidden">
                    <div class="p-4">
                        <h2 class="text-xl font-semibold mb-2 text-gray-800">{{ track.title }}</h2>
                        <p class="text-gray-600 mb-2">{{ track.artist }}</p>
                        <p class="text-sm text-gray-500">{{ track.date }}</p>
                    </div>
                    <div class="aspect-w-16 aspect-h-9 relative">
                        <img src="https://img.youtube.com/vi/{{ get_youtube_id(track.url) }}/0.jpg" 
                             alt="{{ track.title }}" 
                             class="w-full h-full object-cover cursor-pointer"
                             onclick="playAudio('{{ get_youtube_id(track.url) }}', this)">
                        <div id="player-{{ get_youtube_id(track.url) }}" class="absolute inset-0 hidden"></div>
                    </div>
                </div>
                {% endfor %}
            </div>
            <div class="mt-8 flex justify-center">
                {% if page > 1 %}
                    <a href="?page={{ page - 1 }}" class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-l">
                        Previous
                    </a>
                {% endif %}
                {% if page < total_pages %}
                    <a href="?page={{ page + 1 }}" class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-r">
                        Next
                    </a>
                {% endif %}
            </div>
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
                        }
                    }
                });
            } else {
                if (players[videoId].getPlayerState() === YT.PlayerState.PLAYING) {
                    players[videoId].pauseVideo();
                    imgElement.style.opacity = '1';
                } else {
                    players[videoId].playVideo();
                    imgElement.style.opacity = '0.5';
                }
            }
        }
        </script>
    </body>
    </html>
    ''', playlist_page=playlist_page, page=page, total_pages=total_pages, get_youtube_id=get_youtube_id)

if __name__ == '__main__':
    app.run(debug=True)
