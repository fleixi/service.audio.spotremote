import os
import sys
import xbmc
import dbus
import xbmcaddon
import xbmcgui

from subprocess import Popen, PIPE, call, check_output


class SpotifyPlayer(xbmc.Player):
    
    def __init__(self):
        super(SpotifyPlayer, self).__init__()
        
        my_addon = xbmcaddon.Addon()
        self.DebugLog = my_addon.getSetting('debug')
        self.SyncPulseaudio = my_addon.getSetting('pulseaudio')
        
        if self.DebugLog:
            xbmc.log('Spotremote_Player - init', level=xbmc.LOGDEBUG)
        
        try:
            p = Popen(['whereis', 'spotify'], stdin=PIPE, stdout=PIPE, stderr=PIPE)
            output, err = p.communicate()
            paths = output.split(" ")
            for i in paths:
                if "share" in i:
                    self.path = i.strip() + "/spotify"
        except:
            self.path = "/usr/share/spotify/spotify"
        self.monitor_enalbed = True
        self.Pause = False
        self.Next = False
        self.title = "Spotremote - init title"
        self.title_old = "Spotremote - init title_old"
        self.spotify = None
        self.properties_manager = None
        self.stopflag = True
        
    def getStopFlag(self):
        return self.stopflag
        
    def onPlayBackStarted(self):
        if self.DebugLog:
            xbmc.log('Spotremote_Player - PlayBackStarted', level=xbmc.LOGDEBUG)
        self.Pause = False
        try:
            status = str(self.properties_manager.Get('org.mpris.MediaPlayer2.Player', 'PlaybackStatus'))
        except:
            self.stopAll()
        if status == "Paused" :
            self.spotify.Play()
    
    def onPlayBackPaused(self):
        if self.DebugLog:
            xbmc.log('Spotremote_Player - PlayBackPaused', level=xbmc.LOGDEBUG)
        self.monitor_enalbed = True
        self.Pause = True
        try:
            status = str(self.properties_manager.Get('org.mpris.MediaPlayer2.Player', 'PlaybackStatus'))
        except:
            self.stopAll()
        if status == "Playing" :
            self.spotify.Pause()
            
    def onPlayBackResumed(self):
        if self.DebugLog:
            xbmc.log('Spotremote_Player - PlayBackResumed', level=xbmc.LOGDEBUG)
        self.onPlayBackStarted()

    def onPlayBackEnded(self):
        if self.DebugLog:
            xbmc.log('Spotremote_Player - PlayBackEnded', level=xbmc.LOGDEBUG)
        self.onPlayBackFinished()

    def onPlayBackFinished(self):
        if self.DebugLog:
            xbmc.log('Spotremote_Player - PlayBackFinished', level=xbmc.LOGDEBUG)
        self.monitor_enalbed = True
        self.Pause = True
        try:
            status = str(self.properties_manager.Get('org.mpris.MediaPlayer2.Player', 'PlaybackStatus'))
        except:
            self.stopAll()
        if status == 'Playing':
            self.spotify.Pause()
            
    def onPlayBackStopped(self):
        if self.DebugLog:
            xbmc.log('Spotremote_Player - PlayBackStopped', level=xbmc.LOGDEBUG)
        self.monitor_enalbed = False
        xbmc.sleep(1000)
        if self.isPlaying():
            if self.DebugLog:
                xbmc.log('Spotremote_Player - PlayBackNext', level=xbmc.LOGDEBUG)
            self.Next = True
            self.monitor_enalbed = True
        else:
            self.onPlayBackFinished()
            
    def generateMetadata(self):
        try:
            self.metadata = self.properties_manager.Get('org.mpris.MediaPlayer2.Player', 'Metadata')
        except:
            self.stopAll()
        self.title = self.metadata['xesam:title']
        self.album = self.metadata['xesam:album']
        self.artist = self.metadata['xesam:artist']
        self.duration = self.metadata['mpris:length'] / 1000000
        self.album_cover = self.metadata['mpris:artUrl']
        
    def generateDummyVideo(self):
        call(['ffmpeg' , '-y', '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=mono', '-t' ,str(self.duration), '-q:a', '0', '-acodec', 'wavpack', self.dummy_video])
    
    def playDummyVideo(self):
        play_item = xbmcgui.ListItem(path=self.dummy_video, iconImage=self.album_cover, thumbnailImage=self.album_cover)
        play_item.setInfo('music', {'duration': self.duration ,'title': self.title, 'album': self.album ,'artist': self.artist[0] })
        
        prev_item = xbmcgui.ListItem(path=self.dummy_video)
        prev_item.setInfo('music', { 'duration': 10 ,'title': "Previous"})
        
        next_item = xbmcgui.ListItem(path=self.dummy_video)
        next_item.setInfo('music', { 'duration': 10 ,'title': "Next"})
        
        pl=xbmc.PlayList(1)
        pl.clear()
        pl.add(self.dummy_video, prev_item)
        pl.add(self.dummy_video, play_item)
        pl.add(self.dummy_video, next_item)
        self.play(pl,play_item,False,1)
    
    def generateDummyVideoPath(self):
        my_addon = xbmcaddon.Addon('service.audio.spotremote')
        addon_dir = xbmc.translatePath( my_addon.getAddonInfo('path') )
        self.dummy_video = os.path.join(addon_dir, 'resources', 'data',  'dummy.wv')
    
    def removeDummyVideo(self):
        self.generateDummyVideo()
        os.remove(self.dummy_video)
    
    def controlVolume(self):
        if self.SyncPulseaudio:
            if self.DebugLog:
                xbmc.log('Spotremote_Player - Pulseaudio sync', level=xbmc.LOGDEBUG)
            self.pacmd = check_output(["pacmd", "list-sink-inputs"])
            self.indexs = self.pacmd.split("index: ")
            self.muted_kodi = None
            self.muted_spotify = None
            self.index_kodi = None
            self.index_spotify = None
            for i in self.indexs:
                if "Kodi" in i and not xbmc.abortRequested:
                    self.index_kodi = i.split("driver:")[0].strip()
                    self.volume_kodi = i.split("front-left: " )[1].split(" /")[0].strip()
                    self.muted_kodi = i.split("muted: " )[1].split("current")[0].strip()
                if "Spotify" in i and not xbmc.abortRequested:
                    self.index_spotify = i.split("driver:")[0].strip()
                    self.volume_spotify = i.split("front-left: " )[1].split(" /")[0].strip()
                    self.muted_spotify = i.split("muted: " )[1].split("current")[0].strip()
        
            if not self.index_kodi == None and not self.index_spotify == None and not xbmc.abortRequested:
                if not self.muted_kodi == self.muted_spotify and not xbmc.abortRequested:
                    if self.muted_kodi == "yes":
                        check_output(["pacmd", "set-sink-input-mute", self.index_spotify, str(1)])
                    else:
                        check_output(["pacmd", "set-sink-input-mute", self.index_spotify, str(0)])
        
                if not self.volume_kodi == self.volume_spotify and not xbmc.abortRequested:
                    check_output(["pacmd", "set-sink-input-volume", self.index_spotify, self.volume_kodi])
        
    def generateAndRun(self):
        self.generateMetadata()
        self.generateDummyVideoPath()
        self.generateDummyVideo()
    
    def getProcess(self):
        try:
            p = Popen(['ps', 'aux'], stdin=PIPE, stdout=PIPE, stderr=PIPE)
            output, err = p.communicate()
            process = output.split(self.path)[1].strip()
            return process
        except:
            return None
    
    def stopAll(self):
        if self.DebugLog:
            xbmc.log('Spotremote_Player - Stop All', level=xbmc.LOGDEBUG)
        xbmcgui.Window(10000).setProperty('Spotremote_Monitor', 'False')
        self.monitor_enalbed = False
        pl = xbmc.PlayList(1)
        pl.clear()
        self.stop()
        self.stopflag = False
        try:
            sys.exit(0)
        except SystemExit as e:
             os._exit(0)


    def getDBus(self):
        try:
            self.bus = dbus.SessionBus(private=True)
            self.spotify = self.bus.get_object('org.mpris.MediaPlayer2.spotify', '/org/mpris/MediaPlayer2')
            self.spotify = dbus.Interface(self.spotify, 'org.mpris.MediaPlayer2.Player')
            self.properties_manager = dbus.Interface(self.spotify, 'org.freedesktop.DBus.Properties')
        except:
            self.stopAll()

    def monitorChanges(self):
        running = self.getProcess()
        if self.spotify == None or self.properties_manager == None:
            self.getDBus()
        if running == None or running == "":
            self.stopAll()
        if self.monitor_enalbed and not xbmc.abortRequested:
            xbmcgui.Window(10000).setProperty('Spotremote_Monitor', 'Running')
            status = ""
            if self.isPlaying() and not xbmc.abortRequested and self.monitor_enalbed:
                status = self.getMusicInfoTag().getTitle()
                if status == 'Previous' and self.Next and not xbmc.abortRequested and self.monitor_enalbed:
                    if self.DebugLog:
                        xbmc.log('Spotremote_Player - Monitor Previous', level=xbmc.LOGDEBUG)
                    self.spotify.Previous()
                    self.spotify.Previous()
                    self.generateAndRun()
                elif status == 'Next' and self.Next and not xbmc.abortRequested and self.monitor_enalbed:
                    if self.DebugLog:
                        xbmc.log('Spotremote_Player - Monitor Next', level=xbmc.LOGDEBUG)
                    self.spotify.Next()
                    self.generateAndRun()
                elif status == 'Spotify' and not xbmc.abortRequested and self.monitor_enalbed:
                    if self.DebugLog:
                        xbmc.log('Spotremote_Player - Monitor Spotify', level=xbmc.LOGDEBUG)
                    self.generateAndRun()
                
                self.Next = False
                self.title_old = status
                self.generateMetadata()
            
            if not self.title == self.title_old and not xbmc.abortRequested and self.monitor_enalbed:
                    if self.DebugLog:
                        xbmc.log('Spotremote_Player - Monitor Title Cache', level=xbmc.LOGDEBUG)
                        xbmc.log('Spotremote_Player Title: old: ' + self.title_old, level=xbmc.LOGDEBUG)
                        xbmc.log('Spotremote_Player Title: new: ' + self.title, level=xbmc.LOGDEBUG)
                    if self.title == "Spotremote - init title":
                        self.generateMetadata()
                    self.title_old = self.title
                    self.generateDummyVideoPath()
                    self.generateDummyVideo()
                    self.playDummyVideo()
                
            try:
                status = str(self.properties_manager.Get('org.mpris.MediaPlayer2.Player', 'PlaybackStatus'))
            except:
                status = "Stopped"
            if not self.Pause and status == "Paused" and not xbmc.abortRequested and self.monitor_enalbed:
                if self.DebugLog:
                    xbmc.log('Spotremote_Player - Monitor Paused', level=xbmc.LOGDEBUG)
                self.Pause = True
                self.pause()
        
            elif self.Pause and status == "Playing" and not xbmc.abortRequested and self.monitor_enalbed:
                if self.DebugLog:
                    xbmc.log('Spotremote_Player - Monitor Played', level=xbmc.LOGDEBUG)
                if self.isPlaying():
                    self.pause()
                else:
                    self.play()
            
            pl=xbmc.PlayList(1)
            if pl.size() <= 2 and not xbmc.abortRequested and self.monitor_enalbed:
                if self.DebugLog:
                    xbmc.log('Spotremote_Player - Monitor Playlist reload', level=xbmc.LOGDEBUG)
                self.removeDummyVideo()
                self.generateAndRun()
                self.playDummyVideo()
                
            if not pl.getposition() == 1 and not self.Pause and not xbmc.abortRequested and self.monitor_enalbed:
                if self.DebugLog:
                    xbmc.log('Spotremote_Player - Monitor Playlist restart', level=xbmc.LOGDEBUG)
                    xbmc.log('Spotremote_Player - Monitor Restart position: ' + str(pl.getposition()), level=xbmc.LOGDEBUG)
                self.removeDummyVideo()
                self.generateAndRun()
                self.playDummyVideo()
            self.controlVolume()
