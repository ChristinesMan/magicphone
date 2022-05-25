import os
import time
import signal
import RPi.GPIO as GPIO

# Initialize global GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

import log
import phonestate
import cputemp
import lowbattery
import dialer
import hook
import volswitch
import sounds
import play
import record
# import httpserver

if __name__ == "__main__":

    # We were here
    log.main.info('Script started')

    # play the startup sound
    play.thread.QueueSound(FromCollection = 'startup')

    # handle getting killed gracefully
    kill_now = False

    # this def gets called when a signal comes in
    def exit_gracefully(*args):

        log.main.info('Caught kill signal')

        # set this global var that will signal the script to end
        global kill_now
        kill_now = True

    # setup signal handlers
    signal.signal(signal.SIGINT, exit_gracefully)
    signal.signal(signal.SIGTERM, exit_gracefully)

    # wait here until a kill signal comes in
    while not kill_now:
        time.sleep(1)
