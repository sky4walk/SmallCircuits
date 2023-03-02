// Andre Betz
// github@AndreBetz.de

$fn=100;

sa                = 0.1;
DeckelDurchmesser = 325;
DeckelDicke       = 6;
DeckelNutD        = 5;
DeckelNutH        = 3;
DeckelRand        = DeckelNutD*2;
MillOutL          = 156;
MillOutB          = 50;
MillMountScrew    = 8.6;
MillScrewMidX     = 12.6;
MillScrewSideY    = 3.1;
MillScrewSideD    = 101.1;
MillB             = 80;
MillL             = 152+2*28;
MillPodest        = 26.5;
MotorScrewDist    = 44;
MotorM6           = 6;
MotorRotMount     = 20;
MotorMountThick   = 18;
MotorScrewGround  = 37;
MotorMillPosY     = 80;
MotorMillPosX     = 35;

module Nut()
{
  difference()
  {  
    cylinder(d=DeckelDurchmesser+2*DeckelNutD,h=DeckelNutH);
    translate([0,0,-sa])
        cylinder(d=DeckelDurchmesser,h=DeckelNutH+2*sa);   
  }
}  

module MillMount(posx, posy, posZ, dicke)
{
    moveX = (MillL - MillOutL) / 2;
    moveY = (MillB - MillOutB) / 2;
    translate([posx+moveX ,posy+moveY,posZ-sa])
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
                //translate([MotorM6/2,MotorM6/2,-sa])
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
      MillMount(posX,posY,0,MillPodest);
  }
}  

module MotorMillCombiPlate(posX,posY)
{
    MotorMountScrews(MotorMillPosX,-MotorMillPosY);
    translate([posX,posY-MotorMillPosY,0])
    {
        difference()
        {
            cube([MillL,MotorMountThick,MillPodest]);
            translate([MillMountScrew,MillMountScrew,-sa])
                cylinder(d=MillMountScrew,h=MillPodest+2*sa);
            translate([MillL-MillMountScrew,MillMountScrew,-sa])
                cylinder(d=MillMountScrew,h=MillPodest+2*sa);
        }
    }
    translate([posX,posY-MotorMillPosY+MotorMountThick,0])
        cube([MotorMountThick,MotorMillPosY-MotorMountThick,MillPodest]);
    translate([posX+MillL-MotorMountThick,posY-MotorMillPosY+MotorMountThick,0])
        cube([MotorMountThick,MotorMillPosY-MotorMountThick,MillPodest]);
    translate([posX+(MillL-MotorMountThick)/2,posY-MotorMillPosY+MotorMountThick,0])
        cube([MotorMountThick,MotorMillPosY-MotorMountThick,MillPodest]);    
}

module Deckel(posX,posY)
{  
  difference()
  {
    translate([posX,posY,-DeckelDicke])
        cylinder(d=DeckelDurchmesser+2*DeckelRand,h=DeckelDicke);
    translate([posX,posY,-DeckelDicke-sa])
        Nut();
    MillMount(0,0,-DeckelDicke,DeckelDicke);
    translate([0,-MotorMillPosY,-DeckelDicke-sa])
    {  
        translate([MillMountScrew,MillMountScrew,-sa])
            cylinder(d=MillMountScrew,h=MillPodest+2*sa);
        translate([MillL-MillMountScrew,MillMountScrew,-sa])
            cylinder(d=MillMountScrew,h=MillPodest+2*sa);
    }
  }
}  

MillMountPodest(0,0);
MotorMillCombiPlate(0,0);
//Deckel((DeckelDurchmesser+DeckelRand)/3,-(DeckelDurchmesser+DeckelRand)/10);
