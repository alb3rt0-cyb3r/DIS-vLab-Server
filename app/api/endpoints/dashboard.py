from .hosts import get_host_details
from app.models import Template, Lab
from app.api.utils import *
from app.core import app, logger
import libvirt

# ======================================================================================================================
# ==========> DASHBOARD METHODS <=======================================================================================
# ======================================================================================================================


@app.route('/api/dashboard', methods=['GET'])
def get_dashboard():
    logger.info('Cargando dashboard')
    try:
        conn = libvirt.open(app.config['LOCAL_QEMU_URI'])
        host_info = get_host_details(conn)
        host_info['templates'] = len(Template.get())
        host_info['labs'] = len(Lab.get())
        conn.close()
        return json_response(data=host_info)
    except Exception as e:
        logger.error('No se pudo obtener el dashboard: %s', libvirt.virGetLastErrorMessage())
        return json_response(status=500)
