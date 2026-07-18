from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.proveedores import bp
from app.models import Proveedor, Historial
from app import db
from app.decorators import admin_required

@bp.route('/')
@login_required
def listar():
    proveedores = Proveedor.query.order_by(Proveedor.nombre).all()
    return render_template('proveedores/listar.html', proveedores=proveedores)

@bp.route('/agregar', methods=['GET', 'POST'])
@login_required
@admin_required
def agregar():
    if request.method == 'POST':
        p = Proveedor(
            nombre=request.form.get('nombre', '').strip(),
            empresa=request.form.get('empresa', '').strip(),
            ruc=request.form.get('ruc', '').strip(),
            telefono=request.form.get('telefono', '').strip(),
            correo=request.form.get('correo', '').strip(),
            direccion=request.form.get('direccion', '').strip(),
            ciudad=request.form.get('ciudad', '').strip(),
            observaciones=request.form.get('observaciones', '').strip()
        )
        db.session.add(p)
        db.session.commit()

        Historial.registrar(
            usuario_id=current_user.id,
            accion='Crear proveedor',
            entidad='Proveedor',
            entidad_id=p.id,
            detalle=f'Proveedor {p.nombre} creado',
            ip=request.remote_addr
        )

        flash('Proveedor registrado correctamente.', 'success')
        return redirect(url_for('proveedores.listar'))

    return render_template('proveedores/agregar.html')

@bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar(id):
    p = Proveedor.query.get_or_404(id)
    if request.method == 'POST':
        p.nombre = request.form.get('nombre', '').strip()
        p.empresa = request.form.get('empresa', '').strip()
        p.ruc = request.form.get('ruc', '').strip()
        p.telefono = request.form.get('telefono', '').strip()
        p.correo = request.form.get('correo', '').strip()
        p.direccion = request.form.get('direccion', '').strip()
        p.ciudad = request.form.get('ciudad', '').strip()
        p.observaciones = request.form.get('observaciones', '').strip()
        db.session.commit()

        Historial.registrar(
            usuario_id=current_user.id,
            accion='Editar proveedor',
            entidad='Proveedor',
            entidad_id=p.id,
            detalle=f'Proveedor {p.nombre} editado',
            ip=request.remote_addr
        )

        flash('Proveedor actualizado.', 'success')
        return redirect(url_for('proveedores.listar'))

    return render_template('proveedores/agregar.html', proveedor=p, editando=True)

@bp.route('/eliminar/<int:id>')
@login_required
@admin_required
def eliminar(id):
    p = Proveedor.query.get_or_404(id)
    Historial.registrar(
        usuario_id=current_user.id,
        accion='Eliminar proveedor',
        entidad='Proveedor',
        entidad_id=p.id,
        detalle=f'Proveedor {p.nombre} eliminado',
        ip=request.remote_addr
    )
    db.session.delete(p)
    db.session.commit()
    flash('Proveedor eliminado.', 'success')
    return redirect(url_for('proveedores.listar'))
