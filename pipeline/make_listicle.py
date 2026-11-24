"""Formato TikTok 'listicle' con presentadora ilustrada (estilo referencia: fondo beige, // tags, titular Anton, tarjetas UI).
Uso: python3 make_listicle.py spec.json out_dir
Tipos de tarjeta: chips, compare, checklist, swatches, jacket, comments."""
import asyncio, json, math, os, subprocess, sys, wave
import numpy as np, edge_tts
from PIL import Image, ImageDraw, ImageFilter, ImageFont
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import musiclib
HERE=os.path.dirname(os.path.abspath(__file__)); F=lambda n,s: ImageFont.truetype(os.path.join(HERE,"fonts",n),s)
W,H,FPS=1080,1920,30
BG=(236,231,224); INK=(28,26,26); GRAY=(170,163,155); RED=(224,72,64); WHITE=(255,255,255)
PROXY=os.environ.get("TTS_PROXY") or os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
spec=json.load(open(sys.argv[1])); OUT=sys.argv[2]; os.makedirs(OUT,exist_ok=True)
SEC=spec["sections"]
def sh(*a): subprocess.run(a,check=True)
async def tts(i,text):
    for _ in range(3):
        try:
            c=edge_tts.Communicate(text,spec.get("voice","es-ES-ElviraNeural"),rate=spec.get("rate","+0%"),boundary="WordBoundary",proxy=PROXY)
            ws=[]
            with open(f"{OUT}/s{i}.mp3","wb") as f:
                async for ch in c.stream():
                    if ch["type"]=="audio": f.write(ch["data"])
                    elif ch["type"]=="WordBoundary": ws.append([ch["offset"]/1e7,(ch["offset"]+ch["duration"])/1e7,ch["text"]])
            if ws: return ws
        except Exception as e: print("retry",e)
    raise SystemExit("edge-tts falló: no se usa voz alternativa")
async def run(): return [await tts(i,s["say"]) for i,s in enumerate(SEC)]
WB=asyncio.run(run())
t=0.2; ST=[]
for i in range(len(SEC)):
    ST.append(t); t+=WB[i][-1][1]+spec.get("gap",0.3)
DUR=round(t+spec.get("tail",1.2),2); print("duración",DUR)
for i,s in enumerate(SEC):
    s["t0"]=ST[i]; s["t1"]=ST[i+1] if i+1<len(SEC) else DUR
    s["words"]=[(ST[i]+a,ST[i]+b,txt) for a,b,txt in WB[i]]
# ---- audio
inp=[];flt=[]
for i,s in enumerate(ST):
    ms=int(s*1000); inp+=["-i",f"{OUT}/s{i}.mp3"]; flt.append(f"[{i}:a]aresample=44100,adelay={ms}|{ms}[v{i}]")
flt.append("".join(f"[v{i}]" for i in range(len(ST)))+f"amix=inputs={len(ST)}:normalize=0,apad,atrim=0:{DUR},loudnorm=I=-15:TP=-1.5:LRA=11[o]")
sh("ffmpeg","-y","-loglevel","error",*inp,"-filter_complex",";".join(flt),"-map","[o]","-ac","2","-ar","44100",f"{OUT}/voice.wav")
musiclib.piano(f"{OUT}/music.wav",DUR,spec.get("music_seed",3))
def lufs(f):
    o=subprocess.run(["ffmpeg","-hide_banner","-i",f,"-af","ebur128","-f","null","-"],capture_output=True,text=True).stderr
    return float([l for l in o.splitlines() if l.strip().startswith("I:")][-1].split()[1])
