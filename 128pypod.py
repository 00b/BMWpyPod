#!/usr/bin/python3
'''
-Revice commands from car USB/Head unit
-Parse & respond to commands
-Translate and pass metadata from avrcp device (phone) over serial to Head unit.
-Translate and pass commands (play, pause, next, prev) to avrcp device (phone). 

Super crap and ugly code below...

'''

import serial
import time

#following lib to come. 
import avrcp
#import btbdc

#Setup serial port:
ser = serial.Serial() # open serial port
ser.port = '/dev/ttyS0'
#ser.port = '/dev/ttyACM0'
ser.baudrate = 19200 
#ser.baudrate =57600 #turns out the car likes 57600
ser.bytesize = serial.EIGHTBITS
ser.parity = serial.PARITY_NONE
ser.stopbits = serial.STOPBITS_ONE
ser.timeout = 2

#name to report to headunit/car.
ipodname='128piPod'

'''
localecho will print the data sent out when True:
remoteecho will print the data received when True:
'''
localecho=True
remoteecho=False

'''
Car appears to send first 2 commands  
mode 4 request and ipod type at 19200, 
then many other commands at 57600. 
If bumpaudrate is True baud rate will incrase to 57600 
after ipod type command is received. 
b'\xffU\x03\x04\x00\x12\xe7'  FF 55 03 04 00 12 E7 
'''
bumpbaudrate=True

#set inital start states 
polling=False
runningmode=[0x00]
#playing=False
BTconnected=False
indexpos=0


#open serial port...or fail. 
try:
    ser.open()
    print(ser.isOpen)
    print(ser.name) # check which port was really used
    ser.flushInput()
except:
    print('error opening serial port')
    exit()

def sersend(val):
    #print('sending: ' + str(val))
    if localecho:
        try:
            print('>> ' + str(bytes(val)))
        #print(val)
        except:
            print('error: with ' + str(val))

    ser.write(serial.to_bytes(val))

def IsPlaying():
    FirstPos=avrcp.TrackPosition()
    time.sleep(.01) #give it a bit time to advance. 
    #if the values match not playing. 
    if FirstPos == avrcp.TrackPosition():
        return(False)
    else:
        return(True)

def checksumer(val):
    """
    Step 1 Put everthing in in a list as a byte
    Step 2 checksumer(thatlist)
    Step 3 checksum calculated and returned. 
    """
    #Incorrect can result in value of 256
    #checksum=[(0x100 - ( sum(val) & 0xFF))]
    #Hopefully corrected... 
    checksum=[(0x100 - sum(val))& 0xff]
    return(checksum)

def cmdr(mode,sendthis):
    """
    Build responses/commands to queries/commands.
    prepends mode to sendthis variarble
    calculates length and prepends to sendthis
    gets checksum and appends to sendthis
    prepends 0xff 0x55 to sendthis.
    """
    header=[0xFF,0x55]
    #mode=[0x04]
    serresp=mode+sendthis
    serresp=[len(serresp)]+serresp
    serresp=serresp+checksumer(serresp)
    serresp=header+serresp
    return(serresp)

