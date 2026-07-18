from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date

# --------------- Roles ---------------
class Rol(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    descripcion = db.Column(db.String(200))
    usuarios = db.relationship('Usuario', backref='rol', lazy=True)

    @staticmethod
    def inicializar_roles():
        roles = ['Administrador', 'Vendedor']
        for r in roles:
            if not Rol.query.filter_by(nombre=r).first():
                db.session.add(Rol(nombre=r, descripcion=f'Rol {r}'))
        db.session.commit()

# --------------- Usuarios ---------------
class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    activo = db.Column(db.Boolean, default=True)
    rol_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    ultimo_acceso = db.Column(db.DateTime)
    fecha_creacion = db.Column(db.DateTime, default=datetime.now)

    ventas = db.relationship('Venta', backref='usuario', lazy=True)
    compras = db.relationship('Compra', backref='usuario', lazy=True)
    historial = db.relationship('Historial', backref='usuario', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def es_admin(self):
        return self.rol and self.rol.nombre == 'Administrador'

    @staticmethod
    def crear_admin_default():
        admin_rol = Rol.query.filter_by(nombre='Administrador').first()
        if admin_rol and not Usuario.query.filter_by(username='admin').first():
            u = Usuario(
                username='admin',
                nombre='Administrador',
                email='admin@sistema.com',
                rol_id=admin_rol.id,
                activo=True
            )
            u.set_password('admin123')
            db.session.add(u)
            db.session.commit()

    def __repr__(self):
        return f'<Usuario {self.username}>'

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# --------------- Categorias ---------------
class Categoria(db.Model):
    __tablename__ = 'categorias'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    descripcion = db.Column(db.String(255))
    productos = db.relationship('Producto', backref='categoria', lazy=True)

    def __repr__(self):
        return self.nombre

# --------------- Marcas ---------------
class Marca(db.Model):
    __tablename__ = 'marcas'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    productos = db.relationship('Producto', backref='marca', lazy=True)

    def __repr__(self):
        return self.nombre

# --------------- Proveedores ---------------
class Proveedor(db.Model):
    __tablename__ = 'proveedores'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    empresa = db.Column(db.String(100))
    ruc = db.Column(db.String(50))
    telefono = db.Column(db.String(50))
    correo = db.Column(db.String(100))
    direccion = db.Column(db.String(255))
    ciudad = db.Column(db.String(100))
    observaciones = db.Column(db.Text)
    fecha_registro = db.Column(db.DateTime, default=datetime.now)
    productos = db.relationship('Producto', backref='proveedor', lazy=True)
    compras = db.relationship('Compra', backref='proveedor', lazy=True)

    def __repr__(self):
        return f'{self.nombre} - {self.empresa}'

# --------------- Productos ---------------
class Producto(db.Model):
    __tablename__ = 'productos'
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True, nullable=False)
    nombre = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id'))
    marca_id = db.Column(db.Integer, db.ForeignKey('marcas.id'))
    precio_compra = db.Column(db.Numeric(12, 0), default=0)
    precio_venta = db.Column(db.Numeric(12, 0), default=0)
    stock = db.Column(db.Integer, default=0)
    stock_minimo = db.Column(db.Integer, default=10)
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedores.id'))
    codigo_barras = db.Column(db.String(100))
    imagen = db.Column(db.String(255))
    estado = db.Column(db.String(20), default='Disponible')
    fecha_creacion = db.Column(db.DateTime, default=datetime.now)
    ubicacion = db.Column(db.String(100))

    detalles_venta = db.relationship('DetalleVenta', backref='producto', lazy=True)
    detalles_compra = db.relationship('DetalleCompra', backref='producto', lazy=True)

    @property
    def ganancia(self):
        return float(self.precio_venta or 0) - float(self.precio_compra or 0)

    @property
    def estado_stock(self):
        if self.stock <= 0:
            return 'sin_stock'
        elif self.stock <= self.stock_minimo:
            return 'poco_stock'
        return 'con_stock'

    def __repr__(self):
        return f'{self.codigo} - {self.nombre}'

# --------------- Clientes ---------------
class Cliente(db.Model):
    __tablename__ = 'clientes'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100))
    ci = db.Column(db.String(50))
    ruc = db.Column(db.String(50))
    telefono = db.Column(db.String(50))
    correo = db.Column(db.String(100))
    direccion = db.Column(db.String(255))
    fecha_nac = db.Column(db.Date)
    observaciones = db.Column(db.Text)
    total_gastado = db.Column(db.Numeric(12, 0), default=0)
    ultima_compra = db.Column(db.DateTime)
    fecha_registro = db.Column(db.DateTime, default=datetime.now)
    ventas = db.relationship('Venta', backref='cliente', lazy=True)

    @property
    def nombre_completo(self):
        return f'{self.nombre} {self.apellido or ""}'.strip()

    def __repr__(self):
        return self.nombre_completo

