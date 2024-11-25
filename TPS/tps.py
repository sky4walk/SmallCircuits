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
        self.page   = 0
        self.ret    = 0
        self.regA   = 0
        self.regB   = 0
        self.regC   = 0
        self.regD   = 0
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
        print("PC:              ",self.PC)
        print("regA:            ",self.regA)
        print("Ret:             ",self.ret)
        print("regB:            ",self.regB)
        print("regC:            ",self.regC)
        print("regD:            ",self.regD)
        print("Pin1_DinE4_PA3:  ",self.Pin1_DinE4_PA3)
        print("Pin2_DinE3_PA2:  ",self.Pin2_DinE3_PA2)
        print("Pin3_DinE2_PA1:  ",self.Pin3_DinE2_PA1)
        print("Pin4_DinE1_PA0:  ",self.Pin4_DinE1_PA0)
        print("Pin15_Dout4_PA7: ",self.Pin15_Dout4_PA7)
        print("Pin16_Dout3_PA6: ",self.Pin16_Dout3_PA6)
        print("Pin17_Dout2_PA5: ",self.Pin17_Dout2_PA5)
        print("Pin18_Dout1_PA4: ",self.Pin18_Dout1_PA4)
        print("Pin7_AD2_PB1:    ",self.Pin7_AD2_PB1)
        print("Pin8_AD1_PB0:    ",self.Pin8_AD1_PB0)
        print("Pin10_PWM_PD0:   ",self.Pin10_PWM_PD0)
        print("Pin11_Res:       ",self.Pin11_Res)
        print("Pin5_SW1_PB3:    ",self.Pin5_SW1_PB3)
        print("Pin6_SW2_PB2:    ",self.Pin6_SW2_PB2)
        print("Command:         ",self.command)
        print("Param:           ",self.param)

def convertNr2Bits(number):
    bit1 = False
    bit2 = False
    bit3 = False
    bit4 = False

    if is_bit_set( number,0 ) :
        bit1 = True
    if is_bit_set( number,1 ) :
        bit2 = True
    if is_bit_set( number,2 ) :
        bit3 = True
    if is_bit_set( number,3 ) :
        bit4 = True
    return bit4,bit3,bit2,bit1

def convertBits2Nr(bit4, bit3, bit2, bit1):
    result = 0
    result  = int(bit1) << 3  # bit1 wird in die höchste Position (2^3) verschoben
    result |= int(bit2) << 2  # bit2 wird um 2 Positionen verschoben
    result |= int(bit3) << 1  # bit3 wird um 1 Position verschoben
    result |= int(bit4)       # bit4 bleibt in der niedrigsten Position
    return result

