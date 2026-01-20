from flask import Flask, render_template_string, request, session, redirect, url_for
import sqlite3
import os

app = Flask(__name__)
# Ein geheimer Schlüssel für die Sicherheit der Sitzungen (Sessions)
app.secret_key = os.urandom(24) 

DB_NAME = "vereinsdaten.db"
ADMIN_PASSWORD = "mein-sicheres-passwort" # <-- ÄNDERE DAS HIER!

# --- DATENBANK FUNKTION ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS mitglieder 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  vorname TEXT, nachname TEXT, email TEXT, status TEXT)''')
    conn.commit()
    conn.close()

# --- HTML DESIGN ---
HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vereinsverwaltung</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <nav class="navbar navbar-dark bg-dark mb-4">
        <div class="container">
            <span class="navbar-brand">Mein Verein Online</span>
            {% if session.get('logged_in') %}
            <a href="/logout" class="btn btn-outline-light btn-sm">Abmelden</a>
            {% endif %}
        </div>
    </nav>
    <div class="container">
        {% block content %}{% endblock %}
    </div>
</body>
</html>
"""

LOGIN_HTML = """
{% extends "layout" %}
{% block content %}
<div class="row justify-content-center">
    <div class="col-md-4 mt-5">
        <div class="card shadow">
            <div class="card-body">
                <h3 class="card-title text-center">Login</h3>
                <form method="POST">
                    <div class="mb-3"><input type="password" name="password" class="form-control" placeholder="Passwort" required></div>
                    <button type="submit" class="btn btn-primary w-100">Einloggen</button>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
"""

INDEX_HTML = """
{% extends "layout" %}
{% block content %}
<div class="card shadow-sm mb-4">
    <div class="card-body">
        <h4>Neues Mitglied hinzufügen</h4>
        <form action="/add" method="POST" class="row g-3">
            <div class="col-md-3"><input type="text" name="vorname" class="form-control" placeholder="Vorname" required></div>
            <div class="col-md-3"><input type="text" name="nachname" class="form-control" placeholder="Nachname" required></div>
            <div class="col-md-3"><input type="email" name="email" class="form-control" placeholder="E-Mail"></div>
            <div class="col-md-2">
                <select name="status" class="form-select">
                    <option value="Aktiv">Aktiv</option>
                    <option value="Passiv">Passiv</option>
                </select>
            </div>
            <div class="col-md-1"><button type="submit" class="btn btn-success w-100">+</button></div>
        </form>
    </div>
</div>

<div class="card shadow-sm">
    <div class="card-body">
        <table class="table table-hover">
            <thead><tr><th>Name</th><th>E-Mail</th><th>Status</th><th>Aktion</th></tr></thead>
            <tbody>
                {% for m in mitglieder %}
                <tr>
                    <td>{{ m[1] }} {{ m[2] }}</td>
                    <td>{{ m[3] }}</td>
                    <td><span class="badge bg-info text-dark">{{ m[4] }}</span></td>
                    <td><a href="/delete/{{ m[0] }}" class="btn btn-sm btn-danger">Löschen</a></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endblock %}
"""

# --- ROUTEN / LOGIK ---

@app.route('/layout') # Nur interner Helfer
def layout(): return render_template_string(HTML_LAYOUT)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['password'] == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
    return render_template_string(HTML_LAYOUT.replace('{% block content %}{% endblock %}', LOGIN_HTML))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
def index():
    if not session.get('logged_in'): return redirect(url_for('login'))
    conn = sqlite3.connect(DB_NAME)
    mitglieder = conn.execute("SELECT * FROM mitglieder").fetchall()
    conn.close()
    return render_template_string(HTML_LAYOUT.replace('{% block content %}{% endblock %}', INDEX_HTML), mitglieder=mitglieder)

@app.route('/add', methods=['POST'])
def add_member():
    if not session.get('logged_in'): return redirect(url_for('login'))
    conn = sqlite3.connect(DB_NAME)
    conn.execute("INSERT INTO mitglieder (vorname, nachname, email, status) VALUES (?, ?, ?, ?)",
                 (request.form['vorname'], request.form['nachname'], request.form['email'], request.form['status']))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete_member(id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    conn = sqlite3.connect(DB_NAME)
    conn.execute("DELETE FROM mitglieder WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)