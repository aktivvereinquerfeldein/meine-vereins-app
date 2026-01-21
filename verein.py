from flask import Flask, render_template_string, request, session, redirect, url_for
import psycopg2
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

DB_URL = os.environ.get('DATABASE_URL')
ADMIN_PASSWORD = "mein-sicheres-passwort" 

def get_db_connection():
    return psycopg2.connect(DB_URL)

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    # Tabelle Mitglieder
    cur.execute('''CREATE TABLE IF NOT EXISTS mitglieder 
                 (id SERIAL PRIMARY KEY, vorname TEXT, nachname TEXT, status TEXT)''')
    # Tabelle Finanzen
    cur.execute('''CREATE TABLE IF NOT EXISTS finanzen 
                 (id SERIAL PRIMARY KEY, zweck TEXT, betrag DECIMAL, typ TEXT, datum DATE DEFAULT CURRENT_DATE)''')
    conn.commit()
    cur.close()
    conn.close()

# --- CSS & LAYOUT ---
BASE_LAYOUT = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>quer.feld.ein | Verwaltung</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        :root { --primary-color: #2c3e50; --accent-color: #27ae60; }
        body { background-color: #f4f7f6; font-family: 'Segoe UI', sans-serif; }
        .navbar { background-color: var(--primary-color) !important; }
        .nav-link { color: rgba(255,255,255,0.8) !important; }
        .nav-link.active { color: white !important; font-weight: bold; border-bottom: 2px solid var(--accent-color); }
        .card { border: none; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
        .btn-primary { background-color: var(--accent-color); border: none; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark shadow-sm mb-4">
        <div class="container">
            <a class="navbar-brand" href="/">quer<b>.feld.ein</b></a>
            <div class="navbar-nav ms-auto">
                {% if session.get('logged_in') %}
                    <a class="nav-link {{ 'active' if active_page == 'home' }}" href="/">Start</a>
                    <a class="nav-link {{ 'active' if active_page == 'mitglieder' }}" href="/mitglieder">Mitglieder</a>
                    <a class="nav-link {{ 'active' if active_page == 'finanzen' }}" href="/finanzen">Finanzen</a>
                    <a class="nav-link ms-lg-4" href="/logout">Abmelden</a>
                {% endif %}
            </div>
        </div>
    </nav>
    <div class="container">{{ content | safe }}</div>
</body>
</html>
"""

# --- SEITEN-INHALTE ---

DASHBOARD_HTML = """
<div class="row">
    <div class="col-md-12 mb-4"><h1>Willkommen bei quer.feld.ein</h1><p class="text-muted">Heute ist ein guter Tag zur Verwaltung.</p></div>
    <div class="col-md-6">
        <div class="card p-4 bg-white text-center">
            <h3>Mitglieder</h3>
            <h1 class="display-4">{{ m_count }}</h1>
            <a href="/mitglieder" class="btn btn-outline-primary">Verwalten</a>
        </div>
    </div>
    <div class="col-md-6">
        <div class="card p-4 bg-white text-center">
            <h3>Kontostand</h3>
            <h1 class="display-4 text-success">{{ saldo }} €</h1>
            <a href="/finanzen" class="btn btn-outline-success">Details</a>
        </div>
    </div>
</div>
"""

# (Die anderen HTML-Teile für Mitglieder und Finanzen sind im Python-Code unten integriert)

@app.route('/')
def index():
    if not session.get('logged_in'): return redirect(url_for('login'))
    init_db()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM mitglieder")
    m_count = cur.fetchone()[0]
    cur.execute("SELECT SUM(CASE WHEN typ='Einnahme' THEN betrag ELSE -betrag END) FROM finanzen")
    saldo = cur.fetchone()[0] or 0
    cur.close()
    conn.close()
    return render_template_string(BASE_LAYOUT, active_page='home', content=render_template_string(DASHBOARD_HTML, m_count=m_count, saldo=saldo))

@app.route('/mitglieder')
def mitglieder():
    if not session.get('logged_in'): return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM mitglieder ORDER BY nachname ASC")
    m_liste = cur.fetchall()
    cur.close()
    conn.close()
    
    html = """
    <div class="card p-4 mb-4">
        <h3>Neues Mitglied</h3>
        <form action="/add_m" method="POST" class="row g-2">
            <div class="col-md-4"><input name="v" class="form-control" placeholder="Vorname" required></div>
            <div class="col-md-4"><input name="n" class="form-control" placeholder="Nachname" required></div>
            <div class="col-md-3"><select name="s" class="form-select"><option>Aktiv</option><option>Passiv</option></select></div>
            <div class="col-md-1"><button class="btn btn-primary w-100">+</button></div>
        </form>
    </div>
    <div class="card p-0 overflow-hidden">
        <table class="table mb-0 table-hover">
            <thead class="table-light"><tr><th>Name</th><th>Status</th><th>Aktion</th></tr></thead>
            <tbody>
                {% for m in m_liste %}
                <tr><td>{{ m[1] }} {{ m[2] }}</td><td>{{ m[3] }}</td><td><a href="/del_m/{{ m[0] }}" class="text-danger">Löschen</a></td></tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    """
    return render_template_string(BASE_LAYOUT, active_page='mitglieder', content=render_template_string(html, m_liste=m_liste))

@app.route('/finanzen', methods=['GET', 'POST'])
def finanzen():
    if not session.get('logged_in'): return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor()
    
    if request.method == 'POST':
        cur.execute("INSERT INTO finanzen (zweck, betrag, typ) VALUES (%s, %s, %s)",
                    (request.form['z'], request.form['b'], request.form['t']))
        conn.commit()
        
    cur.execute("SELECT * FROM finanzen ORDER BY datum DESC")
    f_liste = cur.fetchall()
    cur.close()
    conn.close()
    
    html = """
    <div class="card p-4 mb-4">
        <h3>Buchung erfassen</h3>
        <form method="POST" class="row g-2">
            <div class="col-md-5"><input name="z" class="form-control" placeholder="Zweck" required></div>
            <div class="col-md-3"><input type="number" step="0.01" name="b" class="form-control" placeholder="Betrag €" required></div>
            <div class="col-md-3"><select name="t" class="form-select"><option>Einnahme</option><option>Ausgabe</option></select></div>
            <div class="col-md-1"><button class="btn btn-success w-100">OK</button></div>
        </form>
    </div>
    <div class="card p-0">
        <table class="table mb-0">
            <thead class="table-light"><tr><th>Datum</th><th>Zweck</th><th>Betrag</th></tr></thead>
            <tbody>
                {% for f in f_liste %}
                <tr class="{{ 'text-success' if f[3]=='Einnahme' else 'text-danger' }}">
                    <td>{{ f[4] }}</td><td>{{ f[1] }}</td><td>{{ '+' if f[3]=='Einnahme' else '-' }}{{ f[2] }} €</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    """
    return render_template_string(BASE_LAYOUT, active_page='finanzen', content=render_template_string(html, f_liste=f_liste))

# --- HILFSFUNKTIONEN ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['password'] == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
    return render_template_string(BASE_LAYOUT, content='<div class="row justify-content-center mt-5"><div class="col-md-4 card p-4"><form method="POST"><input type="password" name="password" class="form-control mb-3" placeholder="Passwort"><button class="btn btn-primary w-100">Login</button></form></div></div>')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/add_m', methods=['POST'])
def add_m():
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("INSERT INTO mitglieder (vorname, nachname, status) VALUES (%s, %s, %s)", (request.form['v'], request.form['n'], request.form['s']))
    conn.commit(); cur.close(); conn.close()
    return redirect(url_for('mitglieder'))

@app.route('/del_m/<int:id>')
def del_m(id):
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("DELETE FROM mitglieder WHERE id=%s", (id,))
    conn.commit(); cur.close(); conn.close()
    return redirect(url_for('mitglieder'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
