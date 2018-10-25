# DIS vLab Server

DIS vLab Server (DVLS) is a 'full-stack' application to manage virtual labs in the Computer Engineering School of the University of Las Palmas de Gran Canaria (ULPGC). Really, a virtual lab is just a room with a set of physical computers with a CentOS 7.x Desktop installation with libvirt and virt-manager. Also, DVLS runs on CentOS 7.x Minimal in a powerful computer or server. This workstation manages the local hypervisor to generate templates and connects remotely via SSH with the computers in virtual labs to deploy these templates and realize standard operations with virtual machines.

## Table of Contents

1. [Requirements](#requirements)<br>
2. [Repository and dependencies](#repository-and-dependencies)<br>
3. [System configuration](#system-configuration)<br>
  i. [User and groups](#user-and-groups)<br>
  ii. [Firewall](#firewall)<br>
  ii. [PolicyKit](#policykit)<br>
  iii. [Pluggable Authentication Modules](#pluggable-authentication-modules)<br>
4. [DVLS Service](#dvls-service)<br>
5. [Nginx configuration](#nginx-configuration)<br>
  i. [Secure Socket Layer](#secure-sockets-layer)<br>
  ii. [Reverse proxy configuration](#reverse-proxy-configuration)<br>
6. [Accessing to web interface](#accessing-to-web-interface)<br>
7. [Troubleshooting](#troubleshooting)<br>
8. [License](#license)<br>
9. [Author information](#author-information)<br>

## Requirements
To deploy DVLS you will need have installed CentOS 7.x Minimal installation with [EPEL](https://fedoraproject.org/wiki/EPEL/es) and [IUS](https://ius.io/GettingStarted/) repositories and these groups/packages:
* "Virtualization Platform" (group)
* "Virtualization Hypervisor" (group)
* "Virtualization Tools" (group)
* "Virtualization Client" (group)
* "Development" (group)
* "libvirt-devel.x86_64"
* "libguestfs-tools"
* "python36u"
* "python36u-devel"
* "python36u-pip"
* "nginx"
* "openssl"

## Repository and dependencies

Clone the repository with source code into recommended directory **/usr/lib**:
```bash
# cd /usr/lib
# git clone https://www.github.com/albertososa95/dvls.git
```
You need virtualenv to install Python dependencies. For it, use ```# pip3.6 install virtualenv```. Then, create a virtualenv inside DVLS folder:
```bash
# cd dvls
# virtualenv venv
```
Activate the virtual environment with ```# source venv/bin/activate```, and install the dependencies with ```(venv) # pip install -r requirements.txt```.

## System configuration

#### User and groups

The DVLS service will be started by a non-root user named as "dvls" for security reasons, so you need to create if you didn't it at CentOS 7 installer. This will be the user that will access the application. Also, it should be part of nginx and libvirt groups.
```bash
# useradd dvls
# passwd dvls
# usermod -a -G libvirt dvls
```

#### Firewall

CentOS 7 has firewalld running, so you should add a rule for incoming HTTP or HTTPS traffic, depending if you'll configure SSL in Nginx:
```bash
# firewall-cmd --add-service=http --permanent
# firewall-cmd --add-service=https --permanent
# firewall-cmd --reload
```

#### PolicyKit

By default, all non-root users that be part of libvirt group have privileges to manage and use libvirt. You can find that rule file in **/usr/share/polkit-1/rules.d/50-libvirt.rules**.

#### Pluggable Authentication Modules

DVLS uses a PAM Python library to authenticate the user against **/etc/shadow** file. So that it works correctly, you need to create a new PAM service called 'dvls': 
```bash
# echo "auth required pam_unix.so" > /etc/pam.d/dvls 
```

## DVLS service

Create a new file into **/etc/systemd/system/** directory, e.g. dvls.service, with these content to handle DVLS application as a system service:
```bash
[Unit]
Description=uWSGI instance for DIS vLab Server
After=network.target

[Service]
WorkingDirectory=/usr/lib/dvls
Environment="PATH=/usr/lib/dvls/venv/bin:/usr/bin"
ExecStart=/usr/lib/dvls/venv/bin/uwsgi --ini dvls.ini

[Install]
WantedBy=multi-user.target
```
Before **enable** and **start** dvls.service, change the owner of DVLS folder with: ```# chown dvls:dvls /usr/lib/dvls```

## Nginx configuration

#### Secure Sockets Layer

It's a good practise use HTTPS instead HTTP in web applications inside corporate environment that is susceptible to traffic monitoring, redirection and manipulation. For that reason, it's recommendable generate an auto-signed certificate using OpenSSL. First of all, make sure that exists **/etc/nginx/ssl** directory, where server certificate and its key will be stored. To generate the key and certificate, use this command: ```# openssl req -x509 -nodes -days 3650 -newkey rsa:2048 -keyout /etc/nginx/ssl/nginx.key -out /etc/nginx/ssl/nginx.crt```.
> NOTE: Change the firewall rule if you configure SSL in Nginx.

#### Reverse proxy configuration

Really, the application server is uWSGI that is included in the project dependencies, so Nginx is working as reverse proxy. Create new config file into **/etc/nginx/conf.d/dvls.conf** with your preferred text editor and fill it with these statement:
```nginx
server {
    listen 443 ssl;
    server_name dvls.dis.ulpgc.es;
    ssl_certificate /etc/nginx/ssl/nginx.crt;
    ssl_certificate_key /etc/nginx/ssl/nginx.key;

    location / {
        include uwsgi_params;
        uwsgi_pass unix:/usr/lib/dvls/dvls.sock;
    }
}
```

## Accessing to web interface

Open your preferred browser and navigate via HTTP or HTTPS, depending of your configuration, to ```<protocol>://dvls.dis.ulpgc.es/``` and enter the credentials of dvls user in login page.

## Troubleshooting

You can get a 502 nginx error when accessing to web interface if you're using SELinux in enforcing mode. It happens due to wrong SELinux policy to use the dvls.sock. To fix that, you'll need to add the correct SELinux policy module. Once you get the error in browser, use ```audit2allow``` to generate the correct SELinux module. With CentOS 7 Minimal installation you should install ```policycoreutils-python``` to use it.
```bash
# grep nginx /var/log/audit/audit.log | audit2allow -M nginx
# semodule -i nginx.pp
```

## License

Pending

## Author Information

Alberto Sosa, student of Computer Engineering at University of Las Palmas de Gran Canaria, 2018.

