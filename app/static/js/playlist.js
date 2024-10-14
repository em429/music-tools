function toggleDropdown(trackId) {
    var dropdown = document.getElementById('dropdown-' + trackId);
    dropdown.classList.toggle('hidden');
}

// Close the dropdown when clicking outside
window.onclick = function(event) {
    if (!event.target.matches('.bg-sky-800')) {
        var dropdowns = document.getElementsByClassName("origin-top-right");
        for (var i = 0; i < dropdowns.length; i++) {
            var openDropdown = dropdowns[i];
            if (!openDropdown.classList.contains('hidden')) {
                openDropdown.classList.add('hidden');
            }
        }
    }
}

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