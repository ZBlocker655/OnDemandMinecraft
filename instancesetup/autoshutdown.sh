#!/bin/bash
printenv
set -x
SERVICE='server.jar'
if ps ax | grep -v grep | grep $SERVICE > /dev/null; then
    no_players_regex="There[[:space:]]are[[:space:]]0[[:space:]]of[[:space:]]a[[:space:]]max[[:space:]](of[[:space:]])?[[:digit:]]+[[:space:]]players[[:space:]]online"
	$(screen -S minecraft -p 0 -X stuff "list^M")
	sleep 5
	$(screen -S minecraft -p 0 -X stuff "list^M")
	sleep 5
	PLAYERSLIST=$(tail -n 1 /home/ubuntu/logs/latest.log | cut -f2 -d"/" | cut -f2 -d":")
	echo $PLAYERSLIST
	if [[ "$PLAYERSLIST" =~ $no_players_regex ]]
	then
		echo "Waiting for players to come back in 12m, otherwise shutdown"
		sleep 12m
		$(screen -S minecraft -p 0 -X stuff "list^M")
		sleep 5
		$(screen -S minecraft -p 0 -X stuff "list^M")
		sleep 5
		PLAYERSLIST=$(tail -n 1 /home/ubuntu/logs/latest.log | cut -f2 -d"/" | cut -f2 -d":")
		if [[ "$PLAYERSLIST" =~ $no_players_regex ]]
		then
			echo "Server has been idle long enough. Shutting down..."
			$(sudo /sbin/shutdown -P +1)
		fi
	fi
else
	echo "Screen does not exist, briefly waiting before trying again"
	sleep 5m
	if ! ps ax | grep -v grep | grep $SERVICE > /dev/null; then
		echo "Screen does not exist, shutting down"
		$(sudo /sbin/shutdown -P +1)
	fi
fi
set +x
