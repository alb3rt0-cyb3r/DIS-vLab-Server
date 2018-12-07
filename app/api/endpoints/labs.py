from app.api.utils import *
from app.models import *
from app.core import app, logger


# ======================================================================================================================
# ==========> LAB METHODS <=============================================================================================
# ======================================================================================================================


@app.route('/api/labs', methods=['POST'])
@token_required
def create_lab(cu):
    logger.info('Añadiendo laboratorio')
    try:
        lab = Lab(request.json)
        ip_range = ip_range_to_list(lab.start_ip_range, lab.end_ip_range)
        for ip in ip_range:
            data = dict(code=lab.code+'_'+str(ip_range.index(ip)),
                        ip_address=ip,
                        conn_user='root',
                        lab_uuid=lab.uuid)
            lab.add_host(Host(data))
        lab.save()
        return json_response()
    except Exception as e:
        logger.error('No se pudo añadir el laboratorio: %s', str(e))
        return json_response(status=500)


@app.route('/api/labs', methods=['GET'])
@token_required
def get_labs(cu):
    logger.info('Obteniendo laboratorios')
    try:
        labs = Lab.get()
        data = [l.to_dict() for l in labs]
        return json_response(data=data)
    except Exception as e:
        logger.error('No se pudo obtener los laboratorios: %s', str(e))
        return json_response(status=500)


@app.route('/api/labs/<lab_uuid>', methods=['DELETE'])
@token_required
def delete_lab(cu, lab_uuid):
    logger.info('Eliminando laboratorio')
    try:
        lab = Lab.get(lab_uuid)
        Lab.delete(lab)
        return json_response()
    except Exception as e:
        logger.error('No se pudo eliminar el laboratorio seleccionado: %s', str(e))
        return json_response(status=500)
