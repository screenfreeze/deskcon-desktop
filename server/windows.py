#!/usr/bin/env python2
import threading
import os
import sys
import socket
import configmanager
from OpenSSL import SSL, crypto
from gi.repository import Gio, GLib, Gtk, GObject, Gdk

def build_Pairing_Window(MyFp, DeviceFp):
    pairing = PairingWindow(MyFp, DeviceFp)
    choice = pairing.start()
    return choice

class PairingWindow(Gtk.Window):
    def __init__(self, myfp, devicefp):
        Gtk.Window.__init__(self, title="Pairing")
        self.set_resizable(False)
        self.set_size_request(300, 300)
        self.accepted = False

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(vbox)

        infolabel = Gtk.Label("Please check whether these Fingerprints are the same as"+
                        "\nthe ones displayed on your mobile Device")
        info2label = Gtk.Label("This Desktops Fingerprint:")
        myfplabel = Gtk.Label(myfp)
        myfplabel.set_line_wrap(True)
        myfplabel.set_max_width_chars(10)
        info3label = Gtk.Label("Mobile Device Fingerprint:")
        devicefplabel = Gtk.Label(devicefp)
        devicefplabel.set_line_wrap(True)
        devicefplabel.set_max_width_chars(10)
        info4label = Gtk.Label("Are they the same? (Do you trust this Device?)")
        infolabel.set_padding(5,0)
        info2label.set_padding(5,5)
        info3label.set_padding(5,5)
        info4label.set_padding(5,5)
        infolabel.set_alignment(0, 0)        
        info2label.set_alignment(0, 0) 
        info3label.set_alignment(0, 0) 
        info4label.set_alignment(0, 0)  
        vbox.pack_start(infolabel, False, True, 10)
        vbox.pack_start(info2label, False, True, 10)
        vbox.pack_start(myfplabel, False, False, 0)
        vbox.pack_start(info3label, False, True, 10)
        vbox.pack_start(devicefplabel, False, False, 0)
        vbox.pack_start(info4label, True, True, 10)

        hbox = Gtk.Box(spacing=6)
        self.nobutton = Gtk.Button(label="no")
        self.nobutton.connect("clicked", self.on_cancel_button_clicked)
        self.yesbutton = Gtk.Button(label="yes")
        self.yesbutton.connect("clicked", self.on_yes_button_clicked)
        hbox.pack_start(self.nobutton, True, True, 0)
        hbox.pack_start(self.yesbutton, True, True, 0)
        vbox.pack_start(hbox, False, False, 10)

    def start(self):        
        self.connect("destroy", Gtk.main_quit)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.show_all()
        GObject.threads_init()
        Gtk.main()
        return self.accepted

    def on_yes_button_clicked(self, widget):
        self.accepted = True
        Gtk.main_quit()

    def on_cancel_button_clicked(self, widget):
        self.accepted = False
        Gtk.main_quit()
