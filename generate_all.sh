#!/bin/bash

find temp/L* -type d | xargs -P 4 -I {} python simple.py --full {}
echo "Mogrifying, please wait"
find L*/accepted -maxdepth 0 | xargs -I {} -P 4 mogrify -resize 500x500 {}/*.png
echo "Done"
