from sqlalchemy.exc import IntegrityError
from app.api.utils import *
from app.models import *
from app.core import app


# ======================================================================================================================
# ==========> LAB METHODS <=============================================================================================
# ======================================================================================================================


@app.route('/api/labs', methods=['POST'])
@token_required
def create_lab(cu):
    # 1) Create a Lab
    # 2) Create and add Hosts
    try:
        lab = Lab.create(request.json)
        msg = "Laboratorio añadido correctamente"
        code = 200
    except Exception as e:
        if isinstance(e, KeyError):
            msg = "Ha ocurrido un error al añadir el laboratorio - Faltan parámetros"
            code = 400
        elif isinstance(e, IntegrityError):
            msg = "Ha ocurrido un error al añadir el laboratorio - Se ha violado una restricción de integridad"
            code = 400
        else:
            msg = "Ha ocurrido un error al añadir el laboratorio - " + str(e)
            code = 500
        return json_response(msg, code)

    try:
        ip_range = ip_range_to_list(lab.start_ip_range, lab.end_ip_range)
        for ip in ip_range:
            data = dict(code=lab.code+'_'+str(ip_range.index(ip)),
                        ip_address=ip,
                        conn_user='root',
                        lab_uuid=lab.uuid)
            Host.create(data)
    except Exception as e:
        if isinstance(e, KeyError):
            msg = "Ha ocurrido un error al añadir un host al laboratorio "+lab.code+" - Faltan parámetros"
            code = 400
        elif isinstance(e, IntegrityError):
            msg = "Ha ocurrido un error al añadir un host al laboratorio "+lab.code+" - Se ha violado una " \
                                                                                    "restricción de integridad"
            code = 400
        else:
            msg = "Ha ocurrido un error al añadir un host al laboratorio "+lab.code+" - " + str(e)
            code = 500
    return json_response(msg, code)


@app.route('/api/labs', methods=['GET'])
@token_required
def get_labs(cu):
    try:
        labs = Lab.get()
        msg = [l.to_dict() for l in labs]
        code = 200
    except Exception as e:
        msg = 'Ha ocurrido un error al obtener los laboratorios - ' + str(e)
        code = 500
    return json_response(msg, code)


@app.route('/api/labs/<lab_uuid>', methods=['DELETE'])
@token_required
def delete_lab(cu, lab_uuid):
    lab = Lab.get(lab_uuid)
    try:
        Lab.delete(lab)
        msg = "Laboratorio eliminado correctamente"
        code = 200
    except Exception as e:
        msg = "No existe el laboratorio seleccionado - " + str(e)
        code = 400
    return json_response(msg, code)
