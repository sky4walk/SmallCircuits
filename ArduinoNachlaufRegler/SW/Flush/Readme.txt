Install USB Arduino Driver:
---------------------------
- Run CH341SER\Setup.exe
- Press install
- connect Arduino Board with USB
- wait until hardware is installed (this could take some minutes)

Flush Arduino Board:
--------------------
- press <Windows>+R and put in "cmd" and press <OK>
- go to directory "avrdude"
- start listComPorts.exe
- in the ouput there is the com port where the arduino is. set the com port in the avrdude command -PCOM<Nr>
- upload flush file: avrdude.exe -v -patmega328p -carduino -PCOM3 -b115200 -D -Uflash:w:Brausteuerung.cpp.hex:i

