SET COMPORT=COM4

REM Arduino über USB Bus anschliessen
REM %AVRPATH%\listComPorts.exe aufrufen um COM Port zu bestimmen
REM erhaltenen COM Port anstatt COM9 eintragen

SET AVRPATH=..\Flush\avrdude

%AVRPATH%\avrdude.exe -C%AVRPATH%\avrdude.conf -v -patmega328p -carduino -P%COMPORT% -b57600 -D -Uflash:w:NachlaufRegelung.ino.hex:i 

cmd .