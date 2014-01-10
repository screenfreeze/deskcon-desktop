import random
from OpenSSL import SSL, crypto
import socket
import ssl
import configmanager
import hashlib
import subprocess
import os

PROGRAMDIR = os.getcwd()

def generate_keypair(uuid):
    hostname = socket.gethostname()
    # create a key pair
    keypair = crypto.PKey()
    keypair.generate_key(crypto.TYPE_RSA, 2048)

    # create a self-signed cert
    cert = crypto.X509()
    cert.set_version(2)
    cert.get_subject().CN = str(uuid)+"/"+hostname
    cert.get_issuer().CN = str(uuid)+"/"+hostname
    cert.set_serial_number(1000)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(10*365*24*60*60)
    cert.set_pubkey(keypair)
    cert.sign(keypair, 'sha256')

    certificate = crypto.dump_certificate(crypto.FILETYPE_PEM, cert)
    privatekey = crypto.dump_privatekey(crypto.FILETYPE_PEM, keypair)
    return certificate, privatekey    



def pair(clientsocket):
    print "wants to pair"       
    mycert = open(os.path.join(configmanager.keydir, "server.crt"), "r").read()

    myder_cert = ssl.PEM_cert_to_DER_cert(mycert)
    m = hashlib.sha256(myder_cert)
    myfp = m.hexdigest().upper()
    myfp = " ".join(myfp[i:i+4] for i in range(0, len(myfp), 4))
    print "\nMy SHA256: "+myfp
    #send my certiuficate
    clientsocket.sendall(myder_cert.encode('base64'))

    #receive client Certificate
    clientcert = clientsocket.recv(2048)

    m = hashlib.sha256(clientcert)
    devicefp = m.hexdigest().upper()
    devicefp = " ".join(devicefp[i:i+4] for i in range(0, len(devicefp), 4))
    print "\nClient SHA256: "+devicefp
    
    fpdiag = subprocess.Popen([PROGRAMDIR+"/fingerprints.py", myfp, devicefp], stdout=subprocess.PIPE)
    (vout, verr) = fpdiag.communicate()
    print vout

    if (vout.strip()=="True"):
        clientsocket.sendall("OK\n")        
    else:
        clientsocket.sendall("0\n");
        pass

    ack = clientsocket.recv(2)
    if (ack=="OK"):
        #save pub key
        with open(os.path.join(configmanager.keydir, "cas.pem"), 'a') as the_file:
            the_file.write(ssl.DER_cert_to_PEM_cert(clientcert))
        print "Successfully paired the Device!"

    else:
        print "Failed to pair Device."

