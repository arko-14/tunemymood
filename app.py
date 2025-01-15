from flask import Flask, render_template, request, jsonify
import psycopg2
from psycopg2.extras import DictCursor
import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Spotify API credentials
SPOTIFY_CLIENT_ID = '86738e072df64352afdd63b9c42e0fac'
SPOTIFY_CLIENT_SECRET = '448977bf7a2f4111a17c605d91a15f43'

app = Flask(__name__)

class SpotifyManager:
    def __init__(self):
        self.spotify = None
        try:
            client_credentials_manager = SpotifyClientCredentials(
                client_id=SPOTIFY_CLIENT_ID,
                client_secret=SPOTIFY_CLIENT_SECRET
            )
            self.spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
        except Exception as e:
            logger.error(f"Failed to initialize Spotify client: {e}")

    def search_song(self, artist, song):
        """Search for a song on Spotify"""
        try:
            query = f"artist:{artist} track:{song}"
            results = self.spotify.search(q=query, type='track', limit=1)

            if results['tracks']['items']:
                track = results['tracks']['items'][0]
                artist_name = track['artists'][0]['name']
                song_name = track['name']
                year = int(track['album']['release_date'][:4])
                preview_url = track['preview_url']
                
                return {
                    'exists': True,
                    'artist': artist_name,
                    'song': song_name,
                    'year': year,
                    'preview_url': preview_url,
                    'from_spotify': True
                }
            return None
        except Exception as e:
            logger.error(f"Spotify search error: {e}")
            return None

