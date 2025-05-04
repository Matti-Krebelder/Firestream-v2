import flask_cors
from flask import Flask, request, render_template, jsonify, redirect, url_for, session, flash, g
import os
import requests
import sys
import json
import requests
from bs4 import BeautifulSoup
import re
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime



#Error Code List:
# HTTP Status Codes
# 404 = Not Found
# 403 = Forbidden

# Additional status codes

# 401 = Unauthorized - Authentication is required and has failed or has not yet been provided.
# 400 = Bad Request - The request could not be understood or was missing required parameters.
# 429 = Too Many Requests - The user has sent too many requests in a given amount of time ("rate limiting").
# 503 = Service Unavailable - The server is currently unavailable (overloaded or down).
# 405 = Method Not Allowed - The request method is not supported for the requested resource.

# Custom error codes or application-specific status
# 450 = Registration Disabled - Custom status code indicating registration is currently disabled.


# ____  _             _               
#/ ___|| |_ __ _ _ __| |_ _   _ _ __  
#\___ \| __/ _` | '__| __| | | | '_ \ 
# ___) | || (_| | |  | |_| |_| | |_) |
#|____/ \__\__,_|_|   \__|\__,_| .__/ 
#                              |_|    

app = Flask(__name__)
app.secret_key = 'sduj23hj89h9ziuhT6tgizugh9'

from flask_cors import CORS
CORS(app)

REGISTRATION = 0 # Enable / Disable Registration 0 = Disable, 1 = Enable
LOGO_SRC = '../static/utility/images/logo.png'
MEDIA_DIR = "./static/Media/"
UPLOAD_DIR = "./static/Uploads/"
METADATA_DIR ="./static/metadata/"
GENRES_DIR = "./static/utility/"
YOUTUBE_LINKS_DIR = "./static/utility/youtube_links/"
THE_MOVIE_DB_KEY = "4b94f857a0c0c333c98dbd3e1a937e85" # https://www.themoviedb.org/settings/api here you can get your own (no worries if you dont upload 500 new Movies Per day you wont reach your limit)
FIRESTREAM_APIKEY = "FST-2025-XYZ123-ABCD4567-EFGH8901"
SERVER_PORT = "5000" # Standard is 80 or 8080
SERVER_IP = "http://127.0.0.1" # Please include http:// / https:// enter server ip or if you have the domain :)
PANEL_NAME = "Firestream v2" # come on! you can do it think a name on your own.
DATABASE = f"{PANEL_NAME}.db" # you can change it how ever you like :)
BACKGROUND_DESIGN = "https://repository-images.githubusercontent.com/299409710/b42f7780-0fe1-11eb-8460-e459acd20fb4" # enter any background image you like



