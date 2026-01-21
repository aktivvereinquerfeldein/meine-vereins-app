from flask import Blueprint, render_template_string, request, session, redirect, url_for
import psycopg2, os

# WICHTIG: Diese Zeile muss ganz oben stehen!
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
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM mitglieder"); mc = cur.fetchone()[0]
    # Saldo berechnen
    try:
        cur.execute("SELECT SUM(CASE WHEN typ='Einnahme' AND status='Bezahlt' THEN betrag WHEN typ='Ausgabe' THEN -betrag ELSE 0 END) FROM finanzen")
        saldo = cur.fetchone()[0] or 0
    except: saldo = 0
    cur.close(); conn.close()
    
    content = f'''<h3>Dashboard</h3>
    <div class="row mt-4">
        <div class="col-md-6 mb-3"><div class="card p-4 shadow-sm"><h5>Mitglieder</h5><h1>{mc}</h1></div></div>
        <div class="col-md-6 mb-3"><div class="card p-4 shadow-sm"><h5>Kassenstand (Bezahlt)</h5><h1 class="text-success">{saldo} €</h1></div></div>
    </div>'''
    return admin_layout(content)

@admin_bp.route('/finanzen')
def finanzen():
    if not session.get('is_admin'): return redirect('/login')
    conn = get_db(); cur = conn.cursor()
    # Wir holen uns die Namen der Mitglieder direkt dazu
    cur.execute("""
        SELECT f.id, m.vorname, m.nachname, f.zweck, f.betrag, f.status, f.datum 
        FROM finanzen f 
        LEFT JOIN mitglieder m ON f.mitglied_id = m.id 
        ORDER BY f.datum DESC, f.id DESC
    """)
    fl = cur.fetchall(); cur.close(); conn.close()
    
    rows = ""
    for f in fl:
        name = f"{f[1]} {f[2]}" if f[1] else "Allgemein"
        status_color = "text-success" if f[5] == "Bezahlt" else "text-warning"
        status_html = f'<span class="badge bg-success">Bezahlt</span>' if f[5] == "Bezahlt" else f'<a href="/admin/pay/{f[0]}" class="btn btn-sm btn-outline-warning">Zahlung markieren</a>'
        
        rows += f"<tr><td>{f[6]}</td><td>{name}</td><td>{f[3]}</td><td>{f[4]} €</td><td>{status_html}</td></tr>"

    content = f'''<div class="card p-4 mb-3 shadow-sm">
        <div class="d-flex justify-content-between align-items-center mb-3">
            <h4>Finanzen & Beiträge</h4>
            <a href="/admin/einzug_neu" class="btn btn-warning" onclick="return confirm('Beiträge (50€) für alle Mitglieder als OFFEN anlegen?')">Jahresbeiträge anfordern</a>
        </div>
        <table class="table table-hover mb-0">
            <thead><tr><th>Datum</th><th>Mitglied</th><th>Zweck</th><th>Betrag</th><th>Status</th></tr></thead>
            <tbody>{rows}</tbody>
        </table>
    </div>'''
    return admin_layout(content)

@admin_bp.route('/pay/<int:fid>')
def pay(fid):
    if not session.get('is_admin'): return redirect('/login')
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE finanzen SET status = 'Bezahlt' WHERE id = %s", (fid,))
    conn.commit(); cur.close(); conn.close()
    return redirect('/admin/finanzen')

@admin_bp.route('/einzug_neu')
def einzug_neu():
    if not session.get('is_admin'): return redirect('/login')
    conn
