from flask import Flask, render_template, request, jsonify
import psycopg2
from psycopg2.extras import DictCursor
import os

app = Flask(__name__)

class SongRatingManager:
    def __init__(self):
        self.db_config = {
            'dbname': 'songsdb_vfc3',
            'user': 'songsdb_vfc3_user',
            'password': 'xnHayWhq3pxTVOyDmyZZL2O32cm8fqOl',
            'host': 'dpg-cu2jt89opnds738l28f0-a.oregon-postgres.render.com',
            'port': '5432'
        }

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
        # Convert inputs to lowercase
        artist = artist.lower()
        song = song.lower()
        
        conn = self.get_db_connection()
        cursor = conn.cursor(cursor_factory=DictCursor)

        try:
            cursor.execute("""
                SELECT * FROM merged_songs 
                WHERE LOWER(artist) = %s AND LOWER(song) = %s
            """, (artist, song))
            result = cursor.fetchone()
            
            if result is None:
                return None
                
            # Convert result to dictionary
            result_dict = dict(result)
            return {'exists': True, 'data': result_dict}
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
            return result[0] if result else None
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
        return jsonify({'exists': True, 'artist': artist, 'song': song})
    return jsonify({'exists': False, 'error': 'Song not found'}), 404

@app.route('/get_artist_image', methods=['POST'])
def get_artist_image():
    artist = request.form['artist'].lower()
    image_url = rating_manager.get_artist_image(artist)

    if image_url:
        return jsonify({'imageUrl': image_url})
    return jsonify({'error': 'Artist image not found'}), 404

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
    verify_database_structure()  # Run verification before starting the app
    app.run(debug=True)
