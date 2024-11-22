import time

def parse_hex_file_with_address(filename):
    commands = []  # Liste für die Adressen

    with open(filename, 'r') as file:
        for line in file:
            comment = ""
            address_hex = ""

            # Entfernen von führenden und nachfolgenden Leerzeichen
            line = line.strip()

            # Falls die Zeile leer ist oder nur ein Kommentar enthält, überspringen
            if not line or line.startswith('#'):
                continue

            # Die Zeile aufteilen: Adresse, Hex-Wert und Kommentar
            if '#' in line:
                address_hex, comment = line.split('#', 1)
            address_value, hex_value = address_hex.split()           
            
            # Validierung: Adresse und Hex-Wert
            if len(address_value) == 3 and all(c in '0123456789' for c in address_value):
                address_value = int(address_value,10)
                if len(hex_value) == 2 and all(c in '0123456789ABCDEFabcdef' for c in hex_value):
                    commands.append([address_value,hex_value,comment])
    return commands

def is_bit_set(number, position):
    mask = 1 << position  # Verschiebe 1 um die angegebene Bit-Position
    return (number & mask) != 0  # Prüfe, ob das Bit gesetzt ist

class cpu_HT46F47E:
    def __init__(self,startAdr):
        self.PC     = startAdr
        self.regA   = 0
        self.regB   = 0
        self.regC   = 0
        self.regD   = 0
        self.page   = 0
        self.Pin1_DinE4_PA3   = False
        self.Pin2_DinE3_PA2   = False
        self.Pin3_DinE2_PA1   = False
        self.Pin4_DinE1_PA0   = False
        self.Pin15_Dout4_PA7  = False
        self.Pin16_Dout3_PA6  = False
        self.Pin17_Dout2_PA5  = False
        self.Pin18_Dout1_PA4  = False
        self.Pin7_AD2_PB1     = 0
        self.Pin8_AD1_PB0     = 0
        self.Pin10_PWM_PD0    = 0
        self.Pin11_Res        = False
        self.Pin5_SW1_PB3     = False
        self.Pin6_SW2_PB2     = False
        self.command          = 0
        self.param            = 0
    def print(self):
        print("PC:",self.PC)
        print("regA:",self.regA)
        print("regB:",self.regB)
        print("regC:",self.regC)
        print("regD:",self.regD)
        print("Page:",self.page)
        print("Pin1_DinE4_PA3:",self.Pin1_DinE4_PA3)
        print("Pin2_DinE3_PA2:",self.Pin2_DinE3_PA2)
        print("Pin3_DinE2_PA1:",self.Pin3_DinE2_PA1)
        print("Pin4_DinE1_PA0:",self.Pin4_DinE1_PA0)
        print("Pin15_Dout4_PA7:",self.Pin15_Dout4_PA7)
        print("Pin16_Dout3_PA6:",self.Pin16_Dout3_PA6)
        print("Pin17_Dout2_PA5:",self.Pin17_Dout2_PA5)
        print("Pin18_Dout1_PA4:",self.Pin18_Dout1_PA4)
        print("Pin7_AD2_PB1:",self.Pin7_AD2_PB1)
        print("Pin8_AD1_PB0:",self.Pin8_AD1_PB0)
        print("Pin10_PWM_PD0:",self.Pin10_PWM_PD0)
        print("Pin11_Res:",self.Pin11_Res)
        print("Pin5_SW1_PB3:",self.Pin5_SW1_PB3)
        print("Pin6_SW2_PB2:",self.Pin6_SW2_PB2)
        print("command:",self.command)
        print("param:",self.param)

def convertNr2Bits(number):
    bit0 = False
    bit1 = False
    bit2 = False
    bit3 = False

    if is_bit_set( number,0 ) :
        bit0 = True
    if is_bit_set( number,1 ) :
        bit1 = True
    if is_bit_set( number,2 ) :
        bit2 = True
    if is_bit_set( number,3 ) :
        bit3 = True
    return bit0,bit1,bit2,bit3

def simulateTPS_Step(cpuDef,commands):
    command = commands[cpuDef.PC]

    if len(command[1]) == 2:
        cpuDef.command = int(command[1][0],16)
        cpuDef.param = int(command[1][1],16)

        match cpuDef.command:
            case 0: 
                print("0 not used")    
            case 1: #port ausgabe
                cpuDef.Pin18_Dout1_PA4, cpuDef.Pin17_Dout2_PA5, cpuDef.Pin16_Dout3_PA6, cpuDef.Pin15_Dout4_PA7 = convertNr2Bits(cpuDef.param)
                cpuDef.PC = cpuDef.PC + 1
            case 2: #Wartezeit
                cpuDef.PC = cpuDef.PC + 1
            case 3: #sprung zurueck relativ
                cpuDef.PC = cpuDef.PC - cpuDef.param
            case 4: #Weise der Variable A (Akku) neuen Wert zu
                cpuDef.regA = cpuDef.param
                cpuDef.PC = cpuDef.PC + 1
            case 5:
                #1: B = A / 2: C = A / 3: D = A / 4: Dout = A / 5: Dout.0 = A.0
                #6: Dout.1 = A.0 / 7: Dout.2 = A.0 / 8: Dout.3 = A.0 / 9: PWM = A
                match cpuDef.param:
                    case 1:
                        cpuDef.regB = cpuDef.regA
                    case 2:
                        cpuDef.regC = cpuDef.regA
                    case 3:
                        cpuDef.regD = cpuDef.regA
                    case 4:
                        cpuDef.Pin18_Dout1_PA4, cpuDef.Pin17_Dout2_PA5, cpuDef.Pin16_Dout3_PA6, cpuDef.Pin15_Dout4_PA7 = convertNr2Bits(cpuDef.regA)
                    case 5: 
                        if is_bit_set( cpuDef.regA,0 ) :
                            cpuDef.Pin18_Dout1_PA4 = True    
                    case 6: 
                        if is_bit_set( cpuDef.regA,0 ) :
                            cpuDef.Pin17_Dout2_PA5 = True    
                    case 7: 
                        if is_bit_set( cpuDef.regA,0 ) :
                            cpuDef.Pin16_Dout3_PA6 = True    
                    case 8: 
                        if is_bit_set( cpuDef.regA,0 ) :
                            cpuDef.Pin15_Dout4_PA7 = True
                    case 9:
                        cpuDef.Pin10_PWM_PD0 = cpuDef.regA


                cpuDef.PC = cpuDef.PC + 1

    return cpuDef

commands = parse_hex_file_with_address("test.tps")
cpuDef =  cpu_HT46F47E(0)
cpuDef.print()
print("---------------------------------")
cpuDef = simulateTPS_Step(cpuDef,commands)
cpuDef.print()
print("---------------------------------")
cpuDef = simulateTPS_Step(cpuDef,commands)
cpuDef.print()
print("---------------------------------")
cpuDef = simulateTPS_Step(cpuDef,commands)
cpuDef.print()
print("---------------------------------")
