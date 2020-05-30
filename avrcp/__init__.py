#!/usr/bin/python3
import dbus, dbus.mainloop.glib, sys
import time
from gi.repository import GLib

playback_status = ''
current_info = ['No Title', 'No Artist', 'No Album', 'No Durration', 'No Position']

def on_property_changed(interface, changed, invalidated):
    global current_info
    if interface != 'org.bluez.MediaPlayer1':

        return
    for prop, value in changed.items():
        if prop == 'Status':
            playback_status = value
            display_status()
        elif prop == 'Track':
            if value.get('Title') != None:
                current_info[0] = value.get('Title')
            if value.get('Title') != None:
                current_info[1] = value.get('Artist')
            if value.get('Title') != None:
                current_info[2] = value.get('Album')
            #if value.get('Title') != None:
            #    current_info[3] = value.get('Duration')
            #if value.get('title') != None: 
            #    current_info[4] = value.get('Position')
                display_status()

def display_status(title='', artist='', album=''):
    global current_info
    if title == '':
        #print(current_info[0] + " | " + current_info[1] + " | " + current_info[2] + " | " + current_info[3] + " | " + current_info[4])
        return
    #print(title + " | " + artist + " | " + album)

def Next():
    player_iface.Next()
def Prev():
    player_iface.Previous()
def Play():
    player_iface.Play()
def Pause():
    player_iface.Pause()
def Stop():
    player_iface.Stop()

def Album():
    try:
        track_info = player_props.Get('org.bluez.MediaPlayer1', 'Track')
        if 'Title' in track_info:
            display_status(track_info['Title'], track_info['Artist'], track_info['Album'])
            return(track_info['Album'])
        else:
            #print('No title found, grabbing from history')
            display_status()
    except:
        pass
    return(current_info[0])

def Artist():
    try:
        track_info = player_props.Get('org.bluez.MediaPlayer1', 'Track')
        if 'Title' in track_info:
            display_status(track_info['Title'], track_info['Artist'], track_info['Album'])
            return(track_info['Artist'])
        else:
            #print('No title found, grabbing from history')
            display_status()
    except:
        pass
    return(current_info[0])

def TrackTitle():
    try:
        track_info = player_props.Get('org.bluez.MediaPlayer1', 'Track')
        if 'Title' in track_info:
            display_status(track_info['Title'], track_info['Artist'], track_info['Album'])
            return(track_info['Title'])
        else:
            #print('No title found, grabbing from history')
            display_status()
    except:
        pass
    return(current_info[0])

def TrackDuration():
    try:
        track_info = player_props.Get('org.bluez.MediaPlayer1', 'Track')
        if 'Duration' in track_info:
            display_status(track_info['Title'], track_info['Artist'], track_info['Album'])
            return(track_info['Duration'])
        else:
            #print('No title found, grabbing from history')
            display_status()
    except:
        pass
    return(current_info[0])

def TrackPosition():
    try:
        Track_Position= player_props.Get('org.bluez.MediaPlayer1', 'Position')
        #print(Track_Position)
        return(Track_Position)
        #if 'Position' in track_info:
        #    display_status(track_info['Title'], track_info['Artist'], track_info['Album'])
        #    return(track_info['Position'])
    except:
        print('No Position')
        return(0)
           #print('No title found, grabbing from history')
        display_status()
    #except:
    #    pass
    return(current_info[0])

def PlayingInfo():
    try:
        track_info = player_props.Get('org.bluez.MediaPlayer1', 'Track')
        if 'Title' in track_info:
            #display_status(track_info['Title'], track_info['Artist'], track_info['Album'])
            return(track_info)
        else:
            #print('No title found, grabbing from history')
            display_status()
    except:
        pass
    return(current_info)

def PlayerName():
    try: 
        Player_Name = player_props.Get('org.bluez.MediaPlayer1', 'Name')
        #print(Player_Name)
        return(Player_Name)
    except:
        pass

def PlayStatus():
    try:
        PlayStatus = player_props.Get('org.blue.MediaPlayer1', 'Status')
        #print(PlayStatus)
        return(PlayStatus)
    except:
        pass

def on_playback_control(fd, condition):
    str = fd.readline()
    #str = fd
    if str.startswith('play'):
        player_iface.Play()
    elif str.startswith('next'):
        player_iface,Next()
    elif str.startswith('prev'):
        player_iface.Previous()
    elif str.startswith('pause'):
        player_iface.Pause()
    
    elif str.startswith('status'):
        try:
            track_info = player_props.Get('org.bluez.MediaPlayer1', 'Track')
            if 'Title' in track_info:
                display_status(track_info['Title'], track_info['Artist'], track_info['Album'])
            else:
                #print('No title found, grabbing from history')
                display_status()
        except:
            #print('Track property missing from stream, grabbing from history')
            display_status()
    return True

#if __name__ == '__main__':
adapter=False
#def initadapter():
while not adapter:
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()
    obj = bus.get_object('org.bluez', "/")
    mgr = dbus.Interface(obj, 'org.freedesktop.DBus.ObjectManager')
    for path, ifaces in mgr.GetManagedObjects().items():
        adapter = ifaces.get('org.bluez.MediaPlayer1')
        if not adapter:
            continue
        player = bus.get_object('org.bluez', path)
        player_iface = dbus.Interface(player, dbus_interface='org.bluez.MediaPlayer1')
        player_props = dbus.Interface(player, "org.freedesktop.DBus.Properties")
        break

    if not adapter:
        #sys.exit('Error: Media Player not found.')
        print('Waiting for BT connection')
        time.sleep(2)
    elif adapter:
        print('BT Device connected')
#initadapter()
#while not adapter:
#    print('Waiting for BT Connection')
#    time.sleep(1)
#    initadapter()

#print(PlayStatus())
#print(TrackDuration())
#print(TrackPosition())
#print(PlayerName())
bus.add_signal_receiver(
        on_property_changed,
        bus_name='org.bluez',
        signal_name='PropertiesChanged',
        dbus_interface='org.freedesktop.DBus.Properties')
#GLib.io_add_watch(sys.stdin, GLib.IO_IN, on_playback_control)
#GLib.MainLoop().run()
