#!/bin/bash
datum=$(date +"%Y-%-m-%d")
echo $datum
datumAgo=$(date +"%Y-%-m-%d" -d"7 day ago")
echo $datumAgo
mkdir /home/pi/Diskstation/Cam/Cam1/$datum
mv /home/pi/Diskstation/Cam/Cam1/*.jpg /home/pi/Diskstation/Cam/Cam1/$datum/
rm -r /home/pi/Diskstation/Cam/Cam1/$datumAgo/
mkdir /home/pi/Diskstation/Cam/Cam2/$datum
mv /home/pi/Diskstation/Cam/Cam2/*.jpg /home/pi/Diskstation/Cam/Cam2/$datum/
mv /home/pi/Diskstation/Cam/Cam2/*.mp4 /home/pi/Diskstation/Cam/Cam2/$datum/
rm -r /home/pi/Diskstation/Cam/Cam2/$datumAgo/
