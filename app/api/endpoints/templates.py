import subprocess
import paramiko
import libvirt
import pickle
import time
from app.api.utils import *
from app.models import *
from app.core import app


# ======================================================================================================================
# ==========> TEMPLATE METHODS <========================================================================================
# ======================================================================================================================

# (C) Create a template from domain
@app.route('/api/templates', methods=['POST'])
@token_required
def create_template(cu):
    domain_uuid = request.json['domain_uuid']
    template_name = request.json['template_name']
    template_description = request.json['template_description']

    # Check domain state
    conn = libvirt.open(app.config['LOCAL_QEMU_URI'])
    domain = conn.lookupByUUIDString(domain_uuid)
    if domain.isActive():
        return json_response('El dominio debe estar apagado', 500)

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

    # Decontextualize the template and dumps XML --> USING POLICYKIT WITH 'virt-sysprep'
    subprocess.check_call(['pkexec', '/usr/bin/virt-sysprep',
                           '--connect', app.config['LOCAL_QEMU_URI'],
                           '--domain', template_name])
    template_xml = str(app.config['TEMPLATE_DEFINITIONS_DIR'] + template_name + '.xml')
    proc = subprocess.Popen(['virsh', '--connect', app.config['LOCAL_QEMU_URI'], 'dumpxml', template_name],
                            stdout=subprocess.PIPE)
    out = proc.stdout.read().decode('utf-8')
    print(out)

    file = open(str(template_xml), 'w')
    file.write(out)
    file.close()

    # Delete base domain (and disks?) --> TODO - Make it in an option inside wizard
    # domain.undefine()

    # Undefine template
    template = conn.lookupByName(template_name)
    template.undefine()

    # Add template to database
    try:
        Template.create(dict(name=template_name,
                             description=template_description,
                             vcpus=vcpus,
                             memory=memory,
                             xml_path=template_xml,
                             images_path=template_images_path))
        msg = "La plantilla se ha generado correctamente"
        code = 200
    except Exception as e:
        msg = "Ha ocurrido un error al generar la plantilla - " + str(e)
        code = 400
    return json_response(msg, code)


# (R) Get all templates
@app.route('/api/templates', methods=['GET'])
@token_required
def get_templates(cu):
    try:
        templates = Template.get()
        msg = [t.to_dict() for t in templates]
        code = 200
    except Exception as e:
        msg = 'Ha ocurrido un error al obtener las plantillas - ' + str(e)
        code = 500
    return json_response(msg, code)


# (U) Update a template
@app.route('/api/templates/<template_uuid>', methods=['PUT'])
@token_required
def update_template(cu, template_uuid):
    # TODO - Implement this method
    return


# (D) Delete a template
@app.route('/api/templates/<template_uuid>', methods=['DELETE'])
@token_required
def delete_template(cu, template_uuid):
    template = Template.get(template_uuid)

    for image_path in pickle.loads(template.images_path):
        subprocess.check_call(['rm', '-f', image_path])
    subprocess.check_call(['rm', '-f', template.xml_path])
    Template.delete(template)
    return json_response('Plantilla eliminada correctamente', 200)


# Clone template into domain, in other words, it generates a new domain from a template
@app.route('/api/templates/<template_uuid>', methods=['POST'])
@token_required
def clone_template(cu, template_uuid):
    # TODO - Add optional params to virt-clone (?)
    # TODO - Check if lab or localhost deployment
    try:
        template = Template.get(template_uuid).to_dict()
        domain_name = request.json['domain_name']
        lab_uuid = request.json['lab_uuid']
        lab = Lab.get(lab_uuid)
        hosts = lab.hosts

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
        if hosts.__len__() == 0:
            msg = 'El laboratorio no tiene ningún host asociado'
            code = 401
            return json_response(msg, code)
        for h in hosts:
            host = h.ip_address
            username = h.conn_user
            print('--> host,username: ', host, ' -- ', username)
            # NO PASSWORD!! Server SSH key is previously distributed among lab PCs
            try:
                ssh.connect(str(host), username=str(username))
                # TODO - Study how to get ssh_stdout/ssh_stderror output
                ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(' '.join(cmd))
                msg = 'virt-clone llamado correctamente'
                code = 200
            except paramiko.ssh_exception.AuthenticationException as e:
                msg = 'Ha ocurrido un error al llamar a virt-clone: ' + str(e)
                code = 500
            # ssh.close()
    except Exception as e:
        msg = 'Ha ocurrido un error inesperado - ' + str(e)
        code = 500
    return json_response(msg, code)
