"""Tiny 65816 disassembler (HiROM mapping helper included). Dev tool only."""
import sys

OPS = {}
def _t(s):
    for item in s.split(','):
        op, m, mode = item.split()
        OPS[int(op, 16)] = (m, mode)
_t("00 BRK imm8,01 ORA dpxi,02 COP imm8,03 ORA sr,04 TSB dp,05 ORA dp,06 ASL dp,07 ORA dpil,08 PHP imp,09 ORA immm,0A ASL imp,0B PHD imp,0C TSB abs,0D ORA abs,0E ASL abs,0F ORA long,"
   "10 BPL rel,11 ORA dpiy,12 ORA dpi,13 ORA sriy,14 TRB dp,15 ORA dpx,16 ASL dpx,17 ORA dpily,18 CLC imp,19 ORA absy,1A INC imp,1B TCS imp,1C TRB abs,1D ORA absx,1E ASL absx,1F ORA longx,"
   "20 JSR abs,21 AND dpxi,22 JSL long,23 AND sr,24 BIT dp,25 AND dp,26 ROL dp,27 AND dpil,28 PLP imp,29 AND immm,2A ROL imp,2B PLD imp,2C BIT abs,2D AND abs,2E ROL abs,2F AND long,"
   "30 BMI rel,31 AND dpiy,32 AND dpi,33 AND sriy,34 BIT dpx,35 AND dpx,36 ROL dpx,37 AND dpily,38 SEC imp,39 AND absy,3A DEC imp,3B TSC imp,3C BIT absx,3D AND absx,3E ROL absx,3F AND longx,"
   "40 RTI imp,41 EOR dpxi,42 WDM imm8,43 EOR sr,44 MVP mv,45 EOR dp,46 LSR dp,47 EOR dpil,48 PHA imp,49 EOR immm,4A LSR imp,4B PHK imp,4C JMP abs,4D EOR abs,4E LSR abs,4F EOR long,"
   "50 BVC rel,51 EOR dpiy,52 EOR dpi,53 EOR sriy,54 MVN mv,55 EOR dpx,56 LSR dpx,57 EOR dpily,58 CLI imp,59 EOR absy,5A PHY imp,5B TCD imp,5C JML long,5D EOR absx,5E LSR absx,5F EOR longx,"
   "60 RTS imp,61 ADC dpxi,62 PER rell,63 ADC sr,64 STZ dp,65 ADC dp,66 ROR dp,67 ADC dpil,68 PLA imp,69 ADC immm,6A ROR imp,6B RTL imp,6C JMP absi,6D ADC abs,6E ROR abs,6F ADC long,"
   "70 BVS rel,71 ADC dpiy,72 ADC dpi,73 ADC sriy,74 STZ dpx,75 ADC dpx,76 ROR dpx,77 ADC dpily,78 SEI imp,79 ADC absy,7A PLY imp,7B TDC imp,7C JMP absxi,7D ADC absx,7E ROR absx,7F ADC longx,"
   "80 BRA rel,81 STA dpxi,82 BRL rell,83 STA sr,84 STY dp,85 STA dp,86 STX dp,87 STA dpil,88 DEY imp,89 BIT immm,8A TXA imp,8B PHB imp,8C STY abs,8D STA abs,8E STX abs,8F STA long,"
   "90 BCC rel,91 STA dpiy,92 STA dpi,93 STA sriy,94 STY dpx,95 STA dpx,96 STX dpy,97 STA dpily,98 TYA imp,99 STA absy,9A TXS imp,9B TXY imp,9C STZ abs,9D STA absx,9E STZ absx,9F STA longx,"
   "A0 LDY immx,A1 LDA dpxi,A2 LDX immx,A3 LDA sr,A4 LDY dp,A5 LDA dp,A6 LDX dp,A7 LDA dpil,A8 TAY imp,A9 LDA immm,AA TAX imp,AB PLB imp,AC LDY abs,AD LDA abs,AE LDX abs,AF LDA long,"
   "B0 BCS rel,B1 LDA dpiy,B2 LDA dpi,B3 LDA sriy,B4 LDY dpx,B5 LDA dpx,B6 LDX dpy,B7 LDA dpily,B8 CLV imp,B9 LDA absy,BA TSX imp,BB TYX imp,BC LDY absx,BD LDA absx,BE LDX absy,BF LDA longx,"
   "C0 CPY immx,C1 CMP dpxi,C2 REP imm8,C3 CMP sr,C4 CPY dp,C5 CMP dp,C6 DEC dp,C7 CMP dpil,C8 INY imp,C9 CMP immm,CA DEX imp,CB WAI imp,CC CPY abs,CD CMP abs,CE DEC abs,CF CMP long,"
   "D0 BNE rel,D1 CMP dpiy,D2 CMP dpi,D3 CMP sriy,D4 PEI dp,D5 CMP dpx,D6 DEC dpx,D7 CMP dpily,D8 CLD imp,D9 CMP absy,DA PHX imp,DB STP imp,DC JML absil,DD CMP absx,DE DEC absx,DF CMP longx,"
   "E0 CPX immx,E1 SBC dpxi,E2 SEP imm8,E3 SBC sr,E4 CPX dp,E5 SBC dp,E6 INC dp,E7 SBC dpil,E8 INX imp,E9 SBC immm,EA NOP imp,EB XBA imp,EC CPX abs,ED SBC abs,EE INC abs,EF SBC long,"
   "F0 BEQ rel,F1 SBC dpiy,F2 SBC dpi,F3 SBC sriy,F4 PEA abs,F5 SBC dpx,F6 INC dpx,F7 SBC dpily,F8 SED imp,F9 SBC absy,FA PLX imp,FB XCE imp,FC JSR absxi,FD SBC absx,FE INC absx,FF SBC longx")
