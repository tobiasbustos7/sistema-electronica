from flask import Blueprint
bp = Blueprint('configuracion', __name__)
from app.configuracion import routes
