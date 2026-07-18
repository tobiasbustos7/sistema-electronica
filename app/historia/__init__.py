from flask import Blueprint
bp = Blueprint('historia', __name__)
from app.historia import routes