SZ = {'imp': 1, 'imm8': 2, 'dp': 2, 'dpx': 2, 'dpy': 2, 'dpi': 2, 'dpxi': 2, 'dpiy': 2, 'dpil': 2, 'dpily': 2,
      'sr': 2, 'sriy': 2, 'rel': 2, 'abs': 3, 'absx': 3, 'absy': 3, 'absi': 3, 'absxi': 3, 'absil': 3,
      'rell': 3, 'mv': 3, 'long': 4, 'longx': 4}
FMT = {'imp': '', 'imm8': '#${:02X}', 'dp': '${:02X}', 'dpx': '${:02X},x', 'dpy': '${:02X},y', 'dpi': '(${:02X})',
       'dpxi': '(${:02X},x)', 'dpiy': '(${:02X}),y', 'dpil': '[${:02X}]', 'dpily': '[${:02X}],y', 'sr': '${:02X},s',
       'sriy': '(${:02X},s),y', 'abs': '${:04X}', 'absx': '${:04X},x', 'absy': '${:04X},y', 'absi': '(${:04X})',
       'absxi': '(${:04X},x)', 'absil': '[${:04X}]', 'long': '${:06X}', 'longx': '${:06X},x'}


def hirom_off(addr):
    return addr & 0x3FFFFF


def dis(rom, addr, count=40, m=1, x=1):
    """m/x: 1 = 8-bit. Tracks REP/SEP."""
    out = []
    for _ in range(count):
        o = hirom_off(addr); op = rom[o]; mn, mode = OPS[op]
        if mode == 'immm': n = 3 if m == 0 else 2
        elif mode == 'immx': n = 3 if x == 0 else 2
        else: n = SZ[mode]
        b = rom[o:o + n]
        v = int.from_bytes(b[1:], 'little') if n > 1 else 0
        if mode in ('immm', 'immx'): arg = ('#${:04X}' if n == 3 else '#${:02X}').format(v)
        elif mode == 'rel': arg = '${:04X}'.format((addr + 2 + (v - 256 if v > 127 else v)) & 0xFFFF)
        elif mode == 'rell': arg = '${:04X}'.format((addr + 3 + (v - 65536 if v > 32767 else v)) & 0xFFFF)
        elif mode == 'mv': arg = '${:02X},${:02X}'.format(b[2], b[1])
        else: arg = FMT[mode].format(v) if FMT[mode] else ''
        if mn == 'REP': m = 0 if v & 0x20 else m; x = 0 if v & 0x10 else x
        if mn == 'SEP': m = 1 if v & 0x20 else m; x = 1 if v & 0x10 else x
        out.append('{:06X}  {:<12} {} {}'.format(addr, b.hex(' '), mn, arg))
        addr = (addr & 0xFF0000) | ((addr + n) & 0xFFFF)
    return '\n'.join(out)


if __name__ == '__main__':
    rom = open(sys.argv[1], 'rb').read()
    print(dis(rom, int(sys.argv[2], 16), int(sys.argv[3]) if len(sys.argv) > 3 else 40,
              int(sys.argv[4]) if len(sys.argv) > 4 else 1, int(sys.argv[5]) if len(sys.argv) > 5 else 1))
