@echo off
rem
rem - parameter is a cemetery name, e.g. voennoe, zapadnoe... etc
rem - maybe you need to add the directory containing pscp to the system path
rem
echo get %1.csv export.csv.partial | psftp.exe -l terminal -i putty.ppk register.ritual-minsk.by
del /Q export.csv 2> nul
rename export.csv.partial export.csv
