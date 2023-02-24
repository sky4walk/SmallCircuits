// Andre Betz
// github@AndreBetz.de

$fn=100;

sa                = 0.1;
DeckelDurchmesser = 325;
DeckelRand        = 10;
DeckelDicke       = 6;
DeckelNutD        = 2;
DeckelNutH        = 3;
MillOutL          = 155;
MillOutB          = 50;
MillMountScrew    = 8.6;
MillScrewMidX     = 12.6;
MillScrewSideY    = 3.1;
MillScrewSideD    = 101.1;
MotorScrewDist    = 44;
MotorM6           = 6;
MotorRotMount     = 20;
MotorMountThick   = 10;//20;
MotorScrewGround  = 20;

module Nut()
{
  difference()
  {  
    cylinder(d=DeckelDurchmesser+2*DeckelNutD,h=DeckelNutH+sa);
    translate([0,0,-sa])
        cylinder(d=DeckelDurchmesser,h=DeckelNutH+2*sa);   
  }
}  

module MillMount(posx, posy)
{
    translate([posx,posy,-sa])
    {
        cube([MillOutL,MillOutB,DeckelDicke+2*sa]);
        // links
        translate([-MillMountScrew/2.0-MillScrewMidX ,MillOutB/2,0])
            cylinder(d=MillMountScrew,h=DeckelDicke+2*sa);
        // rechts
        translate([MillMountScrew/2+MillScrewMidX+MillOutL,MillOutB/2,0])
            cylinder(d=MillMountScrew,h=DeckelDicke+2*sa);
        // oben
        dPos = (MillOutL - MillScrewSideD) / 2.0 - MillMountScrew / 2.0;
        echo ( dPos);
        translate([dPos,MillOutB+MillScrewSideY+MillMountScrew / 2.0,0])
            cylinder(d=MillMountScrew,h=DeckelDicke+2*sa);
        translate([MillOutL-dPos,MillOutB+MillScrewSideY+MillMountScrew / 2.0,0])
            cylinder(d=MillMountScrew,h=DeckelDicke+2*sa);
        // unten
        translate([dPos,-MillScrewSideY-MillMountScrew / 2.0,0])
            cylinder(d=MillMountScrew,h=DeckelDicke+2*sa);
        translate([MillOutL-dPos,-MillScrewSideY-MillMountScrew / 2.0,0])
            cylinder(d=MillMountScrew,h=DeckelDicke+2*sa);
        
    }
}  

module MotorMountScrews(posx, posy)
{
    hight = MotorScrewDist * sqrt(3) / 2.0;
    posY = hight / 3.0;
    posX = MotorScrewDist / 2.0;
    echo (hight - posY );

    rotate([90,0,0])
        translate([posx+2*MotorM6,posy+MotorM6/2+MotorScrewGround,0])
        {
            difference()
            {
                translate([-2*MotorM6,-MotorM6/2-MotorScrewGround,0])
                    cube([MotorScrewDist+4*MotorM6,MotorScrewDist+2*MotorM6+MotorScrewGround,MotorMountThick]);
                translate([0,0,-sa])
                {
                    cylinder(d=MotorM6,h=MotorMountThick+2*sa);
                    translate([MotorScrewDist,0,0])
                        cylinder(d=MotorM6,h=MotorMountThick+2*sa);
                    translate([MotorScrewDist/2.0,hight,0])
                        cylinder(d=MotorM6,h=MotorMountThick+2*sa);
                    translate([MotorScrewDist/2.0,posY,0])
                        cylinder(d=MotorRotMount,h=MotorMountThick+2*sa);
                }
            }
        }
}

module TestMillMount()
{
  tX = 25;
  tY = 20;  
  difference()
  { 
      translate([-tX,-tY,0])
        cube([MillOutL+2*tX,MillOutB+2*tY,DeckelDicke]);      
      MillMount(0,0);
  }
}  

module Deckel()
{
  difference()
  {  
    cylinder(d=DeckelDurchmesser+2*DeckelRand,h=DeckelDicke);
    translate([0,0,0])
        Nut();
    MillMount(-100,0);
  }
}  


TestMillMount();
//MotorMountScrews(0,0);
//Deckel();