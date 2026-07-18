import os, uuid
from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.productos import bp
from app.models import Producto, Categoria, Marca, Proveedor, Historial
from app import db
from app.decorators import admin_required

def allowed_file(filename):
    ALLOWED = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED

@bp.route('/')
@login_required
def listar():
    q = request.args.get('q', '').strip()
    categoria_id = request.args.get('categoria', '').strip()
    marca_id = request.args.get('marca', '').strip()

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
    if marca_id:
        productos = productos.filter_by(marca_id=marca_id)

    categorias = Categoria.query.order_by(Categoria.nombre).all()
    marcas = Marca.query.order_by(Marca.nombre).all()
    return render_template('productos/listar.html',
        productos=productos.all(),
        categorias=categorias,
        marcas=marcas
    )

@bp.route('/agregar', methods=['GET', 'POST'])
@login_required
@admin_required
def agregar():
    categorias = Categoria.query.order_by(Categoria.nombre).all()
    marcas = Marca.query.order_by(Marca.nombre).all()
    proveedores = Proveedor.query.order_by(Proveedor.nombre).all()

    if request.method == 'POST':
        codigo = request.form.get('codigo', '').strip()
        if not codigo:
            ultimo = Producto.query.order_by(Producto.id.desc()).first()
            codigo = f'{ultimo.id + 1:04d}' if ultimo else '0001'

        if Producto.query.filter_by(codigo=codigo).first():
            flash('El código de producto ya existe.', 'danger')
            return render_template('productos/agregar.html', categorias=categorias,
                                   marcas=marcas, proveedores=proveedores)

        imagen = None
        if 'imagen' in request.files:
            file = request.files['imagen']
            if file and file.filename and allowed_file(file.filename):
                ext = file.filename.rsplit('.', 1)[1].lower()
                filename = f'{uuid.uuid4()}.{ext}'
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                imagen = filename

        p = Producto(
            codigo=codigo,
            nombre=request.form.get('nombre', '').strip(),
            descripcion=request.form.get('descripcion', '').strip(),
            categoria_id=request.form.get('categoria_id') or None,
            marca_id=request.form.get('marca_id') or None,
            precio_compra=request.form.get('precio_compra', 0),
            precio_venta=request.form.get('precio_venta', 0),
            stock=request.form.get('stock', 0),
            stock_minimo=request.form.get('stock_minimo', 10),
            proveedor_id=request.form.get('proveedor_id') or None,
            codigo_barras=request.form.get('codigo_barras', '').strip(),
            imagen=imagen,
            estado=request.form.get('estado', 'Disponible'),
            ubicacion=request.form.get('ubicacion', '').strip()
        )
        db.session.add(p)
        db.session.commit()

        Historial.registrar(
            usuario_id=current_user.id,
            accion='Crear producto',
            entidad='Producto',
            entidad_id=p.id,
            detalle=f'Producto {p.nombre} creado',
            ip=request.remote_addr
        )

        flash('Producto agregado correctamente.', 'success')
        return redirect(url_for('productos.listar'))

    return render_template('productos/agregar.html', categorias=categorias,
                           marcas=marcas, proveedores=proveedores)

@bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar(id):
    p = Producto.query.get_or_404(id)
    categorias = Categoria.query.order_by(Categoria.nombre).all()
    marcas = Marca.query.order_by(Marca.nombre).all()
    proveedores = Proveedor.query.order_by(Proveedor.nombre).all()

    if request.method == 'POST':
        p.nombre = request.form.get('nombre', '').strip()
        p.descripcion = request.form.get('descripcion', '').strip()
        p.categoria_id = request.form.get('categoria_id') or None
        p.marca_id = request.form.get('marca_id') or None
        p.precio_compra = request.form.get('precio_compra', 0)
        p.precio_venta = request.form.get('precio_venta', 0)
        p.stock = request.form.get('stock', 0)
        p.stock_minimo = request.form.get('stock_minimo', 10)
        p.proveedor_id = request.form.get('proveedor_id') or None
        p.codigo_barras = request.form.get('codigo_barras', '').strip()
        p.estado = request.form.get('estado', 'Disponible')
        p.ubicacion = request.form.get('ubicacion', '').strip()

        if 'imagen' in request.files:
            file = request.files['imagen']
            if file and file.filename and allowed_file(file.filename):
                ext = file.filename.rsplit('.', 1)[1].lower()
                filename = f'{uuid.uuid4()}.{ext}'
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                p.imagen = filename

        db.session.commit()

        Historial.registrar(
            usuario_id=current_user.id,
            accion='Editar producto',
            entidad='Producto',
            entidad_id=p.id,
            detalle=f'Producto {p.nombre} editado',
            ip=request.remote_addr
        )

        flash('Producto actualizado correctamente.', 'success')
        return redirect(url_for('productos.listar'))

    return render_template('productos/agregar.html', producto=p, categorias=categorias,
                           marcas=marcas, proveedores=proveedores, editando=True)

