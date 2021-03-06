import os
import sys
import time
import random
import math

import log
import db

class SoundsDB():
    """
        This class basically manages everything to do with sounds

        There is a SQLite db that contains all sounds
        The db has all of the sounds in it. There is a preprocess.py script that will take the master sounds and process them into directories to be played
    """

    def __init__(self):

        # This grabs the field names so that it's easier to assign the value of fields to keys or something like that
        self.DBFields = db.conn.FieldNamesForTable('sounds')

    def GetSound(self, sound_id):
        """
            Returns a sound from the database as a dict.
        """

        Rows = db.conn.DoQuery(f'SELECT * FROM sounds WHERE id = {sound_id}')
        if Rows == None:
            return None
        else:
            Sound = {}
            for FieldName, FieldID in self.DBFields.items():
                Sound[FieldName] = Rows[0][FieldID]
            return Sound

    def All(self):
        """
            Return a list of all sounds in the database. Called when building the web interface only, pretty much, so far. 
        """

        Rows = db.conn.DoQuery('SELECT * FROM sounds')
        Sounds = []
        for Row in Rows:
            Sound = {}
            for FieldName, FieldID in self.DBFields.items():
                Sound[FieldName] = Row[FieldID]
            Sounds.append(Sound)
        return Sounds

    def Update(self, sound_id, base_volume_adjust = None, tempo_range = None, replay_wait = None):
        """
            Update one sound
        """

        if base_volume_adjust != None:
            db.conn.DoQuery(f'UPDATE sounds SET base_volume_adjust = {base_volume_adjust} WHERE id = {sound_id}')
        if tempo_range != None:
            db.conn.DoQuery(f'UPDATE sounds SET tempo_range = {tempo_range} WHERE id = {sound_id}')
        if replay_wait != None:
            db.conn.DoQuery(f'UPDATE sounds SET replay_wait = {replay_wait} WHERE id = {sound_id}')
        db.conn.DoCommit()

    def NewSound(self, new_path):
        """
            Add a new sound to the database. Returns the new sound id. The new file will already be there.
        """

        db.conn.DoQuery(f'INSERT INTO sounds (id,name) VALUES (NULL, \'{new_path}\')')
        db.conn.DoCommit()
        Rows = db.conn.DoQuery(f'SELECT id FROM sounds WHERE name = \'{new_path}\'')
        if Rows == None:
            return None
        else:
            return Rows[0][0]

    def DelSound(self, sound_id):
        """
            Delete a sound from the database and files
        """

        DeadSoundWalking = self.GetSound(sound_id = sound_id)
        os.remove('./sounds_master/' + DeadSoundWalking['name'])
        os.system(f'rm -rf ./sounds_processed/{sound_id}/')
        db.conn.DoQuery(f'DELETE FROM sounds WHERE id = {sound_id}')
        db.conn.DoCommit()
        Collections = self.CollectionsForSound(sound_id = sound_id)
        for CollectionName,CollectionState in Collections:
            if CollectionState == True:
                self.CollectionUpdate(sound_id = sound_id, collection_name = CollectionName, state = False)

    def Reprocess(self, sound_id):
        """
            Reprocess one sound.
            This is mostly borrowed from the preprocess.py on the desktop that preprocesses all sounds
        """

        # First go get the sound from the db
        TheSound = self.GetSound(sound_id = sound_id)

        # Get all the db row stuff into nice neat variables
        SoundId = str(TheSound['id'])
        SoundName = str(TheSound['name'])
        SoundBaseVolumeAdjust = TheSound['base_volume_adjust']
        SoundTempoRange = TheSound['tempo_range']

        # Delete the old processed sound
        os.system('rm -rf ./sounds_processed/' + SoundId + '/*.wav')

        # Create the destination directory
        os.makedirs('./sounds_processed/' + SoundId, exist_ok=True)

        # If we're adjusting the sound volume, ffmpeg, otherwise just copy the original file to 0.wav, which is the file with original tempo
        if SoundBaseVolumeAdjust != 1.0:
            exitstatus = os.system('ffmpeg -v 0 -i ./sounds_master/' + SoundName + ' -filter:a "volume=' + str(SoundBaseVolumeAdjust) + '" ./sounds_processed/' + SoundId + '/tmp_0.wav')
            log.main.info('Jacked up volume for ' + SoundName + ' (' + str(exitstatus) + ')')
        else:
            exitstatus = os.system('cp ./sounds_master/' + SoundName + ' ./sounds_processed/' + SoundId + '/tmp_0.wav')
            log.main.info('Copied ' + SoundName + ' (' + str(exitstatus) + ')')

        # If we're adjusting the tempo, use rubberband to adjust 0.wav to various tempos. Otherwise, we just have 0.wav and we're done
        # removed --smoothing because it seemed to be the cause of the noise at the end of adjusted sounds
        if SoundTempoRange != 0.0:
            for Multiplier in [-1, -0.75, -0.5, -0.25, 0.25, 0.5, 0.75, 1]:
                exitstatus = os.system('rubberband --quiet --realtime --pitch-hq --tempo ' + format(1-(SoundTempoRange * Multiplier), '.2f') + ' ./sounds_processed/' + SoundId + '/tmp_0.wav ./sounds_processed/' + SoundId + '/tmp_' + str(Multiplier) + '.wav')
                log.main.info('Rubberbanded ' + SoundId + ' to ' + str(Multiplier) + ' (' + str(exitstatus) + ')')

                exitstatus = os.system('ffmpeg -v 0 -i ./sounds_processed/' + SoundId + '/tmp_' + str(Multiplier) + '.wav -ar 44100 ./sounds_processed/' + SoundId + '/' + str(Multiplier) + '.wav')
                log.main.info('Downsampled ' + SoundId + ' tempo ' + str(Multiplier) + ' (' + str(exitstatus) + ')')

        exitstatus = os.system('ffmpeg -v 0 -i ./sounds_processed/' + SoundId + '/tmp_0.wav -ar 44100 ./sounds_processed/' + SoundId + '/0.wav')
        log.main.info('Downsampled ' + SoundId + ' tempo 0 (' + str(exitstatus) + ')')
        exitstatus = os.system('rm -f ./sounds_processed/' + SoundId + '/tmp_*')
        log.main.info('Removed tmp files for ' + SoundId + ' (' + str(exitstatus) + ')')

    def AmplifyMasterSounds(self):
        """
            Go through all sounds. If there's a BaseVol not 1.0, amplify the master sound and set BaseVol to 1.0 to make it permanent
            I wanted to fix a lot of background noise that got into the sounds, and I think that happened when I set BaseVol,
            so this is for that little fixit job. 
        """
        for Sound in self.All():
            SoundId = Sound['id']
            SoundName = Sound['name']
            SoundBaseVolumeAdjust = Sound['base_volume_adjust']

            if SoundBaseVolumeAdjust != 1.0:
                os.rename(f'./sounds_master/{SoundName}', f'./sounds_master/{SoundName}_backup')
                exitstatus = os.system(f'ffmpeg -v 0 -i ./sounds_master/{SoundName}_backup -filter:a "volume={SoundBaseVolumeAdjust}" ./sounds_master/{SoundName}')
                log.main.info(f'Updated volume for {SoundName} ({exitstatus})')
                self.Update(SoundId, base_volume_adjust = '1.0')

    def ReprocessModified(self):
        """
            Go through all sounds. Run reprocess if the date modified of the master file is later than the processed file. 
            This is for when the master sounds are modified to remove clicks and junk. 
        """
        for Sound in self.All():
            SoundId = Sound['id']
            SoundName = Sound['name']

            if os.stat(f'./sounds_master/{SoundName}').st_mtime > os.stat(f'./sounds_processed/{SoundId}/0.wav').st_mtime:
                self.Reprocess(SoundId)

    def ReprocessAll(self):
        """
            Go through all sounds. Run reprocess. 
            Usually this is run by itself from command line
            On pi this takes hours. Use process_sounds.py on the desktop.
        """
        for Sound in self.All():
            SoundId = Sound['id']
            SoundName = Sound['name']

            self.Reprocess(SoundId)

    def PlayAll(self):
        """
            Go through all sounds, play them one at a time. 
            For debugging and QA
        """

        # wait time
        time.sleep(5)

        for Sound in self.All():
            SoundId = Sound['id']
            SoundName = Sound['name']

            if 'breathe_normal' not in SoundName:
                log.main.info(f'Playing {SoundName}')
                os.system('aplay ./sounds_master/' + SoundName)
                time.sleep(2)

    def Collections(self):
        """
            Returns all the names from the collections table as a list
        """

        Rows = db.conn.DoQuery('SELECT name FROM collections')

        Collections = []
        for Row in Rows:
            Collections.append(Row[0])
        return Collections

    def CollectionsForSound(self, sound_id):
        """
            Returns all the collection names indicating which ones a specific sound is in. Used to build web page with checkboxes.
        """

        sound_id = int(sound_id)

        Rows = db.conn.DoQuery('SELECT name,sound_ids FROM collections')

        CollectionStates = []
        for Row in Rows:

            RowInCollection = False

            if Row[1] != None and Row[1] != 'None':
                for element in Row[1].split(','):
                    if '-' in element:
                        id_bounds = element.split('-')
                        id_min = int(id_bounds[0])
                        id_max = int(id_bounds[1])
                        if sound_id <= id_max and sound_id >= id_min:
                            RowInCollection = True
                            break
                    else:
                        if sound_id == int(element):
                            RowInCollection = True
                            break
            CollectionStates.append((Row[0], RowInCollection))
        return CollectionStates

    def CollectionUpdate(self, sound_id, collection_name, state):
        """
            Updates one collection for one sound
        """

        sound_id = int(sound_id)

        # Get the sound ids for the collection name. Might be None if there were no sounds assigned to it
        Collection = self.GetCollection(collection_name)

        # Unpack the "9-99,999" format into a list of individual sound ids, unless the collection was null
        CollectionIDs = []
        if Collection != None and Collection != 'None':
            for element in Collection.split(','):
                if '-' in element:
                    id_bounds = element.split('-')
                    id_min = int(id_bounds[0])
                    id_max = int(id_bounds[1])
                    for CollectionID in range(id_min, id_max + 1):
                        CollectionIDs.append(CollectionID)
                else:
                    CollectionIDs.append(int(element))

        # Now that we have it in a flat list form, do whatever, add or delete, then sort the list so that it's in integer order again
        if state == True:
            CollectionIDs.append(sound_id)
        else:
            try:
                CollectionIDs.remove(sound_id)
            except ValueError:
                pass
        CollectionIDs.sort()

        # Unless we just emptied the list, pack it back up into a "9-99,999" format and hack off the ending ,
        if len(CollectionIDs) > 0:
            Collection = ''
            CollectionIDPrev = None
            CollectionIDRangeMin = None
            CollectionIDRangeMax = None
            for CollectionID in CollectionIDs:
                if CollectionIDPrev == None:
                    CollectionIDPrev = CollectionID
                    continue
                if CollectionID == CollectionIDPrev:
                    continue
                if CollectionID - CollectionIDPrev == 1:
                    if CollectionIDRangeMin == None:
                        CollectionIDRangeMin = CollectionIDPrev
                    CollectionIDRangeMax = CollectionID
                    CollectionIDPrev = CollectionID
                    continue
                if CollectionID - CollectionIDPrev > 1:
                    if CollectionIDRangeMin != None:
                        Collection += f'{CollectionIDRangeMin}-{CollectionIDRangeMax},'
                        CollectionIDRangeMin = None
                        CollectionIDRangeMax = None
                    else:
                        Collection += f'{CollectionIDPrev},'
                    CollectionIDPrev = CollectionID
                    continue
            if CollectionIDRangeMax != None:
                Collection += f'{CollectionIDRangeMin}-{CollectionIDRangeMax},'
            else:
                Collection += f'{CollectionIDPrev},'
            Collection = Collection[:-1]
        else:
            Collection = None

        # Write the change to db
        self.SetCollection(collection_name = collection_name, sound_ids = Collection)

    def GetCollection(self, collection_name):
        """
            Returns one collection by name
        """

        Rows = db.conn.DoQuery(f'SELECT sound_ids FROM collections WHERE name = \'{collection_name}\'')
        if Rows == None:
            return None
        else:
            return Rows[0][0]

    def SetCollection(self, collection_name, sound_ids):
        """
            Sets one collection
        """

        # I want that field to either be NULL or a string with stuff there
        if sound_ids == None or sound_ids == 'None':
            sound_ids = 'NULL'
        else:
            sound_ids = f'\'{sound_ids}\''

        db.conn.DoQuery(f'UPDATE collections SET sound_ids = {sound_ids} WHERE name = \'{collection_name}\'')
        db.conn.DoCommit()

    def NewCollection(self, collection_name):
        """
            Adds a new collection. Tests for existence first.
        """

        Rows = db.conn.DoQuery(f'SELECT sound_ids FROM collections WHERE name = \'{collection_name}\'')
        if Rows == None:
            db.conn.DoQuery(f'INSERT INTO collections VALUES (NULL, \'{collection_name}\', NULL)')
            db.conn.DoCommit()

    def DelCollection(self, collection_name):
        """
            Delete a collection by name
        """

        db.conn.DoQuery(f'DELETE FROM collections WHERE name = \'{collection_name}\'')
        db.conn.DoCommit()


