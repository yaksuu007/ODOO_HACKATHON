from flask import Flask, render_template,request,redirect
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)

cred=credentials.Certificate("firebase-credentials.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

@app.route("/")
def homepage():
    profiles_ref = db.collection("profiles")
    docs = profiles_ref.stream()
    profiles = [doc.to_dict() for doc in docs]
    return render_template("homepage.html",profiles=profiles)

@app.route("/create", methods=['GET','POST'])
def create_profile():
    if request.method == "POST":
        profile = {
        "name": request.form["name"],
        "email": request.form["email"],
        "phone": request.form["phone"],
        "gender": request.form["gender"],
        "location": request.form["location"],
        "availability": request.form["availability"],
        "profilePublic": "profilePublic" in request.form,
        "skillsOffered": request.form.getlist("skillsOffered[]"),
        "skillsWanted": request.form.getlist("skillsWanted[]"),
        "password": request.form["password"],
        "rating": request.form["rating"]

        }
        db.collection("profiles").add(profile)
        return redirect("/")
    return render_template("Create.html")

@app.route("/swap")
def swap_req():
    return render_template("swap.html")

@app.route("/connections")
def show_profiles():
    profiles_ref = db.collection("profiles")
    docs = profiles_ref.stream()
    profiles = [doc.to_dict() for doc in docs]
    return render_template("connections.html", profiles=profiles)

@app.route("/api/profiles")
def api_profiles():
    profiles_ref = db.collection("profiles")
    docs = profiles_ref.stream()
    profiles = []
    for doc in docs:
        data = doc.to_dict()
        profiles.append({
            "name": data.get("name", ""),
            "availability": data.get("availability", ""),
            "skills": data.get("skillsOffered", []),
            "rating": data.get("rating", "⭐️ N/A"),  # You can store this in Firestore too
            "photo": data.get("photo", "https://via.placeholder.com/60")  # Optional field
        })
    return profiles


@app.route("/profile")
def profile():
    return render_template("profile.html")

@app.route("/login")
def login():
    return render_template("loginn.html")

if __name__ == "__main__":
    app.run(debug=True)