g=lufs(f"{OUT}/voice.wav")-18-lufs(f"{OUT}/music.wav")
sh("ffmpeg","-y","-loglevel","error","-i",f"{OUT}/music.wav","-af",f"volume={g}dB",f"{OUT}/music_n.wav")
# envolvente para la boca
with wave.open(f"{OUT}/voice.wav") as w: a=np.frombuffer(w.readframes(w.getnframes()),np.int16).reshape(-1,2)[:,0].astype(float)/32768
spf=44100//FPS; RMS=np.array([np.sqrt(np.mean(a[i*spf:(i+1)*spf]**2)) if i*spf<len(a) else 0 for i in range(int(DUR*FPS)+2)])
RMS=RMS/ (np.percentile(RMS[RMS>0.01],90) if (RMS>0.01).any() else 1)
# ---- recursos
rng=np.random.default_rng(1)
bg=np.ones((H,W,3))*np.array(BG,float)
yy,xx=np.mgrid[0:H,0:W]; bg+=(np.exp(-(((xx-W/2)/700)**2+((yy-H*0.4)/900)**2))*10)[:,:,None]
bg+=rng.normal(0,2.2,(H,W,1)); dots=(xx%14==0)&(yy%14==0); bg[dots]-=10
BGIM=Image.fromarray(np.clip(bg,0,255).astype(np.uint8)).convert("RGBA")
CH=os.path.join(HERE,"chars"); SC=0.95
def ld(n): im=Image.open(os.path.join(CH,n)).convert("RGBA"); return im.resize((int(im.width*SC),int(im.height*SC)),Image.LANCZOS)
BODY=ld("body.png"); ARM=ld("arm.png"); HEADS={(m,e):ld(f"head_m{m}_e{e}.png") for m in range(3) for e in range(2)}
CX,CY=W-BODY.width+70,H-BODY.height+90
fMono=F("JetBrainsMono.ttf",30); fCap=F("Inter-ExtraBold.ttf",62); fCapI=F("Playfair-BoldItalic.ttf",66)
fBig=F("Anton.ttf",150); fNum=F("Anton.ttf",78); fCard=F("Inter-Bold.ttf",40); fCardS=F("Inter-Bold.ttf",32); fStamp=F("Anton.ttf",64)
def ease(x): x=min(max(x,0),1); return 1-(1-x)**3
def strip(w): return w.strip(".,¿?¡!:;…").lower()
# ---- piezas
def draw_caption(im,s,t):
    d=ImageDraw.Draw(im); words=s["words"]; keys=[k.lower() for k in s.get("key",[])]
    chunks=[]; cur=[]
    for w in words:
        cur.append(w)
        if len(cur)>=3 or w[2][-1] in ".,?:!": chunks.append(cur); cur=[]
    if cur: chunks.append(cur)
    ci=0
    for k,c in enumerate(chunks):
        if t>=c[0][0]-0.05: ci=k
    x=60; y=118
    for w0,w1,txt in chunks[ci]:
        base=strip(txt); kw=base in keys; f=fCapI if kw else fCap
        rep=spec.get("subs",{}).get(base)
        if rep: txt=txt.lower().replace(base,rep) if txt[:1].islower() else txt.replace(txt.strip(".,¿?¡!:;…"),rep)
        col=(RED if kw else INK) if t>=w0-0.03 else GRAY
        d.text((x,y+(-4 if kw else 0)),txt,font=f,fill=col); x+=f.getlength(txt+" ")
def draw_header(im,s,t):
    d=ImageDraw.Draw(im); d.text((60,62),"// "+s["tag"],font=fMono,fill=(120,114,108))
    p=ease((t-s["t0"])/0.35); y=300+(1-p)*40
    lay=Image.new("RGBA",(W,H)); dl=ImageDraw.Draw(lay)
    dl.text((60,y-48),"// "+s.get("sub",""),font=fMono,fill=(120,114,108,int(255*p)))
    x=60; ws=s["title"]; maxw=W-120-(150 if s.get("num") else 0); fb=fBig
    for sz in (150,136,122,110,98,88):
        fb=F("Anton.ttf",sz)
        if fb.getlength(" ".join(ws))<=maxw: break
    yo=(150-fb.size)*0.6
    for j,w in enumerate(ws):
        col=RED if j==len(ws)-1 and len(ws)>1 else INK
        dl.text((x,y+yo),w,font=fb,fill=col+(int(255*p),)); x+=fb.getlength(w+" ")
    if s.get("num"):
        bx=W-60-120; dl.rounded_rectangle([bx,y+22,bx+120,y+190],16,fill=(20,20,20,int(255*p)))
        n=str(s["num"]); dl.text((bx+60-fNum.getlength(n)/2,y+48),n,font=fNum,fill=(255,255,255,int(255*p)))
    im.alpha_composite(lay)
