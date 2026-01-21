from flask import Blueprint, render_template_string, request, session, redirect, url_for
import psycopg2, os

admin_bp = Blueprint('admin', __name__)
DB_URL = os.environ.get('DATABASE_URL')

def get_db():
    return psycopg2.connect(DB_URL)

def admin_layout(content):
    return render_template_string(f"""
    <!DOCTYPE html><html><head><meta charset="UTF-8"><title>Admin | quer.feld.ein</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>body{{background:#f0f2f5}}.navbar{{background:#1c2938 !important}}.nav-link{{color:white !important}}</style></head>
    <body><nav class="navbar navbar-expand navbar-dark mb-4 shadow-sm"><div class="container">
    <a class="navbar-brand" href="/admin"><b>ADMIN-ZENTRALE</b></a>
    <div class="navbar-nav ms-auto">
        <a class="nav-link px-2" href="/admin">Dashboard</a>
        <a class="nav-link px-2" href="/admin/mitglieder">Mitglieder</a>
        <a class="nav-link px-2" href="/admin/finanzen">Finanzen</a>
        <a class="nav-link px-2 text-danger" href="/logout">Logout</a>
    </div></div></nav><div class="container">{content}</div></body></html>""")

@admin_bp.route('/')
def dashboard():
    if not session.get('is_admin'): return redirect('/login')
    # Kurze Statistik für das Dashboard
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM mitglieder"); mc = cur.fetchone()[0]
    cur.execute("SELECT SUM(CASE WHEN typ='Einnahme' THEN betrag ELSE -betrag END) FROM finanzen"); saldo = cur.fetchone()[0] or 0
    cur.close(); conn.close()
    
    content = f'''<h3>Dashboard</h3>
    <div class="row mt-4">
        <div class="col-md-6 mb-3"><div class="card p-4 shadow-sm"><h5>Mitglieder</h5><h1>{mc}</h1></div></div>
        <div class="col-md-6 mb-3"><div class="card p-4 shadow-sm"><h5>Kassenstand</h5><h1 class="text-success">{saldo} €</h1></div></div>
    </div>
    <div class="mt-4"><a href="/admin/finanzen" class="btn btn-primary">Zu den Finanzen</a></div>'''
    return admin_layout(content)

@admin_bp.route('/finanzen')
def finanzen():
    if not session.get('is_admin'): return redirect('/login')
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM finanzen ORDER BY datum DESC")
    fl = cur.fetchall(); cur.close(); conn.close()
    
    rows = "".join([f"<tr class='{'text-success' if f[3]=='Einnahme' else 'text-danger'}'><td>{f[4]}</td><td>{f[1]}</td><td>{f[2]} €</td><td>{f[3]}</td></tr>" for f in fl])
    
    content = f'''<div class="card p-4 mb-3 shadow-sm">
    <div class="d-flex justify-content-between mb-3">
        <h4>Finanzverwaltung</h4>
        <a href="/admin/einzug" class="btn btn-warning btn-sm" onclick="return confirm('Für alle Mitglieder 50€ einziehen?')">Jahresbeitrag einziehen</a>
    </div>
    <form action="/admin/add_f" method="POST" class="row g-2">
        <div class="col-md-5"><input name="z" class="form-control" placeholder="Zweck (z.B. Miete)" required></div>
        <div class="col-md-3"><input name="b" type="number" step="0.01" class="form-control" placeholder="Betrag" required></div>
        <div class="col-md-3"><select name="t" class="form-control"><option>Einnahme</option><option>Ausgabe</option></select></div>
        <div class="col-md-1"><button class="btn btn-success w-100">+</button></div>
    </form></div>
    <div class="card shadow-sm"><table class="table mb-0"><thead><tr><th>Datum</th><th>Zweck</th><th>Betrag</th><th>Typ</th></tr></thead><tbody>{rows}</tbody></table></div>'''
    return admin_layout(content)

@admin_bp.route('/add_f', methods=['POST'])
def add_f():
    if not session.get('is_admin'): return redirect('/login')
    conn = get_db(); cur = conn.cursor()
    cur.execute("INSERT INTO finanzen (zweck, betrag, typ) VALUES (%s,%s,%s)", 
                (request.form['z'], request.form['b'], request.form['t']))
    conn.commit(); cur.close(); conn.close(); return redirect('/admin/finanzen')

@admin_bp.route('/einzug')
def einzug():
    if not session.get('is_admin'): return redirect('/login')
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM mitglieder")
    anzahl = cur.fetchone()[0]
    # Für jedes Mitglied eine Buchung erstellen
    cur.execute("INSERT INTO finanzen (zweck, betrag, typ) SELECT 'Jahresbeitrag 2025', 50.00, 'Einnahme' FROM mitglieder")
    conn.commit(); cur.close(); conn.close()
    return redirect('/admin/finanzen')

# --- MITGLIEDER VERWALTUNG (aus dem vorherigen Schritt) ---
@admin_bp.route('/mitglieder')
def mitglieder():
    if not session.get('is_admin'): return redirect('/login')
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT id, vorname, nachname, email FROM mitglieder ORDER BY nachname")
    ml = cur.fetchall(); cur.close(); conn.close()
    rows = "".join([f"<tr><td>{m[1]} {m[2]}</td><td>{m[3]}</td><td class='text-end'><a href='/admin/del_m/{m[0]}' class='btn btn-sm btn-outline-danger' onclick='return confirm(\"Löschen?\")'>X</a></td></tr>" for m in ml])
    return admin_layout(f'<div class="card p-4 mb-3 shadow-sm"><h4>Neues Mitglied</h4><form action="/admin/add_m" method="POST" class="row g-2"><div class="col-md-5"><input name="v" class="form-control" placeholder="Vorname" required></div><div class="col-md-5"><input name="n" class="form-control" placeholder="Nachname" required></div><div class="col-md-10"><input name="e" type="email" class="form-control" placeholder="E-Mail" required></div><div class="col-md-2"><button class="btn btn-success w-100">Speichern</button></div></form></div><table class="table card shadow-sm">{rows}</table>')

@admin_bp.route('/add_m', methods=['POST'])
def add_m():
    if not session.get('is_admin'): return redirect('/login')
    from werkzeug.security import generate_password_hash
    h = generate_password_hash("querfeldein2025")
    conn = get_db(); cur = conn.cursor()
    cur.execute("INSERT INTO mitglieder (vorname, nachname, email, passwort) VALUES (%s,%s,%s,%s)", (request.form['v'], request.form['n'], request.form['e'], h))
    conn.commit(); cur.close(); conn.close(); return redirect('/admin/mitglieder')

@admin_bp.route('/del_m/<int:id>')
def del_m(id):
    if not session.get('is_admin'): return redirect('/login')
    conn = get_db(); cur = conn.cursor()
    cur.execute("DELETE FROM mitglieder WHERE id=%s", (id,)); conn.commit(); cur.close(); conn.close(); return redirect('/admin/mitglieder')
