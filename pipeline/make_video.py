"""Pipeline de reels: spec JSON -> voz edge-tts + subtítulos palabra a palabra + fondos + piano propio.
Uso: python3 make_video.py spec.json salida_dir
spec = {"voice":"es-ES-AlvaroNeural","rate":"-5%","gap":0.45,"lead":0.25,"tail":1.6,
        "music_seed":1,"cards":[{"say":"texto hablado","show":"texto en pantalla","key":["palabra"],"bg":"ruta.png"}]}
'show' debe tener las mismas palabras que 'say' o se mapean proporcionalmente. 'key' = palabras de 'show' en caja blanca."""
import asyncio, json, math, os, subprocess, sys, wave
import numpy as np, edge_tts
from PIL import Image, ImageDraw, ImageFilter, ImageFont
HERE=os.path.dirname(os.path.abspath(__file__))
W,H,FPS=1080,1920,30
PROXY=os.environ.get("TTS_PROXY") or os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
spec=json.load(open(sys.argv[1])); OUT=sys.argv[2]; os.makedirs(OUT,exist_ok=True)
def sh(*a): subprocess.run(a,check=True)
def dur(f): return float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",f]))
# ---------- voz ----------
async def tts(i,text):
    for attempt in range(3):
        try:
            c=edge_tts.Communicate(text,spec.get("voice","es-ES-AlvaroNeural"),rate=spec.get("rate","-5%"),
                                   boundary="WordBoundary",proxy=PROXY)
            words=[]; p=f"{OUT}/s{i}.mp3"
            with open(p,"wb") as f:
                async for ch in c.stream():
                    if ch["type"]=="audio": f.write(ch["data"])
                    elif ch["type"]=="WordBoundary": words.append(((ch["offset"])/1e7,(ch["offset"]+ch["duration"])/1e7))
            if words: return words
        except Exception as e: print("tts retry",e)
    raise SystemExit("edge-tts falló: no se usa voz alternativa")
cards=spec["cards"]
async def all_tts(): return [await tts(i,c["say"]) for i,c in enumerate(cards)]
WB=asyncio.run(all_tts())
t=spec.get("lead",0.25); starts=[]
for i,c in enumerate(cards):
    starts.append(t- WB[i][0][0]+0.0)
    t=starts[-1]+WB[i][-1][1]+spec.get("gap",0.45)
DUR=round(t-spec.get("gap",0.45)+spec.get("tail",1.6),2)
print("duración",DUR)
# tokens visibles con su instante
def strip(w): return w.strip(".,¿?¡!:;…\"'").lower()
CARD=[]
for i,c in enumerate(cards):
    show=c.get("show",c["say"]).split(); n=len(WB[i]); keys=[k.lower() for k in c.get("key",[])]
    toks=[]
    for j,w in enumerate(show):
        k=min(n-1,round(j*n/len(show))) if len(show)!=n else j
        toks.append([w,starts[i]+WB[i][k][0]-0.04,strip(w) in keys or w.lower() in keys])
    # agrupar palabras clave consecutivas en una sola caja
    merged=[]
    for tk in toks:
        if merged and tk[2] and merged[-1][2]: merged[-1][0]+=" "+tk[0]
        else: merged.append(tk)
    end=(starts[i+1]+WB[i+1][0][0]-0.12) if i+1<len(cards) else DUR
    CARD.append((starts[i]+WB[i][0][0]-0.05,end,merged,c["bg"]))
# ---------- audio ----------
inp=[];flt=[]
for i,s in enumerate(starts):
    ms=max(0,int(s*1000)); inp+=["-i",f"{OUT}/s{i}.mp3"]; flt.append(f"[{i}:a]aresample=44100,adelay={ms}|{ms}[v{i}]")
