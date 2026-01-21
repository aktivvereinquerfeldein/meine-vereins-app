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
    # Mitglieder Tabelle erweitert
    cur.execute('''CREATE TABLE IF NOT EXISTS mitglieder 
                 (id SERIAL PRIMARY KEY, vorname TEXT, nachname TEXT, email TEXT UNIQUE, 
                  geburtstag DATE, eintritt DATE, passwort TEXT, rolle TEXT DEFAULT 'USER')''')
    cur.execute('CREATE TABLE IF NOT EXISTS finanzen (id SERIAL PRIMARY KEY, zweck TEXT, betrag DECIMAL, typ TEXT, datum DATE DEFAULT CURRENT_DATE)')
    conn.commit(); cur.close(); conn.close()

# --- LAYOUT MIT ROLLEN-LOGIK ---
LAYOUT = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><title>quer.feld.ein</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<style>body{background:#f4f7f6}.navbar{background:#2c3e50 !important}.nav-link{color:white !important}</style></head>
<body><nav class="navbar navbar-expand navbar-dark mb-4 shadow-sm"><div class="container">
<a class="navbar-brand" href="/"><b>quer.feld.ein</b></a>
<div class="navbar-nav ms-auto">
{% if session.logged_in %}
    <a class="nav-link px-2" href="/">Profil</a>
    {% if session.is_admin %}
        <a class="nav-link px-2" href="/mitglieder">Mitglieder</a>
        <a class="nav-link px-2" href="/finanzen">Finanzen</a>
    {% endif %}
    <a class="nav-link px-2 text-danger" href="/logout">Logout</a>
{% endif %}
</div></div></nav><div class="container">{{ c|safe }}</div></body></html>
"""

@app.route('/')
def index():
    if not session.get('logged_in'): return redirect('/login')
    init_db()
    conn = get_db(); cur = conn.cursor()
    # Eigene Daten anzeigen
    cur.execute("SELECT vorname, nachname, email, geburtstag, eintritt FROM mitglieder WHERE email=%s", (session['user'],))
    u = cur.fetchone()
    cur.close(); conn.close()
    
    if session.get('is_admin'):
        content = f'<div class="alert alert-info">Eingeloggt als Administrator</div>'
    else:
        content = f'''<div class="card p-4"><h3>Mein Profil</h3>
        <p><b>Name:</b> {u[0]} {u[1]}</p><p><b>Email:</b> {u[2]}</p>
        <hr><form action="/change_pw" method="POST" class="mt-3">
        <h5>Passwort ändern</h5><input name="new_pw" type="password" class="form-control mb-2" placeholder="Neues Passwort">
        <button class="btn btn-sm btn-primary">Speichern</button></form></div>'''
    return render_template_string(LAYOUT, c=content)

@app.route('/mitglieder')
def mitglieder():
    if not session.get('is_admin'): return "Zugriff verweigert", 403
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT id, vorname, nachname, email, geburtstag, eintritt FROM mitglieder ORDER BY nachname ASC")
    ml = cur.fetchall(); cur.close(); conn.close()
    
    rows = "".join([f"<tr><td>{m[1]} {m[2]}</td><td>{m[3]}</td><td>{m[4]}</td><td>{m[5]}</td><td><a href='/del_m/{m[0]}' class='btn btn-danger btn-sm'>X</a></td></tr>" for m in ml])
    content = f'''<div class="card p-4 mb-3"><h4>Neues Mitglied</h4>
    <form action="/add_m" method="POST" class="row g-2">
    <div class="col-md-3"><input name="v" class="form-control" placeholder="Vorname" required></div>
    <div class="col-md-3"><input name="n" class="form-control" placeholder="Nachname" required></div>
    <div class="col-md-3"><input name="e" type="email" class="form-control" placeholder="Email" required></div>
    <div class="col-md-3"><input name="g" type="date" class="form-control" title="Geburtstag"></div>
    <div class="col-md-3"><input name="ein" type="date" class="form-control" title="Eintrittsdatum"></div>
    <div class="col-md-2"><button class="btn btn-success w-100">Anlegen</button></div>
    </form><p class="small text-muted mt-2">Standard-Passwort: querfeldein2025</p></div>
    <table class="table card">{rows}</table>'''
    return render_template_string(LAYOUT, c=content)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('e'); pw = request.form.get('p')
        if email == ADMIN_EMAIL and check_password_hash(ADMIN_PW_HASH, pw):
            session.update({'logged_in':True, 'is_admin':True, 'user':email}); return redirect('/')
        
        conn = get_db(); cur = conn.cursor()
        cur.execute("SELECT passwort, rolle FROM mitglieder WHERE email=%s", (email,))
        res = cur.fetchone(); cur.close(); conn.close()
        if res and check_password_hash(res[0], pw):
            session.update({'logged_in':True, 'is_admin':False, 'user':email}); return redirect('/')
            
    return render_template_string(LAYOUT, v="Login", c='<form method="POST" class="card p-4 mx-auto" style="max-width:400px"><h4 class="text-center mb-3">Login</h4><input name="e" class="form-control mb-2" placeholder="E-Mail"><input type="password" name="p" class="form-control mb-3" placeholder="Passwort"><button class="btn btn-primary w-100">Anmelden</button></form>')

@app.route('/add_m', methods=['POST'])
def add_m():
    if not session.get('is_admin'): return redirect('/')
    pw_hash = generate_password_hash("querfeldein2025")
    c = get_db(); cur = c.cursor()
    cur.execute("INSERT INTO mitglieder (vorname, nachname, email, geburtstag, eintritt, passwort) VALUES (%s,%s,%s,%s,%s,%s)", 
                (request.form['v'], request.form['n'], request.form['e'], request.form.get('g'), request.form.get('ein'), pw_hash))
    c.commit(); return redirect('/mitglieder')

@app.route('/change_pw', methods=['POST'])
def change_pw():
    if not session.get('logged_in'): return redirect('/login')
    new_hash = generate_password_hash(request.form.get('new_pw'))
    c = get_db(); cur = c.cursor()
    cur.execute("UPDATE mitglieder SET passwort=%s WHERE email=%s", (new_hash, session['user']))
    c.commit(); return redirect('/')

@app.route('/finanzen')
def finanzen():
    if not session.get('is_admin'): return redirect('/')
    # ... (Finanz-Code bleibt wie gehabt)
    return render_template_string(LAYOUT, c="<h3>Finanzmodul</h3><p>Hier werden Buchungen verwaltet.</p>")

@app.route('/logout')
def logout(): session.clear(); return redirect('/login')

@app.route('/del_m/<int:id>')
def del_m(id):
    if not session.get('is_admin'): return redirect('/')
    c = get_db(); cur = c.cursor(); cur.execute("DELETE FROM mitglieder WHERE id=%s", (id,)); c.commit(); return redirect('/mitglieder')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
