from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.compras import bp
from app.models import Compra, DetalleCompra, Producto, Proveedor, Historial
from app import db
from app.decorators import admin_required
from datetime import datetime

@bp.route('/')
@login_required
def listar():
    compras = Compra.query.order_by(Compra.fecha.desc()).all()
    return render_template('compras/listar.html', compras=compras)

@bp.route('/nueva', methods=['GET', 'POST'])
@login_required
@admin_required
def nueva():
    proveedores = Proveedor.query.order_by(Proveedor.nombre).all()
    productos = Producto.query.order_by(Producto.nombre).all()

    if request.method == 'POST':
        proveedor_id = request.form.get('proveedor_id')
        if not proveedor_id:
            flash('Selecciona un proveedor.', 'danger')
            return render_template('compras/nueva.html', proveedores=proveedores, productos=productos)

        producto_ids = request.form.getlist('producto_id[]')
        cantidades = request.form.getlist('cantidad[]')
        precios = request.form.getlist('precio_unitario[]')

        if not producto_ids:
            flash('Agrega al menos un producto.', 'danger')
            return render_template('compras/nueva.html', proveedores=proveedores, productos=productos)

        total = 0
        compra = Compra(
            proveedor_id=proveedor_id,
            usuario_id=current_user.id,
            observaciones=request.form.get('observaciones', '').strip()
        )
        db.session.add(compra)
        db.session.flush()

        for i in range(len(producto_ids)):
            if not producto_ids[i] or not cantidades[i] or int(cantidades[i]) <= 0:
                continue
            prod = Producto.query.get(int(producto_ids[i]))
            if not prod:
                continue
            cantidad = int(cantidades[i])
            precio = float(precios[i]) if precios[i] else float(prod.precio_compra)
            subtotal = cantidad * precio
            total += subtotal

            dc = DetalleCompra(
                compra_id=compra.id,
                producto_id=prod.id,
                cantidad=cantidad,
                precio_unitario=precio,
                subtotal=subtotal
            )
            db.session.add(dc)

            prod.stock += cantidad

        compra.total = total
        db.session.commit()

        Historial.registrar(
            usuario_id=current_user.id,
            accion='Crear compra',
            entidad='Compra',
            entidad_id=compra.id,
            detalle=f'Compra a {compra.proveedor.nombre} por Gs. {total:,.0f}',
            ip=request.remote_addr
        )

        flash(f'Compra registrada. Stock actualizado automáticamente.', 'success')
        return redirect(url_for('compras.listar'))

    return render_template('compras/nueva.html', proveedores=proveedores, productos=productos)

@bp.route('/detalle/<int:id>')
@login_required
def detalle(id):
    compra = Compra.query.get_or_404(id)
    return render_template('compras/detalle.html', compra=compra)

@bp.route('/eliminar/<int:id>')
@login_required
@admin_required
def eliminar(id):
    compra = Compra.query.get_or_404(id)
    for dc in compra.detalles:
        dc.producto.stock -= dc.cantidad
    db.session.delete(compra)
    db.session.commit()
    flash('Compra eliminada y stock revertido.', 'success')
    return redirect(url_for('compras.listar'))

@bp.route('/buscar_producto')
@login_required
def buscar_producto():
    q = request.args.get('q', '')
    productos = Producto.query.filter(
        db.or_(
            Producto.nombre.ilike(f'%{q}%'),
            Producto.codigo.ilike(f'%{q}%'),
            Producto.codigo_barras.ilike(f'%{q}%')
        )
    ).limit(20).all()
    return jsonify([{
        'id': p.id,
        'codigo': p.codigo,
        'nombre': p.nombre,
        'precio_compra': float(p.precio_compra),
        'precio_venta': float(p.precio_venta),
        'stock': p.stock
    } for p in productos])
