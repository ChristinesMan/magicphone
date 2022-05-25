import time
import threading

import log
import sounds
import christine
import play
import record

class PhoneState(threading.Thread):
    """ This thread keeps track of phone states
    """
    name = 'PhoneState'

    def __init__ (self):

        threading.Thread.__init__(self)

        # what mode is the phone in
        # INIT, ONHOOK, DIALTONE, DIALING, RINGING, BUSY, OFFHOOK, ANSWERINGMACHINE, RECORDING, etc
        self.CurrentState = 'INIT'

        # keep track of the state of the receiver
        self.IsOffHook = False

        # keep track of the state of the volume switch
        self.IsHigh = False

        # keep track of the phone number somebody just dialed
        self.NumberDialed = ''

        # to keep the sound alive
        self.KeepAliveTime = time.time() + 600

    def run(self):

        try:

            while True:

                # it appears that after being left for a long period, phone stops being able to play sound
                # I believe there's something that times out
                if self.CurrentState =='ONHOOK':
                    if time.time() > self.KeepAliveTime:
                        self.KeepAliveTime = time.time() + 600
                        play.thread.QueueSound(FromCollection = 'keepalive')

                else:
                    self.KeepAliveTime = time.time() + 600

                # log.main.debug(self.CurrentState)
                time.sleep(60)

        # log exception in the main.log
        except Exception as e:
            log.main.error('Thread died. {0} {1} {2}'.format(e.__class__, e, log.format_tb(e.__traceback__)))


    # the play module will let this know when sounds end, and what the sound collection name was
    def SoundEnded(self, CollectionName):

        log.main.debug(f'Sound ended. Collection: {CollectionName}')

        if self.CurrentState == 'CHRISTINE':

            # Pass it to the operator
            christine.thread.SoundEnded()

        elif CollectionName == 'dialtone':

            # after the dialtone, if no dialing happened, I guess play the offhook lady
            self.CurrentState = 'OFFHOOK'

            # play the sound like "if you'd like to make a call, please hang up and try again."
            play.thread.QueueSound(FromCollection = 'offhook', Delay = 10)

        elif CollectionName == 'offhook':

            # if we're done playing the offhook message, just chill until they hang up
            self.CurrentState = 'INIT'

        elif CollectionName == 'ringing':

            if self.NumberDialed == '0' or self.NumberDialed == '100':
                self.CurrentState = 'CHRISTINE'
                record.thread.StartRecording('christine')
                christine.thread.YoureOn()

            elif self.NumberDialed == '001':
                play.thread.QueueSound(FromCollection = 'recordnewgreeting', Delay = 10)

            # didn't get there
            # elif self.NumberDialed == '8675309':
            #     play.thread.QueueSound(FromCollection = 'prank8675309', Delay = 10)

            else:

                # for any other number, go to the answering machine
                self.CurrentState = 'ANSWERINGMACHINE'

                # play the sound for leave a message after the tone
                play.thread.QueueSound(FromCollection = 'answeringmachine', Delay = 5)

        elif CollectionName == 'answeringmachine':

            # play the message beep
            play.thread.QueueSound(FromCollection = 'messagebeep', Delay = 5)

        elif CollectionName == 'messagebeep':

            # change to the next state
            self.CurrentState = 'RECORDING'

            # tell recording module to go now
            RecordTimeStamp = str(round(time.time(), 2)).replace('.', '')
            RecordFileName = f'recordings/{RecordTimeStamp}.wav'
            record.thread.StartRecording(RecordFileName)

        elif CollectionName == 'recordnewgreeting':

            # change to the next state
            self.CurrentState = 'RECORD_GREETING'

            # tell recording module to go now
            RecordFileName = 'sounds_master/phone/greeting.wav'
            record.thread.StartRecording(RecordFileName)


    # this is called by the hook module one time to set initial state, then whenever it changes
    def HookEvent(self, IsOffHook):

        if IsOffHook == True:

            # apparently we just went off hook, so do the dialtone
            self.CurrentState = 'DIALTONE'

            # play the dialtone
            play.thread.QueueSound(FromCollection = 'dialtone', Delay = 5)

        else:

            # apparently we just hung up the phone, so figure out what we were doing and do the right thing
            if self.CurrentState == 'RECORDING':
                record.thread.StopRecording()

            # or we put the phone down after recording the greeting
            elif self.CurrentState == 'RECORD_GREETING':
                record.thread.StopRecording()
                sounds.soundsdb.Reprocess(738)

            # or we put the phone down after recording the greeting
            elif self.CurrentState == 'CHRISTINE':
                record.thread.StopRecording()
                christine.thread.TheyHungUp()

            # stop any sounds from playing unless we're still playing startup sound
            if self.CurrentState != 'INIT':
                play.thread.Stop()

            self.CurrentState = 'ONHOOK'

        # save the current setting
        self.IsOffHook = IsOffHook


    # this is called by the dialer module when a full phone number is dialed
    def DialerEvent(self, number, dialdone=False):

        log.main.debug(f'Dialer event {number}, dialdone {dialdone}')

        if dialdone:

            # just save the number
            self.NumberDialed = number

            # go into the ringing state
            self.CurrentState = 'RINGING'

            # and start the sound
            play.thread.QueueSound(FromCollection = 'ringing', Delay = 10)

        else: 

            play.thread.QueueSound(FromCollection = f'pulsing_{number}')


    # umm, so I don't know why I had to do it this way
    # But after 3 hours of hacking at it, it's now time to flip tables
    def OperatorSound(self, FromCollection):

        play.thread.QueueSound(FromCollection = FromCollection)


    # She hung up on me! 
    def OperatorHungUp(self):

        record.thread.StopRecording()
        self.CurrentState = 'INIT'


# Instantiate and start the thread
thread = PhoneState()
thread.daemon = True
thread.start()
