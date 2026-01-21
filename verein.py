from flask import Flask, render_template_string, request, session, redirect, url_for
import psycopg2 # Für PostgreSQL statt sqlite3
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Render stellt die Datenbank-URL automatisch als Umgebungsvariable bereit
# Falls du lokal testest, kannst du deine URL hier einfügen
DB_URL = os.environ.get('DATABASE_URL')
ADMIN_PASSWORD = "mein-sicheres-passwort" 

def get_db_connection():
    # Stellt die Verbindung zur externen PostgreSQL Datenbank her
    conn = psycopg2.connect(DB_URL)
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS mitglieder 
                 (id SERIAL PRIMARY KEY, 
                  vorname TEXT NOT NULL, 
                  nachname TEXT NOT NULL, 
                  status TEXT)''')
    conn.commit()
    cur.close()
    conn.close()

# --- HTML DESIGNS (Gleich geblieben) ---
BASE_LAYOUT = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vereins-Manager PRO</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <nav class="navbar navbar-dark bg-dark mb-4">
        <div class="container">
            <span class="navbar-brand">⚽ Vereinsverwaltung (Sicher)</span>
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
        <form method="POST">
            <input type="password" name="password" class="form-control mb-3" placeholder="Passwort" required>
            <button type="submit" class="btn btn-primary w-100">Einloggen</button>
        </form>
    </div>
</div>
"""

DASHBOARD_PAGE = """
<div class="card p-4 mb-4 shadow-sm">
    <h4>Neues Mitglied dauerhaft anlegen</h4>
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
            <tr><td>{{ m[1] }} {{ m[2] }}</td><td>{{ m[3] }}</td><td><a href="/delete/{{ m[0] }}" class="btn btn-sm btn-danger">Löschen</a></td></tr>
            {% endfor %}
        </tbody>
    </table>
</div>
"""

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
    init_db()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM mitglieder ORDER BY id DESC")
    mitglieder = cur.fetchall()
    cur.close()
    conn.close()
    return render_template_string(BASE_LAYOUT, content=render_template_string(DASHBOARD_PAGE, mitglieder=mitglieder))

@app.route('/add', methods=['POST'])
def add_member():
    if not session.get('logged_in'): return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO mitglieder (vorname, nachname, status) VALUES (%s, %s, %s)",
                 (request.form['vorname'], request.form['nachname'], request.form['status']))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete_member(id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM mitglieder WHERE id=%s", (id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
