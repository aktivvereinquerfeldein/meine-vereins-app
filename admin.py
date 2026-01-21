from flask import Blueprint, render_template_string, request, session, redirect

# Das "Modul" für den Admin-Bereich
admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
def dashboard():
    if not session.get('is_admin'): return redirect('/login')
    return "<h1>Admin Zentrale</h1><p>Willkommen im geschützten Bereich.</p>"

@admin_bp.route('/mitglieder')
def list_members():
    if not session.get('is_admin'): return redirect('/login')
    # Hier kommt später die Mitgliederliste rein
    return "<h1>Mitgliederliste</h1><p>Hier verwaltest du deine Leute.</p>"
