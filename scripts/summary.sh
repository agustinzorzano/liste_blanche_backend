#!/bin/bash

source $PROJECT_VIRTUAL_ENVIRONMENT_PATH

python $PROJECT_USERNAMES_PATH | while read line
do
python $PROJECT_SUMMARY_PATH "${line}" &
done
