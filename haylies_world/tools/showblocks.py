import sys; sys.path.insert(0, 'tools')
import smwplayer as P
HEX='.123456789ABCDEF'
rom=open('clean_smw.sfc','rb').read(); gfx=P.load_gfx32(rom)
ks=[int(x,16) for x in sys.argv[1:]]
for i in range(0,len(ks),6):
    grp=ks[i:i+6]; bl=[P.block_pixels(gfx,k) for k in grp]
    print('  '.join('%-16s'%('%02X'%k) for k in grp))
    for r in range(16):
        print('  '.join(''.join(HEX[v] for v in b[r]) for b in bl))
