import sqlite3
conn = sqlite3.connect("D:\SONG\songs db.db")  # Replace with your database name
cursor = conn.cursor()


cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
existing_tables = cursor.fetchall()
print("Existing tables:", [table[0] for table in existing_tables])


cursor.execute("""
    CREATE TABLE IF NOT EXISTS Artists (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        artist TEXT NOT NULL,
        link TEXT
    )
""")
print("Table 'Artists' created (if it didn't exist).")


cursor.execute("SELECT DISTINCT Artist FROM new_songs")  # Replace "Songs" with your actual table name
artists = cursor.fetchall()


for artist in artists:
    cursor.execute("INSERT INTO Artists (artist, link) VALUES (?, ?)", (artist[0], None))


conn.commit()
conn.close()

print("Artist data inserted into the 'Artists' table.")