def card_box(lay,box,r=28):
    d=ImageDraw.Draw(lay); x0,y0,x1,y1=box
    sh=Image.new("RGBA",lay.size); ImageDraw.Draw(sh).rounded_rectangle([x0+6,y0+14,x1+6,y1+14],r,fill=(0,0,0,40)); lay.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    d.rounded_rectangle(box,r,fill=WHITE)
def check(d,cx,cy,ok=True,r=24):
    d.ellipse([cx-r,cy-r,cx+r,cy+r],fill=RED if ok else (60,60,60))
    if ok: d.line([(cx-11,cy),(cx-3,cy+9),(cx+12,cy-9)],fill=WHITE,width=6)
    else: d.line([(cx-9,cy-9),(cx+9,cy+9)],fill=WHITE,width=6); d.line([(cx-9,cy+9),(cx+9,cy-9)],fill=WHITE,width=6)
def items_visible(s,t,n):
    span=max(0.8,(s["t1"]-s["t0"])-1.2); return [ease((t-(s["t0"]+0.5+k*span/max(n,1)))/0.3) for k in range(n)]
def card(s,t):
    c=s["card"]; lay=Image.new("RGBA",(W,H)); d=ImageDraw.Draw(lay); typ=c["type"]; Y=520
    if typ=="chips":
        px0,py0=140,Y; card_box(lay,[px0,py0,px0+380,py0+640],46); d.rounded_rectangle([px0+20,py0+20,px0+360,py0+620],32,fill=(30,30,34))
        d.rounded_rectangle([px0+140,py0+34,px0+240,py0+56],11,fill=(10,10,10))
        for k,p in enumerate(items_visible(s,t,len(c["items"]))):
            if p<=0: continue
            yy=py0+100+k*100+(1-p)*30; txt=c["items"][k]; w=fCardS.getlength(txt)+60
            x=560 if k%2==0 else 600
            sh=Image.new("RGBA",(W,H)); ImageDraw.Draw(sh).rounded_rectangle([x,yy,x+w,yy+72],36,fill=(255,255,255,int(255*p))); lay.alpha_composite(sh)
            d.text((x+30,yy+16),txt,font=fCardS,fill=(RED if k%2==0 else INK)+(int(255*p),))
            d.rounded_rectangle([px0+44,py0+90+k*100,px0+336,py0+170+k*100],18,fill=(60,60,66,int(255*p)))
            d.ellipse([px0+60,py0+108+k*100,px0+104,py0+152+k*100],fill=(RED if k%2==0 else (240,200,170))+(int(255*p),))
            d.rounded_rectangle([px0+120,py0+118+k*100,px0+300,py0+132+k*100],7,fill=(150,150,160,int(255*p)))
    elif typ=="compare":
        vis=items_visible(s,t,2)
        for k,(lab,ok) in enumerate(c["items"]):
            p=vis[k]
            if p<=0: continue
            x0=80+k*480; y0=Y+(1-p)*40; card_box(lay,[x0,y0,x0+440,y0+560])
            ci=Image.new("RGBA",(W,H)); dc=ImageDraw.Draw(ci); cx,cy=x0+220,y0+230
            dc.ellipse([cx-150,cy-150,cx+150,cy+150],fill=(241,200,172))
            if ok:
                ci=ci.filter(ImageFilter.GaussianBlur(10)); ov=Image.new("RGBA",(W,H)); ImageDraw.Draw(ov).ellipse([cx-120,cy-140,cx+60,cy+20],fill=(255,255,255,90))
                ci.alpha_composite(ov.filter(ImageFilter.GaussianBlur(40)))
            else:
                dc.ellipse([cx-90,cy-110,cx-20,cy-60],fill=(255,255,255,230)); dc.ellipse([cx+40,cy+20,cx+70,cy+50],fill=(255,255,255,200))
            ci.putalpha(Image.eval(ci.getchannel("A"),lambda v:int(v*p))); lay.alpha_composite(ci)
            d.text((x0+220-fCard.getlength(lab)/2,y0+430),lab,font=fCard,fill=INK); check(d,x0+390,y0+50,ok,28)
    elif typ=="checklist":
        n=len(c["items"]); x0,y0=100,Y; card_box(lay,[x0,y0,W-100,y0+110+n*110])
        d.text((x0+40,y0+36),c.get("head",""),font=fCard,fill=INK)
        for k,p in enumerate(items_visible(s,t,n)):
            txt,ok=c["items"][k]; yy=y0+120+k*110
            d.text((x0+40,yy),txt,font=fCard,fill=INK if p>0 else (200,195,190))
            d.rounded_rectangle([x0+430,yy+18,x0+430+int(300*p),yy+30],6,fill=RED if ok else (80,80,80))
            if p>0.5: check(d,W-160,yy+24,ok)
    elif typ=="swatches":
        n=len(c["items"]); x0,y0=80,Y; card_box(lay,[x0,y0,W-80,y0+560]); d.text((x0+40,y0+34),c.get("head",""),font=fCard,fill=INK)
        sw=(W-160-80)/n
        for k,p in enumerate(items_visible(s,t,n)):
            if p<=0: continue
            name,rgb=c["items"][k]; cx=x0+40+sw*k+sw/2; cy=y0+260; r=int(min(110,sw/2-14)*(0.6+0.4*p))
            d.ellipse([cx-r,cy-r,cx+r,cy+r],fill=tuple(rgb)+(int(255*p),),outline=(0,0,0,30),width=2)
            d.ellipse([cx-r*0.55,cy-r*0.6,cx-r*0.15,cy-r*0.25],fill=(255,255,255,int(90*p)))
            for li,line in enumerate(name.split("\n")): d.text((cx-fCardS.getlength(line)/2,y0+400+li*40),line,font=fCardS,fill=INK+(int(255*p),))
    elif typ=="jacket":
        x0,y0=80,Y; card_box(lay,[x0,y0,W-80,y0+600]); cx=x0+260; col=tuple(c.get("color",[40,46,70]))
        d.polygon([(cx-170,y0+560),(cx-150,y0+150),(cx-60,y0+90),(cx+60,y0+90),(cx+150,y0+150),(cx+170,y0+560)],fill=col)
        d.polygon([(cx-60,y0+90),(cx,y0+60),(cx+60,y0+90),(cx+40,y0+150),(cx-40,y0+150)],fill=tuple(max(0,v-20) for v in col))
        d.polygon([(cx-150,y0+150),(cx-230,y0+520),(cx-185,y0+540),(cx-130,y0+260)],fill=col); d.polygon([(cx+150,y0+150),(cx+230,y0+520),(cx+185,y0+540),(cx+130,y0+260)],fill=col)
        for k in range(5):
            for sx in (-50,50): d.ellipse([cx+sx-14,y0+190+k*70,cx+sx+14,y0+218+k*70],fill=(222,180,70))
            d.line([(cx-36,y0+204+k*70),(cx+36,y0+204+k*70)],fill=(222,180,70),width=4)
        for k,p in enumerate(items_visible(s,t,len(c["items"]))):
            if p<=0: continue
            txt=c["items"][k]; yy=y0+130+k*130+(1-p)*20; xx=x0+520
            d.rounded_rectangle([xx,yy,xx+fCardS.getlength(txt)+90,yy+76],38,outline=RED+(int(255*p),),width=4,fill=(255,255,255,int(255*p)))
            check(d,xx+36,yy+38,True,20); d.text((xx+66,yy+18),txt,font=fCardS,fill=INK+(int(255*p),))
    elif typ=="comments":
        x0,y0=80,Y; card_box(lay,[x0,y0,W-80,y0+600]); d.text((x0+40,y0+34),c.get("head","Comentarios"),font=fCard,fill=INK)
        for k,p in enumerate(items_visible(s,t,len(c["items"]))):
            if p<=0: continue
            yy=y0+120+k*120+(1-p)*20; d.ellipse([x0+40,yy,x0+110,yy+70],fill=[(240,180,160),(170,200,230),(200,220,170),(230,200,120)][k%4]+(int(255*p),))
            d.rounded_rectangle([x0+130,yy,W-130,yy+80],26,fill=(244,240,236,int(255*p))); d.text((x0+160,yy+20),c["items"][k],font=fCardS,fill=INK+(int(255*p),))
        d.rounded_rectangle([x0+40,y0+500,W-130,y0+570],35,outline=(210,205,200),width=3); d.text((x0+80,y0+514),"Añade un comentario…",font=fCardS,fill=GRAY)
    # entrada de la tarjeta
    p=ease((t-s["t0"]-0.15)/0.4); out=Image.new("RGBA",(W,H)); out.alpha_composite(lay,(0,int((1-p)*80)))
    if p<1: out.putalpha(Image.eval(out.getchannel("A"),lambda v:int(v*p)))
    return out
