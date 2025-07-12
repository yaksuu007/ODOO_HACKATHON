from flask import Flask, redirect, url_for, session, render_template
from flask_dance.contrib.google import make_google_blueprint, google
import os

app = Flask(__name__)
app.secret_key = "super_secret_key" 

# client_secret.json
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  
google_bp = make_google_blueprint(
    client_secrets_file="client_secret.json",
    scope=["profile", "email"],
    redirect_to="profile"
)
app.register_blueprint(google_bp, url_prefix="/login")


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


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=9000, debug=True)
