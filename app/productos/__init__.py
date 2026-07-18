from flask import Blueprint
bp = Blueprint('productos', __name__)
from app.productos import routes
