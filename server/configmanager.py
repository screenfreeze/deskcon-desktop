import os
import ConfigParser
import time
import shutil
import authentication
import random

homedir = os.path.expanduser('~')
default_configfile = os.getcwd()+"/share/config.conf"

config = ConfigParser.ConfigParser()
configdir = homedir + "/.deskcon/"
configfile = configdir + "config.conf"
pidfile = configdir + "server.pid"
keydir = os.path.join(configdir, "keys")
privatekeypath = os.path.join(keydir, "private.key")
certificatepath = os.path.join(keydir, "server.crt")
cafilepath = os.path.join(keydir, "cas.pem")

def copy_default_config():
    if os.path.isdir(configdir):
        shutil.copyfile(default_configfile, configfile)  
    else:
        os.mkdir(configdir)
        os.mkdir(keydir)
        shutil.copyfile(default_configfile, configfile)

def gen_and_store_keys(uuid):
    certificate, privatekey = authentication.generate_keypair(uuid)
    with open(privatekeypath, 'w') as the_file:
        the_file.write(privatekey)
    with open(certificatepath, 'w') as the_file:
        the_file.write(certificate)
    with open(cafilepath, 'w') as the_file:
        the_file.write("")

# if no config file present, setup config files
if os.path.isfile(configfile):
    config.read(configfile)    
    privatekey = open(privatekeypath, "r").read()    
    certificate = open(certificatepath, "r").read()
else:
    print "created new config file"
    copy_default_config()
    config.read(configfile)
    #gen uuid
    uuid = random.randint(100000000000000L, 999999999999999L)
    #set Path to Download Folder
    default_download_dir = os.path.join(homedir, "Downloads")
    cfgfile = open(configfile, 'w')
    config.set('general','uuid', uuid)
    config.set('general','download_dir', default_download_dir)
    config.write(cfgfile)
    cfgfile.close()
    #generate Keys and store in keydir
    gen_and_store_keys(uuid)
    config.read(configfile)

def load():
    global port, secure_port, bindip, uuid, downloaddir, auto_store_clipboard
    global auto_open_urls, auto_accept_files
    if os.path.isfile(configfile):
        config.read(configfile)    
    port = config.get('network', 'port')
    secure_port = config.get('network', 'secure_port')
    bindip = config.get('network', 'bindip')
    uuid = config.getint('general', 'uuid')
    downloaddir = os.path.join(config.get('general', 'download_dir'))
    auto_accept_files = config.getboolean('permissions', 'auto_accept_files')
    auto_open_urls = config.getboolean('permissions', 'auto_open_urls')
    auto_store_clipboard = config.getboolean('permissions', 'auto_store_clipboard')

def get_port():
    return port

def get_bindip():
    return bindip

def get_download_dir():
    return downloaddir+"/"

def write_config(datadict):
    if (not config):
        copy_default_config()

    cfgfile = open(configfile, 'w')
    config.set('general','download_dir', datadict['downloaddir'])
    config.set('general','debug', datadict['debug'])
    config.set('network','bindip', datadict['bindip'])
    config.set('network','port', datadict['port'])
    config.set('network','secure_port', datadict['secure_port'])
    config.set('permissions','auto_open_urls', datadict['auto_open_urls'])
    config.set('permissions','auto_store_clipboard', datadict['auto_store_clipboard'])
    config.set('permissions','auto_accept_files', datadict['auto_accept_files'])
    config.write(cfgfile)
    cfgfile.close()

#store server Process ID
def write_pidfile(pid):
    pfile = open(pidfile, 'w')
    pfile.write(pid)
    pfile.close()

load()