import xbmc
import xbmcgui
import xbmcaddon
import dbus
import os
import spotifyplayer

import threading
import time


class RepeatEvery(threading.Thread):
    def __init__(self, interval, func, *args, **kwargs):
        threading.Thread.__init__(self)
        self.interval = interval  # seconds between calls
        self.func = func          # function to call
        self.args = args          # optional positional argument(s) for call
        self.kwargs = kwargs      # optional keyword argument(s) for call
        self.runable = True
    def run(self):
        while self.runable:
            self.func(*self.args, **self.kwargs)
            time.sleep(self.interval)
    def stop(self):
        self.runable = False


def getDBUSManager():
    try:
        bus = dbus.SessionBus(private=True)
        spotify = bus.get_object('org.mpris.MediaPlayer2.spotify', '/org/mpris/MediaPlayer2')
        properties_manager = dbus.Interface(spotify, 'org.freedesktop.DBus.Properties')
        return properties_manager
    except:
        return None
    
def monitor(thread2):
    if DebugLog:
        xbmc.log('Spotremote_Service - ping', level=xbmc.LOGDEBUG)
    manager = getDBUSManager()
    if not manager == None:
        try:
            status = str(manager.Get('org.mpris.MediaPlayer2.Player', 'PlaybackStatus'))
        except:
            status = ""
        if DebugLog:
            xbmc.log('Spotremote_Service - Spotify Status: ' + status, level=xbmc.LOGDEBUG)
        monitorProperty = xbmcgui.Window(10000).getProperty('Spotremote_Monitor')
        if DebugLog:
            xbmc.log('Spotremote_Service - monitor running: ' + monitorProperty, level=xbmc.LOGDEBUG)
        if not monitorProperty == 'Running' and status == "Playing":
            playing = xbmc.Player().isPlaying()
            if not playing:
                if DebugLog:
                    xbmc.log('Spotremote_Service - start monitor', level=xbmc.LOGDEBUG)
                thread2 = RepeatEvery(1, player.monitorChanges)
                thread2.start()
        else:
            if not thread2 == None:
                thread2.stop()

if __name__ == '__main__':
    thread = None
    thread2 = None
    my_addon = xbmcaddon.Addon()
    DebugLog = my_addon.getSetting('debug')
    if DebugLog == "true":
        DebugLog = True
    else:
        DebugLog = False
    player = spotifyplayer.SpotifyPlayer()
    thread = RepeatEvery(1, monitor, thread2)
    thread.start()
        
    if DebugLog:
        xbmc.log('Spotremote_Service - init', level=xbmc.LOGDEBUG)

    while not xbmc.abortRequested:
        try:
            stopflag = player.getStopFlag()
        except:
            stopflag = False
        if not stopflag == True:
            player = spotifyplayer.SpotifyPlayer()
        xbmc.sleep(1000)
    if DebugLog:
        xbmc.log('Spotremote_Service - ende', level=xbmc.LOGDEBUG)
    if not thread == None:
        thread.stop()
    if not thread2 == None:
        thread2.stop()
    sys.exit(0)
