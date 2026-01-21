from flask import Flask, render_template_string, request, session, redirect, url_for
import psycopg2, os
from werkzeug.security import generate_password_hash, check_password_hash
from admin import admin_bp  # Hier binden wir deine admin.py ein!

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.register_blueprint(admin_bp, url_prefix='/admin') # Admin-Bereich unter /admin erreichbar

DB_URL = os.environ.get('DATABASE_URL')
ADMIN_EMAIL = "quer.feld.ein@outlook.com"
ADMIN_PW_HASH = generate_password_hash("_Aktiv2025")

def get_db():
    return psycopg2.connect(DB_URL)

@app.route('/')
def index():
    if not session.get('logged_in'): return redirect('/login')
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT vorname, nachname, email FROM mitglieder WHERE email=%s", (session['user'],))
    u = cur.fetchone(); cur.close(); conn.close()
    
    # Menü oben (für Admin erscheint zusätzlich der Admin-Link)
    admin_link = '<a class="nav-link text-warning" href="/admin">Admin-Bereich</a>' if session.get('is_admin') else ''
    
    html = f"""
    <!DOCTYPE html><html><head><meta charset="UTF-8"><title>Mitgliederbereich</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"></head>
    <body class="bg-light"><nav class="navbar navbar-dark bg-dark mb-4"><div class="container">
    <span class="navbar-brand">quer.feld.ein</span>
    <div class="navbar-nav d-flex flex-row">{admin_link}<a class="nav-link px-3" href="/logout">Logout</a></div>
    </div></nav><div class="container">
    <div class="card p-4 shadow-sm"><h3>Hallo {u[0] if u else "Admin"}!</h3>
    <p>Willkommen im Mitglieder-Bereich.</p>
    {"<p>Deine Daten: " + u[2] + "</p>" if u else ""}
    </div></div></body></html>"""
    return render_template_string(html)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        e, p = request.form.get('e'), request.form.get('p')
        # Check Admin
        if e == ADMIN_EMAIL and check_password_hash(ADMIN_PW_HASH, p):
            session.update({'logged_in':True, 'is_admin':True, 'user':e}); return redirect('/admin')
        # Check Mitglied
        conn = get_db(); cur = conn.cursor()
        cur.execute("SELECT passwort FROM mitglieder WHERE email=%s", (e,))
        r = cur.fetchone(); cur.close(); conn.close()
        if r and check_password_hash(r[0], p):
            session.update({'logged_in':True, 'is_admin':False, 'user':e}); return redirect('/')
    return render_template_string('<body class="bg-light"><div class="container mt-5"><div class="card p-4 mx-auto shadow-sm" style="max-width:400px"><h4>Login</h4><form method="POST"><input name="e" class="form-control mb-2" placeholder="E-Mail"><input name="p" type="password" class="form-control mb-3" placeholder="Passwort"><button class="btn btn-primary w-100">Login</button></form></div></div></body>')

@app.route('/logout')
def logout(): session.clear(); return redirect('/login')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