def simulateTPS_Step(cpuDef,commands):
    command = commands[cpuDef.PC]

    if len(command[1]) == 2:
        cpuDef.command = int(command[1][0],16)
        cpuDef.param = int(command[1][1],16)

        match cpuDef.command:
            case 0: 
                print("0 not used")    
            case 1: #port ausgabe
                cpuDef.Pin15_Dout4_PA7, cpuDef.Pin16_Dout3_PA6, cpuDef.Pin17_Dout2_PA5, cpuDef.Pin18_Dout1_PA4  = convertNr2Bits(cpuDef.param)
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
                        cpuDef.Pin15_Dout4_PA7, cpuDef.Pin16_Dout3_PA6, cpuDef.Pin17_Dout2_PA5, cpuDef.Pin18_Dout1_PA4 = convertNr2Bits(cpuDef.regA)
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
            case 6:
                # Weise die Daten einer Quelle der Variable A zu.
                # Parameter 1-10
                # 1: A = B / 2: A = C / 3: A = D / 4: A = Din / 5: A = Din.0
                #6: A = Din.1 / 7: A = Din.2 / 8: A = Din.3 / 9: A = AD1 / 10: A = AD2
                match cpuDef.param:
                    case 1:
                        cpuDef.regA = cpuDef.regB
                    case 2:
                        cpuDef.regA = cpuDef.regC
                    case 3:
                        cpuDef.regA = cpuDef.regD
                    case 4:
                        cpuDef.regA = convertBits2Nr(cpuDef.Pin15_Dout4_PA7, cpuDef.Pin16_Dout3_PA6, cpuDef.Pin17_Dout2_PA5, cpuDef.Pin18_Dout1_PA4)
                    case 5:
                        cpuDef.regA = int(cpuDef.Pin18_Dout1_PA4)
                    case 6:
                        cpuDef.regA = int(cpuDef.Pin17_Dout2_PA5)
                    case 7:
                        cpuDef.regA = int(cpuDef.Pin16_Dout3_PA6)
                    case 8:
                        cpuDef.regA = int(cpuDef.Pin15_Dout4_PA7)
                    case 9:
                        cpuDef.regA = int(cpuDef.Pin8_AD1_PB0)
                    case 10:
                        cpuDef.regA = int(cpuDef.Pin7_AD2_PB1)
                cpuDef.PC = cpuDef.PC + 1
            case 7:
                #Führe Rechenoperation durch. Ergebnis erhält die Variable A (Akku).
                #Parameter 1-10
                #1: A = A + 1 / 2: A = A – 1 / 3: A = A + B / 4: A = A – B / 5: A = A * B
                #6: A = A / B / 7: A = A and B / 8: A = A or B / 9: A = A xor B / 10: A = not A
                match cpuDef.param:
                    case 1:
                        cpuDef.regA = cpuDef.regA + 1
                    case 2:
                        cpuDef.regA = cpuDef.regA - 1
                    case 3:
                        cpuDef.regA = cpuDef.regA + cpuDef.regB
                    case 4:
                        cpuDef.regA = cpuDef.regA - cpuDef.regB
                    case 5:
                        cpuDef.regA = cpuDef.regA * cpuDef.regB
                    case 6:
                        cpuDef.regA = cpuDef.regA / cpuDef.regB
                    case 7:
                        cpuDef.regA = cpuDef.regA & cpuDef.regB
                    case 8:
                        cpuDef.regA = cpuDef.regA | cpuDef.regB
                    case 9:
                        cpuDef.regA = cpuDef.regA ^ cpuDef.regB
                    case 10:
                        cpuDef.regA = ~cpuDef.regA
                cpuDef.PC = cpuDef.PC + 1
            case 8:
                #Festlegung des High-Anteils der Zieladresse eines Sprunges. Wird bei Sprüngen, Zählschleifen und
                #Unterprogrammen benötigt. Dadurch ist es möglich, alle Adressen innerhalb des Programms zu erreichen. Der
                #Speicher von 128 Bytes wird hier auf 8 Speicherbereiche (mit je 16 Speicherplätzen) unterteilt. Der erste Bereich
                #(Seite) 0 beinhaltet die ersten Adressen 0 bis 15. Befindet sich das Programm auf der Seite 0, muss der Befehl
                cpuDef.page = cpuDef.param
                cpuDef.PC = cpuDef.PC + 1
            case 9:
                #Direkter Sprung auf die Adresse x. Liegt x außerhalb des 0 Bereiches (Adressen 0 – 15), muss der
                #Sprungbereich mit dem Befehl „8“ angegeben werden.
                #Parameter 0-15    
                cpuDef.PC = cpuDef.page * 16 + cpuDef.param
            case 10:
                #Zählschleife. Die Variable C wird dekrementiert. Ist der Zähler abgelaufen und die Variable C den Wert 0 erreicht
                #hat, wird der nächste Befehl ausgeführt. Sonst springt das Programm zu der angegebenen Adresse. Hier muss
                #ggf. mit dem Befehl „8“ der Sprungbereich angegeben werden.
                #Parameter 0-15
                cpuDef.regC = cpuDef.regC - 1
                if ( 0 == cpuDef.regC ) :
                    cpuDef.PC = cpuDef.page * 16 + cpuDef.param
                else:
                    cpuDef.PC = cpuDef.PC + 1
            case 11:
                #Zählschleife. Die Variable D wird dekrementiert. Ist der Zähler abgelaufen und die Variable D den Wert 0 erreicht
                #hat, wird der nächste Befehl ausgeführt. Sonst springt das Programm zu der angegebenen Adresse. Hier muss
                #ggf. mit dem Befehl „8“ der Sprungbereich angegeben werden.
                #Parameter 0-15
                cpuDef.regD = cpuDef.regD - 1
                if ( 0 == cpuDef.regD ) :
                    cpuDef.PC = cpuDef.page * 16 + cpuDef.param
                else:
                    cpuDef.PC = cpuDef.PC + 1
            case 12:
                #Bedingter Sprung. Der folgende Befehl wird, wenn die Bedingung erfüllt ist, übersprungen.
                #Parameter 1-15
                #1: if A > B / 2: if A < B / 3: if A = B / 4: if Din.0 = 1 / 5: if Din.1 = 1 / 6: if Din.2 = 1 / 7: if Din.3 = 1
                #8: if Din.0 = 0 / 9: if Din.1 = 0 / 10: if Din.2 = 0 / 11: if Din.3 = 0 / 12: if S1 = 0 / 13: if S2 = 0 / 14: if S1 = 1 / 15: if
                #S2 = 1
                match cpuDef.param:
                    case 1:
                        if cpuDef.regA > cpuDef.regB:
                            cpuDef.PC = cpuDef.PC + 1
                    case 2:
                        if cpuDef.regA < cpuDef.regB:
                            cpuDef.PC = cpuDef.PC + 1
                    case 3:
                        if cpuDef.regA == cpuDef.regB:
                            cpuDef.PC = cpuDef.PC + 1
                    case 4:
                        if True == cpuDef.cpuDef.Pin18_Dout1_PA4:
                            cpuDef.PC = cpuDef.PC + 1
                    case 5:
                        if True == cpuDef.cpuDef.Pin17_Dout2_PA5:
                            cpuDef.PC = cpuDef.PC + 1
                    case 6:
                        if True == cpuDef.cpuDef.Pin16_Dout3_PA6:
                            cpuDef.PC = cpuDef.PC + 1
                    case 7:
                        if True == cpuDef.cpuDef.Pin15_Dout4_PA7:
                            cpuDef.PC = cpuDef.PC + 1
                    case 8:
                        if False == cpuDef.cpuDef.Pin18_Dout1_PA4:
                            cpuDef.PC = cpuDef.PC + 1
                    case 9:
                        if False == cpuDef.cpuDef.Pin17_Dout2_PA5:
                            cpuDef.PC = cpuDef.PC + 1
                    case 10:
                        if False == cpuDef.cpuDef.Pin16_Dout3_PA6:
                            cpuDef.PC = cpuDef.PC + 1
                    case 11:
                        if False == cpuDef.cpuDef.Pin15_Dout4_PA7:
                            cpuDef.PC = cpuDef.PC + 1
                    case 12:
                        if False == cpuDef.Pin5_SW1_PB3:
                            cpuDef.PC = cpuDef.PC + 1
                    case 13:
                        if False == cpuDef.Pin6_SW2_PB2:
                            cpuDef.PC = cpuDef.PC + 1
                    case 14:
                        if True == cpuDef.Pin5_SW1_PB3:
                            cpuDef.PC = cpuDef.PC + 1
                    case 15:
                        if True == cpuDef.Pin6_SW2_PB2:
                            cpuDef.PC = cpuDef.PC + 1
                cpuDef.PC = cpuDef.PC + 1
            case 13:
                #Aufruf eines Unterprogramms. Ggf. ist mit dem Befehl "8" der Sprungbereich anzugeben. - Parameter 0-15
                cpuDef.ret = cpuDef.PC
                cpuDef.PC  = cpuDef.page * 16 + cpuDef.param
            case 14:
                #Return = Rücksprung vom Unterprogramm - Parameter 0-15
                cpuDef.PC = cpuDef.ret + 1

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
