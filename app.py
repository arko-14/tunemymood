from flask import Flask, render_template, request, jsonify
import sqlite3
import os


app = Flask(__name__)

class SongRatingManager:
    def __init__(self, db_path=None):
        # Use environment variable or default to a relative path
        self.db_path = db_path or os.environ.get('DATABASE_URL', 'instance/songs db.db')
        
        # Create instance directory if it doesn't exist
        os.makedirs('instance', exist_ok=True)

    def get_db_connection(self):
        return sqlite3.connect(self.db_path)

    def update_song_rating(self, artist, song, ratings_string):
        # Convert inputs to lowercase
        artist = artist.lower()
        song = song.lower()
        
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            # Get current table structure
            cursor.execute("PRAGMA table_info(merged_songs)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Get current ratings for this song
            cursor.execute("""
                SELECT * FROM merged_songs 
                WHERE LOWER(Artist) = ? AND LOWER(Song) = ?
            """, (artist, song))
            existing_row = cursor.fetchone()
            
            if not existing_row:
                return "Song not found in database"

            # Find the next available rating column
            next_rating_num = 1
            while f'R{next_rating_num}' in columns:
                if existing_row[columns.index(f'R{next_rating_num}')] is None:
                    break
                next_rating_num += 1

            # Add new rating column if needed
            if f'R{next_rating_num}' not in columns:
                cursor.execute(f"ALTER TABLE merged_songs ADD COLUMN R{next_rating_num} TEXT")
                conn.commit()

            # Update the rating
            update_query = f"UPDATE merged_songs SET R{next_rating_num} = ? WHERE LOWER(Artist) = ? AND LOWER(Song) = ?"
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
            conn.close()

    def get_song_ratings(self, artist, song):
        # Convert inputs to lowercase
        artist = artist.lower()
        song = song.lower()
        
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT * FROM merged_songs 
                WHERE LOWER(Artist) = ? AND LOWER(Song) = ?
            """, (artist, song))
            result = cursor.fetchone()
            if result is None:
                return None
                
            # Get column names
            cursor.execute("PRAGMA table_info(merged_songs)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Create a dictionary with column names and values
            result_dict = dict(zip(columns, result))
            return {'exists': True, 'data': result_dict}
        finally:
            conn.close()

    def get_artist_image(self, artist):
        # Convert input to lowercase
        artist = artist.lower()
        
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT link FROM Artists WHERE LOWER(artist) = ?", (artist,))
            result = cursor.fetchone()
            return result[0] if result else None
        finally:
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

if __name__ == '__main__':
    app.run(debug=True)