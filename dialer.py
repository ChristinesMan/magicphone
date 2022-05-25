# Based on this very helpful tutorial:
# https://www.digikey.com/en/maker/blogs/2021/how-to-connect-a-keypad-to-a-raspberry-pi

# the hardware is similar to a keypad, but it's in the form of
# a round disk with a metal brush thingy, and a switch that causes 
# a momentary connection between specific rows and columns

# An old-style rotary dialer would count pulses. This instead 
# connects specific pins. 

import time
import threading
import RPi.GPIO as GPIO

import log
import phonestate

# Poll the rotary thingy
class Dialer(threading.Thread):
    name = 'Dialer'

    def __init__ (self):
        threading.Thread.__init__(self)

        # these GPIO pins are connected to the rotary dial thing
        self.RowPins = [25, 8, 7, 1]
        self.ColPins = [12, 20, 21]

        # multidimensional list to map digits to row,col
        self.DigitMap = [
                          ['1', '2', '3'],
                          ['4', '5', '6'],
                          ['7', '8', '9'],
                          ['p', '0', 's'],
                        ]

        # Debouncer
        # If the loop runs through and finds the same digit again that it just found 0.06s ago, it's ignored. 
        self.DigitHit = None
        self.DigitHitLast = None

        # How long to sleep between continuity checks
        # will need to tune these to be as low as possible but also very accurate
        self.SleepTime = 0.06
        self.InterRowSleepTime = 0.02

        # How long to wait after a digit before accepting the full number
        # And also a counter
        self.WaitAfterLastDigitSeconds = 2.0
        self.WaitAfterLastDigitIterations = self.WaitAfterLastDigitSeconds / self.SleepTime
        self.LastDigitCounter = self.WaitAfterLastDigitIterations

        # Accumulate digits
        self.NumberDialed = ''

    def run(self):

        try:

            # Initialize the GPIO pins
            for pin in self.RowPins:
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.LOW)

            # Configure the input pins to use the internal pull-down resistors
            for pin in self.ColPins:
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

            # run for.   ev.  er.
            while True:

                # we only want to test this if the phonestate is dialing or dialtone
                if 'DIAL' in phonestate.thread.CurrentState:

                    # if we have dialed something and then timed out, then we're done dialing
                    if self.LastDigitCounter <= 0 and len(self.NumberDialed) > 0:
                        phonestate.thread.DialerEvent(self.NumberDialed, dialdone=True)
                        log.main.info(f'Dialing {self.NumberDialed}')
                        self.NumberDialed = ''

                    # Reset thing I am using as a debouncer
                    self.DigitHit = None

                    # cycle through all rows, turn them on, test continuity
                    for row in range(0, 4, 1):
                        GPIO.output(self.RowPins[row], GPIO.HIGH)
                        time.sleep(self.InterRowSleepTime)
                        for col in range(0, 3, 1):
                            if GPIO.input(self.ColPins[col]) == 1:
                                self.DigitHit = self.DigitMap[row][col]
                                if self.DigitHit != self.DigitHitLast:

                                    # We got a new digit
                                    log.main.debug(f'Hit R{row} C{col} which is {self.DigitHit}')

                                    # Reset the counter we're using to cut off dialing and accept the full number
                                    self.LastDigitCounter = self.WaitAfterLastDigitIterations

                                    # Add the digit to the number we're accumulating
                                    self.NumberDialed += self.DigitHit

                                    # send the digit over to the phonestate module
                                    phonestate.thread.DialerEvent(self.DigitHit)

                        GPIO.output(self.RowPins[row], GPIO.LOW)
                    self.DigitHitLast = self.DigitHit
                    time.sleep(self.SleepTime)

                    # decrement counter
                    self.LastDigitCounter -= 1

                else:

                    # sleep a bit longer if we're not even in a dialing mode
                    time.sleep(0.25)

        # log exception in the main.log
        except Exception as e:
            log.main.error('Thread died. {0} {1} {2}'.format(e.__class__, e, log.format_tb(e.__traceback__)))

# Instantiate and start the thread
thread = Dialer()
thread.daemon = True
thread.start()
