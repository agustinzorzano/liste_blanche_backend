#!/bin/bash

source /home/agustin/Escritorio/Facu-IMT/TAF_Login/Proyecto/flask/venv/bin/activate

cat /home/agustin/Escritorio/Facu-IMT/TAF_Login/Proyecto/flask/usernames.txt | while read line
do
python /home/agustin/Escritorio/Facu-IMT/TAF_Login/Proyecto/flask/email_scan.py "${line}" &
done
