from app.api.utils import *
from app.models import *
from app.core import app, logger
import libvirt


# ======================================================================================================================
# ==========> HOST METHODS <============================================================================================
# ======================================================================================================================

@app.route('/api/hosts', methods=['POST'])
@token_required
def add_host(cu):
    logger.info('Añadiendo host')
    try:
        host = Host(request.json)
        host.save()
        return json_response()
    except Exception as e:
        logger.error('No se ha podido añadir el host: %s', str(e))
        return json_response(status=500)


@app.route('/api/hosts', methods=['GET'])
@token_required
def get_hosts(cu):
    logger.info('Obteniendo los hosts')
    try:
        hosts = Host.get()
        return json_response(data=[h.to_dict() for h in hosts])
    except Exception as e:
        logger.error('No se han podido obtener los hosts: %s', str(e))
        return json_response(status=500)


@app.route('/api/hosts/<host_uuid>', methods=['DELETE'])
@token_required
def delete_host(cu, host_uuid):
    logger.info('Eliminando host %s', host_uuid)
    try:
        host = Host.get(host_uuid)
        Host.delete(host)
        return json_response()
    except Exception as e:
        logger.error('No se ha podido eliminar el host %s: %s', host_uuid, str(e))


def get_host_details(conn):
    host_info = conn.getInfo()
    hostname = conn.getHostname()

    sys_info = ET.fromstring(conn.getSysinfo())
    manufacturer = None
    model = None
    for entry in sys_info.find('system'):
        if entry.get('name') == 'manufacturer':
            manufacturer = entry.text
        elif entry.get('name') == 'product':
            model = entry.text

    system = dict(manufacturer=manufacturer,
                  model=model,
                  hostname=hostname)

    cpu = dict(arch=host_info[0],
               cpus=host_info[2],
               freq=host_info[3],
               numa_nodes=host_info[4],
               sockets_per_node=host_info[5],
               cores_per_socket=host_info[6],
               threads_per_core=host_info[7])

    for entry in sys_info.find('processor'):
        if entry.get('name') == 'version':
            cpu['model'] = entry.text

    mem_total = round(host_info[1] / pow(10, 3), 2)  # MB to GB
    mem_free = round(conn.getFreeMemory() / pow(10, 9), 2)  # Bytes to GB
    mem_used = round(mem_total - mem_free, 2)
    mem_load = round((mem_used * 100) / mem_total)
    memory = dict(total=mem_total, free=mem_free, used=mem_used, load=mem_load)

    domains = dict(total=len(conn.listAllDomains()), active=len(conn.listDomainsID()))

    return dict(system=system, cpu=cpu, memory=memory, domains=domains)
