from flask import Flask, session, redirect, url_for, request, render_template_string
import os
from admin import admin_bp  # Hier binden wir deine neue Datei ein!

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Hier registrieren wir das Admin-Modul
app.register_blueprint(admin_bp, url_prefix='/admin')

@app.route('/')
def home():
    if not session.get('logged_in'): return redirect('/login')
    if session.get('is_admin'):
        return redirect('/admin/dashboard')
    return "Willkommen Mitglied (User-Bereich folgt)"

@app.route('/login', methods=['GET', 'POST'])
def login():
    # ... (Login-Logik wie gehabt)
    if request.method == 'POST':
        # Test-Login
        if request.form.get('e') == "quer.feld.ein@outlook.com":
            session.update({'logged_in':True, 'is_admin':True, 'user':"Admin"})
            return redirect('/admin/dashboard')
    return render_template_string('<form method="POST"><input name="e"><button>Login</button></form>')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
