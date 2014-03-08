import dbus
import dbus.service
import threading
from gi.repository import GObject, Gtk
from dbus.mainloop.glib import DBusGMainLoop

dbusname = 'net.screenfreeze.desktopconnector'

class DbusThread(threading.Thread):
    def __init__(self, connector_object):
        threading.Thread.__init__(self)
        self.connector = connector_object

    def run(self):
        DBusGMainLoop(set_as_default=True)        
        GObject.threads_init()
        dbus.mainloop.glib.threads_init()
        self.dbusservice = self.DbusService(self.connector)        
        Gtk.main()

    def emit_changed_signal(self):
        self.dbusservice.changed()

    def emit_new_notification_signal(self):
        self.dbusservice.new_notification()

    # Defining the Dbus interface
    class DbusService(dbus.service.Object):
        def __init__(self, connector_object):
            self.connector = connector_object
            bus_name = dbus.service.BusName(dbusname, bus=dbus.SessionBus())
            dbus.service.Object.__init__(self, bus_name, '/net/screenfreeze/desktopconnector')

        @dbus.service.method(dbusname, out_signature='s')
        def stats(self):
            return self.connector.get_mid_info()

        @dbus.service.method(dbusname, out_signature='s')
        def notification(self):
            return self.connector.get_last_notification()

        @dbus.service.method(dbusname, in_signature='s')
        def compose_sms(self, host):
            ip = host.split(":")[0]
            port = host.split(":")[1]
            self.connector.compose_sms("", ip, port)

        @dbus.service.method(dbusname, in_signature='s')
        def ping_device(self, host):
            ip = host.split(":")[0]
            port = host.split(":")[1]
            self.connector.ping_device(ip, port)

        @dbus.service.method(dbusname, in_signature='s')
        def send_file(self, host):
            ip = host.split(":")[0]
            port = host.split(":")[1]
            self.connector.send_file(ip, port)

        @dbus.service.method(dbusname)
        def show_settings(self):
            self.connector.show_settings()

        @dbus.service.signal(dbusname)
        def changed(self):
            pass

        @dbus.service.signal(dbusname)
        def new_notification(self):
            pass
