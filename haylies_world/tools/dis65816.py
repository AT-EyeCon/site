"""Tiny 65816 disassembler (for inspecting SMW routines)."""
import sys
M = {}
modes = {'imp':0,'imm8':1,'immM':-1,'immX':-2,'dp':1,'dpx':1,'dpy':1,'abs':2,'absx':2,'absy':2,'long':3,'longx':3,
         'ind':1,'indx':1,'indy':1,'indl':1,'indly':1,'sr':1,'sry':1,'rel':1,'rell':2,'absind':2,'absindx':2,'absindl':2,'bm':2}
fmt = {'imp':'','imm8':'#$%02X','immM':'#$%s','immX':'#$%s','dp':'$%02X','dpx':'$%02X,x','dpy':'$%02X,y','abs':'$%04X','absx':'$%04X,x',
       'absy':'$%04X,y','long':'$%06X','longx':'$%06X,x','ind':'($%02X)','indx':'($%02X,x)','indy':'($%02X),y','indl':'[$%02X]','indly':'[$%02X],y',
       'sr':'$%02X,s','sry':'($%02X,s),y','rel':'%s','rell':'%s','absind':'($%04X)','absindx':'($%04X,x)','absindl':'[$%04X]','bm':'$%04X'}
T = """00 brk imm8;01 ora indx;02 cop imm8;03 ora sr;04 tsb dp;05 ora dp;06 asl dp;07 ora indl;08 php imp;09 ora immM;0A asl imp;0B phd imp;0C tsb abs;0D ora abs;0E asl abs;0F ora long
10 bpl rel;11 ora indy;12 ora ind;13 ora sry;14 trb dp;15 ora dpx;16 asl dpx;17 ora indly;18 clc imp;19 ora absy;1A inc imp;1B tcs imp;1C trb abs;1D ora absx;1E asl absx;1F ora longx
20 jsr abs;21 and indx;22 jsl long;23 and sr;24 bit dp;25 and dp;26 rol dp;27 and indl;28 plp imp;29 and immM;2A rol imp;2B pld imp;2C bit abs;2D and abs;2E rol abs;2F and long
30 bmi rel;31 and indy;32 and ind;33 and sry;34 bit dpx;35 and dpx;36 rol dpx;37 and indly;38 sec imp;39 and absy;3A dec imp;3B tsc imp;3C bit absx;3D and absx;3E rol absx;3F and longx
40 rti imp;41 eor indx;42 wdm imm8;43 eor sr;44 mvp bm;45 eor dp;46 lsr dp;47 eor indl;48 pha imp;49 eor immM;4A lsr imp;4B phk imp;4C jmp abs;4D eor abs;4E lsr abs;4F eor long
50 bvc rel;51 eor indy;52 eor ind;53 eor sry;54 mvn bm;55 eor dpx;56 lsr dpx;57 eor indly;58 cli imp;59 eor absy;5A phy imp;5B tcd imp;5C jml long;5D eor absx;5E lsr absx;5F eor longx
60 rts imp;61 adc indx;62 per rell;63 adc sr;64 stz dp;65 adc dp;66 ror dp;67 adc indl;68 pla imp;69 adc immM;6A ror imp;6B rtl imp;6C jmp absind;6D adc abs;6E ror abs;6F adc long
70 bvs rel;71 adc indy;72 adc ind;73 adc sry;74 stz dpx;75 adc dpx;76 ror dpx;77 adc indly;78 sei imp;79 adc absy;7A ply imp;7B tdc imp;7C jmp absindx;7D adc absx;7E ror absx;7F adc longx
80 bra rel;81 sta indx;82 brl rell;83 sta sr;84 sty dp;85 sta dp;86 stx dp;87 sta indl;88 dey imp;89 bit immM;8A txa imp;8B phb imp;8C sty abs;8D sta abs;8E stx abs;8F sta long
90 bcc rel;91 sta indy;92 sta ind;93 sta sry;94 sty dpx;95 sta dpx;96 stx dpy;97 sta indly;98 tya imp;99 sta absy;9A txs imp;9B txy imp;9C stz abs;9D sta absx;9E stz absx;9F sta longx
A0 ldy immX;A1 lda indx;A2 ldx immX;A3 lda sr;A4 ldy dp;A5 lda dp;A6 ldx dp;A7 lda indl;A8 tay imp;A9 lda immM;AA tax imp;AB plb imp;AC ldy abs;AD lda abs;AE ldx abs;AF lda long
B0 bcs rel;B1 lda indy;B2 lda ind;B3 lda sry;B4 ldy dpx;B5 lda dpx;B6 ldx dpy;B7 lda indly;B8 clv imp;B9 lda absy;BA tsx imp;BB tyx imp;BC ldy absx;BD lda absx;BE ldx absy;BF lda longx
C0 cpy immX;C1 cmp indx;C2 rep imm8;C3 cmp sr;C4 cpy dp;C5 cmp dp;C6 dec dp;C7 cmp indl;C8 iny imp;C9 cmp immM;CA dex imp;CB wai imp;CC cpy abs;CD cmp abs;CE dec abs;CF cmp long
D0 bne rel;D1 cmp indy;D2 cmp ind;D3 cmp sry;D4 pei dp;D5 cmp dpx;D6 dec dpx;D7 cmp indly;D8 cld imp;D9 cmp absy;DA phx imp;DB stp imp;DC jml absindl;DD cmp absx;DE dec absx;DF cmp longx
E0 cpx immX;E1 sbc indx;E2 sep imm8;E3 sbc sr;E4 cpx dp;E5 sbc dp;E6 inc dp;E7 sbc indl;E8 inx imp;E9 sbc immM;EA nop imp;EB xba imp;EC cpx abs;ED sbc abs;EE inc abs;EF sbc long
F0 beq rel;F1 sbc indy;F2 pea abs;F3 sbc sry;F4 pea abs;F5 sbc dpx;F6 inc dpx;F7 sbc indly;F8 sed imp;F9 sbc absy;FA plx imp;FB xce imp;FC jsr absindx;FD sbc absx;FE inc absx;FF sbc longx"""
for e in T.replace('\n', ';').split(';'):
    o, n, m = e.split(); M[int(o, 16)] = (n, m)

