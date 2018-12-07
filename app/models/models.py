from sqlalchemy.orm.exc import UnmappedInstanceError
from sqlalchemy.exc import IntegrityError
from sqlalchemy_utils import UUIDType, IPAddressType
from datetime import datetime
from app.core import app, db
import ipaddress
import pickle
import uuid


class Config(db.Model):
    __tablename__ = 'config'
    id = db.Column(db.Integer, primary_key=True)
    local_qemu_uri = db.Column(db.String(255), nullable=False, default='qemu:///system')
    domain_images_dir = db.Column(db.String(255), nullable=False, default='/var/lib/libvirt/images/')
    template_images_dir = db.Column(db.String(255), nullable=False, default='/var/lib/dvls/images/')
    domain_definitions_dir = db.Column(db.String(255), nullable=False, default='/etc/libvirt/qemu/')
    template_definitions_dir = db.Column(db.String(255), nullable=False, default='/var/lib/dvls/qemu/')
    conn_user = db.Column(db.String(255), nullable=False, default='dvls')

    @staticmethod
    def init():
        try:
            config = Config()
            db.session.add(config)
            db.session.commit()
            app.config.update(config.to_dict())
        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def is_initialized():
        return True if Config.query.all().__len__() != 0 else False

    @staticmethod
    def get():
        return Config.query.all()[0].to_dict()

    def update(self, config):
        if 'LOCAL_QEMU_URI' in config and config['LOCAL_QEMU_URI'] != "":
            self.local_qemu_uri = config['LOCAL_QEMU_URI']
        if 'DOMAIN_IMAGES_DIR' in config and config['DOMAIN_IMAGES_DIR'] != "":
            self.domain_images_dir = config['DOMAIN_IMAGES_DIR']
        if 'TEMPLATE_IMAGES_DIR' in config and config['TEMPLATE_IMAGES_DIR'] != "":
            self.template_images_dir = config['TEMPLATE_IMAGES_DIR']
        if 'DOMAIN_DEFINITIONS_DIR' in config and config['DOMAIN_DEFINITIONS_DIR'] != "":
            self.domain_definitions_dir = config['DOMAIN_DEFINITIONS_DIR']
        if 'TEMPLATE_DEFINITIONS_DIR' in config and config['TEMPLATE_DEFINITIONS_DIR'] != "":
            self.template_definitions_dir = config['TEMPLATE_DEFINITIONS_DIR']
        if 'CONN_USER' in config and config['CONN_USER'] != "":
            self.conn_user = config['CONN_USER']
        try:
            db.session.commit()
            app.config.update(self.to_dict())
        except Exception as e:
            db.session.rollback()
            raise e

    def to_dict(self):
        return dict(LOCAL_QEMU_URI=self.local_qemu_uri,
                    DOMAIN_IMAGES_DIR=self.domain_images_dir,
                    DOMAIN_DEFINITIONS_DIR=self.domain_definitions_dir,
                    TEMPLATE_IMAGES_DIR=self.template_images_dir,
                    TEMPLATE_DEFINITIONS_DIR=self.template_definitions_dir,
                    CONN_USER=self.conn_user)


class Lab(db.Model):
    __tablename__ = 'labs'
    uuid = db.Column(UUIDType(binary=False), primary_key=True, default=uuid.uuid4())
    code = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    start_ip_range = db.Column(IPAddressType, unique=True, nullable=False)
    end_ip_range = db.Column(IPAddressType, unique=True, nullable=False)
    hosts_vcpus = db.Column(db.Integer, nullable=False)
    hosts_memory = db.Column(db.Integer, nullable=False)
    hosts_disk = db.Column(db.Integer, nullable=False)
    hosts = db.relationship('Host', backref='lab', lazy=True, cascade="all, delete-orphan")

    def __init__(self, data):
        self.uuid = uuid.uuid4()
        self.code = data['code'].upper()
        self.description = data['description']
        self.start_ip_range = ipaddress.ip_address(data['start_ip_range'])
        self.end_ip_range = ipaddress.ip_address(data['end_ip_range'])
        self.hosts_vcpus = data['hosts']['vcpus']
        self.hosts_memory = data['hosts']['memory']
        self.hosts_disk = data['hosts']['disk']

    def save(self):
        """Adds into database an existent laboratory

        :return: None
        """
        try:
            db.session.add(self)
            db.session.commit()
        except KeyError or IntegrityError as e:
            db.session.rollback()
            raise e

    def remove(self):
        """Deletes from database an existent laboratory

        :return: None
        """
        try:
            db.session.delete(self)
            db.session.commit()
        except UnmappedInstanceError as e:
            db.session.rollback()
            raise e

    def add_host(self, host):
        """Appends into the laboratory a new host

        :param host:
        :return: None
        """
        if not self.has_host(host):
            self.hosts.append(host)

    def remove_host(self, host):
        """Removes from database an existent host

        :param host:
        :return: None
        """
        if self.has_host(host):
            self.hosts.remove(host)

    def has_host(self, host):
        """Checks if the host is appended in the laboratory

        :param host:
        :return: True or False
        """
        return True if host in self.hosts else False

    @staticmethod
    def get(lab_uuid=None):
        """Gets a list with all laboratories if None lab_uuid is passed. If lab_uuid is present, it returns the
        laboratory defined by lab_uuid

        :param lab_uuid: UUID of the laboratory
        :return:
        """
        try:
            return Lab.query.get(lab_uuid) if lab_uuid else Lab.query.all()
        except Exception as e:
            raise e

    def update(self, data):
        if 'code' in data and data['code'] != "":
            self.code = data['code'].upper()
        if 'description' in data and data['description'] != "":
            self.description = data['description']
        if 'start_ip_range' in data and data['start_ip_range'] != "":
            self.start_ip_range = data['start_ip_range']
        if 'end_ip_range' in data and data['end_ip_range'] != "":
            self.end_ip_range = data['end_ip_range']
        if 'hosts' in data:
            if 'vcpus' in data['hosts'] and data['hosts']['vcpus'] != "":
                self.hosts_vcpus = data['hosts']['vcpus']
            if 'memory' in data['hosts'] and data['hosts']['memory'] != "":
                self.hosts_memory = data['hosts']['memory']
            if 'disk' in data['hosts'] and data['hosts']['disk'] != "":
                self.hosts_disk = data['hosts']['disk']
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def delete(lab):
        try:
            db.session.delete(lab)
            db.session.commit()
        except UnmappedInstanceError as e:
            db.session.rollback()
            raise e

    def to_dict(self):
        return dict(uuid=str(self.uuid),
                    code=self.code,
                    description=self.description,
                    start_ip_range=self.start_ip_range.compressed,
                    end_ip_range=self.end_ip_range.compressed,
                    hosts=dict(total=self.hosts.__len__(),
                               vcpus=self.hosts_vcpus,
                               memory=self.hosts_memory,
                               disk=self.hosts_disk))


