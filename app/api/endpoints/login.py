from app.api.utils import json_response
from flask import request
from app.core import app
from datetime import *
import jwt
import pam


@app.route('/api/login', methods=['GET'])
def login():
    auth = request.authorization
    if not auth or not auth.username or not auth.password:
        return json_response('No se han proporcionado las credenciales de autenticación.', 401)

    p = pam.pam()
    # user = p.authenticate(username=auth.username, password=auth.password, service='dvls')
    user = p.authenticate(username=auth.username, password=auth.password)

    if user and (auth.username == app.config['CONN_USER']):
        token = jwt.encode(dict(username=auth.username, exp=datetime.utcnow() + timedelta(minutes=60)),
                           app.config['SECRET_KEY'])
        return json_response(dict(token=token.decode('UTF-8')), 200)

    return json_response('Las credenciales son incorrectas.', 403)
