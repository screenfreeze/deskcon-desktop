# DesCon Desktop Server
# Version 0.2

import socket
import SocketServer
import webbrowser
import subprocess
import platform
import json
import time
import sms
import os
import notificationmanager
import filetransfer
import authentication
import threading
import thread
import configmanager
import mediacontrol
from gi.repository import Gio, GLib, Gtk, GObject, Gdk
from OpenSSL import SSL, crypto
from dbusservice import DbusThread

configmanager.write_pidfile(str(os.getpid()))
HOST = configmanager.get_bindip()
PORT = int(configmanager.get_port())
SECUREPORT = int(configmanager.secure_port)
PROGRAMDIR = os.getcwd()
BUFFERSIZE = 4096

AUTO_ACCEPT_FILES = configmanager.auto_accept_files
AUTO_OPEN_URLS = configmanager.auto_open_urls
AUTO_STORE_CLIPBOARD = configmanager.auto_store_clipboard

class Connector():
    def __init__(self):     
        self.uuid_list = {}   
        self.mid_info = {'phones': [], 'settings': {}}
        self.last_notification = "";

        self.dbus_service_thread = DbusThread(self)    
        self.dbus_service_thread.daemon = True        

        SocketServer.TCPServer.allow_reuse_address = True
        self.server = self.TCPServer((HOST, PORT), self.TCPHandler, self)
        self.sslserver = sslserver(self)
        self.sslserver.daemon = True

    def run(self):
        GObject.threads_init()
        self.dbus_service_thread.start()   
        self.sslserver.start()     
        self.server.serve_forever()

    def get_mid_info(self):
        return json.dumps(self.mid_info)

    def get_last_notification(self):
        return self.last_notification

    def parseData(self, data, address, csocket):
        jsondata = json.loads(data)
        uuid = jsondata['uuid']
        name = jsondata['devicename']
        msgtype = jsondata['type']
        message = jsondata['data']

        print "UUID ",uuid
        print "NAME ",name
        print "TYPE ",msgtype
        print "MSG ",message    
        
        if uuid not in self.uuid_list:
            self.mid_info['phones'].append({'uuid': uuid, 'name': name, 
                                        'battery': -1, 'volume': -1, 
                                        'batterystate': False, 'missedsmscount': 0, 
                                        'missedcallcount': 0, 'ip': address, 
                                        'canmessage': False, 'controlport': 9096,
                                        'storage': -1})

            apos = 0
            for x in range(0, len(self.mid_info['phones'])):
                if self.mid_info['phones'][x]['uuid'] == uuid:
                    apos = x

            self.uuid_list[uuid] = apos
            print "created "+uuid+" at pos "+str(apos)

        pos = self.uuid_list[uuid]

        if (msgtype == "STATS"):
            newstats = json.loads(message)
            if (newstats.has_key('volume')): 
                self.mid_info['phones'][pos]['volume'] = newstats['volume']
            if (newstats.has_key('controlport')): 
                self.mid_info['phones'][pos]['controlport'] = newstats['controlport']
            if (newstats.has_key('battery')): 
                self.mid_info['phones'][pos]['battery'] = newstats['battery']
                self.mid_info['phones'][pos]['batterystate'] = newstats['batterystate']
            if (newstats.has_key('missedmsgs')): 
                self.mid_info['phones'][pos]['missedsmscount'] = newstats['missedmsgs']
            if (newstats.has_key('missedcalls')): 
                self.mid_info['phones'][pos]['missedcallcount'] = newstats['missedcalls']
            if (newstats.has_key('canmessage')): 
                self.mid_info['phones'][pos]['canmessage'] = newstats['canmessage']
            if (newstats.has_key('storage')): 
                self.mid_info['phones'][pos]['storage'] = newstats['storage']
            self.mid_info['phones'][pos]['ip'] = address
       
        elif (msgtype == "SMS"):
            smsobj = json.loads(message)            
            name = smsobj['name']
            number = smsobj['number']
            smsmess = smsobj['message']
            notificationmanager.buildSMSReceivedNotification(name, number, smsmess, address, self.mid_info['phones'][pos]['controlport'], self.compose_sms)
            
        elif (msgtype == "CALL"):
            notificationmanager.buildTransientNotification(name, "incoming Call from "+message)
            
        elif (msgtype == "URL"):
            if (AUTO_OPEN_URLS):              
                webbrowser.open(message, 0 ,True)
            else:
                notificationmanager.buildNotification("URL", "Link: "+message)

        elif (msgtype == "CLPBRD"):
            clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
            clipboard.set_text(message, -1)
            notificationmanager.buildTransientNotification("Clipboard", message)   

        elif (msgtype == "MIS_CALL"):
            notificationmanager.buildNotification(name, "missed Call from "+message)

        elif (msgtype == "PING"):
            notificationmanager.buildTransientNotification("Ping from "+name, 
                                                            "Name: "+name+
                                                            "\nUUID: "+uuid+
                                                            "\nIP: "+address)

        elif (msgtype == "OTH_NOT"):
            msginfo = message.split(': ', 1)
            new_notification = uuid+"::"+message
            if (self.last_notification != new_notification):
                self.last_notification = new_notification
                self.dbus_service_thread.emit_new_notification_signal()
                if (len(msginfo) > 1):
                    sender = msginfo[0]
                    notification = msginfo[1]
                    notificationmanager.buildTransientNotification(sender, notification)
                else:
                    notificationmanager.buildTransientNotification(name, message)

        elif (msgtype == "FILE_UP"):
            filenames = json.loads(message)
            if (AUTO_ACCEPT_FILES):
                print "accepted"
                filetransfer.write_files(filenames, csocket)
            else:
                accepted = notificationmanager.buildIncomingFileNotification(filenames, name)
                print "wait for ui"       
                if (accepted):
                    print "accepted"
                    fpaths = filetransfer.write_files(filenames, csocket)
                    notificationmanager.buildFileReceivedNotification(fpaths, self.open_file)
                else:
                    print "not accepted"

        elif (msgtype == "MEDIACTRL"):
            thread.start_new_thread(mediacontrol.control, (message,))

        else:
            print "ERROR: Non parsable Data received"

        #print json.dumps(self.mid_info)


    class TCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):

        def __init__(self, server_address, RequestHandlerClass, connector):
            SocketServer.TCPServer.__init__(self, server_address, RequestHandlerClass)
            self.connector = connector

    class TCPHandler(SocketServer.BaseRequestHandler):

        def handle(self):
            csocket = self.request
            address = format(self.client_address[0])
            connector = self.server.connector
            print "connected to ",address

            req = csocket.recv(1)

            if req=="P":
                authentication.pair(csocket)
                    
            elif req=="C":
                #negotiate new secure connection port
                newport = SECUREPORT                
                csocket.sendall(str(newport))
              
            csocket.close()



    def compose_sms(self, number, ip, port):
        subprocess.Popen([PROGRAMDIR+"/sms.py", ip, port, number], stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def ping_device(self, ip, port):
        subprocess.Popen([PROGRAMDIR+"/ping.py", ip, port], stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def send_file(self, ip, port):
        subprocess.Popen([PROGRAMDIR+"/filechooser.py", ip, port], stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def open_file(self, path):
        if (path == ""):
            path = configmanager.downloaddir
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", path], stdin=subprocess.PIPE, 
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            subprocess.Popen(["xdg-open", path], stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def show_settings(self):
        subprocess.Popen([PROGRAMDIR+"/settingswindow.py"], stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)



class sslserver(threading.Thread):

    def __init__(self, conn):
        threading.Thread.__init__(self)
        self.conn = conn

    def run(self):
        # Initialize context
        try:
            ctx = SSL.Context(SSL.SSLv23_METHOD)
            ctx.set_options(SSL.OP_NO_SSLv2|SSL.OP_NO_SSLv3) #TLS1 and up
            ctx.set_verify(SSL.VERIFY_PEER|SSL.VERIFY_FAIL_IF_NO_PEER_CERT, verify_cb) #Demand a certificate
            ctx.use_privatekey_file(configmanager.privatekeypath)
            ctx.use_certificate_file(configmanager.certificatepath)
            ctx.load_verify_locations(configmanager.cafilepath)
        except Exception as e:
            error = e[0]
            if (len(error)>0):  # ignore empty cafile error
                print error
        sslserversocket = SSL.Connection(ctx, socket.socket(socket.AF_INET,
                             socket.SOCK_STREAM))                
        # negotiate new secure connection port
        newport = SECUREPORT   
        sslserversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)     
        sslserversocket.bind(('', newport)) 
        sslserversocket.listen(5)
        while True:
                try:
                    sslcsocket, ssladdress = sslserversocket.accept()
                    address = format(ssladdress[0])
                    print "SSL connected"                
                    # receive data
                    data = sslcsocket.recv(4096)
                    self.conn.parseData(data, address, sslcsocket)
                    # emit new data dbus Signal      
                    self.conn.dbus_service_thread.emit_changed_signal()
                except Exception as e:
                    errnum = e[0]
                    print "Error " + str(e[0])
                finally:
                    # close connection
                    sslcsocket.shutdown()
                    sslcsocket.close() 


def verify_cb(conn, cert, errnum, depth, ok):
    # This obviously has to be updated
    #print "er"+str(errnum)
    #print "de"+str(depth)
    #print "ok "+str(ok)
    return ok


def main():
    app = Connector()
    app.run()

if __name__ == '__main__':
   try:
      main()
   except KeyboardInterrupt:
      print "\nServer stopped"
      pass
