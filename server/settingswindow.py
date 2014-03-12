#!/usr/bin/python

import os
import sys
import configmanager
import json
from gi.repository import Gtk, GObject

class EntryWindow():

    def __init__(self):

        builder = Gtk.Builder()
        builder.add_from_file(os.getcwd()+"/share/ui/settings.glade")
        builder.connect_signals(self)
        self.window = builder.get_object("settingswindow")
        self.ipentry = builder.get_object("ipentry")
        self.portentry = builder.get_object("portentry")
        self.secportentry = builder.get_object("secportentry")
        self.downloadfilechooserbutton = builder.get_object("downloadfilechooserbutton")
        self.uuidlabel = builder.get_object("uuidlabel")
        self.autourlswitch = builder.get_object("autourlswitch")
        self.autoclipboardswitch = builder.get_object("autoclipboardswitch")
        self.autofileswitch = builder.get_object("autofileswitch")

        self.uuidlabel.set_text(str(configmanager.uuid))
        self.downloadfilechooserbutton.set_filename(configmanager.downloaddir)
        self.ipentry.set_text(configmanager.bindip)
        self.portentry.set_text(configmanager.port)
        self.secportentry.set_text(configmanager.secure_port)
        self.autourlswitch.set_active(configmanager.auto_open_urls)
        self.autoclipboardswitch.set_active(configmanager.auto_store_clipboard)
        self.autofileswitch.set_active(configmanager.auto_accept_files)

        self.window.set_wmclass ("DeskCon", "Settings")

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

    def on_closebutton_clicked(self, widget):
        Gtk.main_quit()

    def on_okbutton_clicked(self, widget):
        datadict = {}
        datadict['downloaddir'] = self.downloadfilechooserbutton.get_filename()
        datadict['bindip'] = self.ipentry.get_text()
        datadict['port'] = int(self.portentry.get_text())
        datadict['secure_port'] = int(self.secportentry.get_text())
        datadict['debug'] = False
        datadict['auto_open_urls'] = self.autourlswitch.get_active()
        datadict['auto_store_clipboard'] = self.autoclipboardswitch.get_active()
        datadict['auto_accept_files'] = self.autofileswitch.get_active()
        configmanager.write_config(datadict)
        restart_server()
        Gtk.main_quit()

    def on_settingswindow_destroy(self, *args):
        Gtk.main_quit(*args)

    def on_errordialog_close(self, widget):
        Gtk.main_quit()


def restart_server():
    pid = int(open(configmanager.pidfile, "r").read())
    os.kill(pid, 10)


def main(args):
    GObject.threads_init()
    win = EntryWindow()
    Gtk.main()

if __name__ == '__main__':
    main(sys.argv)
  

