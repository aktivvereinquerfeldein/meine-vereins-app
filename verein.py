from flask import Flask, render_template_string, request, session, redirect, url_for
import psycopg2
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

DB_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    return psycopg2.connect(DB_URL)

def init_db():
    conn = get_db_connection(); cur = conn.cursor()
    # Mitglieder
    cur.execute('CREATE TABLE IF NOT EXISTS mitglieder (id SERIAL PRIMARY KEY, vorname TEXT, nachname TEXT, status TEXT)')
    # Finanzen
    cur.execute('CREATE TABLE IF NOT EXISTS finanzen (id SERIAL PRIMARY KEY, zweck TEXT, betrag DECIMAL, typ TEXT, datum DATE DEFAULT CURRENT_DATE)')
    # Einstellungen (Neu!)
    cur.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)')
    # Standardwerte setzen, falls leer
    cur.execute("INSERT INTO settings (key, value) VALUES ('v_name', 'quer.feld.ein') ON CONFLICT DO NOTHING")
    cur.execute("INSERT INTO settings (key, value) VALUES ('v_pw', 'mein-sicheres-passwort') ON CONFLICT DO NOTHING")
    cur.execute("INSERT INTO settings (key, value) VALUES ('fee_aktiv', '50') ON CONFLICT DO NOTHING")
    cur.execute("INSERT INTO settings (key, value) VALUES ('fee_passiv', '25') ON CONFLICT DO NOTHING")
    conn.commit(); cur.close(); conn.close()

def get_setting(key):
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("SELECT value FROM settings WHERE key=%s", (key,))
    val = cur.fetchone()[0]
    cur.close(); conn.close()
    return val

