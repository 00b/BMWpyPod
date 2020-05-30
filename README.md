i# BluetoothPiPodForBMW6FL

Allows audio playback from Android devices with bluetooth (AVRCP & A2DP) via Raspberry Pi and shows current playing track information and maintaining control from stereo and wheel for next and previous tracks. Should work on BMWs with the 6FL (USB ipod interface) option without idrive. May work on Mini's with same Y-Cable setup.  

Factory BMW Y-Cable plugs into a 30-pin dock connector break out board attached to the serial pins on the PI GPIO Headers.

Have tested with Pi Zero W and Pi 3 B+

Many features are not implemented or otherwise accessible via the stereo such as:
* Browse playlists, albums, artists, genres via the stereo. 
* Random
* Repeat

Script expects bluetooth to connection before it will start communicating with the car. 

On the Pi Zero W I used a USB sound card on the USB Host port. You maybe be able to pull pwm audio off the GPIO headers with a simple circut and run them through the Y cable. On setup the Y cable is only attached to the USB in the car and Audio direct from the USB sound card to the aux port. I am pulling power from the accessory power plug near the USB/Aux ports in the center console. 

Things I used: 
* https://github.com/nicokaiser/rpi-audio-receiver to get the Bluetooth setup. 
* https://learn.adafruit.com/read-only-raspberry-pi for read only filesystem, to help protect from the hard shutdowns). 
* I used a 30pin female ipod connector break out board from http://elabbay.com/. 
* AVRCP library was hacked up from https://scribles.net/controlling-bluetooth-audio-on-raspberry-pi/ with some help from a friend.

The code is ugly. I know. 

Other known issues with the code: 
* 's show up as a ? on the display. 
* Sometimes the display doesn't update. 
* It is ugly and full of commented out code that needs removed. 
* Bluetooth connection needs to be established before the car will identify and ipod, which may take a few seconds. 
* Inital track information may also take another few few seconds after in ipod mode but updates should be pretty quick after.

Other things to note:
* Car must be ingition on for the power near the USB port to be engergized. 
* Bluetooth needs to be paird each time if useing the script above to configure the pi as an audio receiver. This should be solveable with config tweaks.