def stamp(im,s,t):
    if not s.get("stamp"): return
    t0=s["t0"]+(s["t1"]-s["t0"])*0.55; p=ease((t-t0)/0.18)
    if p<=0: return
    txt=s["stamp"]; w=int(fStamp.getlength(txt)+60); lay=Image.new("RGBA",(w+40,140)); d=ImageDraw.Draw(lay)
    d.rounded_rectangle([20,20,20+w,120],14,outline=RED,width=6); d.text((50,30),txt,font=fStamp,fill=RED)
    sc=1.6-0.6*p; lay=lay.resize((int(lay.width*sc),int(lay.height*sc))).rotate(6,expand=True,resample=Image.BICUBIC)
    lay.putalpha(Image.eval(lay.getchannel("A"),lambda v:int(v*p))); im.alpha_composite(lay,(70,1240-lay.height//2+40))
def girl(im,fi,t):
    bob=int(5*math.sin(t*2.3)); r=RMS[min(fi,len(RMS)-1)]; m=0 if r<0.18 else (1 if r<0.6 else 2)
    e=0 if (t%3.4)<0.13 else 1
    sway=math.sin(t*1.6)*3
    im.alpha_composite(BODY,(CX,CY)); arm=ARM.rotate(sway,center=(int(150*SC),int(520*SC)),resample=Image.BICUBIC); im.alpha_composite(arm,(CX,CY))
    im.alpha_composite(HEADS[(m,e)],(CX,CY+bob))
ff=subprocess.Popen(["ffmpeg","-y","-loglevel","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-",
    "-c:v","libx264","-preset","medium","-crf","19","-pix_fmt","yuv420p",f"{OUT}/video_noaudio.mp4"],stdin=subprocess.PIPE)
for fi in range(int(DUR*FPS)):
    t=fi/FPS; si=max(i for i,s in enumerate(SEC) if s["t0"]<=t or i==0); s=SEC[si]
    im=BGIM.copy(); draw_header(im,s,t); im.alpha_composite(card(s,t)); stamp(im,s,t); draw_caption(im,s,t); girl(im,fi,t)
    if t>DUR-0.4: im=Image.blend(Image.new("RGBA",(W,H),BG+(255,)),im,max(0,(DUR-t)/0.4))
    ff.stdin.write(im.convert("RGB").tobytes())
ff.stdin.close(); ff.wait()
sh("ffmpeg","-y","-loglevel","error","-i",f"{OUT}/video_noaudio.mp4","-i",f"{OUT}/voice.wav","-i",f"{OUT}/music_n.wav","-filter_complex",
   "[1:a][2:a]amix=inputs=2:normalize=0,alimiter=limit=0.89[a]","-map","0:v","-map","[a]","-c:v","copy","-c:a","aac","-b:a","192k","-shortest","-movflags","+faststart",f"{OUT}/final.mp4")
ims=[]
for s in SEC:
    tt=s["t1"]-0.35; sh("ffmpeg","-y","-loglevel","error","-ss",f"{tt:.2f}","-i",f"{OUT}/final.mp4","-frames:v","1","-vf","scale=270:480",f"{OUT}/_f.png"); ims.append(Image.open(f"{OUT}/_f.png").copy())
sheet=Image.new("RGB",(270*4,480*math.ceil(len(ims)/4)))
for i,x in enumerate(ims): sheet.paste(x,((i%4)*270,(i//4)*480))
sheet.save(f"{OUT}/check_sheet.png")
print("OK",DUR,"voz",lufs(f"{OUT}/voice.wav"),"música",lufs(f"{OUT}/music_n.wav"))
