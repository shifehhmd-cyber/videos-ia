import json, subprocess, numpy as np, math
from PIL import Image, ImageDraw, ImageFilter, ImageFont
W,H,FPS,DUR=1080,1920,30,25.0
T=json.load(open("timings.json"))
START=[0.5,5.4,8.1,10.3,13.4,18.1,21.0]
# display tokens: (text, spoken-word index that triggers it, keyword?)
DISP=[[("Quedan",0,0),("37 días",1,1),("para",5,0),("que",6,0),("acabe",7,0),("2026.",8,0)],
      [("Hoy",0,0),("te",1,0),("has",2,0),("despertado.",3,1)],
      [("Respiras.",0,1)],
      [("Y",0,0),("estás",1,0),("leyendo",2,0),("esto.",3,1)],
      [("Millones",0,0),("de",1,0),("personas",2,0),("darían",3,0),("todo",4,1),("por",5,0),("tener",6,0),("solo",7,0),("eso.",8,0)],
      [("No",0,0),("esperes",1,0),("a",2,0),("enero.",3,1)],
      [("Empieza",0,0),("hoy.",1,1)]]
BGS={0:"bgA.png",1:"bgB.png",2:"bgB.png",3:"bgC.png",4:"bgC.png",5:"bgD.png",6:"bgD.png"}
# card windows
cards=[]
for i,s in enumerate(DISP):
    st=START[i]; ws=T[i]["words"]
    toks=[(txt,st+ws[k][0]-0.04,kw) for txt,k,kw in s]
    end=START[i+1]-0.15 if i+1<len(DISP) else DUR
    cards.append((st,end,toks))
font=ImageFont.truetype("fonts/Montserrat-900.ttf",112 if True else 0)
def fit_font(toks):
    for size in (118,108,98,90):
        f=ImageFont.truetype("fonts/Montserrat-900.ttf",size)
        lines=layout(toks,f)
        if len(lines)<=4: return f,lines
    return f,lines
def layout(toks,f):
    maxw=900; sp=f.getlength(" ")+8; lines=[[]]; w=0
    for tok in toks:
        tw=f.getlength(tok[0])+(64 if tok[2] else 0)
        if lines[-1] and w+sp+tw>maxw: lines.append([]); w=0
        w+= (sp if lines[-1] else 0)+tw; lines[-1].append((tok,tw))
    return lines
LAY=[fit_font(c[2]) for c in cards]
def ease(x): x=min(max(x,0),1); return 1-(1-x)**3
def text_layer(ci,t):
    st,end,toks=cards[ci]; f,lines=LAY[ci]
    lay=Image.new("RGBA",(W,H),(0,0,0,0)); sh=Image.new("RGBA",(W,H),(0,0,0,0))
    d=ImageDraw.Draw(lay); ds=ImageDraw.Draw(sh)
    lh=f.size*1.32; total=lh*len(lines); y=H*0.44-total/2
    fade=1.0
    if ci+1<len(cards): fade=1-ease((t-(end-0.25))/0.25)
    sp=f.getlength(" ")+8
    for line in lines:
        lw=sum(tw for _,tw in line)+sp*(len(line)-1); x=(W-lw)/2
        for (txt,t0,kw),tw in line:
            p=ease((t-t0)/0.22)
            if p>0:
                a=int(255*p*fade); dy=(1-p)*30
                if kw:
                    pad=32; bx=[x,y+dy+f.size*0.04,x+tw,y+dy+f.size*1.2]
                    s=0.85+0.15*p; cx,cy=(bx[0]+bx[2])/2,(bx[1]+bx[3])/2
                    bb=[cx-(cx-bx[0])*s,cy-(cy-bx[1])*s,cx+(bx[2]-cx)*s,cy+(bx[3]-cy)*s]
                    ds.rounded_rectangle([bb[0]+6,bb[1]+10,bb[2]+6,bb[3]+10],radius=18,fill=(0,0,0,int(a*0.35)))
                    d.rounded_rectangle(bb,radius=18,fill=(255,255,255,a))
                    d.text((x+pad,y+dy),txt,font=f,fill=(58,30,12,a))
                else:
                    ds.text((x+3,y+dy+5),txt,font=f,fill=(0,0,0,int(a*0.75)))
                    d.text((x,y+dy),txt,font=f,fill=(255,255,255,a))
            x+=tw+sp
        y+=lh
    sh=sh.filter(ImageFilter.GaussianBlur(9))
    return Image.alpha_composite(sh,lay)
