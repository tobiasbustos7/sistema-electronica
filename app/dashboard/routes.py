from flask import render_template
from flask_login import login_required
from app.dashboard import bp
from app.models import Venta, Producto, Cliente, DetalleVenta
from app import db
from datetime import datetime, timedelta
from sqlalchemy import func

@bp.route('/')
@login_required
def index():
    hoy = datetime.now().date()

    ventas_hoy = db.session.query(func.sum(Venta.total)).filter(
        func.date(Venta.fecha) == hoy, Venta.estado == 'Completada'
    ).scalar() or 0

    productos_vendidos_hoy = db.session.query(func.sum(DetalleVenta.cantidad)).join(
        Venta, DetalleVenta.venta_id == Venta.id
    ).filter(func.date(Venta.fecha) == hoy, Venta.estado == 'Completada').scalar() or 0

    productos_poco_stock = Producto.query.filter(
        Producto.stock <= Producto.stock_minimo, Producto.stock > 0,
        Producto.estado == 'Disponible'
    ).count()

    productos_sin_stock = Producto.query.filter(
        Producto.stock <= 0, Producto.estado == 'Disponible'
    ).count()

    ganancia_hoy = 0
    ventas_hoy_q = Venta.query.filter(
        func.date(Venta.fecha) == hoy, Venta.estado == 'Completada'
    ).all()
    for v in ventas_hoy_q:
        for d in v.detalles:
            if d.producto:
                ganancia_hoy += (float(d.precio_unitario) - float(d.producto.precio_compra)) * d.cantidad

    clientes_count = Cliente.query.count()
    productos_count = Producto.query.count()

    ventas_7_dias = []
    fechas_7 = []
    for i in range(6, -1, -1):
        dia = hoy - timedelta(days=i)
        total = db.session.query(func.sum(Venta.total)).filter(
            func.date(Venta.fecha) == dia, Venta.estado == 'Completada'
        ).scalar() or 0
        fechas_7.append(dia.strftime('%d/%m'))
        ventas_7_dias.append(float(total))

    productos_mas_vendidos_raw = db.session.query(
        Producto.nombre, func.sum(DetalleVenta.cantidad).label('total')
    ).join(DetalleVenta, Producto.id == DetalleVenta.producto_id
    ).join(Venta, DetalleVenta.venta_id == Venta.id
    ).filter(Venta.estado == 'Completada'
    ).group_by(Producto.id, Producto.nombre
    ).order_by(func.sum(DetalleVenta.cantidad).desc()).limit(5).all()
    productos_mas_vendidos = [{'nombre': r.nombre or 'Sin nombre', 'total': r.total} for r in productos_mas_vendidos_raw]

    ganancias_mes = []
    mes_actual = datetime.now().month
    anio_actual = datetime.now().year
    for i in range(1, 32):
        try:
            dia = datetime(anio_actual, mes_actual, i).date()
        except:
            break
        ganancia = 0
        ventas_dia = Venta.query.filter(
            func.date(Venta.fecha) == dia, Venta.estado == 'Completada'
        ).all()
        for v in ventas_dia:
            for d in v.detalles:
                if d.producto:
                    ganancia += (float(d.precio_unitario) - float(d.producto.precio_compra)) * d.cantidad
        ganancias_mes.append(float(ganancia))

    return render_template('dashboard/index.html',
        ventas_hoy=float(ventas_hoy),
        productos_vendidos_hoy=int(productos_vendidos_hoy),
        productos_poco_stock=productos_poco_stock,
        productos_sin_stock=productos_sin_stock,
        ganancia_hoy=round(ganancia_hoy, 0),
        clientes_count=clientes_count,
        productos_count=productos_count,
        ventas_7_dias=ventas_7_dias,
        fechas_7=fechas_7,
        productos_mas_vendidos=productos_mas_vendidos,
        ganancias_mes=ganancias_mes
    )
