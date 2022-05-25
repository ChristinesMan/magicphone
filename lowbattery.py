# Based on https://github.com/JuiceBoxZero/LowBatteryShutdown.git

import time
import os
import threading
import RPi.GPIO as GPIO

import log

class LowBattery(threading.Thread):
    """ This thread polls the low battery pin and initiates shutdown
    """
    name = 'LowBattery'

    def __init__ (self):

        threading.Thread.__init__(self)

        # using default pin
        self.shutdown_pin = 16

        # keep track of how many occurances of low battery
        # it does seem like it's glitchy so I don't want to shutdown for nothing
        self.LowBatteryHits = 0
        self.LowBatteryHitsToShutdown = 10
        self.LowBatteryHitsResetSeconds = 60
        self.LowBatteryHitsResetCounter = 60

    def run(self):

        try:

            # setup the pin
            GPIO.setup(self.shutdown_pin, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)

            while True:

                # check the pin
                if GPIO.input(self.shutdown_pin) == 1:
                    self.LowBatteryHits += 1
                    self.LowBatteryHitsResetCounter = self.LowBatteryHitsResetSeconds
                    log.main.warning(f'Low Battery Hit {self.LowBatteryHits} / {self.LowBatteryHitsToShutdown}!')


                # if we have hits, keep track of when we're going to reset the number of hits
                # because I don't want a number of glitches over a long period of time to shutdown for no reason
                if self.LowBatteryHits > 0:

                    self.LowBatteryHitsResetCounter -= 1

                    if self.LowBatteryHitsResetCounter <= 0:
                        log.main.warning('LowBatteryHits reset to 0')
                        self.LowBatteryHits = 0


                if self.LowBatteryHits >= self.LowBatteryHitsToShutdown:
                    log.main.critical('The battery is low, shutting down.')
                    os.system("sudo shutdown -h now")

                time.sleep(0.25)


        # log exception in the main.log
        except Exception as e:
            log.main.error('Thread died. {0} {1} {2}'.format(e.__class__, e, log.format_tb(e.__traceback__)))


# Instantiate and start the thread
thread = LowBattery()
thread.daemon = True
thread.start()

