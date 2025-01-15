// State management
let currentState = {
    page: 'search',
    songData: {
        artist: '',
        song: '',
        ratings: []
    }
};

// Initial moods configuration
const initialMoods = [
    { name: 'Soulful', value: 0 },
    { name: 'Chill', value: 0 },
    { name: 'Dramatic', value: 0 },
    { name: 'Love', value: 0 },
    { name: 'Sad', value: 0 },
    { name: 'Exotic', value: 0 },
    { name: 'Dark', value: 0 }
];

// DOM Elements
const pages = {
    search: document.getElementById('searchPage'),
    rating: document.getElementById('ratingPage'),
    thankYou: document.getElementById('thankYouPage')
};

// Navigation function
function navigateTo(page) {
    Object.values(pages).forEach(p => p.classList.add('hidden'));
    pages[page].classList.remove('hidden');
    currentState.page = page;
}

// Initialize mood sliders
function initializeMoodSliders() {
    const moodSlidersContainer = document.getElementById('moodSliders');
    moodSlidersContainer.innerHTML = initialMoods.map((mood, index) => `
        <div class="mood-slider">
            <span class="mood-name">${mood.name}</span>
            <input
                type="range"
                min="0"
                max="5"
                value="${mood.value}"
                class="slider"
                data-index="${index}"
            />
            <input
                type="number"
                min="0"
                max="5"
                value="${mood.value}"
                class="mood-value"
                data-index="${index}"
            />
        </div>
    `).join('');

    // Add event listeners to sliders
    moodSlidersContainer.addEventListener('input', (e) => {
        if (e.target.matches('input[type="range"], input[type="number"]')) {
            const index = e.target.dataset.index;
            const value = e.target.value;
            const slider = moodSlidersContainer.querySelector(`input[type="range"][data-index="${index}"]`);
            const number = moodSlidersContainer.querySelector(`input[type="number"][data-index="${index}"]`);

            // Ensure value is within bounds
            const boundedValue = Math.min(Math.max(Number(value), 0), 5);
            
            slider.value = boundedValue;
            number.value = boundedValue;
            initialMoods[index].value = boundedValue;
        }
    });
}

// Image cache and preload functions
const imageCache = new Map();

function preloadImage(url) {
    return new Promise((resolve, reject) => {
        if (imageCache.has(url)) {
            resolve(imageCache.get(url));
            return;
        }

        const img = new Image();
        img.onload = () => {
            imageCache.set(url, url);
            resolve(url);
        };
        img.onerror = () => {
            // If image loading fails, resolve with default image
            const defaultImage = '/static/images/default-bg.png';
            resolve(defaultImage);
        };
        img.src = url;
    });
}

// API Functions
async function searchSong(artist, song) {
    if (!artist.trim() || !song.trim()) {
        throw new Error('Artist and song are required');
    }

    const formData = new FormData();
    formData.append('artist', artist.trim().toLowerCase());
    formData.append('song', song.trim().toLowerCase());

    try {
        const response = await fetch('/search_song', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Song not found. Please check the artist and song name.');
        }

        return data;
    } catch (error) {
        console.error('Error searching song:', error);
        throw error;
    }
}

