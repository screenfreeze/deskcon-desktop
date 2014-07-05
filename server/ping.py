#!/usr/bin/env python2

import os
import sys
import socket
import configmanager
import json
from OpenSSL import SSL, crypto

def send_ping(ip, port):
    HOST, PORT = ip, int(port)
    uuid = configmanager.uuid
    hostname = socket.gethostname()

    jsonobj = {'uuid': uuid, 'name': hostname, 
               'type': "ping", 'data': ""}

    data = json.dumps(jsonobj)

    # Initialize context
    ctx = SSL.Context(SSL.TLSv1_METHOD)
    ctx.set_options(SSL.OP_NO_SSLv2|SSL.OP_NO_SSLv3) #TLS1 and up
    ctx.set_verify(SSL.VERIFY_PEER, verify_cb) #Demand a certificate
    ctx.use_privatekey_file(configmanager.privatekeypath)
    ctx.use_certificate_file(configmanager.certificatepath)
    ctx.load_verify_locations(configmanager.cafilepath)                
    sslclientsocket = SSL.Connection(ctx, socket.socket(socket.AF_INET, socket.SOCK_STREAM))

    succ = False
    try:
        sslclientsocket.connect((HOST, PORT))
        sslclientsocket.sendall(data)
        sslclientsocket.recv(2)
        succ = True

    except Exception as e:
        print "Error " + str(e[0])

    finally:
        if (succ):
            sslclientsocket.shutdown()
            sslclientsocket.close()



def verify_cb(conn, cert, errnum, depth, ok):
    # This obviously has to be updated
    #print "er"+str(errnum)
    #print "de"+str(depth)
    #print "ok "+str(ok)
    return ok

def main(args):
    ip = args[1]
    port = args[2]
    send_ping(ip, port)


if __name__ == '__main__':
    if(len(sys.argv) < 3):
        print "not enough arguments given"
    else:
        main(sys.argv)
  

