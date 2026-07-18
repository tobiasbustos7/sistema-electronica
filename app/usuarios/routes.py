from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.usuarios import bp
from app.models import Usuario, Rol, Historial
from app import db
from app.decorators import admin_required

@bp.route('/')
@login_required
@admin_required
def listar():
    usuarios = Usuario.query.order_by(Usuario.nombre).all()
    return render_template('usuarios/listar.html', usuarios=usuarios)

@bp.route('/crear', methods=['GET', 'POST'])
@login_required
@admin_required
def crear():
    roles = Rol.query.all()
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        nombre = request.form.get('nombre', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        rol_id = request.form.get('rol_id')

        if not username or not nombre or not password:
            flash('Completa los campos obligatorios.', 'danger')
            return render_template('usuarios/crear.html', roles=roles)

        if Usuario.query.filter_by(username=username).first():
            flash('El nombre de usuario ya existe.', 'danger')
            return render_template('usuarios/crear.html', roles=roles)

        u = Usuario(
            username=username,
            nombre=nombre,
            email=email,
            rol_id=rol_id,
            activo=True
        )
        u.set_password(password)
        db.session.add(u)
        db.session.commit()

        Historial.registrar(
            usuario_id=current_user.id,
            accion='Crear usuario',
            entidad='Usuario',
            entidad_id=u.id,
            detalle=f'Usuario {username} creado',
            ip=request.remote_addr
        )

        flash('Usuario creado correctamente.', 'success')
        return redirect(url_for('usuarios.listar'))

    return render_template('usuarios/crear.html', roles=roles)

@bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar(id):
    u = Usuario.query.get_or_404(id)
    roles = Rol.query.all()
    if request.method == 'POST':
        u.nombre = request.form.get('nombre', '').strip()
        u.email = request.form.get('email', '').strip()
        u.rol_id = request.form.get('rol_id')
        u.activo = 'activo' in request.form

        password = request.form.get('password', '')
        if password:
            u.set_password(password)

        db.session.commit()

        Historial.registrar(
            usuario_id=current_user.id,
            accion='Editar usuario',
            entidad='Usuario',
            entidad_id=u.id,
            detalle=f'Usuario {u.username} editado',
            ip=request.remote_addr
        )

        flash('Usuario actualizado correctamente.', 'success')
        return redirect(url_for('usuarios.listar'))

    return render_template('usuarios/crear.html', usuario=u, roles=roles, editando=True)

@bp.route('/eliminar/<int:id>')
@login_required
@admin_required
def eliminar(id):
    u = Usuario.query.get_or_404(id)
    if u.id == current_user.id:
        flash('No puedes eliminarte a ti mismo.', 'danger')
        return redirect(url_for('usuarios.listar'))

    Historial.registrar(
        usuario_id=current_user.id,
        accion='Eliminar usuario',
        entidad='Usuario',
        entidad_id=u.id,
        detalle=f'Usuario {u.username} eliminado',
        ip=request.remote_addr
    )

    db.session.delete(u)
    db.session.commit()
    flash('Usuario eliminado correctamente.', 'success')
    return redirect(url_for('usuarios.listar'))
