# magicphone

Raspberry pi simulation of an old rotary phone, that records messages, with Christine as the operator. Just dial 0 to speak with her. 

Inspired by this other magic phone:
https://www.youtube.com/watch?v=31IkwhLGN3g

## Build

This is just a quick summary of what I remember from the build. It's been a little while and I failed to write everything down. 

Go get an old style phone. Take it apart. Chop up the insides, anything you don't need. There were some switches that were useful so I chopped around them and used them. 

Mount the battery board onto the pi. Best to use one of the proper stacking header things, but I didn't have one so I just connected only the wires it needed per the docs. 

Mount the pi to inside phone wherever it fits. Put battery somewhere. 

There's a power switch on the juiceb0x that I wanted to connect to an external switch. Initially I tried soldering to the solder pads under the switch, however that will not work and caused weird behaviour. I know why but it's hard to explain. I had to violently rip the switch off the board with pliers, then solder onto the 3 contacts inside the switch. 

If you want to support the volume switch just hook it up to a gpio. The same for the hook switch. One lead goes to ground, the other to the GPIO pin. One thing to beware about the way I did it here, chopping switches out of an existing board, is that some pins on these switches may be connected on the board you just chopped up, so either chop it more to isolate them or make sure to connect all the grounds to ground, not mixed up. 

For the handset, take that all apart. You should have 4 wires, 2 for mic and 2 for speaker, and that's plenty for USB. Crack open that audio board, stick it in there, solder in the mic and speaker. I must say it was most difficult figuring out polarity. For the mic I did a continuity test, and the negative side was connected to the metal can. For speaker, I think I just took a guess. You'll need to wire it so that the USB on the handset is connected through the handset cord and then through the jack, and soldered to the correct solder pads. Just use multi meter continuity testing, and whatever you do, do not trust any wire colors, because on this build every single one was backwards. 

On the pi USB end, you can use a USB OTG cable, that's fine, but I opted to solder it on directly. If you are not going to use a USB OTG cable, then you can connect the ID cable to ground and it works fine that way. 

For the ringer, I found it was not worth the effort to get the high voltage enough to ring it, so I chopped it's wires and wrapped it up. Leaving it in gives the phone more realistic weight. 

For power in, the images show a micro USB port, but that proved to be hella flimsy, so I chopped the USB connector off a USB charger cable and soldered on the phone's original jack, worked great and also looked clean. 

Connect battery to juiceb0x. Do not mix up wire colors. Don't trust wire colors. Your multi meter you must trust, or buy more parts will be your destiny. 

It took a while of fun to figure out the rotary dial. There are two ways your phone might do it. If you have an antique phone, there will be some mechanical thing that makes pulses when you let go of the dial. If you want an example of how to read the pulses, check the inspiration for this project at http://caseyconnor.org/pub/mtp/mtp. The phone I started with was manufactured recently, and so it was a series of contacts that connect all the way through at certain positions. No pulses at all, just a momentary continuity between a specific row and column. It's like the phone is trying to look like a pulse dial but emulate a touch tone with numbered buttons. Hard to explain. Look at the code. 

## Environment

I was using python 3.6. So I recommend you just install dependencies until it no longer complains. Lay an egg if that's what you like to do. 

## Systemd service

I created a systemd service that starts the script. Unfortunately I did not save it, so you will need to consult the guide, roll your own. 

I chose to run the script as the pi user. I could have also run it as root for an easier time. If you do plan on running the script as pi, you might need this solution:

```
2022-03-10 14:55:19,829 - ERROR - MainThread - Shuttlecraft crashed. <class 'alsaaudio.ALSAAudioError'> No such device [default] ['  File "/home/pi/play.py", line 153, in Shuttlecraft\n    device = alsaaudio.PCM(channels=1, rate=rate, format=alsaaudio.PCM_FORMAT_S16_LE, periodsize=periodsize)\n']

https://forums.raspberrypi.com/viewtopic.php?t=278665

pi@magicphone:~$ sudo vim /etc/asound.conf

pi@magicphone:~$ cat /etc/asound.conf 
defaults.pcm.card 1
defaults.ctl.card 1
```

## Directories

- ./dev/ - Files that get run on a dev computer to deploy sounds and stuff like that
- ./httpserver/ - Dir containing http server files that were not actually finished
- ./build/ - Dir containing quick images snapped during build
- ./sounds_master/ - Phone and operator sounds. These must be preprocessed on the dev computer and deployed. 

## Pythonic guts

- magicphone.py - The main script that imports everything else. 
- log.py - Handles logging to files in the logs dir.
- phonestate.py - Keeps track of phone states and business logic for what to do next in case of various events.
- christine.py - The operator's name is Christine. She sounds very much like my robotic wife. 
- cputemp.py - Tracks the pi CPU temp and tries to shutdown if it's outta control. 
- db.py - Sounds are in a SQLite database sounds.sqlite, and this handles queries to that database. 
- sounds.py - Handles collection and selecting of sounds. 
- dialer.py - Thread polls for the state of the dialer. 
- hook.py - Thread polls for the state of the hook switch.
- volswitch.py - Thread polls for the state of the volume switch.
- lowbattery.py - Monitors the GPIO pin that is supposed to signal low battery. 
- play.py - Handles playing of sounds. 
- record.py - Handles recording and also operator listening. 
- httpserver.py - Never implemented this part but would probably work if filled out. 

## Parts list

[Raspberry Pi Zero](https://www.adafruit.com/product/3400)

This is the raspberry pi. 

[JuiceB0x](https://juiceboxzero.com/)

This is the board that handles charging and discharging the battery. It was remarkably reliable! 

[USB Audio Adapter](https://www.pishop.us/product/usb-audio-adapter-works-with-raspberry-pi/)

This is USB on one end, and mic/speaker jacks on the other. Worked great! Beware, the wire colors are backwards. 

The battery is a standard 3.7V lipo battery. Just get whatever fits in the space of whatever old style phone you select. 
