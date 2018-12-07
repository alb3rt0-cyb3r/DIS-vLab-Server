import subprocess
import paramiko
import libvirt
import pickle
from app.api.utils import *
from app.models import *
from app.core import app, logger


# ======================================================================================================================
# ==========> TEMPLATE METHODS <========================================================================================
# ======================================================================================================================

# (C) Create a template from domain
@app.route('/api/templates', methods=['POST'])
@token_required
def create_template(cu):
    logger.info('Creando plantilla')
    try:
        domain_uuid = request.json['domain_uuid']
        template_name = request.json['template_name']
        template_description = request.json['template_description']
        do_sysprep = request.json['do_sysprep']

        # Check domain state
        conn = libvirt.open(app.config['LOCAL_QEMU_URI'])
        domain = conn.lookupByUUIDString(domain_uuid)
        if domain.isActive():
            logger.error('No se pudo crear la plantilla: el dominio debe estar apagado')
            return json_response(status=400)

        # Domain cloning (get disks paths and some hardware stuff)
        info = domain.info()
        memory = info[2]
        vcpus = info[3]

        xml = ET.fromstring(domain.XMLDesc())
        devices = xml.findall('devices/disk')
        disks = list()
        for d in devices:
            if d.get('device') == 'disk':
                file_path = d.find('source').get('file')
                disks.append(file_path)

        cmd = ['virt-clone',
               '--connect', app.config['LOCAL_QEMU_URI'],
               '--original', domain.name(),
               '--name', template_name]
        template_images_path = list()
        for count in range(disks.__len__()):
            template_image_path = app.config['TEMPLATE_IMAGES_DIR'] + template_name + '-disk' + str(count) + '.qcow2'
            template_images_path.append(template_image_path)
            cmd.append('--file')
            cmd.append(template_image_path)
        subprocess.check_call(cmd)

        if do_sysprep:
            # Decontextualize the template and dumps XML --> USING POLICYKIT WITH 'virt-sysprep'
            subprocess.check_call(['pkexec', '/usr/bin/virt-sysprep',
                                   '--connect', app.config['LOCAL_QEMU_URI'],
                                   '--domain', template_name])
        template_xml = str(app.config['TEMPLATE_DEFINITIONS_DIR'] + template_name + '.xml')
        proc = subprocess.Popen(['virsh', '--connect', app.config['LOCAL_QEMU_URI'], 'dumpxml', template_name],
                                stdout=subprocess.PIPE)
        out = proc.stdout.read().decode('utf-8')
        # print(out)

        file = open(str(template_xml), 'w')
        file.write(out)
        file.close()

        # Undefine template
        template = conn.lookupByName(template_name)
        template.undefine()

        # Add template to database

        data = dict(name=template_name,
                    description=template_description,
                    vcpus=vcpus,
                    memory=memory,
                    xml_path=template_xml,
                    images_path=template_images_path)
        template = Template(data)
        template.save()
        return json_response()
    except Exception as e:
        # TODO - Delete template on fs if Exception is instance of sqlite3.OperationalError
        logger.error('No se pudo crear la plantilla: %s', str(e))
        return json_response(status=500)


# (R) Get all templates
@app.route('/api/templates', methods=['GET'])
@token_required
def get_templates(cu):
    logger.info('Obteniendo plantillas')
    try:
        templates = Template.get()
        data = [t.to_dict() for t in templates]
        return json_response(data=data)
    except Exception as e:
        logger.error('No se pudo obtener las plantillas: %s', str(e))
        return json_response(status=500)


# (D) Delete a template
@app.route('/api/templates/<template_uuid>', methods=['DELETE'])
@token_required
def delete_template(cu, template_uuid):
    logger.info('Eliminando plantilla')
    try:
        template = Template.get(template_uuid)
        for image_path in pickle.loads(template.images_path):
            subprocess.check_call(['rm', '-f', image_path])
        subprocess.check_call(['rm', '-f', template.xml_path])
        Template.delete(template)
        return json_response()
    except Exception as e:
        logger.error('No se pudo eliminar la plantilla: %s', str(e))
        return json_response(status=500)


# Clone template into domain, in other words, it generates a new domain from a template
@app.route('/api/templates/<template_uuid>', methods=['POST'])
@token_required
def clone_template(cu, template_uuid):
    logger.info('Desplegando plantilla')
    try:
        template = Template.get(template_uuid).to_dict()
        domain_name = request.json['domain_name']
        lab_uuid = request.json['lab_uuid']

        lab = Lab.get(lab_uuid)
        hosts = lab.hosts

        if hosts.__len__() == 0:
            logger.error('El laboratorio no tiene ningún host asociado')
            return json_response(status=500)

        cmd = ['virt-clone',
               '--connect', app.config['LOCAL_QEMU_URI'],
               '--original-xml', template['xml_path'],
               '--name', domain_name]

        for count in range(template['images_path'].__len__()):
            cmd.append('--file')
            cmd.append(app.config['DOMAIN_IMAGES_DIR'] + domain_name + '-disk' + str(count) + '.qcow2')

        ssh = paramiko.SSHClient()
        # Surrounds 'known_hosts' error
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        errors = list()
        for h in hosts:
            host = h.ip_address
            username = h.conn_user
            try:
                # NO PASSWORD!! Server SSH key is previously distributed among lab PCs
                ssh.connect(hostname=host.compressed, username=username, timeout=4)
                ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(' '.join(cmd))
                errors = [b.rstrip() for b in ssh_stderr.readlines()]
                if len(errors) > 0:
                    logger.error('No se pudo desplegar la plantilla en el host %s (%s)', h.code, h.ip_address.compressed)
                    logger.error(e for e in errors)
            except Exception as e:
                logger.error('No se pudo desplegar la plantilla en el host %s (%s): %s', h.code, h.ip_address.compressed, str(e))
                errors = True
            finally:
                ssh.close()
        if errors or len(errors) > 0:
            return json_response(status=500)
        return json_response()
    except Exception as e:
        logger.error('No se pudo desplegar la plantilla: %s', str(e))
        return json_response(status=500)
