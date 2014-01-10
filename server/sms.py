#!/usr/bin/python

import os
import sys
import socket
import configmanager
import json
from OpenSSL import SSL, crypto
from gi.repository import Gio, GLib, Gtk, GObject, Gdk

class EntryWindow(Gtk.Window):

    def __init__(self, ip, port, number):
        Gtk.Window.__init__(self, title="Compose")
        self.set_size_request(420, 300)

        self.ip = ip
        self.port = port

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(vbox)

        numberlabel = Gtk.Label("Number")
        numberlabel.set_padding(5,0)
        numberlabel.set_alignment(0, 0)
        self.entry = Gtk.Entry()
        self.entry.set_text(number)
        vbox.pack_start(numberlabel, False, False, 0)
        vbox.pack_start(self.entry, False, True, 0)

        self.textview = Gtk.TextView()
        self.textbuffer = self.textview.get_buffer()
        vbox.pack_start(self.textview, True, True, 5)

        hbox = Gtk.Box(spacing=6)
        vbox.pack_start(hbox, False, False, 5)
        
        self.cancelbutton = Gtk.Button(label="cancel")
        self.cancelbutton.connect("clicked", self.on_cancel_button_clicked)
        self.button = Gtk.Button(label="send")
        self.button.connect("clicked", self.on_button_clicked)
        hbox.pack_start(self.cancelbutton, True, True, 5)
        hbox.pack_start(self.button, True, True, 5)

    def on_button_clicked(self, widget):
        siter = self.textbuffer.get_start_iter()
        eiter = self.textbuffer.get_end_iter()
        txt = self.textbuffer.get_text(siter, eiter,  False)
        number = self.entry.get_text()
        send_sms(number.strip(),txt.strip(), self.ip, self.port)
        Gtk.main_quit()

    def on_cancel_button_clicked(self, widget):
        Gtk.main_quit()


def send_sms(recver, msg, ip, port):
    HOST, PORT = ip, int(port)

    jsonobj = {'uuid': "000000001111111", 'name': "Hostname", 
               'type': "sms", 'data': {'number': recver, 'message': msg}}
    #data = recver+"::"+msg
    data = json.dumps(jsonobj)

    # Initialize context
    ctx = SSL.Context(SSL.TLSv1_METHOD)
    ctx.set_options(SSL.OP_NO_SSLv2|SSL.OP_NO_SSLv3) #TLS1 and up
    ctx.set_verify(SSL.VERIFY_PEER, verify_cb) #Demand a certificate
    ctx.use_privatekey_file(configmanager.privatekeypath)
    ctx.use_certificate_file(configmanager.certificatepath)
    ctx.load_verify_locations(configmanager.cafilepath)                
    sslclientsocket = SSL.Connection(ctx, socket.socket(socket.AF_INET, socket.SOCK_STREAM))

    try:
        sslclientsocket.connect((HOST, PORT))
        sslclientsocket.sendall(data)
        sslclientsocket.recv(2)
    finally:
        sslclientsocket.shutdown()
        sslclientsocket.close()

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
    win.connect("destroy", Gtk.main_quit)
    win.set_position(Gtk.WindowPosition.CENTER)
    win.show_all()
    Gtk.main()


if __name__ == '__main__':
    if(len(sys.argv) < 3):
        print "not enough arguments given"
    else:
        main(sys.argv)
  

