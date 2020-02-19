#!/bin/sh -ex

src=$1
dest="result.gif"
font=$2
header=$3
footer=$4

width=$(identify -format %w "${src}")
caption_height=$((width/8))
strokewidth=$((width/500))

ffmpeg -i "${src}" \
 -vf "fps=10,scale=320:-1:flags=lanczos" \
 -c:v pam \
 -f image2pipe - | \
 convert -delay 10 \
 - -loop 0 \
 -layers optimize \
 output.gif

convert "output.gif" \
\( -clone 0 -coalesce -gravity South -background none -size 435x65.5 caption:"${header}" \) -swap -1,0 \
"${dest}"

rm output.gif