from flask import Blueprint, render_template_string, request, session, redirect, url_for
import psycopg2, os

# Blueprint erstellen
admin_bp = Blueprint('admin', __name__)
DB_URL = os.environ.get('DATABASE_URL')

def get_db():
    return psycopg2.connect(DB_URL)

# --- ADMIN LAYOUT ---
def admin_layout(content):
    return render_template_string(f"""
    <!DOCTYPE html><html><head><meta charset="UTF-8"><title>Admin | quer.feld.ein</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>body{{background:#f0f2f5}}.navbar{{background:#1c2938 !important}}.nav-link{{color:white !important}}</style></head>
    <body><nav class="navbar navbar-expand navbar-dark mb-4"><div class="container">
    <a class="navbar-brand" href="/admin"><b>ADMIN-ZENTRALE</b></a>
    <div class="navbar-nav ms-auto">
        <a class="nav-link px-2" href="/admin">Dashboard</a>
        <a class="nav-link px-2" href="/admin/mitglieder">Mitglieder</a>
        <a class="nav-link px-2 text-warning" href="/">Zur Mitglieder-Ansicht</a>
    </div></div></nav><div class="container">{content}</div></body></html>""")

@admin_bp.route('/')
def dashboard():
    if not session.get('is_admin'): return redirect('/login')
    return admin_layout("<h3>Willkommen, Admin!</h3><p>Hier hast du die volle Kontrolle über den Verein.</p>")

@admin_bp.route('/mitglieder')
def mitglieder():
    if not session.get('is_admin'): return redirect('/login')
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT id, vorname, nachname, email FROM mitglieder ORDER BY nachname")
    ml = cur.fetchall(); cur.close(); conn.close()
    rows = "".join([f"<tr><td>{m[1]} {m[2]}</td><td>{m[3]}</td><td class='text-end'><a href='/admin/del_m/{m[0]}' class='btn btn-sm btn-danger'>Löschen</a></td></tr>" for m in ml])
    return admin_layout(f'''<div class="card p-4 mb-3 shadow-sm"><h4>Neues Mitglied anlegen</h4>
    <form action="/admin/add_m" method="POST" class="row g-2">
    <div class="col-6"><input name="v" class="form-control" placeholder="Vorname" required></div>
    <div class="col-6"><input name="n" class="form-control" placeholder="Nachname" required></div>
    <div class="col-12"><input name="e" class="form-control" placeholder="E-Mail" required></div>
    <button class="btn btn-success mt-3">Speichern</button></form></div>
    <table class="table card shadow-sm">{rows}</table>''')

@admin_bp.route('/add_m', methods=['POST'])
def add_m():
    if not session.get('is_admin'): return redirect('/login')
    from werkzeug.security import generate_password_hash
    h = generate_password_hash("querfeldein2025")
    conn = get_db(); cur = conn.cursor()
    cur.execute("INSERT INTO mitglieder (vorname, nachname, email, passwort) VALUES (%s,%s,%s,%s)", 
                (request.form['v'], request.form['n'], request.form['e'], h))
    conn.commit(); cur.close(); conn.close(); return redirect('/admin/mitglieder')

@admin_bp.route('/del_m/<int:id>')
def del_m(id):
    if not session.get('is_admin'): return redirect('/login')
    conn = get_db(); cur = conn.cursor()
    cur.execute("DELETE FROM mitglieder WHERE id=%s", (id,)); conn.commit(); cur.close(); conn.close(); return redirect('/admin/mitglieder')