#    _         _   _                _   _           _   _             
#   / \  _   _| |_| |__   ___ _ __ | |_(_) ___ __ _| |_(_) ___  _ __  
#  / _ \| | | | __| '_ \ / _ \ '_ \| __| |/ __/ _` | __| |/ _ \| '_ \ 
# / ___ \ |_| | |_| | | |  __/ | | | |_| | (_| (_| | |_| | (_) | | | |
#/_/   \_\__,_|\__|_| |_|\___|_| |_|\__|_|\___\__,_|\__|_|\___/|_| |_|

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
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_admin BOOLEAN DEFAULT 0
            )
        ''')

        if not db.execute('SELECT 1 FROM users WHERE is_admin = 1').fetchone():
            db.execute(
                'INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)',
                ('admin', generate_password_hash('admin123'), 1))
        db.commit()

if not os.path.exists(DATABASE):
    init_db()






# _____                 _   _                 
#|  ___|   _ _ __   ___| |_(_) ___  _ __  ___ 
#| |_ | | | | '_ \ / __| __| |/ _ \| '_ \/ __|
#|  _|| |_| | | | | (__| |_| | (_) | | | \__ \
#|_|   \__,_|_| |_|\___|\__|_|\___/|_| |_|___/

def get_movies():
    result = [f for f in os.listdir(MEDIA_DIR) if os.path.isfile(os.path.join(MEDIA_DIR, f))]
    return(result)

def get_youtube_links():
    result = [f for f in os.listdir(YOUTUBE_LINKS_DIR) if os.path.isfile(os.path.join(YOUTUBE_LINKS_DIR, f))]
    return(result)

def get_series():
    result = [f for f in os.listdir(MEDIA_DIR) if os.path.isdir(os.path.join(MEDIA_DIR, f))]
    return(result)

def get_metafiles():
    result = [f for f in os.listdir(METADATA_DIR) if os.path.isfile(os.path.join(METADATA_DIR, f))]
    return(result)

def get_metadata(name):
    if(name + ".json" in get_metafiles()):
        print(f"{name} Schon vorhanden Pulle Metadaten Lokal...")
        with open(f"{METADATA_DIR}{name}.json", "r") as file:
            data = json.load(file)
        return(data)
    else:
        meta = requests.get(f"https://api.themoviedb.org/3/search/movie?api_key={THE_MOVIE_DB_KEY}&query={name}")
        obj = meta.json()
        ranked = (obj["results"][0])
        with open(f"{METADATA_DIR}{name}.json", "w") as file:
            json.dump(ranked, file)

        with open(f"{METADATA_DIR}Fulldata/{name}.json", "w") as f:
            json.dump(meta.json(), f)
        return(ranked)
    
def get_movie_list():
    movies = get_movies()
    Series = get_series()

    merged_data = {
        "series": [],
        "movies": []
    }

    for serie in Series:
        metadata = get_metadata(serie)
        trailer = get_trailer_embed(serie)
        metadata['trailer'] = trailer["url"]
        metadata['url'] = f'/static/{serie}/'
        merged_data["series"].append(metadata)
    for movie in movies:
        formatted = movie[:-4]
        if "." in formatted:
            print(f"Error Your File {movie} is not an MP4!")
        else:
            metadata = get_metadata(formatted)
            trailer = get_trailer_embed(formatted)
            metadata['trailer'] = trailer["url"]
            metadata['url'] = f'/static/{movie}.mp4'
            merged_data["movies"].append(metadata)

    json_data = json.dumps(merged_data)
    return json_data



def get_trailer_embed(search_query):
    movies = get_youtube_links()
    if search_query +".json" in movies:
        print(f"Pulling {search_query} Embed link local...")
        with open(f"{YOUTUBE_LINKS_DIR}{search_query}.json", "r") as file:
            return json.load(file)
    else:
        print(f"{search_query} is not local trying to Pull it from youtube")
        url = f"https://www.youtube.com/results?search_query={search_query}"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            match = re.search(r'{"videoId":"([a-zA-Z0-9_-]{11})"', response.text)
            
            if match:
                video_id = match.group(1)
                video_url = f"https://www.youtube.com/embed/{video_id}?si=imapQDk78P6blfcW"
                with open(f"{YOUTUBE_LINKS_DIR}{search_query}.json", "w") as file:
                    data = {
                        "url" : video_url
                    }
                    json.dump(data, file)
                return data
            
            else:
                return("none")

        except requests.RequestException as e:
            print("Fehler beim Abrufen der Seite:", e)








#    _                  ____             _            
#   / \   _ __  _ __   |  _ \ ___  _   _| |_ ___  ___ 
#  / _ \ | '_ \| '_ \  | |_) / _ \| | | | __/ _ \/ __|
# / ___ \| |_) | |_) | |  _ < (_) | |_| | ||  __/\__ \
#/_/   \_\ .__/| .__/  |_| \_\___/ \__,_|\__\___||___/
#        |_|   |_|                                    

@app.route('/')
def index():
    if 'username' in session:
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = ?', (session['username'],)).fetchone()
        return render_template('index.html', 
                             username=user['username'],
                             is_admin=user['is_admin'],
                             created_at=user['created_at'],
                             panel_name=PANEL_NAME,
                             logo=LOGO_SRC,
                             serverip=SERVER_IP,
                             port=SERVER_PORT
                             
                             )
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        
        if user and check_password_hash(user['password'], password):
            session['username'] = user['username']
            session['is_admin'] = bool(user['is_admin'])
            flash('Login erfolgreich!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Falsche Anmeldedaten', 'error')
    
    return render_template('login.html', panel_name=PANEL_NAME, logo=LOGO_SRC, background=BACKGROUND_DESIGN)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if REGISTRATION == 1:
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            email = request.form.get('email', '')
            
            db = get_db()
            try:
                db.execute(
                    'INSERT INTO users (username, password, email) VALUES (?, ?, ?)',
                    (username, generate_password_hash(password), email)
                )
                db.commit()
                flash('Registrierung erfolgreich! Bitte einloggen.', 'success')
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                flash('Benutzername bereits vergeben', 'error')
        
        return render_template('register.html', panel_name=PANEL_NAME, logo=LOGO_SRC, background=BACKGROUND_DESIGN)
    else:
        return render_template('error.html', errorcode=450, background=BACKGROUND_DESIGN)

@app.route('/logout')
def logout():
    session.clear()
    flash('Sie wurden ausgeloggt', 'info')
    return redirect(url_for('login'))
   
@app.route("/API/GET/MOVIELIST")
def get_movie_lists():
    data = get_movie_list()
    return data

@app.route("/API/GET/GENRES")
def get_genres():
    with open(f"{GENRES_DIR}genres.json", "r") as file:
            genres = json.load(file)
            return jsonify(genres)

@app.route('/API/GET/TRAILER/<moviename>')
def get_trailer(moviename):
    return get_trailer_embed(moviename)


@app.route('/watch/<moviename>')
def watch(moviename):
    return render_template("watch.html", title=moviename, panel_name=PANEL_NAME, serverip=SERVER_IP, port=SERVER_PORT)




if __name__ == "__main__":
   app.run(debug=True, host="0.0.0.0", port=SERVER_PORT)
