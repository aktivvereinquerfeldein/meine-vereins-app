from flask import Flask, render_template_string, request, session, redirect, url_for
import psycopg2, os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.urandom(24)
DB_URL = os.environ.get('DATABASE_URL')

ADMIN_EMAIL = "quer.feld.ein@outlook.com"
ADMIN_PW_HASH = generate_password_hash("_Aktiv2025")

def get_db():
    return psycopg2.connect(DB_URL)

def init_db():
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT email FROM mitglieder LIMIT 1")
    except:
        conn.rollback()
        cur.execute('DROP TABLE IF EXISTS mitglieder')
    cur.execute('''CREATE TABLE IF NOT EXISTS mitglieder 
                 (id SERIAL PRIMARY KEY, vorname TEXT, nachname TEXT, email TEXT UNIQUE, 
                  geburtstag TEXT, eintritt TEXT, passwort TEXT, rolle TEXT DEFAULT 'USER')''')
    cur.execute('CREATE TABLE IF NOT EXISTS finanzen (id SERIAL PRIMARY KEY, zweck TEXT, betrag DECIMAL, typ TEXT, datum DATE DEFAULT CURRENT_DATE)')
    conn.commit(); cur.close(); conn.close()

LAYOUT = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><title>quer.feld.ein</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<style>body{background:#f4f7f6}.navbar{background:#2c3e50 !important}.nav-link{color:white !important}</style></head>
<body><nav class="navbar navbar-expand navbar-dark mb-4 shadow-sm"><div class="container">
<a class="navbar-brand" href="/"><b>quer.feld.ein</b></a>
<div class="navbar-nav ms-auto">
{% if session.logged_in %}
    <a class="nav-link px-2" href="/">Start</a>
    {% if session.is_admin %}<a class="nav-link px-2" href="/mitglieder">Mitglieder</a>{% endif %}
    <a class="nav-link px-2 text-danger" href="/logout">Logout</a>
{% endif %}
</div></div></nav><div class="container">{{ c|safe }}</div></body></html>
"""

@app.route('/')
def index():
    if not session.get('logged_in'): return redirect('/login')
    init_db()
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT vorname, nachname, email, geburtstag, eintritt FROM mitglieder WHERE email=%s", (session['user'],))
    u = cur.fetchone(); cur.close(); conn.close()
    
    if session.get('is_admin'):
        res = f'<div class="card p-4"><h3>Admin-Zentrale</h3><p>Willkommen, {session["user"]}</p><div class="list-group"><a href="/mitglieder" class="list-group-item list-group-item-action">Mitglieder verwalten</a></div></div>'
    elif u:
        res = f'''<div class="card p-4"><h3>Mein Profil</h3><p><b>Name:</b> {u[0]} {u[1]}</p><p><b>Email:</b> {u[2]}</p>
        <p><b>Geburtstag:</b> {u[3]}</p><p><b>Eintritt:</b> {u[4]}</p><hr>
        <form action="/pw_self" method="POST" style="max-width:300px"><h5>Passwort ändern</h5>
        <input name="n" type="password" class="form-control mb-2" placeholder="Neues Passwort" required>
        <button class="btn btn-primary btn-sm">Speichern</button></form></div>'''
    else: res = "Profil nicht gefunden."
    return render_template_string(LAYOUT, c=res)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        e = request.form.get('e'); p = request.form.get('p')
        if e == ADMIN_EMAIL and check_password_hash(ADMIN_PW_HASH, p):
            session.update({'logged_in':True, 'is_admin':True, 'user':e}); return redirect('/')
        conn = get_db(); cur = conn.cursor()
        cur.execute("SELECT passwort FROM mitglieder WHERE email=%s", (e,))
        r = cur.fetchone(); cur.close(); conn.close()
        if r and check_password_hash(r[0], p):
            session.update({'logged_in':True, 'is_admin':False, 'user':e}); return redirect('/')
    return render_template_string(LAYOUT, c='<div class="row justify-content-center mt-5"><div class="col-md-4"><form method="POST" class="card p-4 shadow-sm"><h4 class="text-center mb-3">Login</h4><input name="e" class="form-control mb-2" placeholder="E-Mail" required><input type="password" name="p" class="form-control mb-3" placeholder="Passwort" required><button class="btn btn-primary w-100">Anmelden</button></form></div></div>')

@app.route('/mitglieder')
def mitglieder():
    if not session.get('is_admin'): return redirect('/')
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT id, vorname, nachname, email FROM mitglieder ORDER BY nachname")
    ml = cur.fetchall(); cur.close(); conn.close()
    rows = "".join([f"<tr><td>{m[1]} {m[2]}</td><td>{m[3]}</td><td class='text-end'><a href='/del_m/{m[0]}' class='btn btn-sm btn-outline-danger'>Löschen</a></td></tr>" for m in ml])
    content = f'''<div class="card p-4 mb-3 shadow-sm"><h4>Neues Mitglied anlegen</h4>
    <form action="/add_m" method="POST" class="row g-2">
    <div class="col-md-6"><label class="small">Vorname</label><input name="v" class="form-control" required></div>
    <div class="col-md-6"><label class="small">Nachname</label><input name="n" class="form-control" required></div>
    <div class="col-md-12"><label class="small">E-Mail (Login)</label><input name="e" type="email" class="form-control" required></div>
    <div class="col-md-6"><label class="small">Geburtstag</label><input name="g" type="date" class="form-control"></div>
    <div class="col-md-6"><label class="small">Eintritt am</label><input name="ein" type="date" class="form-control"></div>
    <div class="col-12 mt-3"><button class="btn btn-success w-100">Mitglied speichern</button></div></form></div>
    <div class="card shadow-sm"><table class="table mb-0">{rows}</table></div>'''
    return render_template_string(LAYOUT, c=content)

@app.route('/add_m', methods=['POST'])
def add_m():
    if not session.get('is_admin'): return redirect('/')
    h = generate_password_hash("querfeldein2025")
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("INSERT INTO mitglieder (vorname, nachname, email, geburtstag, eintritt, passwort) VALUES (%s,%s,%s,%s,%s,%s)", 
                    (request.form['v'], request.form['n'], request.form['e'], request.form.get('g', ''), request.form.get('ein', ''), h))
        conn.commit(); cur.close(); conn.close()
    except Exception as e: return f"Fehler beim Speichern: {str(e)}"
    return redirect('/mitglieder')

@app.route('/pw_self', methods=['POST'])
def pw_self():
    if not session.get('logged_in'): return redirect('/login')
    h = generate_password_hash(request.form.get('n'))
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE mitglieder SET passwort=%s WHERE email=%s", (h, session['user']))
    conn.commit(); cur.close(); conn.close(); return redirect('/')

@app.route('/del_m/<int:id>')
def del_m(id):
    if not session.get('is_admin'): return redirect('/')
    conn = get_db(); cur = conn.cursor()
    cur.execute("DELETE FROM mitglieder WHERE id=%s", (id,)); conn.commit(); cur.close(); conn.close(); return redirect('/mitglieder')

@app.route('/logout')
def logout(): session.clear(); return redirect('/login')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
