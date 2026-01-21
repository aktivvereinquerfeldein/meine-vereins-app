from flask import Flask, render_template_string, request, session, redirect, url_for
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "ein-ganz-beliebiger-langer-text-fuer-die-sicherheit"

# WICHTIG: Auf Render nutzen wir den /tmp/ Ordner für die Datenbank
DB_NAME = "/tmp/vereinsdaten.db"
ADMIN_PASSWORD = "mein-sicheres-passwort" # <-- Prüfe dieses Passwort!

def init_db():
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.execute('''CREATE TABLE IF NOT EXISTS mitglieder 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      vorname TEXT, nachname TEXT, email TEXT, status TEXT)''')
        conn.commit()
        conn.close()
        print("Datenbank erfolgreich initialisiert.")
    except Exception as e:
        print(f"Fehler bei Datenbank-Initialisierung: {e}")

# --- HTML DESIGNS ---
BASE_LAYOUT = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vereins-Manager</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <nav class="navbar navbar-dark bg-primary mb-4">
        <div class="container">
            <span class="navbar-brand">⚽ Vereinsverwaltung</span>
            {% if session.get('logged_in') %}<a href="/logout" class="btn btn-outline-light btn-sm">Abmelden</a>{% endif %}
        </div>
    </nav>
    <div class="container">{{ content | safe }}</div>
</body>
</html>
"""

LOGIN_PAGE = """
<div class="row justify-content-center mt-5">
    <div class="col-md-4 card p-4 shadow-sm">
        <h3 class="text-center mb-4">Login</h3>
        {% if error %}<div class="alert alert-danger">{{ error }}</div>{% endif %}
        <form method="POST">
            <input type="password" name="password" class="form-control mb-3" placeholder="Passwort" required>
            <button type="submit" class="btn btn-primary w-100">Einloggen</button>
        </form>
    </div>
</div>
"""

DASHBOARD_PAGE = """
<div class="card p-4 mb-4 shadow-sm">
    <h4>Neues Mitglied</h4>
    <form action="/add" method="POST" class="row g-2">
        <div class="col-md-4"><input type="text" name="vorname" class="form-control" placeholder="Vorname" required></div>
        <div class="col-md-4"><input type="text" name="nachname" class="form-control" placeholder="Nachname" required></div>
        <div class="col-md-3"><select name="status" class="form-select"><option>Aktiv</option><option>Passiv</option></select></div>
        <div class="col-md-1"><button type="submit" class="btn btn-success w-100">+</button></div>
    </form>
</div>
<div class="table-responsive card shadow-sm">
    <table class="table mb-0">
        <thead class="table-light"><tr><th>Name</th><th>Status</th><th>Aktion</th></tr></thead>
        <tbody>
            {% for m in mitglieder %}
            <tr><td>{{ m[1] }} {{ m[2] }}</td><td>{{ m[4] }}</td><td><a href="/delete/{{ m[0] }}" class="btn btn-sm btn-danger">Löschen</a></td></tr>
            {% endfor %}
        </tbody>
    </table>
</div>
"""

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['password'] == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            error = "Falsches Passwort!"
    return render_template_string(BASE_LAYOUT, content=render_template_string(LOGIN_PAGE, error=error))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
def index():
    if not session.get('logged_in'): return redirect(url_for('login'))
    init_db() # Sicherstellen, dass DB existiert
    conn = sqlite3.connect(DB_NAME)
    mitglieder = conn.execute("SELECT * FROM mitglieder").fetchall()
    conn.close()
    return render_template_string(BASE_LAYOUT, content=render_template_string(DASHBOARD_PAGE, mitglieder=mitglieder))

@app.route('/add', methods=['POST'])
def add_member():
    if not session.get('logged_in'): return redirect(url_for('login'))
    conn = sqlite3.connect(DB_NAME)
    conn.execute("INSERT INTO mitglieder (vorname, nachname, status) VALUES (?, ?, ?)",
                 (request.form['vorname'], request.form['nachname'], request.form['status']))
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