# --------------- Compras ---------------
class Compra(db.Model):
    __tablename__ = 'compras'
    id = db.Column(db.Integer, primary_key=True)
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedores.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    total = db.Column(db.Numeric(12, 0), default=0)
    fecha = db.Column(db.DateTime, default=datetime.now)
    observaciones = db.Column(db.Text)
    detalles = db.relationship('DetalleCompra', backref='compra', lazy=True, cascade='all, delete-orphan')

class DetalleCompra(db.Model):
    __tablename__ = 'detalle_compra'
    id = db.Column(db.Integer, primary_key=True)
    compra_id = db.Column(db.Integer, db.ForeignKey('compras.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Numeric(12, 0), nullable=False)
    subtotal = db.Column(db.Numeric(12, 0), nullable=False)

# --------------- Ventas ---------------
class Venta(db.Model):
    __tablename__ = 'ventas'
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    subtotal = db.Column(db.Numeric(12, 0), default=0)
    descuento = db.Column(db.Numeric(12, 0), default=0)
    total = db.Column(db.Numeric(12, 0), default=0)
    metodo_pago = db.Column(db.String(50), default='Efectivo')
    monto_efectivo = db.Column(db.Numeric(12, 0), default=0)
    monto_tarjeta = db.Column(db.Numeric(12, 0), default=0)
    monto_transferencia = db.Column(db.Numeric(12, 0), default=0)
    monto_qr = db.Column(db.Numeric(12, 0), default=0)
    vuelto = db.Column(db.Numeric(12, 0), default=0)
    fecha = db.Column(db.DateTime, default=datetime.now)
    factura_numero = db.Column(db.String(50), unique=True)
    estado = db.Column(db.String(20), default='Completada')
    detalles = db.relationship('DetalleVenta', backref='venta', lazy=True, cascade='all, delete-orphan')

class DetalleVenta(db.Model):
    __tablename__ = 'detalle_venta'
    id = db.Column(db.Integer, primary_key=True)
    venta_id = db.Column(db.Integer, db.ForeignKey('ventas.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Numeric(12, 0), nullable=False)
    subtotal = db.Column(db.Numeric(12, 0), nullable=False)

# --------------- Caja ---------------
class Caja(db.Model):
    __tablename__ = 'caja'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id_apertura = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    usuario_id_cierre = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    monto_inicial = db.Column(db.Numeric(12, 0), default=0)
    total_ventas = db.Column(db.Numeric(12, 0), default=0)
    total_gastos = db.Column(db.Numeric(12, 0), default=0)
    dinero_esperado = db.Column(db.Numeric(12, 0), default=0)
    dinero_contado = db.Column(db.Numeric(12, 0), default=0)
    diferencia = db.Column(db.Numeric(12, 0), default=0)
    fecha_apertura = db.Column(db.DateTime, default=datetime.now)
    fecha_cierre = db.Column(db.DateTime)
    estado = db.Column(db.String(20), default='Abierta')
    movimientos = db.relationship('MovimientoCaja', backref='caja', lazy=True, cascade='all, delete-orphan')

class MovimientoCaja(db.Model):
    __tablename__ = 'movimientos_caja'
    id = db.Column(db.Integer, primary_key=True)
    caja_id = db.Column(db.Integer, db.ForeignKey('caja.id'), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)
    descripcion = db.Column(db.String(255))
    monto = db.Column(db.Numeric(12, 0), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.now)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)

# --------------- Configuracion ---------------
class Configuracion(db.Model):
    __tablename__ = 'configuracion'
    id = db.Column(db.Integer, primary_key=True)
    clave = db.Column(db.String(100), unique=True, nullable=False)
    valor = db.Column(db.Text)

    @staticmethod
    def get(clave, default=''):
        conf = Configuracion.query.filter_by(clave=clave).first()
        return conf.valor if conf else default

    @staticmethod
    def set(clave, valor):
        conf = Configuracion.query.filter_by(clave=clave).first()
        if conf:
            conf.valor = valor
        else:
            conf = Configuracion(clave=clave, valor=valor)
            db.session.add(conf)
        db.session.commit()

# --------------- Historial ---------------
class Historial(db.Model):
    __tablename__ = 'historial'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    accion = db.Column(db.String(100), nullable=False)
    entidad = db.Column(db.String(50))
    entidad_id = db.Column(db.Integer)
    detalle = db.Column(db.Text)
    ip = db.Column(db.String(50))
    fecha = db.Column(db.DateTime, default=datetime.now)

    @staticmethod
    def registrar(usuario_id, accion, entidad=None, entidad_id=None, detalle=None, ip=None):
        h = Historial(
            usuario_id=usuario_id,
            accion=accion,
            entidad=entidad,
            entidad_id=entidad_id,
            detalle=detalle,
            ip=ip
        )
        db.session.add(h)
        db.session.commit()
