#!/usr/bin/python

import os
import sys
import configmanager
import json
import socket
from gi.repository import Gtk, GObject
import pair
from multiprocessing import Process, Queue
import threading
import thread

class EntryWindow():

    def __init__(self):
        builder = Gtk.Builder()
        builder.add_from_file(os.getcwd()+"/share/ui/pairingwindow.glade")
        builder.connect_signals(self)
        self.window = builder.get_object("pairingwindow")
        self.notebook = builder.get_object("notebook1")
        self.cancelbutton = builder.get_object("cancelbutton")
        self.forwardbutton = builder.get_object("forwardbutton")
        self.openportslabel = builder.get_object("openportslabel")
        self.hostlabel = builder.get_object("hostlabel")
        self.desktopfplabel = builder.get_object("desktopfplabel")
        self.devicefplabel = builder.get_object("devicefplabel")

        pairport = str(configmanager.port)
        openports = pairport + ", " + str(configmanager.secure_port)
        lanip = socket.gethostname()
        hosttxt = "Host: "+lanip+"\nPort: "+pairport

        self.stage = 0

        self.openportslabel.set_text(openports)
        self.hostlabel.set_text(hosttxt)

        self.window.set_wmclass ("DeskCon", "Setup Device")

        self.window.show_all()

    def on_cancelbutton_clicked(self, widget):
        if (self.stage == 2):
            self.pthread.response(0)
            self.notebook.set_current_page(3)
            self.stage = 3
        else:
            Gtk.main_quit()

    def on_forwardbutton_clicked(self, widget):
        if (self.stage == 0):
            self.pthread = pairingThread(self)
            self.pthread.start()
            self.forwardbutton.set_sensitive(False)
            self.notebook.set_current_page(1)
            self.stage = 1

        elif (self.stage == 2):
            self.pthread.response(1)         
            #self.notebook.set_current_page(3)
            #self.stage = 3

        elif (self.stage == 4):            
            Gtk.main_quit()

    def on_pairingwindow_destroy(self, *args):
        Gtk.main_quit(*args)

    def on_errordialog_close(self, widget):
        Gtk.main_quit()

class pairingThread (threading.Thread):

    def __init__(self, window):
        threading.Thread.__init__(self)
        self.window = window
        self.q = Queue()
        self.pairprocess = Process(target=pair.pairserver, args=(self.q,))

    def run(self):
        self.pairprocess.start()
        fingerprints = self.q.get(True)
        self.window.desktopfplabel.set_text(fingerprints[0])
        self.window.devicefplabel.set_text(fingerprints[1])
        self.window.forwardbutton.set_sensitive(True)
        self.window.notebook.set_current_page(2)
        self.window.stage = 2

    def response(self, r):
        if (r == 1):
            self.q.put("True", True)
            result = self.q.get(True)
            if (result == 1):
                self.window.notebook.set_current_page(3)
                self.window.stage = 3
            else:
                self.window.notebook.set_current_page(3)
                self.window.stage = 3
            self.window.forwardbutton.set_text("Finish")


        else:
            self.q.put("False", True)



def main(args):
    GObject.threads_init()
    win = EntryWindow()
    Gtk.main()

if __name__ == '__main__':
    main(sys.argv)
  

