// Andre Betz
// github@AndreBetz.de

$fn=100;

sa                = 0.1;
DeckelDurchmesser = 325;
DeckelRand        = 10;
DeckelDicke       = 6;
DeckelNutD        = 2;
DeckelNutH        = 3;

module Nut()
{
  difference()
  {  
    cylinder(d=DeckelDurchmesser+2*DeckelNutD,h=DeckelNutH+sa);
    translate([0,0,-sa])
        cylinder(d=DeckelDurchmesser,h=DeckelNutH+2*sa);   
  }
}  
module Deckel()
{
  difference()
  {  
    cylinder(d=DeckelDurchmesser+2*DeckelRand,h=DeckelDicke);
    translate([0,0,-sa])
        Nut();
  }
}  



Deckel();