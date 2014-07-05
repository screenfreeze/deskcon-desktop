#!/usr/bin/env python2

import os
import sys
import socket
import configmanager
import json
from OpenSSL import SSL, crypto
from gi.repository import Gtk, GObject

class EntryWindow():

    def __init__(self, ip, port, number):

        builder = Gtk.Builder()
        builder.add_from_file(os.getcwd()+"/share/ui/sms.glade")
        builder.connect_signals(self)
        self.window = builder.get_object("smswindow")
        self.numberentry = builder.get_object("numberentry")
        self.messagetextview = builder.get_object("messagetextview")
        self.charlabel = builder.get_object("charcountlabel")
        self.errordialog = builder.get_object("errordialog")

        self.window.set_wmclass ("DeskCon", "Compose")

        self.ip = ip
        self.port = port

        self.numberentry.set_text(number)
        self.textbuffer = self.messagetextview.get_buffer()
        self.window.show_all()

    def on_sendbutton_clicked(self, widget):
        siter = self.textbuffer.get_start_iter()
        eiter = self.textbuffer.get_end_iter()
        txt = self.textbuffer.get_text(siter, eiter,  False).strip()
        number = self.numberentry.get_text().strip()

        if (number == ""):
            self.errordialog.format_secondary_text("No Number.")
            self.errordialog.run()
            self.errordialog.hide()
        elif (txt == ""):
            self.errordialog.format_secondary_text("Text is empty.")
            self.errordialog.run()
            self.errordialog.hide()
        else:
            send_sms(number,txt, self.ip, self.port, self.errordialog)
        

    def on_cancelbutton_clicked(self, widget):
        Gtk.main_quit()

    def on_smswindow_destroy(self, *args):
        Gtk.main_quit(*args)

    def on_errordialog_close(self, widget):
        Gtk.main_quit()


def send_sms(recver, msg, ip, port, errordialog):
    HOST, PORT = ip, int(port)
    uuid = configmanager.uuid
    hostname = socket.gethostname()

    jsonobj = {'uuid': uuid, 'name': hostname, 
               'type': "sms", 'data': {'number': recver, 'message': msg}}

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
        errnum = e[0]
        print "Error " + str(e[0])
        if (errnum == -5):
            errordialog.format_secondary_text("The Device is not reachable. Maybe it's not on your Network")
        else:
            errordialog.format_secondary_text("Errornumber "+str(errnum))
        errordialog.run()
        errordialog.hide()

    finally:
        if (succ):
            sslclientsocket.shutdown()
            sslclientsocket.close()
            Gtk.main_quit()



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
    if (len(args) == 4):       
        number = args[3]
    else:
        number = ""

    win = EntryWindow(ip, port, number)
    Gtk.main()


if __name__ == '__main__':
    if(len(sys.argv) < 3):
        print "not enough arguments given"
    else:
        main(sys.argv)
  

