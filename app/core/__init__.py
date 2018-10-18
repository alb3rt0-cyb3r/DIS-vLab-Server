from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from .config import Config


app = Flask(__name__, static_folder='../static')
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
CORS(app, supports_credentials=True)

from app.models import models
from app.api import api

# IMPORTANT!! Comment below lines to make database migrations and upgrades
if not models.Config.is_initialized():
    models.Config.init()
