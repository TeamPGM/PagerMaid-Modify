#!/bin/sh -ex

src=$1
dest="result.png"
font=$2
header=$3
footer=$4

width=$(identify -format %w "${src}")
caption_height=$((width/8))
strokewidth=$((width/500))

convert "${src}" \
  -background none \
  -font "${font}" \
  -fill white \
  -stroke black \
  -strokewidth ${strokewidth} \
  -size "${width}"x${caption_height} \
  -gravity north caption:"${header}" -composite \
  -gravity south caption:"${footer}" -composite \
  "${dest}"
