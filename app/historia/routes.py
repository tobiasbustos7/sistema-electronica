from flask import render_template, request
from flask_login import login_required
from app.historia import bp
from app.models import Historial, Usuario
from app import db
from app.decorators import admin_required
from sqlalchemy import or_

@bp.route('/')
@login_required
@admin_required
def index():
    page = request.args.get('page', 1, type=int)
    q = request.args.get('q', '').strip()

    query = Historial.query.order_by(Historial.fecha.desc())

    if q:
        query = query.filter(
            or_(
                Historial.accion.ilike(f'%{q}%'),
                Historial.detalle.ilike(f'%{q}%'),
                Historial.entidad.ilike(f'%{q}%'),
                Historial.usuario.has(Usuario.nombre.ilike(f'%{q}%'))
            )
        )

    historial = query.paginate(page=page, per_page=50)
    return render_template('historia/index.html', historial=historial, q=q)