bgcache={k:Image.open(v).convert("RGB") for k,v in set(BGS.items())} if False else {}
srcs={n:Image.open(n).convert("RGB") for n in set(BGS.values())}
def bg_frame(name,t,t0):
    im=srcs[name]; z=1.0+0.035*((t-t0)/8)
    w,h=W*z,H*z; iw,ih=im.size; s=max(iw/w,ih/h)
    cw,ch=W*s/z*z/z, H*s/z
    cw,ch=iw/ z/ (iw/W) * 1, 0
    # crop box in source coords
    scale=min(iw/W,ih/H)/z; bw,bh=W*scale,H*scale
    cx,cy=iw/2,ih/2-(t-t0)*3
    return im.crop((int(cx-bw/2),int(cy-bh/2),int(cx+bw/2),int(cy+bh/2))).resize((W,H),Image.BILINEAR)
# scene segments by background change
segs=[]; 
for i in range(len(cards)):
    n=BGS[i]
    if segs and segs[-1][0]==n: continue
    segs.append([n,START[i] if i else 0.0])
rng=np.random.default_rng(5); NP=70
P=np.column_stack([rng.uniform(0,W,NP),rng.uniform(0,H,NP),rng.uniform(2,7,NP),rng.uniform(20,70,NP),rng.uniform(0,6.28,NP)])
def particles(t):
    lay=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(lay)
    for x,y,r,v,ph in P:
        yy=(y-v*t)%H; xx=x+25*math.sin(t*0.6+ph)
        a=int(150+100*math.sin(t*2+ph))
        d.ellipse([xx-r*2.2,yy-r*2.2,xx+r*2.2,yy+r*2.2],fill=(255,200,110,a//4))
        d.ellipse([xx-r,yy-r,xx+r,yy+r],fill=(255,225,150,a))
    return lay.filter(ImageFilter.GaussianBlur(1.5))
ff=subprocess.Popen(["ffmpeg","-y","-loglevel","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-",
    "-c:v","libx264","-preset","medium","-crf","18","-pix_fmt","yuv420p","video_noaudio.mp4"],stdin=subprocess.PIPE)
N=int(DUR*FPS)
for fi in range(N):
    t=fi/FPS
    si=max(i for i,s in enumerate(segs) if s[1]<=t)
    frame=bg_frame(segs[si][0],t,segs[si][1])
    if si>0 and t-segs[si][1]<0.7:
        prev=bg_frame(segs[si-1][0],t,segs[si-1][1]); frame=Image.blend(prev,frame,ease((t-segs[si][1])/0.7))
    # darken band for readability
    frame=frame.convert("RGBA")
    if fi==0:
        band=np.zeros((H,W,4),np.uint8); yy=np.arange(H); a=(np.exp(-((yy-H*0.44)/430)**2)*95).astype(np.uint8)
        band[:,:,3]=a[:,None]; BAND=Image.fromarray(band,"RGBA")
    frame=Image.alpha_composite(frame,BAND)
    frame=Image.alpha_composite(frame,particles(t))
    for ci,(st,end,_) in enumerate(cards):
        if st<=t<end: frame=Image.alpha_composite(frame,text_layer(ci,t))
    # global fade in/out
    g=min(1,t/0.4, (DUR-t)/0.6)
    if g<1: frame=Image.blend(Image.new("RGBA",(W,H),(0,0,0,255)),frame,max(g,0))
    ff.stdin.write(frame.convert("RGB").tobytes())
ff.stdin.close(); ff.wait()
print("ok")