def ack(cmdtoack):
    '''
    This sends a sucesfull ack when called. 

    Mode 4 Ack:
        0xFF Header
        0x55 Start of packet
        0x06 Length
        0x04 Lingo/Mode
        0x00 command id bits (15:8)/ack
        0x01 command id bits (7:0)
        0xNN status 0x00 sucess. 
        0xNN command being acked.
        0xNN checksum
    Mode 3 Ack:
        0xFF Header
        0x55 Start of packet
        0x04 Length
        0x03 Lingo/Mode
        0x00 command (ack)
        0xNN status 0x00 sucess.
        0xNN command being acked. 
        0xNN checksum
    Mode 2 Ack:
        0xFF Header
        0x55 Start of packet
        0X04 Length
        0x02 Lingo/Mode
        0x01 command id/ACK
        0xNN Status 0x00 sucess.
        0xNN command acked. 
        0xNN checksum
    Mode 0 Ack:
        0xFF Header
        0x55 Start of packet
        0x04 Length
        0x02 command (ack)
        0xNN result (0x00 sucess)
        0xNN command acked.
        0xNN checksum
    '''
    cmdlingo=cmdtoack[3]
    if cmdtoack[3] == 4:
        print('Mode/Lingo 4 ack')
        ack=[0x00,0x01,0x00,0x00] 
        cmdacked=[cmdtoack[5]]
        #ack=ack+cmdacked
        #cmdr([cmdlingo],ack)
    elif cmdtoack[3]==3:
        Print('Mode/Lingo 3 ack')
        ack=[0x03,0x00,0x00]
        cmdacked=[cmdtoack[4]]
        #ack=ack+cmdacked
        #cmdr([cmdlingo],ack)
    elif cmdtoack[3]==2:
        Print('Mode/Lingo 2 ack')
        ack=[0x02,0x01,0x00]
        cmdacked=[cmdtoack[4]]
        #ack=ack+cmdacked
        #cmdr([cmdlingo],ack)
    elif cmdtoack[3]==0:
        print('Mode/Ling 0 ack')
        ack=[0x00,0x02,0x00]
        cmdacked=[cmdtoack[4]]

    ack=ack+cmdacked 
    return(cmdr([cmdlingo],ack))

