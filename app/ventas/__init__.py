from flask import Blueprint
bp = Blueprint('ventas', __name__)
from app.ventas import routes
