from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from .config import Config
import logging
import logging.config


def configure_logger(name, log_path):
    logging.config.dictConfig({
        'version': 1,
        'formatters': {
            'default': {'format': '%(asctime)s - [%(levelname)s] - %(message)s', 'datefmt': '%Y-%m-%d %H:%M:%S'}
        },
        'handlers': {
            'file': {
                'level': 'DEBUG',
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'default',
                'filename': log_path
            }
        },
        'loggers': {
            'default': {
                'level': 'DEBUG',
                'handlers': ['file']
            }
        },
        'disable_existing_loggers': False
    })
    return logging.getLogger(name)


logger = configure_logger('default', 'dvls.log')
logger.debug('Inicializando aplicación')
app = Flask(__name__, static_folder='../static')
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
CORS(app, supports_credentials=True)

from app.models import models
from app.api import api

# IMPORTANT!! Comment below lines to make database migrations and upgrades
if not models.Config.is_initialized():
    logger.debug('Cargando configuración con valores por defecto')
    models.Config.init()
logger.debug('Cargando configuración')
app.config.update(models.Config.get())
