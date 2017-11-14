#!/bin/bash

find temp/L* -type d | xargs -P 4 -I {} python simple.py --full {}
echo "Mogrifying, please wait"
find L*/accepted | xargs -P 2 -I {} find {}/*.png | xargs - P 2 mogrify -resize 500x500
echo "Done"