def parsedata(parsethis):
    global runningmode
    global polling
    #global playing
    global indexpos

    '''
    NO IDEA WHAT TO DO HERE YET!!! 
    Brute force with if/elif statements? 
    actually parse things out... seems really hard. 
    Cleary went ham/brute force with the ifs & elifs... sorry. maybe refactor latr. 
    '''
    #might be able to delete the mode 2 commands if the car never uses these 
    mode2req = b'\xffU\x03\x00\x01\x02\xfa'
    mode2play = b'\xffU\x04\x02\x00\x00\x01\xf9'
    mode2playpause= b'\xffU\x03\x02\x00\x01\xfa' 
    mode2stop = b'\xffU\x03\x02\x00\x80\xfb'
    mode2release=b'\xffU\x03\x02\x00\x00\xfb'
    mode2pause= b'\xffU\x04\x02\x00\x00\x02\xf8'
    mode2next = b'\xffU\x03\x02\x00\x08\xf3'
    mode2prev = b'\xffU\x03\x02\x00\x10\xeb'
    mode2shuft = b'\xffU\x04\x02\x00\x00\x80z'
    
    Identify = b'\xffU\x03\x00\x01\x04\xf8'
    IdentifyDeviceLingoes=b'\xffU\x0e\x00\x13\x00\x00\x00\x11\x00\x00\x00\x00\x00\x00\x00\x00\xce'
    EnterRemoteUIMode = b'\xffU\x02\x00\x05\xf9'
    ExitRemoteUIMode = b'\xffU\x02\x00\x06\xf8'
    RequestRemoteUIMode =  b'\xffU\x02\x00\x03\xfb'
    RequestiPodName = b'\xffU\x03\x04\x00\x14\xe5'
    RequestProtocolVersion = b'\xffU\x03\x04\x00\x12\xe7' 
    RequestLingo0ProtocolVersion = b'\xffU\x03\x00\x0f\x00\xee'
    RequestLingo4ProtocolVersion = b'\xffU\x03\x00\x0f\x04\xea' 
    RequestLingo0AProtocolVersion= b'\xffU\x03\x00\x0f\n\xe4'
    RequestiPodOptions= b'\xffU\x02\x00$\xda'
    RequestiPodName=b'\xffU\x02\x00\x07\xf7'
    RequestiPodSerialNum=b'\xffU\x02\x00\x0b\xf3'
    RequestiPodSoftwareVersion=b'\xffU\x02\x00\t\xf5'
    RequestiPodModelNum=b'\xffU\x02\x00\r\xf1'
    RetAccessoryInfo=b'\xffU\x07\x00(\x00\x00\x00\x00\x01\xd0'
    ResetDBSelection=b'\xffU\x03\x04\x00\x16\xe3'
    RetrieveCategorizedDatabaseRecordsPlayLists=b'\xffU\x0c\x04\x00\x1a\x01\x00\x00\x00\x01\x00\x00\x00\x02\xd2'
    RetrieveCategorizedDatabaseRecordsTracks=b'\xffU\x0c\x04\x00\x1a\x05\x00\x00\x00\x00\x00\x00\x00\x02\xcf' 
    SelectSortDBRecordByName = b'\xffU\t\x04\x008\x01\x00\x00\x00\x00\x04\xb6'
    SelectSortDBRecordByAlbum = b'\xffU\t\x04\x008\x01\x00\x00\x00\x00\x03\xb7'

    GetMonoDisplayImageLimits=b'\xffU\x03\x04\x003\xc6'
    GetColorDisplayImageLimits=b'\xffU\x03\x04\x009\xc0'
    GetCurrentPlayingTrackChapterInfo=b'\xffU\x03\x04\x00\x02\xf7'
    GetPlayStatus = b'\xffU\x03\x04\x00\x1c\xdd'
    GetNumberCategorizedDBRecordsPlayLists=b'\xffU\x04\x04\x00\x18\x01\xdf'
    GetNumberCategorizedDBRecordsTracks=b'\xffU\x04\x04\x00\x18\x05\xdb'
    GetCurrentPlayingTrackIndex = b'\xffU\x03\x04\x00\x1e\xdb'
    GetShuffle = b'\xffU\x03\x04\x00,\xcd'
    GetRepeat = b'\xffU\x03\x04\x00/\xca'
    GetNumPlayingTracks = b'\xffU\x03\x04\x005\xc4'
    
    PlayControlPlayPause = b'\xffU\x04\x04\x00)\x01\xce'
    PlayControlStop = b'\xffU\x04\x04\x00)\x02\xcd'
    PlayControlNext = b'\xffU\x04\x04\x00)\x03\xcc'
    PlayControlPrev = b'\xffU\x04\x04\x00)\x04\xcb'
    PlayControlEndFFRew = b'\xffU\x04\x04\x00)\x07\xc8'
    PlayControlStartFF = b'\xffU\x04\x04\x00)\x05\xca' 
    PlayControlStartRew = b'\xffU\x04\x04\x00)\x06\xc9' #checksum might be incorrect.

    SetCurrentPlayingTrack = b'\xffU\x07\x04\x007\x00\x00\x00\x01\xbd'
    SetPlayStatusChangeNotificationOn = b'\xffU\x04\x04\x00&\x01\xd1'
    SetPlayStatusChangeNotificationOff =b'\xffU\x04\x04\x00&\x00\xd2'
    

    #The following are matching with startswith if parsethis.startswith(X): 
    #GetIndexedPlayingTrackTitle = b'\xffU\x07\x04\x00 \x00\x00\x00\x01\xd4' 
    SetShuffle = b'\xffU\x05\x04\x00.'
    GetIndexedPlayingTrackTitle = b'\xffU\x07\x04\x00 '
    #GetIndexedPlayingTrackArtistName = b'\xffU\x07\x04\x00#'
    GetIndexedPlayingTrackArtistName = b'\xffU\x07\x04\x00"'
    GetIndexedPlayingTrackAlbumName = b'\xffU\x07\x04\x00$'
    GetIndexedPlayingTrackInfoComposer = b'\xffU\n\x04\x00\x0c\x06' #\x00\x00\x00\x03\xff\xff\xdf' ff550a04000c0600000003ffffdf
    GetIndexedPlayingTrackInfoGenre = b'\xffU\n\x04\x00\x0c\x05'   #\x00\x00\x00\x03\xff\xff\xe0' ff550a04000c0500000003ffffe0 
    GetIndexedPlayingTrackInfoTrackRelaseDate =  b'\xffU\n\x04\x00\x0c\x02' #\x00\x00\x00\x03\x00\x00\xe1' ff550a04000c02000000030000e1


    #Clearly i went brute with the ifs... 
    if parsethis == RequestiPodName:
        print('Name Request')
        #ipodname=list(b'128piPod')
        resptype=[0x00,0x15]
        terminator=[0x00]
        sersend(cmdr([0x04],resptype + list(ipodname.encode()) + terminator))
        #sersend(b'\ixffU\x0b\x04\x00\x15128iPod\x00\xb5')
    
    elif parsethis == RequestiPodName:
        print('RequestiPodName')
        resptype=[0x00,0x08]
        terminator=[0x00]
        sersend(cmdr([0x02],resptype + list(ipodname.encode()) + terminator))
        #b'\xffU\n\x00\x08128iPod\x00\xc7'

    elif parsethis == RequestiPodSerialNum:
        print('RequestiPodSerialNum')
        sersend(b'\xffU\x0e\x00\x0c8K644SQVV9R\x00\xea')
        #response taken direct from ipod classic 80gig 5.5 gen.
        #change this later... 

    elif parsethis == RequestiPodModelNum:
        print('RequestiPodModelNum')
        sersend(b'\xffU\x0e\x00\x0e\x00\x0b\x00\x11MA450LL\x00\t')
        #response taken direct from ipod classic 80gig 5.5 gen. 

    elif parsethis == RequestiPodSoftwareVersion:
        print('RequestiPodSoftwareVersion')
        sersend(b'\xffU\x05\x00\n\x01\x03\x00\xed')
        #response taken direct from ipod classic 80gig 5.5 gen. 

    #Duplicate elif and the one below appears to be doing more... 
    #elif parsethis == RequestRemoteUIMode:
    #    print('RequestRemoteUIMode')
    #    sersend(b'\xffU\x03\x00\x04\x01\xf8')
    #    #avrcp.Pause()
       #polling=False
        #playing=False
    
    
    elif parsethis == ExitRemoteUIMode:
        print('ExitRemoteUIMode')
        #need a pending ack and an ack. 
        sersend(cmdr([0x00],[0x02,0x06,0x06,0x00,0x00,0x0B,0xB8]))
        sersend(ack(parsethis))
        avrcp.Stop()
        #playing=False
        polling=False
    
    elif parsethis == EnterRemoteUIMode:
        print('EnterRemoteUIMode:')
        #sersend(ack(parsethis)) #
        sersend(b'\xffU\x08\x00\x02\x06\x05\x00\x00\x0b\xb8(\xffU\x04\x00\x02\x00\x05\xf5')
        #response taken direct from ipod classic 80 gig 5.5 gen. 
        #response is ACK with the time it might take and an ACK when its done. 
        #avrcp.Play()
        #playing=True
        #polling=True
    
    elif parsethis == RequestRemoteUIMode:
        '''
        The iPod returns the current operating mode of the iPod UI. This is either Standard UI mode or
        Extended Interface mode. If the returned mode byte is nonzero (true), the iPod is in Extended Interface
        mode. This command may be used only if the accessory requests Lingo 0x04, using Identify or
        IdentifyDeviceLingoes.
        '''
        if runningmode == [0x04]:
            print('RequestRemoteUIMode : Mode is 0x04 (extended) sending 0x01')
            sersend(cmdr([0x00],[0x04,0x01]))
        else:
            print('RequestRemoteUIMode : Mode is not 0x04 (extended) sending 0x00')
            sersend(cmdr([0x00],[0x04,0x00]))

    elif parsethis == GetShuffle:
        print('GetShuffle')
        sersend(cmdr([0x04],[0x00,0x2D,0x00]))

    elif parsethis == GetRepeat:
        print('GetRepeat')
        sersend(cmdr([0x04],[0x00,0x30,0x02]))

    elif parsethis == GetNumPlayingTracks:
        print('GetNumPlayingTracks')
        #b'\xffU\x07\x04\x006\x00\x00\x00\x00\xbf ff 55 07 04 00 36 00 00 00 00bf
        #sersend(cmdr([0x04],[0x00,0x36,0x00,0x00,0x00,0x00]))
        #NumTracks=3 
        sersend(cmdr([0x04],[0x00,0x36,0x00,0x00,0x00,0x02]))

    elif parsethis == GetColorDisplayImageLimits:
        print('GetColorDisplayImageLimits')
        sersend(b'\xffU\r\x04\x00:\x016\x00\xa8\x02\x016\x00\xa8\x03\xf2')
        #response taken direct from ipod classic 80 gig 5.5 gen.

    elif parsethis == GetMonoDisplayImageLimits:
        print('GetMonoDisplayImageLimits')
        sersend(b'\xffU\x08\x04\x004\x016\x00\xa8\x01\xe0')
        #response taken direct from ipod classic 80 gig 5.5 gen.

    elif parsethis == ResetDBSelection:
        print('ResetDBSelection')
        #ACK!
        sersend(ack(parsethis))
    
    elif parsethis == GetNumberCategorizedDBRecordsPlayLists:
        print('GetNumberCategorizedDBRecordsPlayLists')
        #returns 1, maybe 2. 
        sersend(cmdr([0x04],[0x00,0x19,0x00,0x00,0x00,0x01]))

    elif parsethis == GetNumberCategorizedDBRecordsTracks:
        print('GetNumberCategorizedDBRecordsTracks')
        #returns 3. which might be 4 if it indexes at 0... 
        sersend(cmdr([0x04],[0x00,0x19,0x00,0x00,0x00,0x02]))
    
    elif parsethis == SetCurrentPlayingTrack:
        print('SetCurrentPlayingTrack')
        #ACK!
        sersend(ack(parsethis))

    elif parsethis.startswith(SetShuffle):
        print('SetShuffle Mode')
        #ACK!
        sersend(ack(parsethis))

    elif parsethis == SelectSortDBRecordByName or parsethis == SelectSortDBRecordByAlbum:
        print('SelectSortDBRecord')
        #ACK!
        sersend(ack(parsethis))

    elif parsethis == RetrieveCategorizedDatabaseRecordsPlayLists:
        #b'\xffU\x0c\x04\x00\x1a\x01\x00\x00\x00\x01\x00\x00\x00\x02\xd2' 
        print('RetrieveCategorizedDatabaseRecordsPlayLists') 
        resptype=[0x00,0x1B]
        terminator=[0x00]
        #plnames=['128piPod!','PL1','PL2']
        plnames=['128piPod!','Fake Playlist']
        #plnames=['128piPod!']
        for plnum, playlists in enumerate(plnames, start=0):
            playlist=list(playlists.encode())
            playlist=[plnum]+playlist
            sersend(cmdr([0x04],resptype + playlist + terminator))
            time.sleep(.02)

    elif parsethis == RetrieveCategorizedDatabaseRecordsTracks:
        print('RetrieveCategorizedDatabaseRecordsTracks')
        print('<< ' + str(parsethis) + ' ' + parsethis.hex())
        resptype=[0x00,0x1B]
        terminator=[0x00]
        tracknames=['Fake Track #0','Fake Trak #1','Fake Track #2']
        for tracknum, tracks in enumerate(tracknames, start=0):
            track=list(tracks.encode())
            track=[tracknum]+track
            sersend(cmdr([0x04],resptype + track + terminator))
            time.sleep(.02)

    elif parsethis == GetCurrentPlayingTrackIndex:
        print('GetCurrentPlayingTrackIndex')
        resptype=[0x00,0x1F]
        if IsPlaying():
            sersend(cmdr([0x04],resptype+list(indexpos.to_bytes(4, byteorder='big', signed='true'))))
        else:
            sersend(cmdr([0x04],resptype+[0xFF,0xFF,0xFF,0xFF]))

    elif parsethis.startswith(GetIndexedPlayingTrackAlbumName):
        print('GetIndexedPlayingTrackAlbumName')
        resptype=[0x00,0x25]
        terminator=[0x00]
        #place holder album: 
        #album='Always Outnumbered, Never Outgunned'
        album=avrcp.Album()
        album=list(album.encode())
        sersend(cmdr([0x04],resptype + album + terminator))

    elif parsethis.startswith(GetIndexedPlayingTrackArtistName):
        print('GetIndexedPlayingArtistName')
        artistname=avrcp.Artist()
        resptype=[0x00,0x23]
        terminatior=[0x00]
        artistname=list(artistname.encode())
        sersend(cmdr([0x04],resptype + artistname + terminatior))

    elif parsethis.startswith(GetIndexedPlayingTrackTitle):
        print('GetIndexedPlayingTrackTitle') 
        trackname=avrcp.TrackTitle()
        resptype=[0x00,0x21]
        terminator=[0x00]
        trackname=list(trackname.encode())
        sersend(cmdr([0x04],resptype+trackname+terminator))


    #Needs work
    #Check a real ipod
    elif parsethis.startswith(GetIndexedPlayingTrackInfoGenre):
        print('GetIndexedPlayingTrackInfoGenre')
        resptype=[0x00,0x0D,0x05]
        terminator=[0x00]
        genre='Music'
        genre=list(genre.encode())
        sersend(cmdr([0x04],resptype+genre+terminator))

    #Needs work
    #Check a real ipod
    elif parsethis.startswith(GetIndexedPlayingTrackInfoComposer):
        print('GetIndexedPlayingTrackInfoComposer')
        resptype=[0x00,0x0D,0x06]
        terminator=[0x00]
        composer='Somebody'
        composer=list(composer.encode())
        sersend(cmdr([0x04],resptype+composer+terminator))
    #Needs work 
    #Check a real ipod
    
    elif parsethis.startswith(GetIndexedPlayingTrackInfoTrackRelaseDate):
        print('GetIndexedPlayingTrackInfoTrackReleaseDate')
        resptype=[0x00,0x0D,0x02]
        #reldate bytes: Seconds, Minutes, Hours, Day of Month, Month, Year Year, Day of week..
        reldate=[0x00,0x00,0x00,0x01,0x01,0x07,0xD0,0x06]
        #hopefully that encodes to 12:00:00 January 1 2000 Saturday 
        sersend(cmdr([0x04],resptype+reldate))
    
    elif parsethis == GetCurrentPlayingTrackChapterInfo:
        print('GetCurrentPlayingTrackChapterInfo')
        #Think this is a ping... Resp direct from real ipod.
        #sersend(b'\xffU\x06\x04\x00\x01\x02\x00\x02\xf1')
        #ACK?
        #above assumption is clearly wrong. 
        #but sending back an ack/error maybe a good idea here. 

    elif parsethis == RequestProtocolVersion: 
        print('iPod Type') 
        #Response is direct from real ipod 5.5 gen 80gb. 
        sersend(b'\xffU\x05\x04\x00\x13\x01\x0c\xd7')
        if bumpbaudrate:
            print('Increaseing Baud Rate to 57600')
            ser.baudrate=57600
        
        #response is direct from real ipod touch. 
        #sersend(b'\xffU\x05\x04\x00\x13\x01\x0e\xd5')
        #response from from another real ipod touch. Same ias ipod 5th gen...
        #sersend(b'\xffU\x05\x04\x00\x13\x01\x0c\xd7')
        #response from carpro bluetooth thing
        #also from podemu app. 
        #sersend(b'\xffU\x05\x04\x00\x13\x01\x0e\xd5')
        #response from someone elses phone. 
        #sersend(b'\xffU\x05\x04\x00\x13\x01\x0e\xd5')
        #polling=True
    
    elif parsethis == RequestLingo0ProtocolVersion:
        print ('RequestLingo 0 ProtocolVersion')
        sersend(b'\xffU\x05\x00\x10\x00\x01\x06\xe4')
        #response taken direct from ipod classic 80 gig 5.5 gen. 

    elif parsethis == RequestLingo4ProtocolVersion:
        print ('RequestLingo 4 ProtocolVersion')
        sersend(b'\xffU\x05\x00\x10\x04\x01\x0c\xda')
        #sersend(b'\xffU\x04\x00\x02\x04\x0f\xe7') 
        #response taken direct from ipod classic 80 gig 5.5 gen. 

    elif parsethis == RequestLingo0AProtocolVersion:
        print('RequestLingo0AProtocolVersion')
        sersend(b'\xffU\x05\x00\x10\n\x01\x01\xdf')
        #response taken direct from ipod classic 80 gig 5.5 gen. 

    elif parsethis == IdentifyDeviceLingoes:
        print('IdentifyDeviceLingoes')
        sersend(b'\xffU\x04\x00\x02\x00\x13\xe7\xffU\x03\x00\'\x00\xd6') 
        #response taken direct from ipod classic 80 gig 5.5 gen. 
    
    elif parsethis == RequestiPodOptions:
        print('RequestiPodOptions')
        sersend(b'\xffU\n\x00%\x00\x00\x00\x00\x00\x00\x00\x01\xd0')
        #response taken direct from ipod classic 80 gig 5.5 gen. 
    
    elif parsethis == RetAccessoryInfo:
        print('RetAccessoryInfo')

    elif parsethis == SetPlayStatusChangeNotificationOn:
        print('SetPlayStatusChangeNotificationOn/Polling mode ON')
        polling=True
        #ACK!  
        sersend(ack(parsethis))
        #sersend(b'\xffU\x04\x04\x00&\x00\xd2')

    elif parsethis == SetPlayStatusChangeNotificationOff:
        print('SetPlaySTatusChangeNotificationOff/Polling mode OFF')
        polling=False
        sersend(ack(parsethis))
        #sersend(b'\xffU\x04\x04\x00&\x00\xd2')
        #Use an ACK? 

    elif parsethis == mode2req:
        print('Mode 2 Request: Entering mode 2')
        runningmode = [0x02]

    elif parsethis == mode2playpause:
        print('Mode 2 Play/Pause')

    elif parsethis == mode2play:
        print('Mode 2 Play')
        #playing=True

    elif parsethis == mode2pause:
        print('Mode 2 Pause')

    elif parsethis == mode2stop:
        print('Mode 2 Stop')
        #playing=False
    elif parsethis == mode2release:
        print('Mode 2 Release')

    elif parsethis == mode2next:
        print('Mode 2 Next Track')

    elif parsethis == mode2prev:
        print('Mode 2 Prev Track')

    elif parsethis == mode2shuft:
        print('Mode 2 Shufle toggle')
    
    elif parsethis == Identify:
        print('Identify Received')
        runningmode = [0x04]
        #ipod doesn't send anything back on these... 

    elif parsethis == PlayControlNext:
        print('PlayControl Next')
        avrcp.Next()  
        #ACK
        sersend(ack(parsethis))

    elif parsethis == PlayControlPrev:
        print('PlayControlPrevious')
        #if BTConnected:
            #avrcp(previous)
        #ACK
        avrcp.Prev()
        sersend(ack(parsethis))

    elif parsethis == PlayControlPlayPause:
        print('PlayControlPlay/Pause')
        if IsPlaying():
            #playing=False
            avrcp.Pause()
        else:
            #playing=True
            avrcp.Play()
        #ACK!
        sersend(ack(parsethis))
        
    elif parsethis == PlayControlStop:
        print('PlayControlStop')
        #avrcp(stop or pause)?
        avrcp.Stop()
        #playing=False
        #ACK!
        sersend(ack(parsethis))

    elif parsethis == PlayControlEndFFRew:
        print('PlayControlEndFFRew')
        #ACK!
        sersend(ack(parsethis))

    elif parsethis == GetPlayStatus:
        #print('GetPlayStatus')
        if IsPlaying():
            PlayStatus=[0x01]
            print('GetPlayStatus: Playing sending status 0x01 (playing)')
        else: #if not playing paused
            PlayStatus=[0x02]
            print('GetPlayStatus: Not Playing sending status to 0x02 (paused)')
        #resp 0x00 0x1D +length 0x00 0x00 0x00 + time in ms :0x00 0x00 0x00 0x00 + status=0x0 stop, 0x01 playing, 0x02 paused
        resptype=[0x00,0x1D]
        #tracklength=avrcp.TrackDuration()
        #tracklengthbytes=[(tracklength >> 24) & 0xff,(tracklength >> 16) & 0xff, (tracklength >> 8) & 0xff, tracklength & 0xff]
        #playpos=avrcp.TrackPosition()
        #playposbytes=[(playpos >> 24 ) &  0xFF,(playpos >> 16) & 0xff, (playpos >> 8) & 0xff, playpos & 0xff]
        #lengthbytes=[0x00,0xf1,0x00,0x00]
        #encode a randomish time from the status change routine?
        #timecode=[0x00,0x00,0x0F,0x12] 
        #status=[0x01]
        #sersend(cmdr([0x04],resptype + length + timecode + status))
        #sersend(cmdr([0x04],resptype + tracklengthbytes + playposbytes + PlayStatus))
        sersend(cmdr([0x04],resptype + list(avrcp.TrackDuration().to_bytes(4, byteorder='big',signed='True')) + list(avrcp.TrackPosition().to_bytes(4, byteorder='big',signed='True')) + PlayStatus))
        
   else:
        TextColor='\033[91m'
        ResetText='\033[0m'
        print(TextColor + 'Unknown: ' + str(parsethis) +' '+ parsethis.hex()  +ResetText)

