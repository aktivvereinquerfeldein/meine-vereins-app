from flask import Flask, render_template_string, request, session, redirect, url_for
import sqlite3
import os

app = Flask(__name__)
# Erzeugt einen zufälligen Schlüssel für die Session-Sicherheit
app.secret_key = os.urandom(24) 

DB_NAME = "vereinsdaten.db"
# ÄNDERE DIESES PASSWORT FÜR DEINEN LOGIN:
ADMIN_PASSWORD = "1234" 

# --- DATENBANK-LOGIK ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute('''CREATE TABLE IF NOT EXISTS mitglieder 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  vorname TEXT, nachname TEXT, email TEXT, status TEXT)''')
    conn.commit()
    conn.close()

# --- HTML DESIGNS (Als Strings direkt im Code) ---

# Das Grundgerüst (Navbar, Styles)
BASE_LAYOUT = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vereins-Manager</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #f8f9fa; }
        .navbar { margin-bottom: 30px; }
        .card { border: none; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    </style>
</head>
<body>
    <nav class="navbar navbar-dark bg-primary shadow-sm">
        <div class="container">
            <span class="navbar-brand mb-0 h1">⚽ Vereinsverwaltung</span>
            {% if session.get('logged_in') %}
            <a href="/logout" class="btn btn-outline-light btn-sm">Abmelden</a>
            {% endif %}
        </div>
    </nav>
    <div class="container">
        {{ content | safe }}
    </div>
</body>
</html>
"""

# Die Login-Seite
LOGIN_PAGE = """
<div class="row justify-content-center mt-5">
    <div class="col-md-4">
        <div class="card p-4">
            <h3 class="text-center mb-4">Login</h3>
            <form method="POST">
                <div class="mb-3">
                    <label class="form-label">Passwort</label>
                    <input type="password" name="password" class="form-control" required autofocus>
                </div>
                <button type="submit" class="btn btn-primary w-100">Einloggen</button>
            </form>
        </div>
    </div>
</div>
"""

# Die Hauptseite (Dashboard)
DASHBOARD_PAGE = """
<div class="card p-4 mb-4">
    <h4 class="mb-3">Neues Mitglied anlegen</h4>
    <form action="/add" method="POST" class="row g-3">
        <div class="col-md-3"><input type="text" name="vorname" class="form-control" placeholder="Vorname" required></div>
        <div class="col-md-3"><input type="text" name="nachname" class="form-control" placeholder="Nachname" required></div>
        <div class="col-md-3"><input type="email" name="email" class="form-control" placeholder="E-Mail"></div>
        <div class="col-md-2">
            <select name="status" class="form-select">
                <option value="Aktiv">Aktiv</option>
                <option value="Passiv">Passiv</option>
                <option value="Ehrenmitglied">Ehrenmitglied</option>
            </select>
        </div>
        <div class="col-md-1"><button type="submit" class="btn btn-success w-100">+</button></div>
    </form>
</div>

<div class="card p-0">
    <div class="table-responsive">
        <table class="table table-hover mb-0">
            <thead class="table-light">
                <tr><th>Name</th><th>E-Mail</th><th>Status</th><th class="text-end">Aktion</th></tr>
            </thead>
            <tbody>
                {% for m in mitglieder %}
                <tr>
                    <td class="align-middle"><strong>{{ m[1] }} {{ m[2] }}</strong></td>
                    <td class="align-middle">{{ m[3] }}</td>
                    <td class="align-middle"><span class="badge bg-info text-dark">{{ m[4] }}</span></td>
                    <td class="text-end"><a href="/delete/{{ m[0] }}" class="btn btn-sm btn-outline-danger">Löschen</a></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
"""

# --- FUNKTIONEN & ROUTEN ---

def get_db():
    conn = sqlite3.connect(DB_NAME)
    return conn

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['password'] == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
    return render_template_string(BASE_LAYOUT, content=LOGIN_PAGE)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
def index():
    if not session.get('logged_in'): return redirect(url_for('login'))
    conn = get_db()
    mitglieder = conn.execute("SELECT * FROM mitglieder").fetchall()
    conn.close()
    return render_template_string(BASE_LAYOUT, content=DASHBOARD_PAGE, mitglieder=mitglieder)

@app.route('/add', methods=['POST'])
def add_member():
    if not session.get('logged_in'): return redirect(url_for('login'))
    conn = get_db()
    conn.execute("INSERT INTO mitglieder (vorname, nachname, email, status) VALUES (?, ?, ?, ?)",
                 (request.form['vorname'], request.form['nachname'], request.form['email'], request.form['status']))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete_member(id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    conn = get_db()
    conn.execute("DELETE FROM mitglieder WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
