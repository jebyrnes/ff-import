#!/bin/bash

find temp/L* -type d | xargs basename | xargs -P 4 -I {} python simple.py --full {}
find L*/accepted/*.png | xargs -P 4 mogrify -resize 500x500