# There is a table in the db called collections which basically groups together sounds for specific purposes. The sound_ids column is in the form such as 1,2,3-9,10
# A collection is a grouping of sound ids for a specific purpose
# Looking back, I realize I should have put the collection ids in the sounds table and dynamically built the collections that way, but it's done.
class SoundCollection():

    def __init__(self, name):
        self.name = name

        # Thought for a while how to handle the replay_wait that will be per sound
        # There will be a master list, and a list updated every 100s that sounds will actually be selected from
        # And we need a LastUpdate var to keep track of when we last updated the available list
        self.SoundsInCollection = []
        self.SoundsAvailableToPlay = []
        self.NextUpdateSeconds = 0

        # Generator that yields all the sound ids in the collection, from the db
        self.SoundIDs = self.SoundIDGenerator()

        # For each sound in this collection, get the sound and store all it's details
        for sound_id in self.SoundIDs:
            if sound_id != None:
                Sound = soundsdb.GetSound(sound_id = sound_id)
                if Sound != None:
                    Sound['SkipUntil'] = time.time() + ( Sound['replay_wait'] * random.uniform(0.0, 1.2) )
                    self.SoundsInCollection.append(Sound)
                else:
                    log.main.warning(f'Removed derelict sound id {sound_id} from {name} collection')
                    soundsdb.CollectionUpdate(sound_id = sound_id, collection_name = name, state = False)

        # initialize the skip untils to a random amount of time
        self.UpdateAvailableSounds()

    def SoundIDGenerator(self):
        """Generator that yields sound ids
        """

        Row = soundsdb.GetCollection(self.name)

        # In case the db row has null in that field, like no sounds in the collection
        if Row == None or Row == 'None':
            yield None
        else:
            for element in Row.split(','):
                if '-' in element:
                    id_bounds = element.split('-')
                    id_min = int(id_bounds[0])
                    id_max = int(id_bounds[1])
                    for id in range(id_min, id_max+1):
                        yield id
                else:
                    yield int(element)

    def UpdateAvailableSounds(self):
        """Updates the list that keeps track of sounds that are available to play
        """

        # Store the time so that we don't have to call time so much
        CurrentSeconds = time.time()

        # Throw this 5s in the future
        self.NextUpdateSeconds = CurrentSeconds + 5

        # Empty the list of available sounds
        self.SoundsAvailableToPlay = []

        # Go through all the sounds and add available ones to the list
        for Sound in self.SoundsInCollection:
            if Sound['SkipUntil'] < CurrentSeconds:
                self.SoundsAvailableToPlay.append(Sound)

    def GetRandomSound(self, intensity = None):
        """Returns some weird ass rando sound. 
        """

        # if it's time to update the available list, do it
        if self.NextUpdateSeconds < time.time():
            self.UpdateAvailableSounds()

        # There may be times that we run out of available sounds and have to throw a None
        if len(self.SoundsAvailableToPlay) == 0:
            log.sound.warning(f'No sounds available to play in {self.name}')
            return None

        # if the desired intensity is specified, we want to only select sounds near that intensity
        if intensity == None:
            RandoSound = random.choice(self.SoundsAvailableToPlay)
        else:
            SoundsNearIntensity = []
            for Sound in self.SoundsAvailableToPlay:
                if math.isclose(Sound['intensity'], intensity, abs_tol = 0.25):
                    SoundsNearIntensity.append(Sound)
            if len(SoundsNearIntensity) == 0:
                log.sound.warning(f'No sounds near intensity {intensity} in {self.name}')
                return None
            RandoSound = random.choice(SoundsNearIntensity)

        return RandoSound

    def SetSkipUntil(self, SoundID):
        """It used to be that skipuntil got updated in GetRandomSound. That caused a lot of sounds to become unavailable due to a lot of sounds
           being queued but not played in times of heavy activity. So now this is only updated when played. 
        """

        for Sound in self.SoundsInCollection:
            if Sound['id'] == SoundID:
                log.sound.debug(f'Made unavailable: {Sound}')
                Sound['SkipUntil'] = time.time() + ( Sound['replay_wait'] * random.uniform(0.8, 1.2) )
                self.SoundsAvailableToPlay.remove(Sound)
                break

# Initialize this class that handles the sound database
soundsdb = SoundsDB()

# Load all the sound collections
collections = {}
for CollectionName in soundsdb.Collections():
    collections[CollectionName] = SoundCollection(CollectionName)
