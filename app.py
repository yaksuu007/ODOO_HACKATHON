from flask import Flask, render_template

app = Flask(__name__)

# Route for login page (home)
@app.route('/')
def login():
    return render_template('login.html')

# Route for profile edit page
@app.route('/profile')
def profile():
    return render_template('profile.html')

# Route for connections page
@app.route('/connections')
def connections():
    return '<h1>Connections Page</h1>'

# Optional login redirect route
@app.route('/login')
def login_redirect():
    return render_template('login.html')

# Run Flask server
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=9000, debug=True)
