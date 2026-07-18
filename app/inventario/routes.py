from flask import render_template, request
from flask_login import login_required
from app.inventario import bp
from app.models import Producto, Categoria, Marca
from app import db

@bp.route('/')
@login_required
def index():
    q = request.args.get('q', '').strip()
    categoria_id = request.args.get('categoria', '')
    estado_filtro = request.args.get('estado', '')

    productos = Producto.query.order_by(Producto.nombre)

    if q:
        productos = productos.filter(
            db.or_(
                Producto.nombre.ilike(f'%{q}%'),
                Producto.codigo.ilike(f'%{q}%'),
                Producto.codigo_barras.ilike(f'%{q}%')
            )
        )
    if categoria_id:
        productos = productos.filter_by(categoria_id=categoria_id)

    if estado_filtro == 'sin_stock':
        productos = productos.filter(Producto.stock <= 0)
    elif estado_filtro == 'poco_stock':
        productos = productos.filter(Producto.stock <= Producto.stock_minimo, Producto.stock > 0)
    elif estado_filtro == 'con_stock':
        productos = productos.filter(Producto.stock > Producto.stock_minimo)

    categorias = Categoria.query.order_by(Categoria.nombre).all()
    return render_template('inventario/index.html',
        productos=productos.all(),
        categorias=categorias
    )
