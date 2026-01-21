from flask import Flask, render_template_string, request, session, redirect, url_for
import psycopg2, os
from werkzeug.security import generate_password_hash, check_password_hash
from admin import admin_bp  # Importiert deine admin.py

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.register_blueprint(admin_bp, url_prefix='/admin')

DB_URL = os.environ.get('DATABASE_URL')
ADMIN_EMAIL = "quer.feld.ein@outlook.com"
ADMIN_PW_HASH = generate_password_hash("_Aktiv2025")

def get_db():
    return psycopg2.connect(DB_URL)

# --- LOGIN SEITE (Wieder mit zwei Feldern) ---
LOGIN_HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Login | quer.feld.ein</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<style>body{background:#f4f7f6}.card{border:none; border-radius:15px; shadow: 0 4px 15px rgba(0,0,0,0.1)}</style></head>
<body><div class="container"><div class="row justify-content-center mt-5"><div class="col-md-4">
<div class="card p-4 mt-5 shadow-sm">
    <h3 class="text-center mb-4">quer.feld.ein</h3>
    <form method="POST">
        <div class="mb-3">
            <label class="form-label">E-Mail Adresse</label>
            <input name="e" type="email" class="form-control" placeholder="name@beispiel.de" required autofocus>
        </div>
        <div class="mb-3">
            <label class="form-label">Passwort</label>
            <input name="p" type="password" class="form-control" placeholder=" Dein Passwort" required>
        </div>
        <button class="btn btn-primary w-100 py-2">Anmelden</button>
    </form>
    <p class="text-muted small text-center mt-3">Anmeldung für Admin & Mitglieder</p>
</div></div></div></div></body></html>
"""

@app.route('/')
def index():
    if not session.get('logged_in'): return redirect('/login')
    # Falls Admin, zeige Info oder leite weiter
    if session.get('is_admin'):
        return render_template_string("""
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <div class="container mt-5 text-center">
                <h2>Admin-Modus aktiv</h2>
                <a href="/admin" class="btn btn-warning mt-3">Zur Admin-Zentrale</a>
                <a href="/logout" class="btn btn-outline-danger mt-3">Logout</a>
            </div>
        """)
    
    # Normales Mitglied
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT vorname, nachname, email FROM mitglieder WHERE email=%s", (session['user'],))
    u = cur.fetchone(); cur.close(); conn.close()
    
    return render_template_string(f"""
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <div class="container mt-5">
            <div class="card p-4 shadow-sm">
                <h3>Hallo {u[0]} {u[1]}!</h3>
                <p>Willkommen in deinem persönlichen Mitgliederbereich.</p>
                <hr><a href="/logout" class="btn btn-danger btn-sm">Abmelden</a>
            </div>
        </div>
    """)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        e, p = request.form.get('e'), request.form.get('p')
        # 1. Admin prüfen
        if e == ADMIN_EMAIL and check_password_hash(ADMIN_PW_HASH, p):
            session.update({'logged_in':True, 'is_admin':True, 'user':e})
            return redirect('/admin')
        
        # 2. Mitglied prüfen
        conn = get_db(); cur = conn.cursor()
        cur.execute("SELECT passwort FROM mitglieder WHERE email=%s", (e,))
        r = cur.fetchone(); cur.close(); conn.close()
        if r and check_password_hash(r[0], p):
            session.update({'logged_in':True, 'is_admin':False, 'user':e})
            return redirect('/')
            
    return render_template_string(LOGIN_HTML)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
