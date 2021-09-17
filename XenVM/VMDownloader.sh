#!/bin/bash
fileid="1SF6A7tdrjqnpJqOSWyjfQZzgrIAorgiE"
filename="vm-image.zip"

curl -c ./cookie -s -L "https://drive.google.com/uc?export=download&id=${fileid}" > /dev/null

curl -Lb ./cookie "https://drive.google.com/uc?export=download&confirm=`awk '/download/ {print $NF}' ./cookie`&id=${fileid}" -o ${filename}

jar xvf ${filename}

mv expran-disk pmon-disk
mv expran-swap pmon-swap

rm ${filename}
rm cookie


