import os
import sys
import time
import random
import math
from multiprocessing import Pool

import sounds_db


def do_work(work_data):

    # Get all the db row stuff into nice neat variables
    SoundId = str(work_data[0])
    SoundName = str(work_data[1])
    SoundBaseVolumeAdjust = work_data[2]
    SoundTempoRange = work_data[3]

    print(f'Processing {SoundName}')


    # Delete the old processed sounds
    os.system('rm -rf ./sounds_processed/' + SoundId + '/*.wav')

    # Create the destination directory
    os.makedirs('./sounds_processed/' + SoundId, exist_ok=True)

    # If we're adjusting the sound volume, ffmpeg, otherwise just copy the original file to 0.wav, which is the file with original tempo
    if SoundBaseVolumeAdjust != 1.0:
        exitstatus = os.system('ffmpeg -v 0 -i ./sounds_master/' + SoundName + ' -filter:a "volume=' + str(SoundBaseVolumeAdjust) + '" ./sounds_processed/' + SoundId + '/tmp_0.wav')
        # print('Jacked up volume for ' + SoundName + ' (' + str(exitstatus) + ')')
    else:
        exitstatus = os.system('cp ./sounds_master/' + SoundName + ' ./sounds_processed/' + SoundId + '/tmp_0.wav')
        # print('Copied ' + SoundName + ' (' + str(exitstatus) + ')')

    # If we're adjusting the tempo, use rubberband to adjust 0.wav to various tempos. Otherwise, we just have 0.wav and we're done
    # removed --smoothing because it seemed to be the cause of the noise at the end of adjusted sounds
    if SoundTempoRange != 0.0:
        for Multiplier in [-1, -0.75, -0.5, -0.25, 0.25, 0.5, 0.75, 1]:
            exitstatus = os.system('rubberband --quiet --realtime --pitch-hq --tempo ' + format(1-(SoundTempoRange * Multiplier), '.2f') + ' ./sounds_processed/' + SoundId + '/tmp_0.wav ./sounds_processed/' + SoundId + '/tmp_' + str(Multiplier) + '.wav')
            # print('Rubberbanded ' + SoundId + ' to ' + str(Multiplier) + ' (' + str(exitstatus) + ')')

            exitstatus = os.system('ffmpeg -v 0 -i ./sounds_processed/' + SoundId + '/tmp_' + str(Multiplier) + '.wav -ar 44100 ./sounds_processed/' + SoundId + '/' + str(Multiplier) + '.wav')
            # print('Downsampled ' + SoundId + ' tempo ' + str(Multiplier) + ' (' + str(exitstatus) + ')')

    exitstatus = os.system('ffmpeg -v 0 -i ./sounds_processed/' + SoundId + '/tmp_0.wav -ar 44100 ./sounds_processed/' + SoundId + '/0.wav')
    # print('Downsampled ' + SoundId + ' tempo 0 (' + str(exitstatus) + ')')
    exitstatus = os.system('rm -f ./sounds_processed/' + SoundId + '/tmp_*')
    # print('Removed tmp files for ' + SoundId + ' (' + str(exitstatus) + ')')



    print(f'Processing sound id {SoundName} finished')

def pool_handler():
    p = Pool(4)
    p.map(do_work, work)


# If the script is called directly
if __name__ == "__main__":

    # Create the sounds_processed directory
    os.makedirs('./sounds_processed/', exist_ok=True)

    # init work list
    work = []

    # This grabs the field names so that it's easier to assign the value of fields to keys or something like that
    DBFields = sounds_db.conn.FieldNamesForTable('sounds')

    Rows = sounds_db.conn.DoQuery('SELECT * FROM sounds')
    for Row in Rows:
        Sound = {}
        for FieldName, FieldID in DBFields.items():
            Sound[FieldName] = Row[FieldID]

        try:
            if os.stat(f'./sounds_master/{Sound["name"]}').st_mtime < os.stat(f'./sounds_processed/{Sound["id"]}/0.wav').st_mtime:
                continue
        except FileNotFoundError:
            pass

        work.append([Sound['id'], Sound['name'], Sound['base_volume_adjust'], Sound['tempo_range']])

    if len(work) == 0:
        print('Found nothing to do')

    else:
        pool_handler()
        print('Done')
