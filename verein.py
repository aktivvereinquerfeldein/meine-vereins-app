from flask import Flask, render_template_string, request, session, redirect, url_for
import psycopg2, os

app = Flask(__name__)
app.secret_key = os.urandom(24)
DB_URL = os.environ.get('DATABASE_URL')

def get_db():
    return psycopg2.connect(DB_URL)

def init_db():
    conn = get_db(); cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS mitglieder (id SERIAL PRIMARY KEY, vorname TEXT, nachname TEXT, status TEXT)')
    cur.execute('CREATE TABLE IF NOT EXISTS finanzen (id SERIAL PRIMARY KEY, zweck TEXT, betrag DECIMAL, typ TEXT, datum DATE DEFAULT CURRENT_DATE)')
    cur.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)')
    cur.execute("INSERT INTO settings (key, value) VALUES ('v_name', 'quer.feld.ein') ON CONFLICT DO NOTHING")
    cur.execute("INSERT INTO settings (key, value) VALUES ('v_pw', 'mein-sicheres-passwort') ON CONFLICT DO NOTHING")
    cur.execute("INSERT INTO settings (key, value) VALUES ('f_a', '50'), ('f_p', '25') ON CONFLICT DO NOTHING")
    conn.commit(); cur.close(); conn.close()

def get_s(k):
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("SELECT value FROM settings WHERE key=%s", (k,))
        r = cur.fetchone(); cur.close(); conn.close()
        return r[0] if r else ""
    except: return ""

