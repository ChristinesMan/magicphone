import os
import time
import threading
import smbus

import log

# Poll the Pi CPU temperature
class CPUTemp(threading.Thread):
    name = 'CPUTemp'

    def __init__ (self):
        threading.Thread.__init__(self)

        # Raspberry pi CPU temp
        self.CPU_Temp = 45

    def run(self):
        log.cputemp.debug('Thread started.')

        try:
            while True:
                # Get the temp
                measure_temp = os.popen('/usr/bin/vcgencmd measure_temp')
                self.CPU_Temp = float(measure_temp.read().replace('temp=', '').replace("'C\n", ''))
                measure_temp.close()

                # Log it
                log.cputemp.info('%s', self.CPU_Temp)

                # The official pi max temp is 85C
                # I expect this will only really get hot enough if it's sitting in the sun on a hot day
                if self.CPU_Temp >= 72:

                    log.main.critical(f'SHUTTING DOWN FOR SAFETY ({self.CPU_Temp}C)')

                    # Flush all the disk buffers
                    os.popen('sync')

                    # wait a sec or 5
                    time.sleep(5)

                    # shutdown
                    os.system("sudo shutdown -h now")

                time.sleep(32)

        # log exception in the main.log
        except Exception as e:
            log.main.error('Thread died. {0} {1} {2}'.format(e.__class__, e, log.format_tb(e.__traceback__)))

# Instantiate and start the thread
thread = CPUTemp()
thread.daemon = True
thread.start()
