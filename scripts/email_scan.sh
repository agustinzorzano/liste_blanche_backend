#!/bin/bash

source $PROJECT_VIRTUAL_ENVIRONMENT_PATH

cat $PROJECT_USERNAMES_PATH | while read line
do
python $PROJECT_EMAIL_SCAN_PATH "${line}" &
done
