# polls the switch that controls volume, normal / high

import time
import threading
import RPi.GPIO as GPIO

# Note: I installed the latest version from the repo, not using pip
import alsaaudio

import log
import phonestate

# Poll the switch
class VolSwitch(threading.Thread):
    name = 'VolSwitch'

    def __init__ (self):

        threading.Thread.__init__(self)

        # GPIO pin that is hooked up to the switch
        self.SwitchPin = 27

        # Debouncer
        # If the loop runs through and finds the same, it's ignored. 
        self.SwitchStatus = None
        self.SwitchStatusLast = None
        self.SwitchStatusDebounce = 2

        # How long to sleep between continuity checks
        # will need to tune these to be as low as possible but also very accurate
        self.SleepTime = 0.5


    def run(self):

        try:

            # init the mixer thing
            self.mix = alsaaudio.Mixer(control='Speaker', id=0, cardindex=1)

            # Initialize the GPIO pin
            GPIO.setup(self.SwitchPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

            # run for.   ev.  er.
            while True:

                self.SwitchStatus = GPIO.input(self.SwitchPin)

                if self.SwitchStatus != self.SwitchStatusLast:

                    if self.SwitchStatusDebounce > 0:

                        self.SwitchStatusDebounce -= 1

                    else:

                        if self.SwitchStatus == 1:
                            log.main.debug('Volume high')
                            self.mix.setvolume(100)
                        else:
                            log.main.debug('Volume norm')
                            self.mix.setvolume(50)

                        self.SwitchStatusLast = self.SwitchStatus

                else:
                    
                    self.SwitchStatusDebounce = 2

                time.sleep(self.SleepTime)

        # log exception in the main.log
        except Exception as e:
            log.main.error('Thread died. {0} {1} {2}'.format(e.__class__, e, log.format_tb(e.__traceback__)))

# Instantiate and start the thread
thread = VolSwitch()
thread.daemon = True
thread.start()