async function getArtistImage(artist) {
    if (!artist.trim()) {
        return '/static/images/default-bg.png';  // Return default image if no artist
    }

    const formData = new FormData();
    formData.append('artist', artist.trim().toLowerCase());

    try {
        const response = await fetch('/get_artist_image', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        return data.imageUrl;  // Will always have an image URL now
    } catch (error) {
        console.error('Error fetching artist image:', error);
        return '/static/images/default-bg.png';  // Return default image on error
    }
}

async function rateSong(artist, song, ratings) {
    if (!artist || !song || !ratings) {
        throw new Error('Missing required rating data');
    }

    const formData = new FormData();
    formData.append('artist', artist.toLowerCase());
    formData.append('song', song.toLowerCase());
    formData.append('ratings', JSON.stringify(ratings));

    try {
        const response = await fetch('/rate_song', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Rating submission failed');
        }

        return data;
    } catch (error) {
        console.error('Error submitting rating:', error);
        throw error;
    }
}

// Audio player functions
let audioPlayer = null;
let progressInterval = null;
let isPlaying = false;

function setupAudioPlayer(previewUrl) {
    if (!previewUrl) {
        console.log('No preview URL available');
        document.getElementById('audioControls').classList.add('hidden');
        return;
    }

    document.getElementById('audioControls').classList.remove('hidden');
    
    // Create new audio player if needed
    if (!audioPlayer) {
        audioPlayer = new Audio();
    }
    
    audioPlayer.src = previewUrl;
    audioPlayer.volume = 1;
    
    // Reset state
    isPlaying = false;
    updatePlayPauseButton();
    
    // Setup event listeners
    audioPlayer.addEventListener('ended', handleAudioEnd);
    audioPlayer.addEventListener('timeupdate', updateProgress);
}

function updatePlayPauseButton() {
    const playIcon = document.getElementById('playIcon');
    const pauseIcon = document.getElementById('pauseIcon');
    
    if (isPlaying) {
        playIcon.classList.add('hidden');
        pauseIcon.classList.remove('hidden');
    } else {
        playIcon.classList.remove('hidden');
        pauseIcon.classList.add('hidden');
    }
}

function updateProgress() {
    if (!audioPlayer) return;
    
    const progress = document.getElementById('progress');
    const percentage = (audioPlayer.currentTime / audioPlayer.duration) * 100;
    progress.style.width = `${percentage}%`;

    // Start fade out at 27 seconds (for 30-second preview)
    if (audioPlayer.currentTime >= 27 && audioPlayer.volume > 0) {
        audioPlayer.volume = Math.max(0, (30 - audioPlayer.currentTime) / 3);
    }
}

function handleAudioEnd() {
    audioPlayer.currentTime = 0;
    audioPlayer.volume = 1;
    
    // Wait 5 seconds before playing again
    setTimeout(() => {
        if (isPlaying) {
            audioPlayer.play();
        }
    }, 5000);
}

// Event Listeners
document.getElementById('searchForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const artist = formData.get('artist');
    const song = formData.get('song');
    const submitButton = e.target.querySelector('button[type="submit"]');
    const errorDisplay = document.getElementById('searchError') || document.createElement('div');
    errorDisplay.id = 'searchError';

    try {
        submitButton.disabled = true;
        errorDisplay.textContent = '';

        // Start fetching the image early
        const imagePromise = getArtistImage(artist).then(imageUrl => preloadImage(imageUrl));
        
        // Meanwhile, search for the song
        const searchResult = await searchSong(artist, song);
        currentState.songData = {
            artist: searchResult.artist,
            song: searchResult.song,
            source: searchResult.source
        };

        // Update page content with capitalized text
        document.getElementById('songTitle').textContent = 
            currentState.songData.song.split(' ')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
            .join(' ');
        document.getElementById('artistName').textContent = 
            currentState.songData.artist.split(' ')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
            .join(' ');

        // Optional: Display source information
        const sourceInfo = document.createElement('div');
        sourceInfo.className = 'text-cyan text-sm mt-2';
        sourceInfo.textContent = currentState.songData.source === 'spotify' 
            ? 'Song found via Spotify and added to database'
            : 'Song found in existing database';
        document.getElementById('artistName').parentNode.appendChild(sourceInfo);

        // Wait for image to be ready
        const imageUrl = await imagePromise;
        const artistImageContainer = document.getElementById('artistImageContainer');
        artistImageContainer.style.backgroundImage = `url('${imageUrl}')`;

        // Initialize and navigate
        initializeMoodSliders();
        navigateTo('rating');

        // Setup audio player with preview URL
        setupAudioPlayer(searchResult.preview_url);
    } catch (error) {
        console.error('Error:', error);
        errorDisplay.textContent = error.message;
        errorDisplay.className = 'error-message';
        if (!errorDisplay.parentNode) {
            e.target.insertBefore(errorDisplay, e.target.firstChild);
        }
    } finally {
        submitButton.disabled = false;
    }
});

document.getElementById('rateNowButton').addEventListener('click', async () => {
    const button = document.getElementById('rateNowButton');
    const errorDisplay = document.getElementById('ratingError') || document.createElement('div');
    errorDisplay.id = 'ratingError';

    try {
        button.disabled = true;
        errorDisplay.textContent = '';

        // Validate ratings
        const ratings = initialMoods.map(mood => mood.value);
        if (ratings.every(r => r === 0)) {
            throw new Error('Please rate at least one mood before submitting');
        }

        const result = await rateSong(
            currentState.songData.artist,
            currentState.songData.song,
            ratings
        );

        // Update thank you page with properly capitalized text
        document.getElementById('thankYouSongTitle').textContent = 
            currentState.songData.song.split(' ')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
            .join(' ');
        document.getElementById('thankYouArtistName').textContent = 
            currentState.songData.artist.split(' ')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
            .join(' ');
        document.getElementById('ratingMessage').textContent = result.message;

        navigateTo('thankYou');
    } catch (error) {
        errorDisplay.textContent = error.message;
        errorDisplay.className = 'error-message';
        if (!errorDisplay.parentNode) {
            button.parentNode.insertBefore(errorDisplay, button);
        }
    } finally {
        button.disabled = false;
    }
});

document.getElementById('rateMoreButton').addEventListener('click', () => {
    // Reset form and state
    document.getElementById('searchForm').reset();
    document.getElementById('searchError')?.remove();
    currentState.songData = { artist: '', song: '', ratings: [] };
    initialMoods.forEach(mood => mood.value = 0);
    navigateTo('search');
});

// Share functionality
document.querySelectorAll('.share-button').forEach(button => {
    button.addEventListener('click', async () => {
        const platform = button.dataset.platform;
        const text = `I just rated "${currentState.songData.song}" by ${currentState.songData.artist} on Tune My Mood!`;
        const url = window.location.href;

        switch(platform) {
            case 'twitter':
                window.open(`https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(url)}`);
                break;
            case 'facebook':
                window.open(`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`);
                break;
            case 'link':
                try {
                    await navigator.clipboard.writeText(url);
                    alert('Link copied to clipboard!');
                } catch (error) {
                    console.error('Failed to copy link:', error);
                    alert('Failed to copy link. Please try again.');
                }
                break;
        }
    });
});

// Add play/pause button listener
document.getElementById('playPauseBtn').addEventListener('click', () => {
    if (!audioPlayer) return;
    
    if (isPlaying) {
        audioPlayer.pause();
    } else {
        audioPlayer.volume = 1;
        audioPlayer.play();
    }
    
    isPlaying = !isPlaying;
    updatePlayPauseButton();
});

// Add this to your submitRating function
document.getElementById('submitRatingBtn').addEventListener('click', async () => {
    // Stop audio when rating is submitted
    if (audioPlayer) {
        audioPlayer.pause();
        audioPlayer.currentTime = 0;
        isPlaying = false;
        updatePlayPauseButton();
    }
    
    // ... rest of your existing submit rating code ...
});

// Initialize the app
initializeMoodSliders();
navigateTo('search'); 
