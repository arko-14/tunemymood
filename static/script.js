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

            slider.value = value;
            number.value = value;
            initialMoods[index].value = Number(value);
        }
    });
}

// API Functions
async function searchSong(artist, song) {
    if (!artist.trim() || !song.trim()) {
        throw new Error('Artist and song are required');
    }

    const formData = new FormData();
    formData.append('artist', artist.trim());
    formData.append('song', song.trim());

    try {
        const response = await fetch('/search_song', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error('Song search failed');
        }

        return await response.json();
    } catch (error) {
        console.error('Error searching song:', error);
        throw error;
    }
}

async function getArtistImage(artist) {
    if (!artist.trim()) {
        throw new Error('Artist name is required');
    }

    const formData = new FormData();
    formData.append('artist', artist.trim());

    try {
        const response = await fetch('/get_artist_image', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error('Failed to fetch artist image');
        }

        const data = await response.json();
        return data.imageUrl;
    } catch (error) {
        console.error('Error fetching artist image:', error);
        throw error;
    }
}

async function rateSong(artist, song, ratings) {
    if (!artist || !song || !ratings) {
        throw new Error('Missing required rating data');
    }

    const formData = new FormData();
    formData.append('artist', artist);
    formData.append('song', song);
    formData.append('ratings', JSON.stringify(ratings));

    try {
        const response = await fetch('/rate_song', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error('Rating submission failed');
        }

        return await response.json();
    } catch (error) {
        console.error('Error submitting rating:', error);
        throw error;
    }
}

// Add this at the top of your script
const imageCache = new Map();

// Preload image function
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
        img.onerror = reject;
        img.src = url;
    });
}

// Event Listeners
document.getElementById('searchForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const artist = formData.get('artist');
    const song = formData.get('song');

    try {
        e.target.querySelector('button[type="submit"]').disabled = true;

        // Start fetching the image early
        const imagePromise = getArtistImage(artist).then(imageUrl => preloadImage(imageUrl));
        
        // Meanwhile, search for the song
        const searchResult = await searchSong(artist, song);
        currentState.songData = {
            artist: searchResult.artist,
            song: searchResult.song
        };

        // Update page content
        document.getElementById('songTitle').textContent = currentState.songData.song;
        document.getElementById('artistName').textContent = currentState.songData.artist;

        // Wait for image to be ready
        const imageUrl = await imagePromise;
        const artistImageContainer = document.getElementById('artistImageContainer');
        artistImageContainer.style.backgroundImage = `url('${imageUrl}')`;

        // Initialize and navigate
        initializeMoodSliders();
        navigateTo('rating');
    } catch (error) {
        console.error('Error:', error);
        alert('Error searching for song. Please try again.');
    } finally {
        e.target.querySelector('button[type="submit"]').disabled = false;
    }
});

document.getElementById('rateNowButton').addEventListener('click', async () => {
    const button = document.getElementById('rateNowButton');
    button.disabled = true;

    try {
        // Collect ratings from mood sliders
        const ratings = initialMoods.map(mood => mood.value);

        const result = await rateSong(
            currentState.songData.artist,
            currentState.songData.song,
            ratings
        );

        // Update thank you page
        document.getElementById('thankYouSongTitle').textContent = currentState.songData.song;
        document.getElementById('thankYouArtistName').textContent = currentState.songData.artist;
        document.getElementById('ratingMessage').textContent = result.message;

        // Navigate to thank you page
        navigateTo('thankYou');
    } catch (error) {
        alert('Error submitting rating. Please try again.');
    } finally {
        button.disabled = false;
    }
});

document.getElementById('rateMoreButton').addEventListener('click', () => {
    // Reset form and state
    document.getElementById('searchForm').reset();
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

// Initialize the app
initializeMoodSliders();
navigateTo('search');
