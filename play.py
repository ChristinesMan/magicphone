import time
import argparse
import threading
from collections import deque
import random
from multiprocessing import Process, Pipe
import wave

# Note: I installed the latest version from the repo, not using pip
import alsaaudio

import log
import phonestate
import sounds

class Play(threading.Thread):
    """ This thread is where the sounds are actually output. 
    """
    name = 'Play'

    def __init__ (self):

        threading.Thread.__init__(self)

        # A queue to queue stuff
        self.Queue_Play = deque()

        # Keep track of currently playing sound
        self.CurrentSound = None

        # setup the separate process with pipe
        # The enterprise sent out a shuttlecraft with Data at the helm. The shuttlecraft is a subprocess. 
        # This was done because sound got really choppy because too much was going on in the enterprise
        self.PipeToShuttlecraft, self.PipeToStarship = Pipe()
        self.ShuttlecraftProcess = Process(target = self.Shuttlecraft, args = (self.PipeToStarship,))
        self.ShuttlecraftProcess.start()

    def run(self):
        log.sound.debug('Thread started.')

        try:

            while True:

                # Get everything out of the queue and process it
                while len(self.Queue_Play) != 0:
                    IncomingSound = self.Queue_Play.popleft()

                    log.sound.debug('Accepted: %s', IncomingSound)
                    self.CurrentSound = IncomingSound
                    if self.CurrentSound['cutsound'] == True:
                        log.sound.debug('Playing immediately')
                        self.Play()

                # This will block here until the shuttlecraft sends a true/false which is whether the sound is still playing. 
                # The shuttlecraft will send this every 0.2s, which will setup the approapriate delay
                # So all this logic here will only run when the shuttlecraft finishes playing the current sound
                # If there's some urgent sound that must interrupt, that happens up there ^ and that is communicated to the shuttlecraft through the pipe
                if self.PipeToShuttlecraft.recv() == False:

                    # if we're here, it means there's no sound actively playing
                    log.sound.debug('No sound playing')

                    # only do this stuff if there is a current sound
                    if self.CurrentSound != None:

                        # if we're here, it means no sound is currently playing at this moment, and if is_playing True, that means the sound that was playing is done
                        if self.CurrentSound['is_playing'] == True:

                            # let the business logic module know whatever was playing is done
                            phonestate.thread.SoundEnded(self.CurrentSound['collection'])

                            # destroy the current sound, it's done
                            self.CurrentSound = None

                        else:

                            # In case we want to add a delay before starting a sound
                            if self.CurrentSound['delayer'] > 0:
                                self.CurrentSound['delayer'] -= 1

                            else:
                                self.Play()

        # log exception in the main.log
        except Exception as e:
            log.main.error('Thread died. {0} {1} {2}'.format(e.__class__, e, log.format_tb(e.__traceback__)))

    def Play(self):

        log.sound.debug(f'Playing: {self.CurrentSound}')
        log.main.debug(f'Sound start. Collection: {self.CurrentSound["collection"]}')

        # Now that we're actually playing the sound, tell the sound collection to not play it for a while
        if self.CurrentSound['replay_wait'] != 0 and self.CurrentSound['collection'] != None:
            sounds.collections[self.CurrentSound['collection']].SetSkipUntil(SoundID = self.CurrentSound['id'])

        # send the sound file over there
        self.PipeToShuttlecraft.send(f'./sounds_processed/{self.CurrentSound["id"]}/0.wav')

        # let stuff know this sound is playing, not just waiting in line
        self.CurrentSound['is_playing'] = True

    def Stop(self):

        log.sound.debug('FULL STOP')

        # send the signal to stop all sound
        self.PipeToShuttlecraft.send('')

        # let stuff know this sound is playing, not just waiting in line
        self.CurrentSound = None

    # Runs in a separate process for performance reasons. Sounds got crappy and this solved it. 
    def Shuttlecraft(self, PipeToStarship):

        try:

            # All the wav files are forced to the same format during preprocessing, currently mono 44100
            # chopping the rate into 10 pieces, so that's 10 chunks per second. I might adjust later.
            rate = 44100
            periodsize = rate // 10

            # The current wav file buffer thing
            WavData = None

            # I want to keep track to detect when we're at the last chunk so we can chuck it away and also tell the enterprise to send more sounds. 
            WavDataFrames = 0

            # Start up some alsa, if the sound card is present
            # if the handset is not plugged in, it should throw the exception
            # keep trying
            log.main.info('Connecting handset speaker')
            while True:
                try:
                    device = alsaaudio.PCM(channels=1, rate=rate, format=alsaaudio.PCM_FORMAT_S16_LE, periodsize=periodsize)
                    log.main.info('Handset speaker connected')
                    break
                except alsaaudio.ALSAAudioError:
                    time.sleep(10)

            while True:

                # So basically, if there's something in the pipe, get it all out
                if PipeToStarship.poll():

                    # Normally the pipe will receive a path to a new wav file to start playing, stopping the previous sound
                    # or if it receives an empty strong, that's a signal to just stop immediately
                    WavFile = PipeToStarship.recv()
                    log.sound.debug(f'Shuttlecraft received: {WavFile}')

                    # This is to allow the sound to be just stopped
                    if WavFile == '':
                        WavDataFrames = 0

                    else:
                        WavData = wave.open(WavFile)
                        WavDataFrames = WavData.getnframes()

                else:

                    # If there are still frames enough to write without being short
                    if WavDataFrames >= periodsize:
                        WavDataFrames = WavDataFrames - periodsize

                        # write the frames, and if the buffer is full it will block here and provide the delay we need
                        device.write(WavData.readframes(periodsize))

                        # send a signal back to enterprise letting them know something is still being played
                        PipeToStarship.send(True)

                    else:
                        # otherwise, in this case the current wav has been sucked dry and we need something else
                        PipeToStarship.send(False)

                        # just masturbate for a little while
                        time.sleep(0.1)

        # log exception in the main.log
        except Exception as e:
            log.main.error('Shuttlecraft crashed. {0} {1} {2}'.format(e.__class__, e, log.format_tb(e.__traceback__)))

    # Add a sound to the queue to be played
    def QueueSound(self, Sound = None, FromCollection = None, CutAllSoundAndPlay = True, Delay = 0):
        if Sound == None and FromCollection != None:
            Sound = sounds.collections[FromCollection].GetRandomSound()

        # If a collection is empty, or no sounds available at this time, it's possible to get a None sound. Just chuck it. 
        if Sound != None:
            # Take the Sound and add all the options to it. Merges the two dicts into one. 
            # The collection name is saved so that we can update the delay wait only when the sound is played
            Sound.update({'collection': FromCollection, 'cutsound': CutAllSoundAndPlay, 'delayer': Delay, 'is_playing': False})
            self.Queue_Play.append(Sound)
            # log.sound.info(f'Queued: {Sound}')


# Instantiate and start the thread
thread = Play()
thread.daemon = True
thread.start()

