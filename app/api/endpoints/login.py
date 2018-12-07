from app.api.utils import json_response
from flask import request
from app.core import app, logger
from datetime import *
import jwt
import pam


@app.route('/api/login', methods=['GET'])
def login():
    logger.debug('Autenticando usuario')
    try:
        auth = request.authorization
        if not auth or not auth.username or not auth.password:
            logger.error('No se ha podido autenticar al usuario: faltan las credenciales!')
            return json_response(status=400)

        p = pam.pam()
        # user = p.authenticate(username=auth.username, password=auth.password, service='dvls')
        user = p.authenticate(username=auth.username, password=auth.password)

        if user and (auth.username == app.config['CONN_USER']):
            token = jwt.encode(dict(username=auth.username, exp=datetime.utcnow() + timedelta(minutes=60)),
                               app.config['SECRET_KEY'])
            return json_response(data=dict(token=token.decode('UTF-8')))

        logger.error('No se ha podido autenticar al usuario: las credenciales son incorrectas!')
        return json_response(status=403)
    except Exception as e:
        logger.error('No se ha podido autenticar al usuario: %s', str(e))
        return json_response(status=500)
