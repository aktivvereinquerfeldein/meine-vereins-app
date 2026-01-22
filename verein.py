from flask import Flask, render_template_string, request, session, redirect, url_for
import psycopg2, os
from werkzeug.security import generate_password_hash, check_password_hash
from admin import admin_bp

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.register_blueprint(admin_bp, url_prefix='/admin')

DB_URL = os.environ.get('DATABASE_URL')
ADMIN_EMAIL = "quer.feld.ein@outlook.com"
ADMIN_PW_HASH = generate_password_hash("_Aktiv2025")

def get_db():
    return psycopg2.connect(DB_URL)

def init_db():
    conn = get_db(); cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS mitglieder 
                 (id SERIAL PRIMARY KEY, vorname TEXT, nachname TEXT, email TEXT UNIQUE, 
                  geburtstag TEXT, eintritt TEXT, passwort TEXT, rolle TEXT DEFAULT 'USER')''')
    try:
        cur.execute("SELECT mitglied_id, status FROM finanzen LIMIT 1")
    except:
        conn.rollback()
        cur.execute("DROP TABLE IF EXISTS finanzen")
        cur.execute('''CREATE TABLE finanzen 
                     (id SERIAL PRIMARY KEY, zweck TEXT, betrag DECIMAL, typ TEXT, 
                      datum DATE DEFAULT CURRENT_DATE, mitglied_id INTEGER, status TEXT DEFAULT 'Bezahlt')''')
    conn.commit(); cur.close(); conn.close()

# Einheitliches Layout für alle
def base_layout(content, title="quer.feld.ein"):
    nav = ""
    if session.get('logged_in'):
        if session.get('is_admin'):
            nav = '<a class="nav-link text-warning" href="/admin">Admin-Zentrale</a>'
        nav += '<a class="nav-link" href="/">Mein Profil</a><a class="nav-link text-danger" href="/logout">Logout</a>'
    
    return render_template_string(f"""
    <!DOCTYPE html><html><head><meta charset="UTF-8"><title>{title}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>body{{background:#f4f7f6}}.navbar{{background:#2c3e50 !important}}.nav-link{{color:white !important}}</style></head>
    <body><nav class="navbar navbar-expand navbar-dark mb-4 shadow-sm"><div class="container">
    <a class="navbar-brand" href="/"><b>quer.feld.ein</b></a>
    <div class="navbar-nav ms-auto">{nav}</div></div></nav>
    <div class="container">{content}</div></body></html>""")

@app.route('/')
def index():
    if not session.get('logged_in'): return redirect('/login')
    init_db()
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT vorname, nachname, email, geburtstag, eintritt FROM mitglieder WHERE email=%s", (session['user'],))
    u = cur.fetchone(); cur.close(); conn.close()
    
    if session.get('is_admin'):
        res = '<div class="card p-4 text-center shadow-sm"><h3>Admin-Zentrale</h3><p>Willkommen zurück! Nutze die gelbe Schaltfläche oben für die Verwaltung.</p><a href="/admin/mitglieder" class="btn btn-primary">Direkt zur Mitgliederliste</a></div>'
    elif u:
        res = f'''<div class="card p-4 shadow-sm"><h3>Hallo {u[0]}!</h3><hr>
        <p><b>Name:</b> {u[0]} {u[1]}</p><p><b>E-Mail:</b> {u[2]}</p>
        <p><b>Geburtstag:</b> {u[3]}</p><p><b>Eintritt:</b> {u[4]}</p></div>'''
    else: res = "Profil nicht gefunden."
    return base_layout(res)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        e, p = request.form.get('e'), request.form.get('p')
        if e == ADMIN_EMAIL and check_password_hash(ADMIN_PW_HASH, p):
            session.update({'logged_in':True, 'is_admin':True, 'user':e}); return redirect('/')
        conn = get_db(); cur = conn.cursor()
        cur.execute("SELECT passwort FROM mitglieder WHERE email=%s", (e,))
        r = cur.fetchone(); cur.close(); conn.close()
        if r and check_password_hash(r[0], p):
            session.update({'logged_in':True, 'is_admin':False, 'user':e}); return redirect('/')
    return base_layout('<div class="row justify-content-center"><div class="col-md-4"><form method="POST" class="card p-4 shadow-sm"><h4 class="text-center mb-3">Anmelden</h4><input name="e" type="email" class="form-control mb-2" placeholder="E-Mail" required><input type="password" name="p" class="form-control mb-3" placeholder="Passwort" required><button class="btn btn-primary w-100">Login</button></form></div></div>', "Login")

@app.route('/logout')
def logout(): session.clear(); return redirect('/login')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
