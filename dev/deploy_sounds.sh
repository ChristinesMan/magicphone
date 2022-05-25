#!/bin/bash

# run the sound processor
echo ''
python3 sounds_process.py
echo ''

# did that go ok?
echo ''
read -ep 'Press a key to continue if that went well'
echo ''

# Stop
echo ''
echo Stopping
echo ''
ssh magicphone.wifi 'sudo systemctl stop magicphone.service'

# Wait for stoppage
echo ''
echo Waiting 2s
echo ''
sleep 2s

# rsync db up
echo ''
echo Rsync up db
echo ''
rsync -Pz ./sounds.sqlite magicphone.wifi:./

# rsync up master sounds
echo ''
echo Rsync up master sounds
echo ''
rsync -ralz --stats --delete ./sounds_master/ magicphone.wifi:./sounds_master/

# rsync processed sounds
echo ''
echo Rsync up processed sounds
echo ''
rsync -ralz --stats --delete ./sounds_processed/ magicphone.wifi:./sounds_processed/

# Start
#echo Starting
#echo ''
#ssh magicphone.wifi 'systemctl start magicphone.service'
