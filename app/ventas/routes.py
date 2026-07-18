from flask import render_template, redirect, url_for, flash, request, jsonify, Response
from flask_login import login_required, current_user
from app.ventas import bp
from app.models import Venta, DetalleVenta, Producto, Cliente, Historial, Caja, Categoria, Marca
from app import db
from datetime import datetime
from decimal import Decimal
from sqlalchemy import or_

@bp.route('/pos')
@login_required
def pos():
    caja_abierta = Caja.query.filter_by(estado='Abierta').first()
    if not caja_abierta:
        flash('Debes abrir la caja antes de vender.', 'warning')
        return redirect(url_for('caja.index'))
    productos = Producto.query.filter(
        Producto.stock > 0, Producto.estado == 'Disponible'
    ).order_by(Producto.nombre).all()
    clientes = Cliente.query.order_by(Cliente.nombre).all()
    return render_template('ventas/pos.html', productos=productos, clientes=clientes)

@bp.route('/buscar')
@login_required
def buscar():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])

    productos = Producto.query.outerjoin(Producto.marca).outerjoin(Producto.categoria).outerjoin(Producto.proveedor).filter(
        or_(
            Producto.nombre.ilike(f'%{q}%'),
            Producto.codigo.ilike(f'%{q}%'),
            Producto.codigo_barras.ilike(f'%{q}%'),
            Marca.nombre.ilike(f'%{q}%'),
            Categoria.nombre.ilike(f'%{q}%'),
            Producto.descripcion.ilike(f'%{q}%')
        ),
        Producto.stock > 0,
        Producto.estado == 'Disponible'
    ).limit(30).all()

    return jsonify([{
        'id': p.id,
        'codigo': p.codigo,
        'nombre': p.nombre,
        'precio': float(p.precio_venta),
        'stock': p.stock,
        'imagen': p.imagen or '',
        'categoria': p.categoria.nombre if p.categoria else '',
        'marca': p.marca.nombre if p.marca else ''
    } for p in productos])

@bp.route('/buscar_barras')
@login_required
def buscar_barras():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify(None)
    p = Producto.query.filter(
        db.or_(Producto.codigo == q, Producto.codigo_barras == q),
        Producto.stock > 0,
        Producto.estado == 'Disponible'
    ).first()
    if not p:
        return jsonify(None)
    return jsonify({
        'id': p.id,
        'codigo': p.codigo,
        'nombre': p.nombre,
        'precio': float(p.precio_venta),
        'stock': p.stock
    })

@bp.route('/buscar_cliente')
@login_required
def buscar_cliente():
    q = request.args.get('q', '')
    clientes = Cliente.query.filter(
        db.or_(
            Cliente.nombre.ilike(f'%{q}%'),
            Cliente.apellido.ilike(f'%{q}%'),
            Cliente.ci.ilike(f'%{q}%'),
            Cliente.telefono.ilike(f'%{q}%')
        )
    ).limit(10).all()
    return jsonify([{
        'id': c.id,
        'nombre': c.nombre_completo,
        'ci': c.ci or '',
        'telefono': c.telefono or ''
    } for c in clientes])

@bp.route('/procesar', methods=['POST'])
@login_required
def procesar():
    data = request.get_json()
    if not data or not data.get('productos'):
        return jsonify({'success': False, 'message': 'Carrito vacío.'})

    caja_abierta = Caja.query.filter_by(estado='Abierta').first()
    if not caja_abierta:
        return jsonify({'success': False, 'message': 'Caja cerrada. Abre la caja primero.'})

    productos_data = data['productos']
    metodo_pago = data.get('metodo_pago', 'Efectivo')
    monto_efectivo = float(data.get('monto_efectivo', 0))
    monto_tarjeta = float(data.get('monto_tarjeta', 0))
    monto_transferencia = float(data.get('monto_transferencia', 0))
    monto_qr = float(data.get('monto_qr', 0))
    total_recibido = monto_efectivo + monto_tarjeta + monto_transferencia + monto_qr

    cliente_id = data.get('cliente_id') or None
    factura_cliente = data.get('factura_cliente', '').strip()
    factura_ruc = data.get('factura_ruc', '').strip()

    subtotal = 0
    descuento = float(data.get('descuento', 0))

    detalles = []
    for item in productos_data:
        prod = Producto.query.get(item['id'])
        if not prod:
            return jsonify({'success': False, 'message': f'Producto no encontrado.'})
        cantidad = int(item['cantidad'])
        if cantidad > prod.stock:
            return jsonify({'success': False, 'message': f'Stock insuficiente para {prod.nombre}. Quedan {prod.stock}.'})
        precio = float(item.get('precio', float(prod.precio_venta)))
        st = cantidad * precio
        subtotal += st
        detalles.append({
            'producto': prod,
            'cantidad': cantidad,
            'precio': precio,
            'subtotal': st
        })

    total = subtotal - descuento
    if total < 0:
        total = 0

    vuelto = total_recibido - total if total_recibido >= total else 0

    # Generar número de factura
    ultima = Venta.query.order_by(Venta.id.desc()).first()
    num_factura = f'F{datetime.now().strftime("%Y%m%d")}-{(ultima.id + 1) if ultima else 1:04d}'

    venta = Venta(
        cliente_id=cliente_id,
        usuario_id=current_user.id,
        subtotal=subtotal,
        descuento=descuento,
        total=total,
        metodo_pago=metodo_pago,
        monto_efectivo=monto_efectivo,
        monto_tarjeta=monto_tarjeta,
        monto_transferencia=monto_transferencia,
        monto_qr=monto_qr,
        vuelto=vuelto,
        factura_numero=num_factura,
        estado='Completada'
    )
    db.session.add(venta)
    db.session.flush()

    for d in detalles:
        dv = DetalleVenta(
            venta_id=venta.id,
            producto_id=d['producto'].id,
            cantidad=d['cantidad'],
            precio_unitario=d['precio'],
            subtotal=d['subtotal']
        )
        db.session.add(dv)
        d['producto'].stock -= d['cantidad']

    caja_abierta.total_ventas = float(caja_abierta.total_ventas or 0) + total

    if cliente_id:
        cl = Cliente.query.get(cliente_id)
        cl.total_gastado = float(cl.total_gastado or 0) + total
        cl.ultima_compra = datetime.now()

    db.session.commit()

    Historial.registrar(
        usuario_id=current_user.id,
        accion='Realizar venta',
        entidad='Venta',
        entidad_id=venta.id,
        detalle=f'Venta {num_factura} por Gs. {total:,.0f}',
        ip=request.remote_addr
    )

    return jsonify({
        'success': True,
        'venta_id': venta.id,
        'factura': num_factura,
        'total': total,
        'vuelto': vuelto,
        'subtotal': subtotal,
        'descuento': descuento,
        'metodo_pago': metodo_pago,
        'monto_efectivo': monto_efectivo,
        'monto_tarjeta': monto_tarjeta,
        'monto_transferencia': monto_transferencia,
        'monto_qr': monto_qr,
        'fecha': venta.fecha.strftime('%d/%m/%Y %H:%M'),
        'usuario': current_user.nombre,
        'cliente': venta.cliente.nombre_completo if venta.cliente else 'Consumidor Final',
        'factura_cliente': factura_cliente if factura_cliente else (venta.cliente.nombre_completo if venta.cliente else 'Consumidor Final'),
        'factura_ruc': factura_ruc,
        'productos': [{
            'nombre': d['producto'].nombre,
            'cantidad': d['cantidad'],
            'precio': d['precio'],
            'subtotal': d['subtotal']
        } for d in detalles]
    })

