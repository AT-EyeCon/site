#!/bin/sh
# Builds the instrumented snes9x libretro core used by tools/snes_emu.py.
# Adds: MK_DMALOG=<file> DMA logging, and retro_mk_trace() memory/exec tracing.
set -e
DEST=${1:-build/emu}
mkdir -p "$DEST"; cd "$DEST"
[ -d snes9x ] || git clone -q --depth 1 https://github.com/libretro/snes9x
cd snes9x
python3 - <<'PY'
s=open('dma.cpp').read()
if 'MK_DMALOG' not in s:
    s=s.replace("    SDMA	*d = &DMA[Channel];\n","    SDMA	*d = &DMA[Channel];\n\t{ static FILE *mklog=(FILE*)-1; if(mklog==(FILE*)-1){const char*e=getenv(\"MK_DMALOG\"); mklog=e?fopen(e,\"w\"):NULL;} if(mklog) fprintf(mklog,\"F%u ch%d B%02X src%02X:%04X n%04X vma%04X cg%02X rev%d\\n\",IPPU.TotalEmulatedFrames,Channel,d->BAddress,d->ABank,d->AAddress,d->TransferBytes,PPU.VMA.Address,PPU.CGADD,d->ReverseTransfer); }\n",1)
    s='#include <stdlib.h>\n#include <stdio.h>\n'+s; open('dma.cpp','w').write(s)
c=open('cpuexec.cpp').read()
if 'mk_trace' not in c:
    c=c.replace('#include "snes9x.h"','#include "snes9x.h"\n#include <stdio.h>\nuint32 mk_pc; FILE *mk_trace=NULL; int mk_exec=0;\nextern "C" void retro_mk_trace(const char *path, int exec){ if(mk_trace){fclose(mk_trace);mk_trace=NULL;} if(path) mk_trace=fopen(path,"w"); mk_exec=exec; }',1)
    c=c.replace("		Registers.PCw++;\n		(*Opcodes[Op].S9xOpcode)();","		mk_pc = Registers.PBPC; if(mk_trace&&mk_exec) fprintf(mk_trace,\"X %06X\\n\",mk_pc);\n		Registers.PCw++;\n		(*Opcodes[Op].S9xOpcode)();",1)
    open('cpuexec.cpp','w').write(c)
g=open('getset.h').read()
if 'mk_trace' not in g:
    g=g.replace('#include "cpuexec.h"','#include <stdio.h>\n#include "cpuexec.h"',1)
    g=g.replace('inline uint8 S9xGetByte (uint32 Address)\n{','extern uint32 mk_pc; extern FILE *mk_trace;\ninline uint8 S9xGetByteX (uint32 Address);\ninline uint8 S9xGetByte (uint32 Address)\n{\n\tuint8 v=S9xGetByteX(Address); if(mk_trace){uint32 a=Address&0xffffff; fprintf(mk_trace,"R %06X %06X %02X\\n",mk_pc,a,v);} return v;\n}\ninline uint8 S9xGetByteX (uint32 Address)\n{',1)
    g=g.replace('inline void S9xSetByte (uint8 Byte, uint32 Address)\n{','inline void S9xSetByte (uint8 Byte, uint32 Address)\n{\n\tif(mk_trace) fprintf(mk_trace,"W %06X %06X %02X\\n",mk_pc,Address&0xffffff,Byte);',1)
    g=g.replace('inline uint16 S9xGetWord (uint32 Address, enum s9xwrap_t w = WRAP_NONE)\n{\n\tuint16	word;\n','inline uint16 S9xGetWord (uint32 Address, enum s9xwrap_t w = WRAP_NONE)\n{\n\tuint16	word;\n\tif(mk_trace){ word=S9xGetByte(Address); return word|(S9xGetByte(Address+1)<<8);} \n',1)
    g=g.replace('inline void S9xSetWord (uint16 Word, uint32 Address, enum s9xwrap_t w = WRAP_NONE, enum s9xwriteorder_t o = WRITE_01)\n{\n','inline void S9xSetWord (uint16 Word, uint32 Address, enum s9xwrap_t w = WRAP_NONE, enum s9xwriteorder_t o = WRITE_01)\n{\n\tif(mk_trace){ S9xSetByte(Word&0xff,Address); S9xSetByte(Word>>8,Address+1); return; }\n',1)
    open('getset.h','w').write(g)
PY
cd libretro && make -j"$(nproc)" >/dev/null && echo "built $(pwd)/snes9x_libretro.so"
