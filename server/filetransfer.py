import socket
from OpenSSL import SSL, crypto
import notificationmanager
import configmanager

DOWNLOAD_DIR = configmanager.get_download_dir()

def write_files(filenames, csocket):
    print "write files"
    csocket.sendall('1') # accept send

    filepaths = []
    for filename in filenames:
        filepath = write_file(filename, csocket)
        filepaths.append(filepath)

    return filepaths


def write_file(filename, csocket):    
    recsocket = csocket
    filepath = DOWNLOAD_DIR + filename
    
    nfile = open(filepath, 'wb')
    filesize = int(recsocket.recv(4096))
    loopcnt = filesize/4096
    if filesize%4096 != 0:
        loopcnt = loopcnt+1

    recsocket.sendall('1') # send ready
    for i in range(0, loopcnt):
        data_chunk = recsocket.recv(4096)
        nfile.write(data_chunk)
    nfile.close()

    return filepath