class Host(db.Model):
    __tablename__ = 'hosts'
    uuid = db.Column(UUIDType(binary=False), primary_key=True, default=uuid.uuid4())
    code = db.Column(db.String(64), unique=True, nullable=False)
    ip_address = db.Column(IPAddressType, unique=True, nullable=False)
    conn_user = db.Column(db.String(64), nullable=False)
    lab_uuid = db.Column(UUIDType(binary=False), db.ForeignKey('labs.uuid'))

    def __init__(self, data):
        self.uuid = uuid.uuid4()
        self.code = data['code'].upper()
        self.ip_address = data['ip_address']
        self.conn_user = data['conn_user']

    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
        except KeyError or IntegrityError as e:
            db.session.rollback()
            raise e

    @staticmethod
    def get(host_uuid=None):
        return Host.query.get(host_uuid) if host_uuid else Host.query.all()

    def update(self, data):
        if 'code' in data and data['code'] != "":
            self.code = data['code']
        if 'ip_address' in data and data['ip_address'] != "":
            self.ip_address = data['ip_address']
        if 'conn_user' in data and data['conn_user'] != "":
            self.conn_user = data['conn_user']
        if 'lab_uuid' in data and data['lab_uuid'] != "":
            self.lab_uuid = uuid.UUID(data['lab_uuid'])
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def delete(host):
        try:
            db.session.delete(host)
            db.session.commit()
        except UnmappedInstanceError as e:
            db.session.rollback()
            raise e

    def to_dict(self):
        return dict(uuid=str(self.uuid),
                    code=self.code,
                    ip_address=self.ip_address.compressed,
                    conn_user=self.conn_user,
                    lab_id=self.lab.id)


class Template(db.Model):
    __tablename__ = 'templates'
    uuid = db.Column(UUIDType(binary=False), primary_key=True, default=uuid.uuid4())
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow())
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    vcpus = db.Column(db.Integer, nullable=False)
    memory = db.Column(db.Integer, nullable=False)
    xml_path = db.Column(db.String(255), nullable=False)
    images_path = db.Column(db.PickleType, nullable=False)

    def __init__(self, data):
        self.uuid = uuid.uuid4()
        self.name = data['name']
        self.description = data['description']
        self.vcpus = data['vcpus']
        self.memory = round(data['memory'] * 0.000976562)  # KiB to MiB
        self.xml_path = data['xml_path']
        self.images_path = pickle.dumps(data['images_path'])

    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
        except KeyError or IntegrityError as e:
            db.session.rollback()
            raise e

    @staticmethod
    def get(template_uuid=None):
        return Template.query.get(template_uuid) if template_uuid else Template.query.all()

    def update(self, data):
        if 'name' in data and data['name'] != "":
            self.name = data['name']
        if 'description' in data and data['description'] != "":
            self.description = data['description']
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def delete(template):
        try:
            db.session.delete(template)
            db.session.commit()
        except UnmappedInstanceError as e:
            db.session.rollback()
            raise e

    def to_dict(self):
        return dict(uuid=str(self.uuid),
                    timestamp=self.timestamp,
                    name=self.name,
                    description=self.description,
                    vcpus=self.vcpus,
                    memory=self.memory,
                    xml_path=self.xml_path,
                    images_path=pickle.loads(self.images_path))
