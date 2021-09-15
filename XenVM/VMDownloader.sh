#!/bin/bash
fileid="12SCRqBGAOJwe3BxknTTarrPd7IJX9uR0"
filename="vm-image.zip"

curl -c ./cookie -s -L "https://drive.google.com/uc?export=download&id=${fileid}" > /dev/null

curl -Lb ./cookie "https://drive.google.com/uc?export=download&confirm=`awk '/download/ {print $NF}' ./cookie`&id=${fileid}" -o ${filename}

unzip ${filename}

mv expran-disk pmon-disk
mv expran-swap pmon-swap

rm ${filename}
rm cookie