# --- LAYOUT ---
BASE_LAYOUT = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ v_name }} | Verwaltung</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        :root { --p: #2c3e50; --a: #27ae60; }
        body { background: #f4f7f6; font-family: sans-serif; }
        .navbar { background: var(--p) !important; }
        .card { border: none; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
        .nav-link.active { font-weight: bold; border-bottom: 2px solid var(--a); }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark mb-4 shadow-sm">
        <div class="container">
            <a class="navbar-brand" href="/">{{ v_name }}</a>
            <div class="navbar-nav ms-auto">
                {% if session.get('logged_in') %}
                <a class="nav-link {{'active' if p=='h'}}" href="/">Start</a>
                <a class="nav-link {{'active' if p=='m'}}" href="/mitglieder">Mitglieder</a>
                <a class="nav-link {{'active' if p=='f'}}" href="/finanzen">Finanzen</a>
                <a class="nav-link {{'active' if p=='s'}}" href="/settings">⚙️</a>
                <a class="nav-link ms-3 text-danger" href="/logout">X</a>
                {% endif %}
            </div>
        </div>
    </nav>
    <div class="container">{{ content | safe }}</div>
</body>
</html>
"""

@app.route('/')
def index():
    if not session.get('logged_in'): return redirect(url_for('login'))
    init_db()
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM mitglieder"); mc = cur.fetchone()[0]
    cur.execute("SELECT SUM(CASE WHEN typ='Einnahme' THEN betrag ELSE -betrag END) FROM finanzen"); s = cur.fetchone()[0] or 0
    cur.close(); conn.close()
    html = f'<div class="row text-center"><div class="col-md-6 mb-3"><div class="card p-5"><h3>Mitglieder</h3><h1>{mc}</h1></div></div><div class="col-md-6"><div class="card p-5"><h3>Saldo</h3><h1 class="text-success">{s} €</h1></div></div></div>'
    return render_template_string(BASE_LAYOUT, v_name=get_setting('v_name'), p='h', content=html)

@app.route('/mitglieder')
def mitglieder():
    if not session.get('logged_in'): return redirect(url_for('login'))
    search = request.args.get('q', '')
    conn = get_db_connection(); cur = conn.cursor()
    if search:
        cur.execute("SELECT * FROM mitglieder WHERE vorname ILIKE %s OR nachname ILIKE %s", (f'%{search}%', f'%{search}%'))
    else:
        cur.execute("SELECT * FROM mitglieder ORDER BY nachname ASC")
    ml = cur.fetchall(); cur.close(); conn.close()
    html = f'''
    <div class="card p-4 mb-3">
        <form class="d-flex mb-3"><input name="q" class="form-control me-2" placeholder="Suchen..." value="{search}"><button class="btn btn-primary">Suche</button></form>
        <form action="/add_m" method="POST" class="row g-2">
            <div class="col-md-4"><input name="v" class="form-control" placeholder="Vorname" required></div>
            <div class="col-md-4"><input name="n" class="form-control" placeholder="Nachname" required></div>
            <div class="col-md-3"><select name="s" class="form-select"><option>Aktiv</option><option>Passiv</option></select></div>
            <div class="col-md-1"><button class="btn btn-success w-100">+</button></div>
        </form>
    </div>
    <div class="card p-0"><table class="table mb-0">{% for m in ml %}<tr><td>{ ml[1] } { ml[2] }</td><td>{ ml[3] }</td><td class="text-end"><a href="/del_m/{ ml[0] }" class="btn btn-sm btn-danger">Löschen</a></td></tr>{% endfor %}</table></div>
    '''
    return render_template_string(BASE_LAYOUT, v_name=get_setting('v_name'), p='m', content=render_template_string(html, ml=ml))

@app.route('/finanzen')
def finanzen():
    if not session.get('logged_in'): return redirect(url_for('login'))
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("SELECT * FROM finanzen ORDER BY datum DESC"); fl = cur.fetchall(); cur.close(); conn.close()
    html = f'''
    <div class="card p-4 mb-3">
        <div class="d-flex justify-content-between mb-3"><h3>Buchungen</h3><a href="/bill_all" class="btn btn-warning btn-sm">Jahresbeiträge einziehen</a></div>
        <form action="/add_f" method="POST" class="row g-2">
            <div class="col-md-5"><input name="z" class="form-control" placeholder="Zweck" required></div>
            <div class="col-md-3"><input type="number" step="0.01" name="b" class="form-control" placeholder="€" required></div>
            <div class="col-md-3"><select name="t" class="form-select"><option>Einnahme</option><option>Ausgabe</option></select></div>
            <div class="col-md-1"><button class="btn btn-success w-100">OK</button></div>
        </form>
    </div>
    <div class="card p-0"><table class="table mb-0">{% for f in fl %}<tr class="{{'text-success' if f[3]=='Einnahme' else 'text-danger'}}"><td>{ f[4] }</td><td>{ f[1] }</td><td>{ f[2] } €</td></tr>{% endfor %}</table></div>
    '''
    return render_template_string(BASE_LAYOUT, v_name=get_setting('v_name'), p='f', content=render_template_string(html, fl=fl))

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if not session.get('logged_in'): return redirect(url_for('login'))
    if request.method == 'POST':
        conn = get_db_connection(); cur = conn.cursor()
        for k in ['v_name', 'v_pw', 'fee_aktiv', 'fee_passiv']:
            cur.execute("UPDATE settings SET value=%s WHERE key=%s", (request.form[k], k))
        conn.commit(); cur.close(); conn.close()
        return redirect(url_for('settings'))
    
    html = f'''
    <div class="card p-4"><h3>⚙️ Einstellungen</h3><form method="POST">
        <label>Vereinsname</label><input name="v_name" class="form-control mb-3" value="{get_setting('v_name')}">
        <label>Admin-Passwort</label><input name="v_pw" class="form-control mb-3" value="{get_setting('v_pw')}">
        <label>Beitrag Aktiv (€)</label><input name="fee_aktiv" class="form-control mb-3" value="{get_setting('fee_aktiv')}">
        <label>Beitrag Passiv (€)</label><input name="fee_passiv" class="form-control mb-3" value="{get_setting('fee_passiv')}">
        <button class="btn btn-primary w-100">Speichern</button></form></div>
    '''
    return render_template_string(BASE_LAYOUT, v_name=get_setting('v_name'), p='s', content=html)

@app.route('/bill_all')
def bill_all():
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("SELECT status FROM mitglieder")
    ms = cur.fetchall()
    f_a = get_setting('fee_aktiv'); f_p = get_setting('fee_passiv')
    for m in ms:
        betrag = f_a if m[0] == 'Aktiv' else f_p
        cur.execute("INSERT INTO finanzen (zweck, betrag, typ) VALUES (%s, %s, %s)", (f"Mitgliedsbeitrag ({m[0]})", betrag, 'Einnahme'))
    conn.commit(); cur.close(); conn.close()
    return redirect(url_for('finanzen'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['password'] == get_setting('v_pw'):
            session['logged_in'] = True
            return redirect(url_for('index'))
    return render_template_string(BASE_LAYOUT, v_name="Login", content='<div class="row justify-content-center mt-5"><div class="col-md-4 card p-4"><form method="POST"><input type="password" name="password" class="form-control mb-3" placeholder="Passwort"><button class="btn btn-primary w-100">Login</button></form></div></div>')

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('login'))

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

@app.route('/add_f', methods=['POST'])
def add_f():
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("INSERT INTO finanzen (zweck, betrag, typ) VALUES (%s, %s, %s)", (request.form['z'], request.form['b'], request.form['t']))
    conn.commit(); cur.close(); conn.close()
    return redirect(url_for('finanzen'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
