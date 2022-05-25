#!/bin/bash

# Stop
echo Stopping
echo ''
ssh magicphone.wifi 'sudo systemctl stop magicphone.service'

# Wait for stoppage
echo Waiting 2s
echo ''
sleep 2s

# rsync db down
echo Rsync db down
echo ''
rsync -Pz magicphone.wifi:./sounds.sqlite ./

# start sqlite browser
echo Starting SQLite Browser
echo ''
sqlitebrowser ./sounds.sqlite

# rsync db back up
echo Rsync db back up
echo ''
rsync -Pz sounds.sqlite magicphone.wifi:./

# Start
#echo Starting
#echo ''
#ssh magicphone.wifi 'sudo systemctl start magicphone.service'