@bp.route('/historial')
@login_required
def historial_ventas():
    ventas = Venta.query.order_by(Venta.fecha.desc()).all()
    return render_template('ventas/historial.html', ventas=ventas)

@bp.route('/detalle/<int:id>')
@login_required
def detalle(id):
    venta = Venta.query.get_or_404(id)
    return render_template('ventas/detalle.html', venta=venta)

@bp.route('/anular/<int:id>')
@login_required
def anular(id):
    venta = Venta.query.get_or_404(id)
    if venta.estado != 'Completada':
        flash('La venta ya fue anulada.', 'warning')
        return redirect(url_for('ventas.historial_ventas'))

    for dv in venta.detalles:
        dv.producto.stock += dv.cantidad
    venta.estado = 'Anulada'
    db.session.commit()

    Historial.registrar(
        usuario_id=current_user.id,
        accion='Anular venta',
        entidad='Venta',
        entidad_id=venta.id,
        detalle=f'Venta {venta.factura_numero} anulada',
        ip=request.remote_addr
    )

    flash('Venta anulada y stock restaurado.', 'success')
    return redirect(url_for('ventas.historial_ventas'))

# Clientes
@bp.route('/clientes')
@login_required
def clientes():
    clientes = Cliente.query.order_by(Cliente.nombre).all()
    return render_template('clientes/listar.html', clientes=clientes)

@bp.route('/clientes/agregar', methods=['GET', 'POST'])
@login_required
def clientes_agregar():
    if request.method == 'POST':
        c = Cliente(
            nombre=request.form.get('nombre', '').strip(),
            apellido=request.form.get('apellido', '').strip(),
            ci=request.form.get('ci', '').strip(),
            ruc=request.form.get('ruc', '').strip(),
            telefono=request.form.get('telefono', '').strip(),
            correo=request.form.get('correo', '').strip(),
            direccion=request.form.get('direccion', '').strip(),
            observaciones=request.form.get('observaciones', '').strip()
        )
        fnac = request.form.get('fecha_nac', '')
        if fnac:
            c.fecha_nac = datetime.strptime(fnac, '%Y-%m-%d').date()
        db.session.add(c)
        db.session.commit()
        flash('Cliente registrado.', 'success')
        return redirect(url_for('ventas.clientes'))
    return render_template('clientes/agregar.html')

@bp.route('/clientes/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def clientes_editar(id):
    c = Cliente.query.get_or_404(id)
    if request.method == 'POST':
        c.nombre = request.form.get('nombre', '').strip()
        c.apellido = request.form.get('apellido', '').strip()
        c.ci = request.form.get('ci', '').strip()
        c.ruc = request.form.get('ruc', '').strip()
        c.telefono = request.form.get('telefono', '').strip()
        c.correo = request.form.get('correo', '').strip()
        c.direccion = request.form.get('direccion', '').strip()
        c.observaciones = request.form.get('observaciones', '').strip()
        fnac = request.form.get('fecha_nac', '')
        if fnac:
            c.fecha_nac = datetime.strptime(fnac, '%Y-%m-%d').date()
        db.session.commit()
        flash('Cliente actualizado.', 'success')
        return redirect(url_for('ventas.clientes'))
    return render_template('clientes/agregar.html', cliente=c, editando=True)

@bp.route('/clientes/detalle/<int:id>')
@login_required
def clientes_detalle(id):
    c = Cliente.query.get_or_404(id)
    ventas = Venta.query.filter_by(cliente_id=c.id).order_by(Venta.fecha.desc()).all()
    return render_template('clientes/detalle.html', cliente=c, ventas=ventas)
