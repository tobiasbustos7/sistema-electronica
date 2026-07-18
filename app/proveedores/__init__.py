from flask import Blueprint
bp = Blueprint('proveedores', __name__)
from app.proveedores import routes
