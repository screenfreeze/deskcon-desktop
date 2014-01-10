import socket
from OpenSSL import SSL, crypto
import notificationmanager
import configmanager

DOWNLOAD_DIR = configmanager.get_download_dir()

def write_files(filenames, csocket):
    fname = filenames
    recsocket = csocket
    print fname
    filepath = DOWNLOAD_DIR + fname
    
    nfile = open(filepath, 'wb')
    recsocket.sendall('1')
    filesize = int(recsocket.recv(4096))
    loopcnt = filesize/4096
    if filesize%4096 != 0:
        loopcnt = loopcnt+1

    recsocket.sendall('1') # send ready
    for i in range(0, loopcnt):
        data_chunk = recsocket.recv(4096)
        nfile.write(data_chunk)
    nfile.close()

    #notificationmanager.buildFileReceivedNotification(filepath)
    return filepath


