PLAYERSLIST=" There are 0 of a max of 20 players online"
no_players_regex="There[[:space:]]are[[:space:]]0[[:space:]]of[[:space:]]a[[:space:]]max[[:space:]](of[[:space:]])?[[:digit:]]+[[:space:]]players[[:space:]]online"

if [[ "$PLAYERSLIST" =~ $no_players_regex ]]
then
    echo "Match"
else
    echo "Not a match"
fi
