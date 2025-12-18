# LibreCalc Komma->Punkt: Extras > Optionen > Sprachen einstellen Gebietsschema USA
import math

class Oszillator(object):
  def __init__(self, frequence=1, amplitude=10, phase=0, samplerate=360, min=-1, max=1 ):
    self.frequence = frequence
    self.amplitude = amplitude
    self.phase = phase
    self.samplerate = samplerate
    self.position = 0
    self.min = min
    self.max = max
  def funcGen(self):
    pass
  def getSamplerate(self):
    return self.samplerate
  def getPosition(self):
    return self.position
  def play(self):
    val = self.funcGen()
    self.position = self.position + 1
    if self.samplerate < self.position :
      self.position = 0
    return val
  def setRange(self,val):
    return (((val + 1) / 2 ) * (self.max - self.min)) + self.min

class Sine(Oszillator):
  def funcGen(self) :
    increment = ( 2 * math.pi * self.frequence ) / self.samplerate
    i = increment * self.position
    p = ( self.phase / 360 ) * 2 * math.pi
    v = math.sin( p + i )
    v = self.setRange( v )
    return v * self.amplitude

class Square(Oszillator):
  def funcGen(self) :
    self.threshold = 0
    increment = ( 2 * math.pi * self.frequence ) / self.samplerate
    p = ( self.phase / 360 ) * 2 * math.pi
    i = increment * self.position
    v = math.sin( p + i )
    if ( v < self.threshold ) :
      ret = self.min
    else:
      ret = self.max
    return ret * self.amplitude

class Saw(Oszillator):
  def funcGen(self) :
    period =  self.samplerate / self.frequence
    increment = ( 2 * math.pi * self.frequence ) / self.samplerate
    p = ( ( self.phase + 180 ) / 360 ) * period
    div = (increment + self.position + p ) / period
    val = 2 * (div - math.floor(0.5 + div))
    val = self.setRange(val)
    return val * self.amplitude

class Triangle(Oszillator):
  def funcGen(self) :
    period =  self.samplerate / self.frequence
    increment = ( 2 * math.pi * self.frequence ) / self.samplerate
    p = ( ( self.phase + 90 ) / 360 ) * period
    div = (increment + self.position + p ) / period
    val = 2 * (div - math.floor(0.5 + div))
    val = (abs(val) - 0.5) * 2
    val = self.setRange(val)
    return val * self.amplitude

class Mixer(object):
  def __init__(self):
    self.oszList = []
  def addOszillator(self,osz):
    self.oszList.append(osz)
  def play(self):
    n = len(self.oszList)
    sum = 0
    for o in self.oszList:
      v = o.play()
      sum = sum + v
    return sum / n

#funcplay = Triangle()
f1 = Sine()
f2 = Sine(2)

m = Mixer()
m.addOszillator(f1)
m.addOszillator(f2)
m.addOszillator(Sine(3))

for pos in range(f1.getSamplerate()) :
  print( m.play() )