class SongRatingManager:
    def __init__(self):
        self.db_config = {
            'dbname': 'songsdb_vfc3',
            'user': 'songsdb_vfc3_user',
            'password': 'xnHayWhq3pxTVOyDmyZZL2O32cm8fqOl',
            'host': 'dpg-cu2jt89opnds738l28f0-a.oregon-postgres.render.com',
            'port': '5432'
        }
        self.default_image = "/static/images/default-bg.png"
        self.spotify_manager = SpotifyManager()

    def get_db_connection(self):
        return psycopg2.connect(**self.db_config)

    def update_song_rating(self, artist, song, ratings_string):
        # Convert inputs to lowercase
        artist = artist.lower()
        song = song.lower()
        
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            # Get current table structure
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'merged_songs'
                ORDER BY ordinal_position;
            """)
            columns = [column[0] for column in cursor.fetchall()]
            
            # Get current ratings for this song
            cursor.execute("""
                SELECT * FROM merged_songs 
                WHERE LOWER(artist) = %s AND LOWER(song) = %s
            """, (artist, song))
            existing_row = cursor.fetchone()
            
            if not existing_row:
                return "Song not found in database"

            # Find the next available rating column
            next_rating_num = 1
            while f'r{next_rating_num}' in columns:
                if existing_row[columns.index(f'r{next_rating_num}')] is None:
                    break
                next_rating_num += 1

            # Add new rating column if needed
            if f'r{next_rating_num}' not in columns:
                cursor.execute(f'ALTER TABLE merged_songs ADD COLUMN r{next_rating_num} TEXT')
                conn.commit()

            # Update the rating
            update_query = f"""
                UPDATE merged_songs 
                SET r{next_rating_num} = %s 
                WHERE LOWER(artist) = %s AND LOWER(song) = %s
            """
            cursor.execute(update_query, (ratings_string, artist, song))
            conn.commit()

            # Return appropriate message
            if next_rating_num == 1:
                return "You are the first one to rate this song!"
            elif next_rating_num == 2:
                return "You are the 2nd one to rate this song!"
            elif next_rating_num == 3:
                return "You are the 3rd one to rate this song!"
            else:
                return f"You are the {next_rating_num}th one to rate this song!"

        except Exception as e:
            conn.rollback()
            raise Exception(f"Error updating rating: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    def get_song_ratings(self, artist, song):
        """Get song ratings with preview URL"""
        # First check database
        db_result = self._check_database(artist, song)
        if db_result:
            return db_result

        # If not in database, check Spotify
        spotify_result = self.spotify_manager.search_song(artist, song)
        if spotify_result:
            # Add to database if found on Spotify
            if self.add_new_song(spotify_result['artist'], spotify_result['song'], spotify_result['year']):
                spotify_result['source'] = 'spotify'
                return spotify_result

        return None

    def _check_database(self, artist, song):
        """Check if song exists in database with two conditions"""
        artist = artist.lower()
        song = song.lower()
        
        conn = self.get_db_connection()
        cursor = conn.cursor(cursor_factory=DictCursor)

        try:
            # First check for exact artist match
            cursor.execute("""
                SELECT ms.*, s.preview_url 
                FROM merged_songs ms
                LEFT JOIN spotify_previews s ON ms.artist = s.artist AND ms.song = s.song
                WHERE LOWER(ms.artist) = %s
            """, (artist,))
            artist_songs = cursor.fetchall()
            
            if not artist_songs:
                return None

            # Priority 1: Exact song name match
            for song_row in artist_songs:
                if song == song_row['song'].lower():
                    result = dict(song_row)
                    return {
                        'exists': True,
                        'data': result,
                        'preview_url': result.get('preview_url'),
                        'from_spotify': False
                    }

            # Priority 2: 20% partial match
            for song_row in artist_songs:
                db_song = song_row['song'].lower()
                min_length = len(db_song) * 0.2
                if len(song) >= min_length and song in db_song:
                    result = dict(song_row)
                    return {
                        'exists': True,
                        'data': result,
                        'preview_url': result.get('preview_url'),
                        'from_spotify': False
                    }

            return None
        finally:
            cursor.close()
            conn.close()

    def get_artist_image(self, artist):
        # Convert input to lowercase
        artist = artist.lower()
        
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT link FROM "Artists" 
                WHERE LOWER(artist) = %s
            """, (artist,))
            result = cursor.fetchone()
            return result[0] if result else self.default_image
        finally:
            cursor.close()
            conn.close()

    def add_new_song(self, artist, song, year):
        """Add a new song to the database with preview URL"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        try:
            # Add to merged_songs
            cursor.execute("""
                INSERT INTO merged_songs (artist, song, year)
                VALUES (%s, %s, %s)
            """, (artist.lower(), song.lower(), year))

            # Add preview URL if available
            spotify_result = self.spotify_manager.search_song(artist, song)
            if spotify_result and spotify_result.get('preview_url'):
                cursor.execute("""
                    INSERT INTO spotify_previews (artist, song, preview_url)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (artist, song) DO UPDATE 
                    SET preview_url = EXCLUDED.preview_url
                """, (artist.lower(), song.lower(), spotify_result['preview_url']))

            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding new song: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

rating_manager = SongRatingManager()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search_song', methods=['POST'])
def search_song():
    artist = request.form['artist'].lower()
    song = request.form['song'].lower()
    result = rating_manager.get_song_ratings(artist, song)

    if result:
        response_data = {
            'exists': True,
            'artist': result['artist'] if result.get('from_spotify') else artist,
            'song': result['song'] if result.get('from_spotify') else result['data']['song'],
            'source': result.get('source', 'database'),
            'preview_url': result.get('preview_url')
        }
        return jsonify(response_data)
    return jsonify({'exists': False, 'error': 'Song not found'}), 404

@app.route('/get_artist_image', methods=['POST'])
def get_artist_image():
    artist = request.form['artist'].lower()
    image_url = rating_manager.get_artist_image(artist)
    return jsonify({'imageUrl': image_url})  # Always returns an image URL now

@app.route('/rate_song', methods=['POST'])
def rate_song():
    artist = request.form['artist'].lower()
    song = request.form['song'].lower()
    ratings = request.form['ratings']

    try:
        message = rating_manager.update_song_rating(artist, song, ratings)
        return jsonify({'message': message, 'artist': artist, 'song': song})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/ml')
def ml():
    return render_template('ml.html')    

def verify_database_structure():
    conn = rating_manager.get_db_connection()
    cursor = conn.cursor()
    try:
        # Check merged_songs table
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'merged_songs'
            ORDER BY ordinal_position;
        """)
        merged_songs_columns = [col[0] for col in cursor.fetchall()]
        print("merged_songs columns:", merged_songs_columns)

        # Check Artists table
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'artists'
            ORDER BY ordinal_position;
        """)
        artists_columns = [col[0] for col in cursor.fetchall()]
        print("Artists columns:", artists_columns)

        # Check for existing ratings
        cursor.execute("SELECT COUNT(*) FROM merged_songs WHERE r1 IS NOT NULL")
        ratings_count = cursor.fetchone()[0]
        print(f"Number of songs with ratings: {ratings_count}")

    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    # Create spotify_previews table if it doesn't exist
    conn = rating_manager.get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS spotify_previews (
                artist TEXT,
                song TEXT,
                preview_url TEXT,
                PRIMARY KEY (artist, song)
            )
        """)
        conn.commit()
    finally:
        cursor.close()
        conn.close()

    verify_database_structure()
    app.run(debug=True)
