import dbus
import subprocess
import time

def control(data):
    mediacmd = data.split("::")[0]
    mediaplayer = data.split("::")[1].lower()
    
    player = getPlayerProxy(mediaplayer)
    if (not player):
        startPlayer(mediaplayer)    
        player = getPlayerProxy(mediaplayer)
        
    if (mediacmd == "PLAY"):
        player.PlayPause()
    elif (mediacmd == "NEXT"):
        player.Next()
    elif (mediacmd == "PREVIOUS"):
        player.Previous()
   
def getPlayerProxy(pname):
    bus = dbus.SessionBus()

    if (pname == "default"):
        objname = ""
        names = bus.list_names()
        for name in names:
            if (name.startswith("org.mpris.")):  #first player it finds
                objname = name
                break

        try:
            proxy = bus.get_object(objname, '/org/mpris/MediaPlayer2')            
            player = dbus.Interface(proxy, 'org.mpris.MediaPlayer2.Player')
        except:
            return None

    else:
        try:
            proxy = bus.get_object('org.mpris.MediaPlayer2.'+pname, #specific player
                '/org/mpris/MediaPlayer2')                
            player = dbus.Interface(proxy, 'org.mpris.MediaPlayer2.Player')
        except:
            return None
        
    return player

# find default media player
def getDefaultPlayer():
    xdgmime = subprocess.Popen(['xdg-mime', 'query', 'default', 'audio/x-mpeg'],
                stdout=subprocess.PIPE)
    (vout, verr) = xdgmime.communicate()
    desktopfile = vout.strip().split(".")
    playername = desktopfile[0]
    return playername
    
def startPlayer(pname):
    if (pname == "default"):
        try:
            pname = getDefaultPlayer()
        except:
            return

    subprocess.Popen([pname], stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(5)
