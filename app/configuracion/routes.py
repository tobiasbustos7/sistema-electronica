from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.configuracion import bp
from app.models import Configuracion, Historial
from app import db
from app.decorators import admin_required

@bp.route('/', methods=['GET', 'POST'])
@login_required
@admin_required
def index():
    if request.method == 'POST':
        campos = [
            'nombre_negocio', 'direccion', 'telefono', 'correo',
            'ruc_empresa', 'iva', 'moneda', 'impresora'
        ]
        for campo in campos:
            valor = request.form.get(campo, '').strip()
            Configuracion.set(campo, valor)

        if 'logo' in request.files:
            file = request.files['logo']
            if file and file.filename:
                import os, uuid
                from flask import current_app
                from werkzeug.utils import secure_filename
                ALLOWED = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
                if '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in ALLOWED:
                    ext = file.filename.rsplit('.', 1)[1].lower()
                    filename = f'logo.{ext}'
                    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                    Configuracion.set('logo', filename)

        Historial.registrar(
            usuario_id=current_user.id,
            accion='Actualizar configuración',
            entidad='Configuracion',
            ip=request.remote_addr
        )

        flash('Configuración actualizada correctamente.', 'success')
        return redirect(url_for('configuracion.index'))

    configs = {}
    for c in Configuracion.query.all():
        configs[c.clave] = c.valor

    return render_template('configuracion/index.html', configs=configs)
