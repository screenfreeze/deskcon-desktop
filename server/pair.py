#!/usr/bin/env python2

import socket
import SocketServer
import subprocess
import platform
import json
import time
from multiprocessing import Process, Queue
import random
import hashlib
import os
import threading
import thread
import configmanager
import ssl
from OpenSSL import SSL, crypto

def pair(q):
    serversocket = socket.socket(
        socket.AF_INET, socket.SOCK_STREAM)

    port = int(configmanager.port)
    host = configmanager.bindip
    serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serversocket.bind((host, port))

    serversocket.listen(1)

    print "waiting for Connection"

    (clientsocket, address) = serversocket.accept()

    req = clientsocket.recv(1)

    if req=="P":
        pair_client(clientsocket, q)
    else:
        print "closed"

    clientsocket.close()


def pair_client(clientsocket, q):
    print "wants to pair"       
    mycert = open(os.path.join(configmanager.keydir, "server.crt"), "r").read()
    secure_port = str(configmanager.secure_port)

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

    if (q): #GUI 
        q.put([myfp, devicefp])
        vout = q.get(True)
    else: #CMDLine only
        vout = raw_input("Do they match?(yes/no)\n") 

    if (vout.strip().lower()=="yes"):
        clientsocket.sendall(secure_port+"\n")
    else:
        clientsocket.sendall("0\n");
        pass

    print "wait for Device..."
    ack = clientsocket.recv(2)

    if (ack=="OK"):
        #save pub key
        with open(os.path.join(configmanager.keydir, "cas.pem"), 'a') as the_file:
            the_file.write(ssl.DER_cert_to_PEM_cert(clientcert))

        if (q):
            q.put(1)

        restart_server()
        print "Successfully paired the Device!"

    else:
        if (q):
            q.put(0)
        print "Failed to pair Device."

def restart_server():
    pid = int(open(configmanager.pidfile, "r").read())
    os.kill(pid, 10)

if __name__ == '__main__':
    pair(None)