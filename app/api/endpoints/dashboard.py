from .hosts import get_host_details
from app.models import Template, Lab
from app.api.utils import *
from app.core import app
import libvirt

# ======================================================================================================================
# ==========> DASHBOARD METHODS <=======================================================================================
# ======================================================================================================================


@app.route('/api/dashboard', methods=['GET'])
def get_dashboard():
    try:
        conn = libvirt.open(app.config['LOCAL_QEMU_URI'])
        host_info = get_host_details(conn)
        host_info['templates'] = len(Template.get())
        host_info['labs'] = len(Lab.get())
        conn.close()
        msg = host_info
        code = 200
    except Exception as ex:
        msg = 'Ha ocurrido un error inesperado - '+libvirt.virGetLastErrorMessage()
        code = 500

    return json_response(msg, code)
