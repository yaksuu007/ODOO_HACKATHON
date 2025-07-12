from flask import Flask, redirect, url_for, session, render_template
from flask_dance.contrib.google import make_google_blueprint, google
import os
import json

app = Flask(__name__)
app.secret_key = "super_secret_key"  # Replace with a secure secret in production


os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

# ✅ Load client credentials from JSON
if not os.path.exists("client_secret.json"):
    raise FileNotFoundError("❌ 'client_secret.json' not found in project directory.")

with open("client_secret.json", "r") as f:
    client_data = json.load(f)["web"]

# ✅ Google OAuth Blueprint
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
app.register_blueprint(google_bp, url_prefix="/login")

#  Home Route
@app.route("/")
def home():
    return render_template("home.html")

@app.route('/profile_view/<name>')
def profile_view(name):
    return render_template("profile.html", name=name)

# Profile Route
@app.route("/profile")
def profile():
    if not google.authorized:
        return redirect(url_for("google.login"))

    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        return f" Failed to fetch user info: {resp.text}"

    user_info = resp.json()
    return render_template("profile.html", user=user_info)

#  Run Flask ONLY on 127.0.0.1 and port 7000
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=7000, debug=True)
