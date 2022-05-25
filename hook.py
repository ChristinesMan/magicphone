# polls the hook
# you know, that switch that you put the receiver on, that hook

import time
import threading
import RPi.GPIO as GPIO

import log
import phonestate

# Poll the switch
class Hook(threading.Thread):
    name = 'Hook'

    def __init__ (self):

        threading.Thread.__init__(self)

        # GPIO pin that is hooked up to the switch
        self.HookPin = 24

        # Debouncer
        # If the loop runs through and finds the same, it's ignored. 
        self.HookStatus = None
        self.HookStatusLast = None
        self.HookStatusDebounce = 3

        # How long to sleep between continuity checks
        # will need to tune these to be as low as possible but also very accurate
        self.SleepTime = 0.1

    def run(self):

        try:

            # Initialize the GPIO pin
            GPIO.setup(self.HookPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

            # run for.   ev.  er.
            while True:

                self.HookStatus = GPIO.input(self.HookPin)

                if self.HookStatus != self.HookStatusLast:

                    if self.HookStatusDebounce > 0:

                        self.HookStatusDebounce -= 1

                    else:

                        if self.HookStatus == 0:
                            log.main.debug('Off Hook')
                            phonestate.thread.HookEvent(True)
                        else:
                            log.main.debug('On Hook')
                            phonestate.thread.HookEvent(False)

                        self.HookStatusLast = self.HookStatus

                else:

                    self.HookStatusDebounce = 3

                time.sleep(self.SleepTime)

        # log exception in the main.log
        except Exception as e:
            log.main.error('Thread died. {0} {1} {2}'.format(e.__class__, e, log.format_tb(e.__traceback__)))

# Instantiate and start the thread
thread = Hook()
thread.daemon = True
thread.start()