def dis(rom, snes, count, m8=True, x8=True):
    pc = snes; out = []
    for _ in range(count):
        off = ((pc >> 16) & 0x7F) * 0x8000 + (pc & 0x7FFF)
        op = rom[off]; n, md = M[op]
        ln = modes[md]
        if md == 'immM': ln = 1 if m8 else 2
        if md == 'immX': ln = 1 if x8 else 2
        arg = int.from_bytes(rom[off + 1:off + 1 + ln], 'little')
        if md in ('immM', 'immX'): s = '#$%0*X' % (ln * 2, arg)
        elif md == 'rel': s = '$%04X' % ((pc + 2 + (arg - 256 if arg > 127 else arg)) & 0xFFFF)
        elif md == 'rell': s = '$%04X' % ((pc + 3 + (arg - 65536 if arg > 32767 else arg)) & 0xFFFF)
        else: s = fmt[md] % arg if fmt[md] else ''
        if n == 'rep':
            if arg & 0x20: m8 = False
            if arg & 0x10: x8 = False
        if n == 'sep':
            if arg & 0x20: m8 = True
            if arg & 0x10: x8 = True
        out.append('%02X:%04X  %-12s %s %s' % (pc >> 16, pc & 0xFFFF, rom[off:off + 1 + ln].hex(' '), n.upper(), s))
        pc += 1 + ln
    return '\n'.join(out)

if __name__ == '__main__':
    rom = open(sys.argv[1], 'rb').read()
    print(dis(rom, int(sys.argv[2], 16), int(sys.argv[3]), sys.argv[4:5] != ['m16'], sys.argv[5:6] != ['x16']))