flt.append("".join(f"[v{i}]" for i in range(len(starts)))+f"amix=inputs={len(starts)}:normalize=0,apad,atrim=0:{DUR},loudnorm=I=-15:TP=-1.5:LRA=11[o]")
sh("ffmpeg","-y","-loglevel","error",*inp,"-filter_complex",";".join(flt),"-map","[o]","-ac","2","-ar","44100",f"{OUT}/voice.wav")
def piano(path,seconds,seed):
    SR=44100; rng=np.random.default_rng(seed); bpm=[66,70,74,62][seed%4]; beat=60/bpm
    out=np.zeros(int(SR*(seconds+8)))
    def note(t0,n,vel,length):
        f=440*2**((n-69)/12); N=int(SR*length); tt=np.arange(N)/SR; s=np.zeros(N)
        for k in range(1,9):
            fk=f*k*math.sqrt(1+0.0004*k*k)
            if fk>SR/2.2: break
            s+=(1/k**1.6)*np.exp(-tt*(0.9+0.55*k)*(f/260)**0.35)*np.sin(2*np.pi*fk*tt+rng.uniform(0,6.28))
        s*=np.minimum(1,tt/0.004); i=int(t0*SR); out[i:i+N]+=vel*s
    progs=[[(41,[60,64,65,69]),(40,[60,64,67,72]),(45,[60,64,67,69]),(43,[59,62,67,71])],
           [(45,[57,60,64,67]),(41,[57,60,65,69]),(48,[55,60,64,67]),(43,[55,59,62,67])],
           [(38,[57,62,65,69]),(43,[59,62,65,67]),(36,[55,60,64,67]),(45,[57,60,64,69])],
           [(40,[59,64,67,71]),(36,[60,64,67,71]),(43,[59,62,67,71]),(38,[57,62,66,69])]]
    prog=progs[seed%4]; pat=[0,2,1,3,2,1,3,2]; t=0.0; ci=0
    while t<seconds:
        bass,ch=prog[ci%4]; note(t,bass,0.55,5); note(t,bass+12,0.22,5)
        for j,p in enumerate(pat): note(t+j*beat/2+rng.uniform(0,0.012),ch[p],0.2+0.06*(j==0)+rng.uniform(-.03,.03),3)
        if ci%2: note(t+2*beat,ch[-1]+12,0.15,4)
        t+=4*beat; ci+=1
    out=np.convolve(out[:int(SR*seconds)],np.ones(5)/5,'same')
    L=int(SR*2.8); ir=rng.normal(0,1,L)*np.exp(-np.arange(L)/SR*2.6); ir[0]=0
    nf=1<<(len(out)+L-1).bit_length(); wet=np.fft.irfft(np.fft.rfft(out,nf)*np.fft.rfft(ir,nf),nf)[:len(out)]
    mix=0.65*out/np.max(np.abs(out))+0.45*wet/np.max(np.abs(wet))
    fi,fo=int(SR*1.2),int(SR*2.5); mix[:fi]*=np.linspace(0,1,fi); mix[-fo:]*=np.linspace(1,0,fo)
    mix=mix/np.max(np.abs(mix))*0.8; st=np.stack([mix,np.roll(mix,int(SR*0.012))],1)
    with wave.open(path,"wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st*32767).astype(np.int16).tobytes())
piano(f"{OUT}/music.wav",DUR,spec.get("music_seed",1))
def lufs(f):
    o=subprocess.run(["ffmpeg","-hide_banner","-i",f,"-af","ebur128","-f","null","-"],capture_output=True,text=True).stderr
    return float([l for l in o.splitlines() if l.strip().startswith("I:")][-1].split()[1])
g=lufs(f"{OUT}/voice.wav")-18-lufs(f"{OUT}/music.wav")
sh("ffmpeg","-y","-loglevel","error","-i",f"{OUT}/music.wav","-af",f"volume={g}dB",f"{OUT}/music_n.wav")
# ---------- vídeo ----------
def ease(x): x=min(max(x,0),1); return 1-(1-x)**3
FONT=os.path.join(HERE,"Montserrat-900.ttf"); SP=8
def layout(toks,f):
    sp=f.getlength(" ")+SP; lines=[[]]; w=0
    for tok in toks:
        tw=f.getlength(tok[0])+(64 if tok[2] else 0)
        if lines[-1] and w+sp+tw>920: lines.append([]); w=0
        w+=(sp if lines[-1] else 0)+tw; lines[-1].append((tok,tw))
    return lines
LAY=[]
for st,en,toks,bg in CARD:
    for size in (124,112,100,90,80):
        f=ImageFont.truetype(FONT,size); L=layout(toks,f)
        if len(L)<=4 and all(sum(tw for _,tw in l)<=980 for l in L): break
    LAY.append((f,L))
def text_layer(ci,t):
    st,end,toks,_=CARD[ci]; f,lines=LAY[ci]
    lay=Image.new("RGBA",(W,H),(0,0,0,0)); shl=Image.new("RGBA",(W,H),(0,0,0,0))
    d=ImageDraw.Draw(lay); ds=ImageDraw.Draw(shl); lh=f.size*1.3; y=H*0.42-lh*len(lines)/2
    fade=1-ease((t-(end-0.2))/0.2) if ci+1<len(CARD) else 1; sp=f.getlength(" ")+SP
    for line in lines:
        x=(W-(sum(tw for _,tw in line)+sp*(len(line)-1)))/2
        for (txt,t0,kw),tw in line:
            p=ease((t-t0)/0.2)
            if p>0:
                a=int(255*p*fade); dy=(1-p)*28
                if kw:
                    bx=[x,y+dy+f.size*0.04,x+tw,y+dy+f.size*1.2]; s=0.85+0.15*p
                    cx,cy=(bx[0]+bx[2])/2,(bx[1]+bx[3])/2
                    bb=[cx-(cx-bx[0])*s,cy-(cy-bx[1])*s,cx+(bx[2]-cx)*s,cy+(bx[3]-cy)*s]
                    ds.rounded_rectangle([bb[0]+6,bb[1]+10,bb[2]+6,bb[3]+10],radius=18,fill=(0,0,0,int(a*.35)))
                    d.rounded_rectangle(bb,radius=18,fill=(255,255,255,a)); d.text((x+32,y+dy),txt,font=f,fill=(40,24,14,a))
                else:
                    ds.text((x+3,y+dy+5),txt,font=f,fill=(0,0,0,int(a*.8))); d.text((x,y+dy),txt,font=f,fill=(255,255,255,a))
            x+=tw+sp
        y+=lh
    return Image.alpha_composite(shl.filter(ImageFilter.GaussianBlur(9)),lay)
srcs={}
def bgimg(p):
    if p not in srcs: srcs[p]=Image.open(p).convert("RGB")
    return srcs[p]
def bg_frame(p,t,t0):
    im=bgimg(p); iw,ih=im.size; z=1.0+0.04*(t-t0)/8; sc=min(iw/W,ih/H)/z; bw,bh=W*sc,H*sc
    cx,cy=iw/2,ih/2-(t-t0)*3
    return im.crop((int(cx-bw/2),int(cy-bh/2),int(cx+bw/2),int(cy+bh/2))).resize((W,H),Image.BILINEAR)
segs=[]
for i,(st,en,_,bg) in enumerate(CARD):
    if not segs or segs[-1][0]!=bg: segs.append([bg,0.0 if i==0 else st-0.3])
rng=np.random.default_rng(5); P=np.column_stack([rng.uniform(0,W,60),rng.uniform(0,H,60),rng.uniform(2,6,60),rng.uniform(20,60,60),rng.uniform(0,6.28,60)])
pc=tuple(spec.get("particle_rgb",[255,220,150]))
def particles(t):
    lay=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(lay)
    for x,y,r,v,ph in P:
        yy=(y-v*t)%H; xx=x+25*math.sin(t*.6+ph); a=int(130+90*math.sin(t*2+ph))
        d.ellipse([xx-r*2.2,yy-r*2.2,xx+r*2.2,yy+r*2.2],fill=pc+(a//4,)); d.ellipse([xx-r,yy-r,xx+r,yy+r],fill=pc+(a,))
    return lay.filter(ImageFilter.GaussianBlur(1.5))
band=np.zeros((H,W,4),np.uint8); yy=np.arange(H); band[:,:,3]=(np.exp(-((yy-H*.42)/450)**2)*spec.get("band",100)).astype(np.uint8)[:,None]
BAND=Image.fromarray(band,"RGBA")
ff=subprocess.Popen(["ffmpeg","-y","-loglevel","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-",
    "-c:v","libx264","-preset","medium","-crf","19","-pix_fmt","yuv420p",f"{OUT}/video_noaudio.mp4"],stdin=subprocess.PIPE)
for fi in range(int(DUR*FPS)):
    t=fi/FPS; si=max(i for i,s in enumerate(segs) if s[1]<=t)
    fr=bg_frame(segs[si][0],t,segs[si][1])
    if si>0 and t-segs[si][1]<0.5: fr=Image.blend(bg_frame(segs[si-1][0],t,segs[si-1][1]),fr,ease((t-segs[si][1])/0.5))
    fr=Image.alpha_composite(Image.alpha_composite(fr.convert("RGBA"),BAND),particles(t))
    for ci,(st,en,_,_) in enumerate(CARD):
        if st<=t<en: fr=Image.alpha_composite(fr,text_layer(ci,t))
    g2=min(1,(DUR-t)/0.5)
    if g2<1: fr=Image.blend(Image.new("RGBA",(W,H),(0,0,0,255)),fr,max(g2,0))
    ff.stdin.write(fr.convert("RGB").tobytes())
ff.stdin.close(); ff.wait()
sh("ffmpeg","-y","-loglevel","error","-i",f"{OUT}/video_noaudio.mp4","-i",f"{OUT}/voice.wav","-i",f"{OUT}/music_n.wav","-filter_complex",
   "[1:a][2:a]amix=inputs=2:normalize=0,alimiter=limit=0.89[a]","-map","0:v","-map","[a]","-c:v","copy","-c:a","aac","-b:a","192k",
   "-shortest","-movflags","+faststart",f"{OUT}/final.mp4")
# hoja de control
times=[c[1]-0.3 for c in CARD]
ims=[]
for tt in times:
    sh("ffmpeg","-y","-loglevel","error","-ss",f"{tt:.2f}","-i",f"{OUT}/final.mp4","-frames:v","1","-vf","scale=270:480",f"{OUT}/_f.png")
    ims.append(Image.open(f"{OUT}/_f.png").copy())
cols=5; sheet=Image.new("RGB",(270*cols,480*math.ceil(len(ims)/cols)))
for i,im in enumerate(ims): sheet.paste(im,((i%cols)*270,(i//cols)*480))
sheet.save(f"{OUT}/check_sheet.png"); json.dump({"duration":DUR,"cards":[[c[0],c[1]] for c in CARD]},open(f"{OUT}/meta.json","w"))
print("OK",f"{OUT}/final.mp4",DUR,"voz",lufs(f"{OUT}/voice.wav"),"música",lufs(f"{OUT}/music_n.wav"))
