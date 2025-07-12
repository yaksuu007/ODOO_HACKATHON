from flask import Flask, redirect, url_for, session, render_template
from flask_dance.contrib.google import make_google_blueprint, google
import os
import json

app = Flask(__name__)
app.secret_key = "super_secret_key"  # use secure key in production

# Allow insecure transport for local dev (don't use in production)
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

# === Load Google credentials from client_secret.json ===
with open("client_secret.json", "r") as f:
    client_data = json.load(f)["web"]

google_bp = make_google_blueprint(
    client_id=client_data["client_id"],
    client_secret=client_data["client_secret"],
    scope=["profile", "email"],
    redirect_url="/profile"
)
app.register_blueprint(google_bp, url_prefix="/login")

# === Routes ===
@app.route("/")
def home():
    return render_template("login.html")


@app.route("/profile")
def profile():
    if not google.authorized:
        return redirect(url_for("google.login"))

    resp = google.get("/oauth2/v2/userinfo")
    assert resp.ok, resp.text
    user_info = resp.json()

    return render_template("profile.html", user=user_info)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


# === Run app ===
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=9000, debug=True)
