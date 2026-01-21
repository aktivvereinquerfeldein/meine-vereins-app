from flask import Blueprint, render_template_string, request, session, redirect, url_for
import psycopg2, os

admin_bp = Blueprint('admin', __name__)
DB_URL = os.environ.get('DATABASE_URL')

def get_db():
    return psycopg2.connect(DB_URL)

def admin_layout(content):
    return render_template_string(f"""
    <!DOCTYPE html><html><head><meta charset="UTF-8">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>body{{background:#f0f2f5}}.navbar{{background:#1c2938 !important}}.nav-link{{color:white !important}}</style></head>
    <body><nav class="navbar navbar-expand navbar-dark mb-4 shadow-sm"><div class="container">
    <a class="navbar-brand" href="/admin"><b>ADMIN-ZENTRALE</b></a>
    <div class="navbar-nav ms-auto">
        <a class="nav-link px-2" href="/admin/mitglieder">Mitglieder</a>
        <a class="nav-link px-2" href="/admin/finanzen">Finanzen</a>
        <a class="nav-link px-2 text-warning" href="/">User-Ansicht</a>
    </div></div></nav><div class="container">{content}</div></body></html>""")

@admin_bp.route('/')
def dashboard():
    return redirect(url_for('admin.mitglieder'))

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
    conn.commit(); cur.close(); conn.close(); return redirect(url_for('admin.mitglieder'))

@admin_bp.route('/del_m/<int:id>')
def del_m(id):
    if not session.get('is_admin'): return redirect('/login')
    conn = get_db(); cur = conn.cursor()
    cur.execute("DELETE FROM mitglieder WHERE id=%s", (id,)); conn.commit(); cur.close(); conn.close(); return redirect(url_for('admin.mitglieder'))

@admin_bp.route('/finanzen')
def finanzen():
    if not session.get('is_admin'): return redirect('/login')
    conn = get_db(); cur = conn.cursor()
    cur.execute("""SELECT f.id, m.vorname, m.nachname, f.zweck, f.betrag, f.status, f.datum 
                   FROM finanzen f LEFT JOIN mitglieder m ON f.mitglied_id = m.id 
                   ORDER BY f.datum DESC, f.id DESC""")
    fl = cur.fetchall(); cur.close(); conn.close()
    rows = "".join([f"<tr><td>{f[6]}</td><td>{f[1]} {f[2] if f[1] else 'System'}</td><td>{f[3]}</td><td>{f[4]}€</td><td>{'<span class=\"badge bg-success\">Bezahlt</span>' if f[5]=='Bezahlt' else f'<a href=\"/admin/pay/{f[0]}\" class=\"btn btn-sm btn-warning\">Zahlung markieren</a>'}</td></tr>" for f in fl])
    return admin_layout(f'<div class="card p-4 mb-3 shadow-sm"><div class="d-flex justify-content-between"><h4>Finanzen</h4><a href="/admin/einzug_neu" class="btn btn-primary" onclick="return confirm(\'Beiträge (50€) anfordern?\')">Jahresbeiträge anfordern</a></div><table class="table mt-3"><thead><tr><th>Datum</th><th>Mitglied</th><th>Zweck</th><th>Betrag</th><th>Status</th></tr></thead><tbody>{rows}</tbody></table></div>')

@admin_bp.route('/pay/<int:fid>')
def pay(fid):
    if not session.get('is_admin'): return redirect('/login')
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE finanzen SET status = 'Bezahlt' WHERE id = %s", (fid,))
    conn.commit(); cur.close(); conn.close()
    return redirect(url_for('admin.finanzen'))

@admin_bp.route('/einzug_neu')
def einzug_neu():
    if not session.get('is_admin'): return redirect('/login')
    conn = get_db(); cur = conn.cursor()
    cur.execute("INSERT INTO finanzen (mitglied_id, zweck, betrag, typ, status) SELECT id, 'Jahresbeitrag 2025', 50.00, 'Einnahme', 'Offen' FROM mitglieder")
    conn.commit(); cur.close(); conn.close()
    return redirect(url_for('admin.finanzen'))
