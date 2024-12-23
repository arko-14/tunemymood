import os
import csv
import requests
from typing import List, Dict

class SpotifyScraper:
    def __init__(self, client_id: str, client_secret: str, output_dir: str = 'spotify_discographies'):
        """
        Initialize the Spotify scraper
        
        Args:
            client_id (str): Spotify API Client ID
            client_secret (str): Spotify API Client Secret
            output_dir (str): Directory to save CSV files
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = self.get_access_token()
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def get_access_token(self) -> str:
        """
        Get an OAuth access token from Spotify API
        
        Returns:
            str: Access token
        """
        url = "https://accounts.spotify.com/api/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {"grant_type": "client_credentials"}
        response = requests.post(url, headers=headers, auth=(self.client_id, self.client_secret), data=data)
        try:
            response.raise_for_status()
            response_json = response.json()
            return response_json.get('access_token')
        except Exception as e:
            print(f"Failed to get access token: {e}")
            return None

    def search_artist(self, artist_name: str) -> str:
        """
        Search for an artist and retrieve their Spotify ID
        
        Args:
            artist_name (str): Name of the artist to search for
        
        Returns:
            str: Spotify artist ID
        """
        url = f"https://api.spotify.com/v1/search?q={artist_name}&type=artist&limit=1"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = requests.get(url, headers=headers)
        try:
            response.raise_for_status()
            response_json = response.json()
            artists = response_json.get("artists", {}).get("items", [])
            if artists:
                return artists[0]["id"]
            print(f"No artist found for '{artist_name}'.")
            return None
        except Exception as e:
            print(f"Error searching artist '{artist_name}': {e}")
            return None

    def get_artist_tracks(self, artist_id: str) -> List[Dict[str, str]]:
        """
        Fetch all albums and songs for an artist
        
        Args:
            artist_id (str): Spotify artist ID
        
        Returns:
            List[Dict[str, str]]: List of songs with their release years
        """
        url = f"https://api.spotify.com/v1/artists/{artist_id}/albums?include_groups=album,single&limit=50"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = requests.get(url, headers=headers)
        tracks = []

        try:
            response.raise_for_status()
            albums = response.json().get("items", [])
            
            for album in albums:
                album_id = album.get("id")
                release_year = album.get("release_date", "N/A")[:4]
                album_name = album.get("name", "Unknown Album")
                album_tracks_url = f"https://api.spotify.com/v1/albums/{album_id}/tracks"
                
                album_response = requests.get(album_tracks_url, headers=headers)
                album_response.raise_for_status()
                for track in album_response.json().get("items", []):
                    tracks.append({
                        "song": track.get("name", "Unknown Track"),
                        "year": release_year
                    })
            return tracks
        except Exception as e:
            print(f"Error fetching tracks for artist ID '{artist_id}': {e}")
            return []

    def save_to_csv(self, artist_name: str, tracks: List[Dict[str, str]]):
        """
        Save artist tracks to a CSV file
        
        Args:
            artist_name (str): Name of the artist
            tracks (List[Dict[str, str]]): List of songs with release years
        """
        sanitized_name = artist_name.replace(" ", "_").replace("/", "_")
        filename = os.path.join(self.output_dir, f"{sanitized_name}_tracks.csv")
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Artist", "Song", "Year"])
                for track in tracks:
                    writer.writerow([artist_name, track["song"], track["year"]])
            print(f"Saved tracks for {artist_name} to {filename}")
        except Exception as e:
            print(f"Error saving tracks for '{artist_name}' to CSV: {e}")

    def scrape_artist(self, artist_name: str):
        """
        Scrape songs for a given artist name
        
        Args:
            artist_name (str): Name of the artist to scrape
        """
        print(f"Fetching data for artist: {artist_name}")
        if not self.access_token:
            print("Access token is invalid. Cannot proceed.")
            return
        
        artist_id = self.search_artist(artist_name)
        if artist_id:
            tracks = self.get_artist_tracks(artist_id)
            if tracks:
                self.save_to_csv(artist_name, tracks)
            else:
                print(f"No tracks found for artist '{artist_name}'.")
        else:
            print(f"Artist '{artist_name}' not found on Spotify.")

def main():
    # Add your Spotify API credentials here
    CLIENT_ID = "5872deacb917467c97db6e999c4bd7d7"
    CLIENT_SECRET = "b1a4c90b046e45b1b94ede8ec4b45a47"
    
    scraper = SpotifyScraper(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
    
    # List of artist names to scrape
    artist_names = [
      "Himesh Reshammiya","Sandhya Mukhopadhyay"
 ]
    
    for artist in artist_names:
        scraper.scrape_artist(artist)

if __name__ == "__main__":
    main()
