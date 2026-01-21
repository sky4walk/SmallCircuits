# https://pythononline.net/
# https://esolangs.org/wiki/FlipJump
BAD_ALIGNMENT  = 1
SELF_FLIP      = 2
SUCCESS_FINISH = 0

def flipJump8(mem):
    ip = 0
    
    while True:
        f = mem[ip // 8]
        j = mem[ip // 8 + 1]

        print(ip,": f:",f," j:",j)
        
        if ip % 8:
            print("bad alignment")
            return BAD_ALIGNMENT
        
        if f >= ip and f < ip + 16: 
            print("self flip")
            return SELF_FLIP
        
        if ip == j: 
            print("success finish")
            return SUCCESS_FINISH

        
        # Flip bit
        mem[f // 8] ^= 1 << (f % 8)
        
        # Jump to new ip
        ip = j

mem = [3,3,3,3,3,3,3]
flipJump8(mem)