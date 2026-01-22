from flask import Blueprint, render_template_string, request, session, redirect, url_for
import psycopg2, os

admin_bp = Blueprint('admin', __name__)
DB_URL = os.environ.get('DATABASE_URL')

def get_db():
    return psycopg2.connect(DB_URL)

def admin_layout(content):
    # Greift auf das gleiche Styling zu
    return render_template_string(f"""
    <!DOCTYPE html><html><head><meta charset="UTF-8">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>body{{background:#f0f2f5}}.navbar{{background:#1c2938 !important}}.nav-link{{color:white !important}}</style></head>
    <body><nav class="navbar navbar-expand navbar-dark mb-4 shadow-sm"><div class="container">
    <a class="navbar-brand" href="/admin/mitglieder"><b>ADMIN</b></a>
    <div class="navbar-nav ms-auto">
        <a class="nav-link px-2" href="/admin/mitglieder">Mitglieder</a>
        <a class="nav-link px-2" href="/admin/finanzen">Finanzen</a>
        <a class="nav-link px-2 text-warning" href="/">User-Ansicht</a>
    </div></div></nav><div class="container">{content}</div></body></html>""")

@admin_bp.route('/mitglieder')
def mitglieder():
    if not session.get('is_admin'): return redirect('/login')
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT id, vorname, nachname, email, geburtstag, eintritt FROM mitglieder ORDER BY nachname")
    ml = cur.fetchall(); cur.close(); conn.close()
    rows = "".join([f"<tr><td>{m[1]} {m[2]}</td><td>{m[3]}</td><td>{m[4]}</td><td>{m[5]}</td><td class='text-end'><a href='/admin/del_m/{m[0]}' class='btn btn-sm btn-outline-danger' onclick='return confirm(\"Löschen?\")'>X</a></td></tr>" for m in ml])
    return admin_layout(f'''<div class="card p-4 mb-3 shadow-sm"><h4>Neues Mitglied</h4>
    <form action="/admin/add_m" method="POST" class="row g-2">
    <div class="col-md-6"><input name="v" class="form-control" placeholder="Vorname" required></div>
    <div class="col-md-6"><input name="n" class="form-control" placeholder="Nachname" required></div>
    <div class="col-md-12"><input name="e" type="email" class="form-control" placeholder="E-Mail" required></div>
    <div class="col-md-6"><label class="small">Geburtstag</label><input name="g" type="date" class="form-control"></div>
    <div class="col-md-6"><label class="small">Eintritt</label><input name="ein" type="date" class="form-control"></div>
    <button class="btn btn-success mt-2">Mitglied anlegen</button></form></div>
    <table class="table card shadow-sm"><thead><tr><th>Name</th><th>E-Mail</th><th>Geburtstag</th><th>Eintritt</th><th></th></tr></thead><tbody>{rows}</tbody></table>''')

@admin_bp.route('/add_m', methods=['POST'])
def add_m():
    if not session.get('is_admin'): return redirect('/login')
    from werkzeug.security import generate_password_hash
    h = generate_password_hash("querfeldein2025")
    conn = get_db(); cur = conn.cursor()
    cur.execute("INSERT INTO mitglieder (vorname, nachname, email, geburtstag, eintritt, passwort) VALUES (%s,%s,%s,%s,%s,%s)", 
                (request.form['v'], request.form['n'], request.form['e'], request.form['g'], request.form['ein'], h))
    conn.commit(); cur.close(); conn.close(); return redirect(url_for('admin.mitglieder'))

@admin_bp.route('/finanzen')
def finanzen():
    if not session.get('is_admin'): return redirect('/login')
    conn = get_db(); cur = conn.cursor()
    cur.execute("""SELECT f.id, m.vorname, m.nachname, f.zweck, f.betrag, f.status, f.datum, f.typ 
                   FROM finanzen f LEFT JOIN mitglieder m ON f.mitglied_id = m.id 
                   ORDER BY f.datum DESC, f.id DESC""")
    fl = cur.fetchall(); cur.close(); conn.close()
    rows = "".join([f"<tr><td>{f[6]}</td><td>{f[1] if f[1] else 'Allgemein'}</td><td>{f[3]}</td><td class='{'text-success' if f[7]=='Einnahme' else 'text-danger'}'>{f[4]}€</td><td>{f[5]}</td><td>{f'<a href=\"/admin/pay/{f[0]}\" class=\"btn btn-sm btn-warning\">Zahlen</a>' if f[5]=='Offen' else ''}</td></tr>" for f in fl])
    return admin_layout(f'''<div class="card p-4 mb-3 shadow-sm">
    <div class="d-flex justify-content-between mb-3"><h4>Kasse & Beiträge</h4>
    <a href="/admin/einzug_neu" class="btn btn-outline-primary" onclick="return confirm('50€ von allen anfordern?')">Jahresbeiträge anfordern</a></div>
    <form action="/admin/add_f" method="POST" class="row g-2">
    <div class="col-md-5"><input name="z" class="form-control" placeholder="Zweck (z.B. Miete)" required></div>
    <div class="col-md-3"><input name="b" type="number" step="0.01" class="form-control" placeholder="Betrag" required></div>
    <div class="col-md-3"><select name="t" class="form-control"><option>Einnahme</option><option>Ausgabe</option></select></div>
    <div class="col-md-1"><button class="btn btn-success w-100">+</button></div></form></div>
    <div class="card shadow-sm"><table class="table mb-0"><thead><tr><th>Datum</th><th>Wer</th><th>Zweck</th><th>Betrag</th><th>Status</th><th>Aktion</th></tr></thead><tbody>{rows}</tbody></table></div>''')

@admin_bp.route('/add_f', methods=['POST'])
def add_f():
    if not session.get('is_admin'): return redirect('/login')
    conn = get_db(); cur = conn.cursor()
    cur.execute("INSERT INTO finanzen (zweck, betrag, typ, status) VALUES (%s,%s,%s,%s)", 
                (request.form['z'], request.form['b'], request.form['t'], 'Bezahlt'))
    conn.commit(); cur.close(); conn.close(); return redirect(url_for('admin.finanzen'))

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

@admin_bp.route('/del_m/<int:id>')
def del_m(id):
    if not session.get('is_admin'): return redirect('/login')
    conn = get_db(); cur = conn.cursor(); cur.execute("DELETE FROM mitglieder WHERE id=%s", (id,)); conn.commit(); cur.close(); conn.close(); return redirect(url_for('admin.mitglieder'))
