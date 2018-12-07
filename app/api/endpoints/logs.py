from app.api.utils import *
from app.core import app, logger


@app.route('/api/logs', methods=['GET'])
@token_required
def get_logs(cu):
    try:
        with open('dvls.log', 'r') as f:
            log = f.readlines()
        return json_response(data=log)
    except Exception as e:
        logger.error('No se ha podido leer el fichero de logs: %s', str(e))
        return json_response(status=500)


@app.route('/api/logs', methods=['DELETE'])
@token_required
def clear_logs(cu):
    logger.info('Limpiando el fichero de logs')
    try:
        logs_file = open('dvls.log', 'w')
        logs_file.truncate()
        logs_file.close()
        return json_response()
    except Exception as e:
        logger.error('No se ha podido limpiar el fichero de logs: %s', str(e))
        return json_response(status=500)
