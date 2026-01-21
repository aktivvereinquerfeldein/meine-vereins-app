@admin_bp.route('/finanzen')
def finanzen():
    if not session.get('is_admin'): return redirect('/login')
    conn = get_db(); cur = conn.cursor()
    
    # Filter: Zeige standardmäßig alle offenen Beiträge
    cur.execute("""
        SELECT f.id, m.vorname, m.nachname, f.zweck, f.betrag, f.status, f.datum 
        FROM finanzen f 
        LEFT JOIN mitglieder m ON f.mitglied_id = m.id 
        ORDER BY f.status DESC, f.datum DESC
    """)
    fl = cur.fetchall(); cur.close(); conn.close()
    
    rows = ""
    for f in fl:
        status_btn = ""
        if f[5] == 'Offen':
            status_btn = f'<a href="/admin/pay/{f[0]}" class="btn btn-sm btn-success">Zahlung erhalten</a>'
        else:
            status_btn = '<span class="badge bg-light text-success">Bezahlt</span>'
            
        rows += f"""<tr>
            <td>{f[6]}</td>
            <td>{f[1] if f[1] else 'System'} {f[2] if f[2] else ''}</td>
            <td>{f[3]}</td>
            <td>{f[4]} €</td>
            <td>{status_btn}</td>
        </tr>"""
    
    content = f'''
    <div class="card p-4 mb-3 shadow-sm">
        <div class="d-flex justify-content-between align-items-center">
            <h4>Beitragsverwaltung & Kasse</h4>
            <a href="/admin/einzug_neu" class="btn btn-warning" onclick="return confirm('Soll-Stellung für alle Mitglieder (50€) erstellen?')">Beiträge anfordern (Soll)</a>
        </div>
    </div>
    <div class="card shadow-sm">
        <table class="table table-hover mb-0">
            <thead class="table-dark"><tr><th>Datum</th><th>Mitglied</th><th>Zweck</th><th>Betrag</th><th>Status</th></tr></thead>
            <tbody>{rows}</tbody>
        </table>
    </div>'''
    return admin_layout(content)

@admin_bp.route('/einzug_neu')
def einzug_neu():
    if not session.get('is_admin'): return redirect('/login')
    conn = get_db(); cur = conn.cursor()
    # Erstellt für jedes Mitglied eine offene Forderung
    cur.execute("""
        INSERT INTO finanzen (mitglied_id, zweck, betrag, typ, status) 
        SELECT id, 'Jahresbeitrag 2025', 50.00, 'Einnahme', 'Offen' FROM mitglieder
    """)
    conn.commit(); cur.close(); conn.close()
    return redirect('/admin/finanzen')

@admin_bp.route('/pay/<int:fid>')
def pay(fid):
    if not session.get('is_admin'): return redirect('/login')
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE finanzen SET status = 'Bezahlt' WHERE id = %s", (fid,))
    conn.commit(); cur.close(); conn.close()
    return redirect('/admin/finanzen')
