from app.api.utils import *
from app.models import *
from app.core import app


# ======================================================================================================================
# ==========> HOST METHODS <============================================================================================
# ======================================================================================================================

@app.route('/api/hosts', methods=['POST'])
@token_required
def add_host(cu):
    try:
        Host.create(request.json)
        msg = 'Host añadido correctamente'
        code = 200
    except Exception as e:
        msg = 'Ha ocurrido un error al añadir el host' + str(e)
        code = 500
    return json_response(msg, code)


@app.route('/api/hosts', methods=['GET'])
@token_required
def get_hosts(cu):
    hosts = Host.all()
    return json_response([h.to_dict() for h in hosts], 200)


@app.route('/api/hosts/<host_uuid>', methods=['GET'])
@token_required
def get_host(cu, host_uuid):
    host = Host.get(host_uuid)
    conn = libvirt.open('qemu+ssh://'+host.user+'@'+host.hostname+'/system?socket=/var/run/libvirt/libvirt-sock')
    msg = get_host_details(conn)
    conn.close()
    code = 200
    return json_response(msg, code)


@app.route('/api/hosts/<host_uuid>', methods=['DELETE'])
@token_required
def delete_host(cu, host_uuid):
    host = Host.get(host_uuid)
    Host.delete(host)
    msg = 'Host eliminado correctamente'
    code = 200
    return json_response(msg, code)


def get_host_details(conn):
    host_info = conn.getInfo()
    hostname = conn.getHostname()

    sys_info = ET.fromstring(conn.getSysinfo())
    model = None
    for entry in sys_info.find('system'):
        if entry.get('name') == 'product':
            model = entry.text

    cpu = dict(arch=host_info[0],
               cpus=host_info[2],
               freq=host_info[3],
               numa_nodes=host_info[4],
               sockets_per_node=host_info[5],
               cores_per_socket=host_info[6],
               threads_per_core=host_info[7])

    mem_total = round(host_info[1] / 1024, 2)
    mem_free = round(conn.getFreeMemory() / 1024000000, 2)
    mem_used = round(mem_total - mem_free, 2)
    mem_load = round((mem_used * 100) / mem_total)
    memory = dict(total=mem_total, free=mem_free, used=mem_used, load=mem_load)

    domains = dict(total=len(conn.listAllDomains()), active=len(conn.listDomainsID()))

    return dict(hostname=hostname, model=model, cpu=cpu, memory=memory, domains=domains)
