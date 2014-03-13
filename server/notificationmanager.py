import os
import subprocess
import platform
import time
import threading
import sms
from gi.repository import GObject
from gi.repository import Notify
from gi.repository import Gio, GLib, Gtk

Notify.init ("Desktop Connector")
icon_name = "phone"
FILE_TIMEOUT = 60

def buildNotification(header, body):
    notification=Notify.Notification.new (header, body, icon_name)
    notification.show()

def buildTransientNotification(header, body):
    notification=Notify.Notification.new (header, body, icon_name)
    notification.set_hint("transient", GLib.Variant.new_boolean(True))
    notification.set_urgency(urgency=Notify.Urgency.NORMAL)
    notification.set_timeout(1)
    notification.show()

def buildIncomingFileNotification(filenames, name):
    filenotification_thread = FileNotification(filenames, name)
    value = filenotification_thread.run()
    return value

def buildFileReceivedNotification(filenames, callback):
    filenotification_thread = FileReceivedNotification(filenames, callback)
    filenotification_thread.daemon = True
    filenotification_thread.start()

def buildSMSReceivedNotification(name, number, message, ip, port, callback):
    smsnotification_thread = SMSReceivedNotification(name, number, message, ip, port, callback)
    smsnotification_thread.daemon = True
    smsnotification_thread.start()


class FileNotification(threading.Thread):
    def __init__(self, filenames, name):
        threading.Thread.__init__(self)   
        self.filenames = filenames
        filestxt = ""
        for filename in self.filenames:
            filestxt = filestxt + "\n" + filename

        self.waiting_for_user_input = True   
        self.accepted = False     
        self.file_notification = Notify.Notification.new ("File upload", 
                                                        "incoming File"+filestxt+
                                                        "\nfrom "+name,"phone")
        # Fedora workaround
        try:
            self.file_notification.add_action("acc_file","accept", self.accept,None, None)
            self.file_notification.add_action("cancel_file","cancel", self.cancel,None, None) 
        except TypeError:
            self.file_notification.add_action("acc_file","accept", self.accept,None)
            self.file_notification.add_action("cancel_file","cancel", self.cancel,None) 
           

    def run(self):
        GObject.threads_init()
        self.file_notification.show()

        timeout_thread = threading.Thread(target=self.input_timeout, args=())
        timeout_thread.daemon = True
        timeout_thread.start()

        Gtk.main()
        return self.accepted

    def accept(self, ac_name, args, a):
        self.waiting_for_user_input = False
        self.accepted = True
        Gtk.main_quit()

    def cancel(self, ac_name, args, a):
        self.waiting_for_user_input = False
        self.accepted = False
        Gtk.main_quit()

    def input_timeout(self):
        GObject.threads_init()
        timeout = FILE_TIMEOUT
        while self.waiting_for_user_input:
            time.sleep(1)
            timeout = timeout - 1
            if timeout == 0:
                self.file_notification.close()
                self.waiting_for_user_input = False
                buildNotification("File", "Filetranfser was canceled after 60 seconds")
                Gtk.main_quit()
                break
    

class FileReceivedNotification(threading.Thread):
    def __init__(self, filenames, callback):
        threading.Thread.__init__(self)       
        self.filenames = filenames  
        self.callback = callback
        filestxt = ""
        for filename in self.filenames:
            filestxt = filestxt + "\n" + filename
        filestxt = filestxt.lstrip("\n")

        self.nnotification = Notify.Notification.new ("File received", filestxt, "phone")
        if (len(self.filenames) == 1):
            # Fedora workaround
            try:
                self.nnotification.add_action("open_path","open", self.open_file, filenames[0], None)
            except TypeError:
                self.nnotification.add_action("open_path","open", self.open_file, filenames[0])
            
         # Fedora workaround
        try:
            self.nnotification.add_action("open_folder","open Folder", self.open_folder, "" , None)
        except TypeError:
            self.nnotification.add_action("open_folder","open Folder", self.open_folder, "" )

    def run(self):
        GObject.threads_init()
        self.nnotification.show()
        Gtk.main()

    def open_file(self, ac_name, filename, a):
        Gtk.main_quit()
        self.callback(a)

    def open_folder(self, ac_name, args, a):
        Gtk.main_quit()
        self.callback("")


class SMSReceivedNotification(threading.Thread):
    def __init__(self, name, number, message, ip, port, callback):
        threading.Thread.__init__(self)       
        self.number = number    
        self.ip = ip
        self.port = str(port)
        self.callback = callback
        if name == "":
            name = number
        self.sms_notification = Notify.Notification.new ("SMS from "+name, message, icon_name)
        # Fedora workaround
        try:
            self.sms_notification.add_action("reply", "reply", self.reply_sms, None, None)
        except TypeError:
            self.sms_notification.add_action("reply", "reply", self.reply_sms, None)
        

    def run(self):
        GObject.threads_init()
        self.sms_notification.show()
        Gtk.main()

    def reply_sms(self, ac_name, filename, obj):
        Gtk.main_quit()
        self.callback(self.number, self.ip, self.port)
