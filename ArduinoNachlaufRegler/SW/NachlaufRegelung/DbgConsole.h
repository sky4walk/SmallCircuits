// brausteuerung@AndreBetz.de
#ifndef __DBGCONSOLE__
#define __DBGCONSOLE__

#ifdef NO_CONSOLE
  #define CONSOLE(x) \
      do             \
      {              \
      } while (0)
  #define CONSOLELN CONSOLE
  #define CONSOLEF CONSOLE
#else
  #define CONSOLE(...)               \
      do                             \
      {                              \
          Serial.print(__VA_ARGS__); \
      } while (0)
  #define CONSOLELN(...)               \
      do                               \
      {                                \
          Serial.println(__VA_ARGS__); \
      } while (0)
#endif

#endif
