// brausteuerung@AndreBetz.de
// hier gilt die Bierlizenz
///////////////////////////////////////////////
// includes
///////////////////////////////////////////////
#include <RCSwitch.h>
#include "DbgConsole.h"
#include "WaitTime.h"
///////////////////////////////////////////////
// defines
///////////////////////////////////////////////
#define PINSWITCH           11  //D11
#define PINKEY              10  //D12
#define PINPOTI             A0
#define STATE_START         1
#define STATE_PRESSED       2
#define STATE_WAIT          3
#define TIMESWITCHSND       1000
#define TIMENACHLAUF        10 //sekunden
#define SWITCH_ON           1631343
#define SWITCH_OFF          1631342
#define SWITCH_PROT         1
#define SWITCH_PULSELENGTH  315
#define SWITCH_BITS         24
#define SWITCH_REPEAT       10
///////////////////////////////////////////////////////////////////////////////
// variablen
///////////////////////////////////////////////////////////////////////////////
RCSwitch  mySwitch    = RCSwitch();
WaitTime  sendSwitch;
WaitTime  switchOb;
bool      swimKey     = false;
bool      switchState = false;
bool      switchChg   = false;
int       actState    = STATE_START;
///////////////////////////////////////////////////////////////////////////////
// Relais
///////////////////////////////////////////////////////////////////////////////
void Relais(bool onOff)
{
  if ( onOff )
  {
    CONSOLELN("On");
    mySwitch.send(SWITCH_ON, SWITCH_BITS);
  }
  else
  {
    CONSOLELN("Off");
    mySwitch.send(SWITCH_OFF, SWITCH_BITS);
  }
}

void setup() {
  pinMode(PINKEY,  INPUT_PULLUP);
  pinMode(LED_BUILTIN, OUTPUT); //D13
  Serial.begin(9600);
  // start 433MHz modul switch  
  mySwitch.enableTransmit(PINSWITCH);
  mySwitch.setProtocol(SWITCH_PROT);
  mySwitch.setPulseLength(SWITCH_PULSELENGTH);
  mySwitch.setRepeatTransmit(SWITCH_REPEAT);
  // timer
  sendSwitch.setTime(TIMESWITCHSND);
  switchOb.setTime(TIMENACHLAUF*1000);
}

void loop() {
  // interval wert lesen
  int potiVal = analogRead(PINPOTI);
  int timeVal = map(potiVal, 0, 1023, 0, TIMENACHLAUF*1000);
  switchOb.setTime(timeVal);
  
  // schalter abfragen
  if ( LOW == digitalRead(PINKEY) ) {
    swimKey = true;
    digitalWrite(LED_BUILTIN, HIGH);
  } else {
    swimKey = false;
    digitalWrite(LED_BUILTIN, LOW);
  }
  
  // state machine
  switch(actState) {
    case STATE_START:
      if ( true == swimKey ) {
        switchState = true;
        switchChg   = true;
        actState = STATE_PRESSED;
        CONSOLE(F("STATE_PRESSED: "));
        CONSOLELN(timeVal);
    }
      break;
    case STATE_PRESSED:
      if ( false == swimKey ) {
        actState = STATE_WAIT;
        switchOb.restart();
        CONSOLELN(F("STATE_WAIT"));
      }
      break;
    case STATE_WAIT:
      if ( switchOb.timeOver() ) {
        actState = STATE_START;
        switchState = false;
        switchChg   = true;
        CONSOLELN(F("STATE_START"));
      } else if ( true == swimKey ) {
        actState = STATE_PRESSED;
        switchOb.restart();
        CONSOLELN(F("STATE_WAIT"));
      }
      break;
    default:
      break;
  }

  sendSwitch.start();
  if ( sendSwitch.timeOver() || true == switchChg ) {
    sendSwitch.restart();
    switchChg = false;
    Relais(switchState);
  }
}
