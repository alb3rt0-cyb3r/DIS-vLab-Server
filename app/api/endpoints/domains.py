from app.api.utils import *
from app.core import app
import subprocess
import libvirt
import time

# ======================================================================================================================
# ==========> DOMAINS METHODS <=========================================================================================
# ======================================================================================================================


# (C) Create new domain using virt-install
@app.route('/api/domains', methods=['POST'])
@token_required
def create_domain(cu):
    try:
        data = request.json
        cmd = ['virt-install',
               '--connect', app.config['LOCAL_QEMU_URI'],
               '--name', data['name'],
               '--memory', str(data['memory']),
               '--vcpus', str(data['vcpus']),
               '--os-variant', data['os_variant'],
               '--noautoconsole']
        if data['graphics']['vnc']:
            cmd.append('--graphics')
            cmd.append('vnc,listen='+data['graphics']['listen']+',password='+data['graphics']['password'])
        if data['installation_type'] == "iso":
            cmd.append('--disk')
            cmd.append('size='+str(data['disk']['size']))
            cmd.append('--cdrom')
            cmd.append(data['cdrom'])
        elif data['installation_type'] == "image":
            cmd.append('--disk')
            cmd.append(data['disk']['path'])
            cmd.append('--import')
        elif data['installation_type'] == "network":
            cmd.append('--disk')
            cmd.append('size='+str(data['disk']['size']))
            cmd.append('--location')
            cmd.append(data['location'])
        elif data['installation_type'] == "pxe":
            cmd.append('--disk')
            cmd.append('size='+str(data['disk']['size']))
            cmd.append('--network')
            cmd.append(data['network'])
            cmd.append('--pxe')
        else:
            msg = "El tipo de instalación no es correcto"
            code = 422
            return json_response(msg, code)
        subprocess.check_call(cmd)
        msg = "La orden se ha ejecutado correctamente"
        code = 200
    except Exception as e:
        msg = "Ha ocurrido un error inesperado - " + str(e)
        code = 500
    return json_response(msg, code)


# (R) LIST ALL DOMAINS
@app.route('/api/domains', methods=['GET'])
@token_required
def get_all_domains(cu, conn=None):
    # TODO - Check what VMs data sends
    try:
        if conn is None:
            conn = libvirt.open(app.config['LOCAL_QEMU_URI'])
        domains = conn.listAllDomains()
        domains_dict = []
        for dom in domains:
            is_active = True if dom.isActive() == 1 else False
            uuid = dom.UUIDString()
            name = dom.name()
            os_type = dom.OSType()
            total_memory = round(dom.info()[1] / 1024, 2)  # KByte to MByte
            used_memory = "-" if not is_active else round(dom.info()[2] / 1024, 2)  # KByte to MByte
            memory = dict(total=total_memory, used=used_memory)
            vcpus = dom.info()[3]
            state = dom.info()[0]
            vnc_port = get_vnc_port(dom)

            domains_dict.append(dict(uuid=uuid,
                                     name=name,
                                     is_active=is_active,
                                     os_type=os_type,
                                     memory=memory,
                                     vcpus=vcpus,
                                     state=state,
                                     vnc_port=vnc_port))
        conn.close()
        msg = domains_dict
        code = 200
    except Exception as e:
        msg = "Ha ocurrido un error al obtener los dominios - " + str(e)
        code = 500

    return json_response(msg, code)


# (U) UPDATE A DOMAIN DESCRIBED BY NAME
@app.route('/api/domains/<domain_name>', methods=['PUT'])
@token_required
def update_domain(cu, domain_name):
    # TODO - Update VM 'vm_name'
    return


# ##################################### #
# (D) DELETE A DOMAIN DESCRIBED BY NAME #
# 1) Look for domain disk devices       #
# 2) Remove disk devices from the fs    #
# 3) Undefine domain                    #
# ##################################### #
@app.route('/api/domains/<domain_uuid>', methods=['DELETE'])
@token_required
def delete_domain(cu, domain_uuid):
    try:
        delete_disks = True
        # delete_disks = request.json['delete_disks']
        conn = libvirt.open(app.config['LOCAL_QEMU_URI'])
        domain = conn.lookupByUUIDString(domain_uuid)
        if delete_disks:
            xml = ET.fromstring(domain.XMLDesc())
            devices = xml.findall('devices/disk')
            for d in devices:
                if d.get('device') == 'disk':
                    file_path = d.find('source').get('file')
                    disk = conn.storageVolLookupByPath(file_path)
                    disk.delete(libvirt.VIR_STORAGE_VOL_DELETE_NORMAL)
        domain.undefine()
        msg = 'Dominio eliminado correctamente'
        code = 200
    except Exception as e:
        msg = 'Ha ocurrido un error al eliminar el dominio - ' + str(e)
        code = 500
    return json_response(msg, code)


# START A DOMAIN DESCRIBED BY NAME
@app.route('/api/domains/<domain_uuid>/start', methods=['PUT'])
@token_required
def start_domain(cu, domain_uuid):
    conn = libvirt.open(app.config['LOCAL_QEMU_URI'])
    domain = conn.lookupByUUIDString(domain_uuid)
    domain.create()
    time.sleep(3)
    domain = conn.lookupByUUIDString(domain_uuid)
    if domain.info()[0] == libvirt.VIR_DOMAIN_RUNNING:
        msg = "Dominio encendido correctamente"
        code = 200
    else:
        msg = "Ha ocurrido un error al encender el dominio"
        code = 500
    return json_response(msg, code)


# REBOOT A DOMAIN DESCRIBED BY NAME
# TODO - Check if it has really rebooted
@app.route('/api/domains/<domain_uuid>/reboot', methods=['PUT'])
@token_required
def reboot_domain(cu, domain_uuid):
    try:
        conn = libvirt.open(app.config['LOCAL_QEMU_URI'])
        domain = conn.lookupByUUIDString(domain_uuid)
        domain.reboot(libvirt.VIR_DOMAIN_REBOOT_DEFAULT)
        time.sleep(3)
        msg = 'Dominio reiniciado correctamente'
        code = 200
    except Exception:
        msg = 'Ha ocurrido un error inesperado - '+libvirt.virGetLastErrorMessage()
        code = 500
    return json_response(msg, code)


# SHUTDOWN A DOMAIN DESCRIBED BY NAME
@app.route('/api/domains/<domain_uuid>/shutdown', methods=['PUT'])
@token_required
def shutdown_domain(cu, domain_uuid):
    conn = libvirt.open(app.config['LOCAL_QEMU_URI'])
    domain = conn.lookupByUUIDString(domain_uuid)
    domain.destroy()
    time.sleep(3)
    domain = conn.lookupByUUIDString(domain_uuid)
    if domain.info()[0] == libvirt.VIR_DOMAIN_SHUTOFF:
        msg = 'Dominio apagado correctamente'
        code = 200
    else:
        msg = 'Ha ocurrido un error al apagar el dominio'
        code = 500
    return json_response(msg, code)
