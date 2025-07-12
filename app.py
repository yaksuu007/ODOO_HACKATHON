from flask import Flask, redirect, url_for, session, render_template, request, jsonify
from flask_dance.contrib.google import make_google_blueprint, google
import os
import json
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "super_secret_key"  # Replace with a secure secret in production

# Database setup
def init_db():
    conn = sqlite3.connect('skill_swap.db')
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            google_id TEXT UNIQUE,
            email TEXT UNIQUE,
            name TEXT,
            photo_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create profiles table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            skills_offered TEXT,
            skills_wanted TEXT,
            bio TEXT,
            rating REAL DEFAULT 0.0,
            total_ratings INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create swap_requests table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS swap_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_user_id INTEGER,
            to_user_id INTEGER,
            offered_skill TEXT,
            wanted_skill TEXT,
            message TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (from_user_id) REFERENCES users (id),
            FOREIGN KEY (to_user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

#  Load client credentials from JSON
if not os.path.exists("client_secret.json"):
    raise FileNotFoundError(" 'client_secret.json' not found in project directory.")

with open("client_secret.json", "r") as f:
    client_data = json.load(f)["web"]

#  Google OAuth Blueprint
google_bp = make_google_blueprint(
    client_id=client_data["client_id"],
    client_secret=client_data["client_secret"],
    redirect_url="/profile",
    scope=[
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email",
        "openid"
    ]
)
app.register_blueprint(google_bp, url_prefix="/login", name="glog")

# Database helper functions
def get_db_connection():
    conn = sqlite3.connect('skill_swap.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_or_create_user(user_info):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute('SELECT * FROM users WHERE google_id = ?', (user_info['id'],))
    user = cursor.fetchone()
    
    if user:
        conn.close()
        return dict(user)
    
    # Create new user
    cursor.execute('''
        INSERT INTO users (google_id, email, name, photo_url)
        VALUES (?, ?, ?, ?)
    ''', (user_info['id'], user_info['email'], user_info['name'], user_info.get('picture', '')))
    
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {'id': user_id, 'google_id': user_info['id'], 'email': user_info['email'], 
            'name': user_info['name'], 'photo_url': user_info.get('picture', '')}

def get_user_profile(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT p.*, u.name, u.email, u.photo_url
        FROM profiles p
        JOIN users u ON p.user_id = u.id
        WHERE p.user_id = ?
    ''', (user_id,))
    
    profile = cursor.fetchone()
    conn.close()
    
    if profile:
        return dict(profile)
    return None

def save_user_profile(user_id, skills_offered, skills_wanted, bio):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if profile exists
    cursor.execute('SELECT id FROM profiles WHERE user_id = ?', (user_id,))
    existing = cursor.fetchone()
    
    if existing:
        # Update existing profile
        cursor.execute('''
            UPDATE profiles 
            SET skills_offered = ?, skills_wanted = ?, bio = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (skills_offered, skills_wanted, bio, user_id))
    else:
        # Create new profile
        cursor.execute('''
            INSERT INTO profiles (user_id, skills_offered, skills_wanted, bio)
            VALUES (?, ?, ?, ?)
        ''', (user_id, skills_offered, skills_wanted, bio))
    
    conn.commit()
    conn.close()

def get_all_profiles():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT p.*, u.name, u.email, u.photo_url
        FROM profiles p
        JOIN users u ON p.user_id = u.id
        ORDER BY p.updated_at DESC
    ''')
    
    profiles = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return profiles

# ✅ Home Route
@app.route("/")
def home():
    return render_template("home.html")

@app.route('/profile_view/<name>')
def profile_view(name):
    return render_template("profile.html", name=name)

#  Profile Route
@app.route("/profile")
def profile():
    if not google.authorized:
        return redirect(url_for("glog.login"))

    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        return f" Failed to fetch user info: {resp.text}"

    user_info = resp.json()
    user = get_or_create_user(user_info)
    profile_data = get_user_profile(user['id'])
    
    return render_template("profile.html", user=user, profile=profile_data)

#  Request Route
@app.route("/request")
def request_page():
    return render_template("request.html")

#  Create Account Route
@app.route("/create_account")
def create_account():
    return render_template("create_acoount.html")

#  Login Route
@app.route("/login")
def login():
    return render_template("login.html")

# API Routes for profile management
@app.route("/api/profile", methods=['GET'])
def api_get_profile():
    if not google.authorized:
        return jsonify({'error': 'Not authenticated'}), 401
    
    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        return jsonify({'error': 'Failed to fetch user info'}), 400
    
    user_info = resp.json()
    user = get_or_create_user(user_info)
    profile_data = get_user_profile(user['id'])
    
    return jsonify({
        'user': user,
        'profile': profile_data
    })

@app.route("/api/profile", methods=['POST'])
def api_save_profile():
    if not google.authorized:
        return jsonify({'error': 'Not authenticated'}), 401
    
    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        return jsonify({'error': 'Failed to fetch user info'}), 400
    
    user_info = resp.json()
    user = get_or_create_user(user_info)
    
    data = request.get_json()
    skills_offered = data.get('skills_offered', '')
    skills_wanted = data.get('skills_wanted', '')
    bio = data.get('bio', '')
    
    save_user_profile(user['id'], skills_offered, skills_wanted, bio)
    
    return jsonify({'message': 'Profile saved successfully'})

@app.route("/api/profiles", methods=['GET'])
def api_get_all_profiles():
    profiles = get_all_profiles()
    return jsonify(profiles)

@app.route("/api/swap_request", methods=['POST'])
def api_create_swap_request():
    if not google.authorized:
        return jsonify({'error': 'Not authenticated'}), 401
    
    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        return jsonify({'error': 'Failed to fetch user info'}), 400
    
    user_info = resp.json()
    from_user = get_or_create_user(user_info)
    
    data = request.get_json()
    to_user_id = data.get('to_user_id')
    offered_skill = data.get('offered_skill')
    wanted_skill = data.get('wanted_skill')
    message = data.get('message', '')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO swap_requests (from_user_id, to_user_id, offered_skill, wanted_skill, message)
        VALUES (?, ?, ?, ?, ?)
    ''', (from_user['id'], to_user_id, offered_skill, wanted_skill, message))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Swap request sent successfully'})

#  Run Flask ONLY on 127.0.0.1 and port 7000
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=7000, debug=True)
