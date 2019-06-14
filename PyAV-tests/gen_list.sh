#!/bin/bash

src="../test_clips"

listDate=$(date +%Y-%m-%d)

playlist="$listDate.xml"

# start time in seconds
listStart="21600"

# build Head for playlist
printf  '<playlist>\n\t<head>
		<meta name="author" content="example"/>
		<meta name="title" content="Live Stream"/>
		<meta name="copyright" content="(c)%s example.org"/>
		<meta name="date" content="%s"/>
	</head>\n\t<body>\n' $(date +%Y) $listDate > "$playlist"

# read playlist
while read -r line; do
	clipPath=$(echo "$line" | sed 's/&/&amp;/g')
	clipDuration=$( ffprobe -v error -show_format  "$line" | awk -F= '/duration/{ print $2 }' )

	printf '\t\t<video src="%s" begin="%s" dur="%s" in="%s" out="%s"/>\n' "$clipPath" "$listStart" "$clipDuration" "0.0" "$clipDuration"  >> "$playlist"

	# add start time
	listStart="$( awk -v lS="$listStart" -v cD="$clipDuration" 'BEGIN{ print lS + cD }' )"

done < <( find "$src" -name "*.mp4" | shuf -r -n 6000 )

printf "\t</body>\n</playlist>\n" >> "$playlist"
