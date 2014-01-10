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
import configmanager
from gi.repository import Gio, GLib, Gtk, GObject, Gdk
from OpenSSL import SSL, crypto
from dbusservice import DbusThread

HOST = configmanager.get_bindip()
PORT = int(configmanager.get_port())
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

    def run(self):
        GObject.threads_init()
        self.dbus_service_thread.start()        
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
            if (newstats.has_key('missedsmscount')): 
                self.mid_info['phones'][pos]['missedsmscount'] = newstats['missedmsgs']
            if (newstats.has_key('missedcallcount')): 
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

        elif (msgtype == "CLPBRD"): #not ready
            #pyperclip.setcb(message)
            notificationmanager.buildTransientNotification("Clipboard", message)   
            print "copy to clipboard"

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
            fname = message
            if (AUTO_ACCEPT_FILES):
                print "accepted"
                filetransfer.write_files(fname, csocket)
            else:
                accepted = notificationmanager.buildIncomingFileNotification(fname, csocket)
                print "wait for ui"       
                if (accepted):
                    print "accepted"
                    fpath = filetransfer.write_files(fname, csocket)
                    notificationmanager.buildFileReceivedNotification(fpath, self.open_file)
                else:
                    print "not accepted"
        else:
            print "ERROR: Non parsable Data received"

        #print json.dumps(self.mid_info)


    class TCPServer(SocketServer.TCPServer):

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
                # Initialize context
                ctx = SSL.Context(SSL.SSLv23_METHOD)
                ctx.set_options(SSL.OP_NO_SSLv2|SSL.OP_NO_SSLv3) #TLS1 and up
                ctx.set_verify(SSL.VERIFY_PEER|SSL.VERIFY_FAIL_IF_NO_PEER_CERT, verify_cb) #Demand a certificate
                ctx.use_privatekey_file(configmanager.privatekeypath)
                ctx.use_certificate_file(configmanager.certificatepath)
                ctx.load_verify_locations(configmanager.cafilepath)                
                sslserversocket = SSL.Connection(ctx, socket.socket(socket.AF_INET,
                                     socket.SOCK_STREAM))                
                #negotiate new secure connection port
                newport = 8026
                sslserversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)     
                sslserversocket.bind(('', newport)) 
                sslserversocket.listen(1)
                csocket.sendall(str(newport))            
                sslcsocket, ssladdress = sslserversocket.accept()
                sslserversocket.close()
                # receive data
                data = sslcsocket.recv(4096)
                connector.parseData(data, address, sslcsocket)
                # close connection
                sslcsocket.shutdown()
                sslcsocket.close()
              
            csocket.close()
            # emit new data dbus Signal      
            connector.dbus_service_thread.emit_changed_signal()


    def compose_sms(self, number, ip, port):
        subprocess.Popen([PROGRAMDIR+"/sms.py", ip, port, number], stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def open_file(self, path):
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", path], stdin=subprocess.PIPE, 
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            subprocess.Popen(["xdg-open", path], stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)


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
