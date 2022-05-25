import time
import threading
from multiprocessing import Process, Pipe
import wave
# import webrtcvad
from pydub import AudioSegment

# Note: I installed the latest version from the repo, not using pip
import alsaaudio

import log
import christine

class Record(threading.Thread):
    """ 
        Handles recording stuff
    """
    name = 'Record'

    def __init__ (self):

        threading.Thread.__init__(self)

    def run(self):

        try:

            # setup the separate process with pipe
            # So... Data, Riker, and Tasha beam down for closer analysis of an alien probe. 
            # A tragic transporter accident occurs and Tasha gets... dollified. 
            self.PipeToAwayTeam, self.PipeToEnterprise = Pipe()
            self.AwayTeamProcess = Process(target = self.AwayTeam, args = (self.PipeToEnterprise,))
            self.AwayTeamProcess.start()

            while True:

                # This will block here until the away team sends a message to the enterprise
                Comm = self.PipeToAwayTeam.recv()

                if Comm == 'speech':
                    christine.thread.TheySaidSomething()

        # log exception in the main.log
        except Exception as e:
            log.main.error('Thread died. {0} {1} {2}'.format(e.__class__, e, log.format_tb(e.__traceback__)))

    # Start and Stop recording
    def StartRecording(self, filename):
        self.PipeToAwayTeam.send(filename)

    def StopRecording(self):
        self.PipeToAwayTeam.send('stop')

    # Runs in a separate process for performance reasons
    def AwayTeam(self, PipeToEnterprise):

        try:

            # Start up some alsa, if the sound card is present
            # if the handset is not plugged in, it should throw the exception
            # keep trying
            log.main.info('Connecting handset mic')
            while True:
                try:
                    Stream = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NONBLOCK, channels=1, rate=16000, format=alsaaudio.PCM_FORMAT_S16_LE, periodsize=160)
                    log.main.info('Handset mic connected')
                    break
                except alsaaudio.ALSAAudioError:
                    time.sleep(30)


            while True:

                # limit the size of recordings
                # it'll be a very long limit, 10m seems reasonable
                # Just don't want somebody to start a recording and leave the phone off hook for a week
                # 10m x 60s x 16000 frames per second = 9600000
                RecordLimiter = 9600000

                # This will block until something comes through the pipe. This should be a filename for a new wav file.
                # and after that there will be another message to stop it
                RecordFileName = PipeToEnterprise.recv()

                log.main.debug(f'Got RecordFileName {RecordFileName}')

                # if we just got the stop command meant to stop recording, chuck it and get the next
                if RecordFileName == 'stop':
                    RecordFileName = PipeToEnterprise.recv()

                if RecordFileName == 'christine':

                    log.main.info(f'Start talk with Christine')

                    # the running average loudness is calculated for each block of data
                    # this helps to set a baseline for comparison
                    # a quiet room is about 200
                    loudness_avg = 200

                    # just get audio data until a message ends it
                    while PipeToEnterprise.poll() == False:
                        length, data = Stream.read()

                        # sometimes we get 0 length when the buffer has nothing
                        if length:

                            # calculate loudness of this block
                            in_audio = AudioSegment(data=data, sample_width=2, frame_rate=16000, channels=1)
                            loudness = float(in_audio.rms)

                            # figure out how loud this is compared to the baseline
                            loudness_ratio = loudness / loudness_avg

                            # log.main.debug(f'Loud: {loudness} Avg: {loudness_avg} Ratio: {loudness_ratio}')
                            # if it's loud enough, we ass u me it's speech
                            if loudness_ratio > 5.0:
                                # log.main.debug('Speech detected')
                                PipeToEnterprise.send('speech')

                            # if it's not loud enough, add that to the running average
                            else:
                                loudness_avg = ((loudness_avg * 2000.0) + loudness) / 2001.0

                        time.sleep(0.001)

                    log.main.info('Stop talk with Christine')


                else:

                    log.main.info(f'Start record with {RecordFileName}')

                    WavFile = wave.open(RecordFileName, 'wb')
                    WavFile.setnchannels(1)
                    WavFile.setsampwidth(2)
                    WavFile.setframerate(16000)

                    while PipeToEnterprise.poll() == False:
                        length, data = Stream.read()

                        if length:
                            WavFile.writeframes(data)
                            RecordLimiter -= length
                            if RecordLimiter < 0:
                                log.main.warning('Breached record limit!')
                                break

                        time.sleep(0.002)

                    log.main.info('Stop record')

                    # Stream.pause()
                    WavFile.close()

        # log exception in the main.log
        except Exception as e:
            log.main.error('The Away Team all died. {0} {1} {2}'.format(e.__class__, e, log.format_tb(e.__traceback__)))


# Instantiate and start the thread
thread = Record()
thread.daemon = True
thread.start()
