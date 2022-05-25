# The "operator"

import time
import threading
import random

import log
import phonestate
import play

class Christine(threading.Thread):
    """ This thread operates the operator
    """
    name = 'Christine'

    def __init__ (self):

        threading.Thread.__init__(self)

        # are we on?
        self.OperatorOn = False

        # keep track of whether or not sound is playing
        self.SoundPlaying = False

        # a number of seconds in the future at which we would like to play an active listening type of sound
        self.ActiveListenTime = time.time() + 1000000

        # a number of seconds in the future at which we're tired of the dead air and want to say something
        self.SmallTalkTime = time.time() + 1000000

        # not going to wait forever
        self.DeadAirTime = time.time() + 1000000

    def run(self):

        try:

            while True:

                # only if the operator is on the line
                if self.OperatorOn == True:

                    # if sound is playing, we want to do nothing, just let it play, otherwise figure out what's next
                    if self.SoundPlaying == False:

                        # smalltalk happens you the caller hasn't said anything for a while
                        if time.time() > self.SmallTalkTime:
                            self.SmallTalkTime = time.time() + 1000000
                            self.Play('smalltalk')

                        # active listening is for when caller just said something and they seem to be done talking
                        elif time.time() > self.ActiveListenTime:
                            self.ActiveListenTime = time.time() + 1000000
                            self.Play('listening')

                        # after a while of dead air, figure caller went away, say bye
                        elif time.time() > self.DeadAirTime:
                            self.DeadAirTime = time.time() + 1000000
                            self.ActiveListenTime = time.time() + 1000000
                            self.SmallTalkTime = time.time() + 1000000
                            self.OperatorOn = False
                            self.Play('bye')
                            phonestate.thread.OperatorHungUp()

                        # if it's not time to do anything else, just breathe
                        else:
                            self.Play('breathe')

                    time.sleep(0.1)

                else:

                    time.sleep(1)

        # log exception in the main.log
        except Exception as e:
            log.main.error('Thread died. {0} {1} {2}'.format(e.__class__, e, log.format_tb(e.__traceback__)))


    # play a sound
    def Play(self, coll):

        log.main.debug(f'Playing: {coll}')
        self.SoundPlaying = True

        phonestate.thread.OperatorSound(FromCollection = coll)


    # the phonestatus module will let this know when sounds end
    def SoundEnded(self):

        log.main.debug('Sound ended')
        self.SoundPlaying = False


    # this is called by the phonestatus module one time to get this operator started
    def YoureOn(self):

        # reset
        self.DeadAirTime = time.time() + 1000000
        self.ActiveListenTime = time.time() + 1000000
        self.SmallTalkTime = time.time() + 1000000

        # helloooo
        self.Play('hello')
        self.OperatorOn = True


    # this is called by the phonestatus module when the phone is hung up
    def TheyHungUp(self):

        self.Play('bye')
        self.OperatorOn = False


    # this is called by the record module when speech is detected
    def TheySaidSomething(self):

        self.ActiveListenTime = time.time() + (random.random() * 2)
        self.SmallTalkTime = time.time() + 10.0 + (random.random() * 4)
        self.DeadAirTime = time.time() + 100

# Instantiate and start the thread
thread = Christine()
thread.daemon = True
thread.start()
