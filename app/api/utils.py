import os
import sys
import jwt
from flask import Response, json, request
from xml.etree import ElementTree as ET
from functools import wraps
from app.core import app, logger


# ########################## #
# >>>> Useful functions <<<< #
# ########################## #


# Returns a HTML response with json content
def json_response(data=None, status=200):
    if data is None and status != 200:
        data = "Se ha producido un error. Consulte el registro de logs."
    return Response(json.dumps(data,
                               sort_keys=True,
                               indent=4,
                               ensure_ascii=False,
                               separators=(',', ': ')) if data else None,
                    mimetype="text/json",
                    status=status)


# Get VNC port for an active domain
def get_vnc_port(domain):
    xml = domain.XMLDesc()
    root = ET.fromstring(xml)
    graphics = root.find('./devices/graphics')
    return graphics.get('port')


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'JWT-Token' in request.headers:
            token = request.headers['JWT-Token']
            if not token:
                logger.error('No se ha encontrado el token de sesión en las cabeceras')
                return json_response(status=401)
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
            current_user = data['username']
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            logger.error('El token de sesión no es válido o ha caducado')
            return json_response(status=401)
        return f(current_user, *args, **kwargs)
    return decorated


# Returns a list with the IPAddresses included in the range
def ip_range_to_list(start, end):
    ip_set = list()
    while start <= end:
        ip_set.append(start)
        start += 1
    return ip_set
