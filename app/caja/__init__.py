from flask import Blueprint
bp = Blueprint('caja', __name__)
from app.caja import routes
