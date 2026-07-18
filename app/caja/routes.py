from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.caja import bp
from app.models import Caja, MovimientoCaja, Venta, Historial
from app import db
from datetime import datetime

@bp.route('/')
@login_required
def index():
    cajas = Caja.query.order_by(Caja.fecha_apertura.desc()).limit(20).all()
    caja_activa = Caja.query.filter_by(estado='Abierta').first()
    return render_template('caja/index.html', cajas=cajas, caja_activa=caja_activa)

@bp.route('/abrir', methods=['GET', 'POST'])
@login_required
def abrir():
    caja_abierta = Caja.query.filter_by(estado='Abierta').first()
    if caja_abierta:
        flash('Ya hay una caja abierta.', 'warning')
        return redirect(url_for('caja.index'))

    if request.method == 'POST':
        monto = float(request.form.get('monto_inicial', 0))
        c = Caja(
            usuario_id_apertura=current_user.id,
            monto_inicial=monto,
            estado='Abierta'
        )
        db.session.add(c)
        db.session.commit()

        Historial.registrar(
            usuario_id=current_user.id,
            accion='Abrir caja',
            entidad='Caja',
            entidad_id=c.id,
            detalle=f'Caja abierta con Gs. {monto:,.0f}',
            ip=request.remote_addr
        )

        flash('Caja abierta correctamente.', 'success')
        return redirect(url_for('caja.index'))

    return render_template('caja/abrir.html')

@bp.route('/cerrar', methods=['GET', 'POST'])
@login_required
def cerrar():
    caja = Caja.query.filter_by(estado='Abierta').first()
    if not caja:
        flash('No hay caja abierta.', 'warning')
        return redirect(url_for('caja.index'))

    if request.method == 'POST':
        dinero_contado = float(request.form.get('dinero_contado', 0))
        caja.dinero_contado = dinero_contado
        caja.dinero_esperado = float(caja.monto_inicial or 0) + float(caja.total_ventas or 0) - float(caja.total_gastos or 0)
        caja.diferencia = dinero_contado - caja.dinero_esperado
        caja.usuario_id_cierre = current_user.id
        caja.fecha_cierre = datetime.now()
        caja.estado = 'Cerrada'
        db.session.commit()

        Historial.registrar(
            usuario_id=current_user.id,
            accion='Cerrar caja',
            entidad='Caja',
            entidad_id=caja.id,
            detalle=f'Caja cerrada. Esperado: Gs. {caja.dinero_esperado:,.0f}, Contado: Gs. {dinero_contado:,.0f}, Dif: Gs. {caja.diferencia:,.0f}',
            ip=request.remote_addr
        )

        flash('Caja cerrada correctamente.', 'success')
        return redirect(url_for('caja.index'))

    total_ventas = float(caja.total_ventas or 0)
    total_gastos = float(caja.total_gastos or 0)
    monto_inicial = float(caja.monto_inicial or 0)
    esperado = monto_inicial + total_ventas - total_gastos

    return render_template('caja/cerrar.html', caja=caja,
        total_ventas=total_ventas, total_gastos=total_gastos,
        monto_inicial=monto_inicial, esperado=esperado)

@bp.route('/detalle/<int:id>')
@login_required
def detalle(id):
    caja = Caja.query.get_or_404(id)
    return render_template('caja/detalle.html', caja=caja)