@bp.route('/eliminar/<int:id>')
@login_required
@admin_required
def eliminar(id):
    p = Producto.query.get_or_404(id)
    Historial.registrar(
        usuario_id=current_user.id,
        accion='Eliminar producto',
        entidad='Producto',
        entidad_id=p.id,
        detalle=f'Producto {p.nombre} eliminado',
        ip=request.remote_addr
    )
    db.session.delete(p)
    db.session.commit()
    flash('Producto eliminado correctamente.', 'success')
    return redirect(url_for('productos.listar'))

@bp.route('/duplicar/<int:id>')
@login_required
@admin_required
def duplicar(id):
    original = Producto.query.get_or_404(id)
    nuevo_codigo = f'{original.codigo}-COPY'
    if Producto.query.filter_by(codigo=nuevo_codigo).first():
        nuevo_codigo = f'{original.codigo}-{uuid.uuid4().hex[:4]}'

    p = Producto(
        codigo=nuevo_codigo,
        nombre=f'{original.nombre} (Copia)',
        descripcion=original.descripcion,
        categoria_id=original.categoria_id,
        marca_id=original.marca_id,
        precio_compra=original.precio_compra,
        precio_venta=original.precio_venta,
        stock=0,
        stock_minimo=original.stock_minimo,
        proveedor_id=original.proveedor_id,
        codigo_barras='',
        estado='Disponible'
    )
    db.session.add(p)
    db.session.commit()

    Historial.registrar(
        usuario_id=current_user.id,
        accion='Duplicar producto',
        entidad='Producto',
        entidad_id=p.id,
        detalle=f'Producto duplicado desde {original.codigo}',
        ip=request.remote_addr
    )

    flash('Producto duplicado correctamente.', 'success')
    return redirect(url_for('productos.editar', id=p.id))

# ---- Categorías ----
@bp.route('/categorias')
@login_required
@admin_required
def categorias():
    cats = Categoria.query.order_by(Categoria.nombre).all()
    return render_template('categorias/index.html', categorias=cats)

@bp.route('/categorias/agregar', methods=['POST'])
@login_required
@admin_required
def categorias_agregar():
    nombre = request.form.get('nombre', '').strip()
    if nombre and not Categoria.query.filter_by(nombre=nombre).first():
        c = Categoria(nombre=nombre, descripcion=request.form.get('descripcion', ''))
        db.session.add(c)
        db.session.commit()
        flash('Categoría agregada.', 'success')
    else:
        flash('La categoría ya existe o el nombre está vacío.', 'danger')
    return redirect(url_for('productos.categorias'))

@bp.route('/categorias/eliminar/<int:id>')
@login_required
@admin_required
def categorias_eliminar(id):
    c = Categoria.query.get_or_404(id)
    if c.productos:
        flash('No se puede eliminar una categoría con productos asociados.', 'danger')
    else:
        db.session.delete(c)
        db.session.commit()
        flash('Categoría eliminada.', 'success')
    return redirect(url_for('productos.categorias'))

# ---- Marcas ----
@bp.route('/marcas')
@login_required
@admin_required
def marcas():
    ms = Marca.query.order_by(Marca.nombre).all()
    return render_template('marcas/index.html', marcas=ms)

@bp.route('/marcas/agregar', methods=['POST'])
@login_required
@admin_required
def marcas_agregar():
    nombre = request.form.get('nombre', '').strip()
    if nombre and not Marca.query.filter_by(nombre=nombre).first():
        m = Marca(nombre=nombre)
        db.session.add(m)
        db.session.commit()
        flash('Marca agregada.', 'success')
    else:
        flash('La marca ya existe o el nombre está vacío.', 'danger')
    return redirect(url_for('productos.marcas'))

@bp.route('/marcas/eliminar/<int:id>')
@login_required
@admin_required
def marcas_eliminar(id):
    m = Marca.query.get_or_404(id)
    if m.productos:
        flash('No se puede eliminar una marca con productos asociados.', 'danger')
    else:
        db.session.delete(m)
        db.session.commit()
        flash('Marca eliminada.', 'success')
    return redirect(url_for('productos.marcas'))
