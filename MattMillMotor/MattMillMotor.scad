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
MillB             = 80;
MillL             = 152+2*28;
MillPodest        = 24.8;
MotorScrewDist    = 44;
MotorM6           = 6;
MotorRotMount     = 20;
MotorMountThick   = 5;//20;
MotorScrewGround  = 37;


module Nut()
{
  difference()
  {  
    cylinder(d=DeckelDurchmesser+2*DeckelNutD,h=DeckelNutH+sa);
    translate([0,0,-sa])
        cylinder(d=DeckelDurchmesser,h=DeckelNutH+2*sa);   
  }
}  

module MillMount(posx, posy,dicke)
{
    moveX = (MillL - MillOutL) / 2;
    moveY = (MillB - MillOutB) / 2;
    translate([posx+moveX ,posy+moveY,-sa])
    {
        cube([MillOutL,MillOutB,dicke+2*sa]);
        // links
        translate([-MillMountScrew/2.0-MillScrewMidX ,MillOutB/2,0])
            cylinder(d=MillMountScrew,h=dicke+2*sa);
        // rechts
        translate([MillMountScrew/2+MillScrewMidX+MillOutL,MillOutB/2,0])
            cylinder(d=MillMountScrew,h=dicke+2*sa);
        // oben
        dPos = (MillOutL - MillScrewSideD) / 2.0 - MillMountScrew / 2.0;
        echo ( dPos);
        translate([dPos,MillOutB+MillScrewSideY+MillMountScrew / 2.0,0])
            cylinder(d=MillMountScrew,h=dicke+2*sa);
        translate([MillOutL-dPos,MillOutB+MillScrewSideY+MillMountScrew / 2.0,0])
            cylinder(d=MillMountScrew,h=dicke+2*sa);
        // unten
        translate([dPos,-MillScrewSideY-MillMountScrew / 2.0,0])
            cylinder(d=MillMountScrew,h=dicke+2*sa);
        translate([MillOutL-dPos,-MillScrewSideY-MillMountScrew / 2.0,0])
            cylinder(d=MillMountScrew,h=dicke+2*sa);
        
    }
}  

module MotorMountScrews(posx, posy)
{
    hight = MotorScrewDist * sqrt(3) / 2.0;
    posY = hight / 3.0;
    posYInv = hight - posY;
    posX = MotorScrewDist / 2.0;
    echo (hight - posY );
    
    translate([posx+MotorMountThick/2,posy+MotorMountThick,MotorScrewGround])
    {
        rotate([90,0,0])
            difference()
            {
                translate([-MotorMountThick/2,-MotorScrewGround,0])
                    cube([MotorScrewDist+MotorM6+MotorMountThick,hight+MotorM6+MotorMountThick/2+MotorScrewGround,MotorMountThick]);
                translate([MotorM6/2,MotorM6/2,-sa])
                {
                    translate([0,hight,0])
                        cylinder(d=MotorM6,h=MotorMountThick+2*sa);
                    translate([MotorScrewDist,hight,0])
                        cylinder(d=MotorM6,h=MotorMountThick+2*sa);
                    translate([MotorScrewDist/2.0,0,0])
                        cylinder(d=MotorM6,h=MotorMountThick+2*sa);
                    translate([MotorScrewDist/2.0,posYInv,0])
                        cylinder(d=MotorRotMount,h=MotorMountThick+2*sa);
                }
            }
    }
}

module MillMountPodest(posX,posY)
{
  difference()
  { 
      translate([posX,posY,0])
      cube([MillL,MillB,MillPodest]);      
      MillMount(posX,posY,MillPodest);
  }
}  

module Deckel()
{
  pX = -100;
  pY = 0;  
  difference()
  {  
    cylinder(d=DeckelDurchmesser+2*DeckelRand,h=DeckelDicke);
    translate([0,0,0])
        Nut();
    MillMount(pX,pY,DeckelDicke);
  }
  translate([0,0,DeckelDicke])
    MillMountPodest(pX,pY);
}  


MillMountPodest(0,0);
//MotorMountScrews(0,0);
//Deckel();