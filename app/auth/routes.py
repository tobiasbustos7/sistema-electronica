from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from app.auth import bp
from app.models import Usuario, Historial

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('Completa todos los campos.', 'danger')
            return render_template('auth/login.html')

        user = Usuario.query.filter_by(username=username).first()

        if user and user.check_password(password):
            if not user.activo:
                flash('Usuario desactivado. Contacta al administrador.', 'danger')
                return render_template('auth/login.html')

            login_user(user)
            user.ultimo_acceso = __import__('datetime').datetime.now()
            from app import db
            db.session.commit()

            Historial.registrar(
                usuario_id=user.id,
                accion='Inicio de sesión',
                ip=request.remote_addr
            )

            flash(f'Bienvenido {user.nombre}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.index'))
        else:
            flash('Usuario o contraseña incorrectos.', 'danger')

    return render_template('auth/login.html')

@bp.route('/logout')
def logout():
    if current_user.is_authenticated:
        Historial.registrar(
            usuario_id=current_user.id,
            accion='Cierre de sesión',
            ip=request.remote_addr
        )
    logout_user()
    flash('Sesión cerrada correctamente.', 'info')
    return redirect(url_for('auth.login'))
