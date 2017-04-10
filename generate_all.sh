#!/bin/bash

find temp/L* -type d | xargs basename | xargs -I {} python simple.py --full {}