LAYOUT = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><title>{{v}}</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<style>body{background:#f4f7f6}.nav-link{color:white !important}</style></head>
<body><nav class="navbar navbar-dark bg-dark mb-4"><div class="container"><a class="navbar-brand" href="/">{{v}}</a>
<div class="navbar-nav d-flex flex-row">
{% if session.logged_in %}<a class="nav-link px-2" href="/mitglieder">Mitglieder</a><a class="nav-link px-2" href="/finanzen">Finanzen</a>
<a class="nav-link px-2" href="/settings">⚙️</a><a class="nav-link px-2 text-danger" href="/logout">X</a>{% endif %}
</div></div></nav><div class="container">{{ c|safe }}</div></body></html>
"""

@app.route('/')
def index():
    if not session.get('logged_in'): return redirect('/login')
    init_db()
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM mitglieder"); mc = cur.fetchone()[0]
    cur.execute("SELECT SUM(CASE WHEN typ='Einnahme' THEN betrag ELSE -betrag END) FROM finanzen"); s = cur.fetchone()[0] or 0
    cur.close(); conn.close()
    content = f'<div class="row text-center"><div class="col-6 card p-4"><h3>Mitglieder</h3><h1>{mc}</h1></div><div class="col-6 card p-4"><h3>Saldo</h3><h1 class="text-success">{s} €</h1></div></div>'
    return render_template_string(LAYOUT, v=get_s('v_name'), c=content)

@app.route('/mitglieder')
def mitglieder():
    if not session.get('logged_in'): return redirect('/login')
    q = request.args.get('q', '')
    conn = get_db(); cur = conn.cursor()
    if q: cur.execute("SELECT * FROM mitglieder WHERE vorname ILIKE %s OR nachname ILIKE %s", (f'%{q}%', f'%{q}%'))
    else: cur.execute("SELECT * FROM mitglieder ORDER BY nachname ASC")
    ml = cur.fetchall(); cur.close(); conn.close()
    rows = "".join([f"<tr><td>{m[1]} {m[2]}</td><td>{m[3]}</td><td><a href='/del_m/{m[0]}' class='btn btn-danger btn-sm'>Löschen</a></td></tr>" for m in ml])
    content = f'<div class="card p-3 mb-3"><form class="d-flex mb-3"><input name="q" class="form-control me-2" placeholder="Suche..." value="{q}"><button class="btn btn-primary">Los</button></form><form action="/add_m" method="POST" class="row g-2"><div class="col-5"><input name="v" class="form-control" placeholder="Vorname"></div><div class="col-5"><input name="n" class="form-control" placeholder="Nachname"></div><div class="col-2"><button class="btn btn-success w-100">+</button></div></form></div><table class="table card">{rows}</table>'
    return render_template_string(LAYOUT, v=get_s('v_name'), c=content)

@app.route('/finanzen')
def finanzen():
    if not session.get('logged_in'): return redirect('/login')
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM finanzen ORDER BY datum DESC"); fl = cur.fetchall(); cur.close(); conn.close()
    rows = "".join([f"<tr class='{'text-success' if f[3]=='Einnahme' else 'text-danger'}'><td>{f[4]}</td><td>{f[1]}</td><td>{f[2]} €</td></tr>" for f in fl])
    content = f'<div class="card p-3 mb-3"><div class="d-flex justify-content-between mb-3"><h3>Finanzen</h3><a href="/bill_all" class="btn btn-warning btn-sm">Beiträge einziehen</a></div><form action="/add_f" method="POST" class="row g-2"><div class="col-6"><input name="z" class="form-control" placeholder="Zweck"></div><div class="col-4"><input name="b" type="number" step="0.01" class="form-control" placeholder="€"></div><div class="col-2"><button class="btn btn-success w-100">OK</button></div></form></div><table class="table card">{rows}</table>'
    return render_template_string(LAYOUT, v=get_s('v_name'), c=content)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if not session.get('logged_in'): return redirect('/login')
    if request.method == 'POST':
        conn = get_db(); cur = conn.cursor()
        for k in ['v_name', 'v_pw', 'f_a', 'f_p']: cur.execute("UPDATE settings SET value=%s WHERE key=%s", (request.form[k], k))
        conn.commit(); cur.close(); conn.close(); return redirect('/settings')
    html = f'<div class="card p-4"><h3>⚙️ Settings</h3><form method="POST"><label>Verein</label><input name="v_name" class="form-control mb-2" value="{get_s("v_name")}"><label>PW</label><input name="v_pw" class="form-control mb-2" value="{get_s("v_pw")}"><button class="btn btn-primary w-100">Speichern</button></form></div>'
    return render_template_string(LAYOUT, v=get_s('v_name'), c=html)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('p') == get_s('v_pw'):
        session['logged_in'] = True; return redirect('/')
    return render_template_string(LAYOUT, v="Login", c='<form method="POST" class="card p-4 mx-auto" style="max-width:300px"><input type="password" name="p" class="form-control mb-3" placeholder="Passwort"><button class="btn btn-primary w-100">Login</button></form>')

@app.route('/logout')
def logout(): session.clear(); return redirect('/login')

@app.route('/add_m', methods=['POST'])
def add_m():
    c = get_db(); cur = c.cursor(); cur.execute("INSERT INTO mitglieder (vorname, nachname, status) VALUES (%s,%s,%s)", (request.form['v'], request.form['n'], 'Aktiv')); c.commit(); return redirect('/mitglieder')

@app.route('/del_m/<int:id>')
def del_m(id):
    c = get_db(); cur = c.cursor(); cur.execute("DELETE FROM mitglieder WHERE id=%s", (id,)); c.commit(); return redirect('/mitglieder')

@app.route('/add_f', methods=['POST'])
def add_f():
    c = get_db(); cur = c.cursor(); cur.execute("INSERT INTO finanzen (zweck, betrag, typ) VALUES (%s,%s,%s)", (request.form['z'], request.form['b'], 'Einnahme')); c.commit(); return redirect('/finanzen')

@app.route('/bill_all')
def bill_all():
    c = get_db(); cur = c.cursor(); cur.execute("SELECT status FROM mitglieder"); ms = cur.fetchall(); fa = get_s('f_a'); fp = get_s('f_p')
    for m in ms: cur.execute("INSERT INTO finanzen (zweck, betrag, typ) VALUES (%s,%s,%s)", (f"Beitrag {m[0]}", fa if m[0]=='Aktiv' else fp, 'Einnahme'))
    c.commit(); return redirect('/finanzen')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
