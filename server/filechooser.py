#!/usr/bin/env python2
import os
import sys
import socket
import configmanager
import json
from OpenSSL import SSL, crypto
from gi.repository import Gtk, GObject

class FileChooserWindow(Gtk.Window):

    def __init__(self):
        Gtk.Window.__init__(self)
        self.dialog = Gtk.FileChooserDialog("Please choose a file", self,
            Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

        homefolder = os.path.expanduser("~")
        self.dialog.set_select_multiple(True)
        self.dialog.set_current_folder(homefolder)

    def run(self, ip, port):
        response = self.dialog.run()
        if response == Gtk.ResponseType.OK:
            files = self.dialog.get_filenames()
            send_data(self.dialog, files, ip, port)
        elif response == Gtk.ResponseType.CANCEL:
            self.dialog.destroy()

def send_data(dialog, files, ip, port):
    HOST, PORT = ip, int(port)
    uuid = configmanager.uuid
    hostname = socket.gethostname()

    filenames = []
    for filepath in files:
        head, name = os.path.split(filepath)
        filenames.append(name)


    jsonobj = {'uuid': uuid, 'name': hostname, 
               'type': "fileup", 'data': json.dumps(filenames)}

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
        print "wait for ack"
        response = sslclientsocket.recv(2) #wait for Ack
        if (response == "OK"):
            print "send files"
            for filepath in files: #send files
                send_file(filepath, sslclientsocket)
            print "succesfully send Files"

        succ = True

    except Exception as e:
        print "Error " + str(e)

    finally:
        if (succ):
            sslclientsocket.shutdown()
            sslclientsocket.close()
            dialog.destroy()

def send_file(filepath, socket):
    filesize = os.path.getsize(filepath)

    socket.send(str(filesize)+"\n")
    socket.recv(1) #wait for ready

    ofile = open(filepath, 'rb')
    fbuffer = ofile.read(4096)
    while (fbuffer):
        socket.send(fbuffer)
        fbuffer = ofile.read(4096)
    ofile.close()

def verify_cb(conn, cert, errnum, depth, ok):
    # This obviously has to be updated
    #print "er"+str(errnum)
    #print "de"+str(depth)
    #print "ok "+str(ok)
    return ok

def main(args):
    GObject.threads_init()
    ip = args[1]
    port = args[2]
    win = FileChooserWindow()
    win.run(ip, port)

if __name__ == '__main__':
    if(len(sys.argv) < 3):
        print "not enough arguments given"
    else:
        main(sys.argv)
  






