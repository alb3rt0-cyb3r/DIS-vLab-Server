import os
import sys
import jwt
from flask import Response, json, request
from xml.etree import ElementTree as ET
from functools import wraps
from app.core import app


# ########################## #
# >>>> Useful functions <<<< #
# ########################## #


# Returns a HTML response with json content
def json_response(data, status=200):
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
                return json_response(dict(type='danger', message='Cannot find the token!'), 401)
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
            current_user = data['username']
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            return json_response(dict(type='danger', message='The token is invalid!'), 401)
        return f(current_user, *args, **kwargs)
    return decorated
