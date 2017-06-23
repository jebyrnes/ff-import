#!/bin/bash

find temp/L* -type d | xargs -P 4 -I {} python simple.py --full {}
echo "Mogrifying, please wait"
find L*/accepted/*.png | xargs -P 4 mogrify -resize 500x500
echo "Done"