#get info form player. 
currplay=avrcp.PlayingInfo()

while True:
    if polling and IsPlaying():
        #Send track playback postion in miliseconds. 
        print('PlayStatusChangeNotification Enabled (polling) and player playing sending position:')
        sersend(cmdr([0x04],[0x00,0x27,0x04] + list(avrcp.TrackPosition().to_bytes(4, byteorder='big',signed='True'))))
    if polling and currplay != avrcp.PlayingInfo():
        print('PlayStatusChangeNotification Enabled (polling) sending track changed')
        indexpos = indexpos + 1
        if indexpos > 2:
            indexpos = 0
        #Send Playback track changed 0x01 New track record index (32 bits)
        #in the indexposh value shouldn't ever be more than 2 but if it is it should be fine.
        sersend(cmdr([0x04],[0x00,0x27,0x01] + list(indexpos.to_bytes(4, byteorder='big',signed='True'))))
        currplay=avrcp.PlayingInfo()
    
    data=[] #0 = headers , 1 = length + mode, 3 = command and parameters
    serdata = ser.read(1) #read a byte from the serial port. 
    if (len(serdata) == 1):
        if (serdata[0] == 0xFF):
            serdata = ser.read(1) #read another byte from the serial port.
            if (serdata[0] == 0x55):
                data.append(bytes([0xFF,0x55]))
                serdata = ser.read(2)
                data.append(serdata)
                length = serdata[0]
                serdata = ser.read(length)
                data.append(serdata)
                fullcommand = data[0]+data[1]+data[2]
                if remoteecho:
                    print('<< ' + str(fullcommand) + ' ' +fullcommand.hex())
                parsedata(fullcommand)
        else:
            print(str(serdata) + ' ' + serdata.hex()) 

ser.close()
