import numpy as np
from PIL import Image, ImageDraw, ImageFilter
W,H=1200,2134
rng=np.random.default_rng(3)
def vgrad(stops):
    ys=np.linspace(0,1,H); img=np.zeros((H,W,3))
    p=[s[0] for s in stops]; cols=np.array([s[1] for s in stops],float)
    for c in range(3): img[:,:,c]=np.interp(ys,p,cols[:,c])[:,None]
    return img
def glow(img,cx,cy,r,col,strength):
    yy,xx=np.mgrid[0:H,0:W]; d=np.sqrt((xx-cx)**2+(yy-cy)**2)/r
    g=np.exp(-d**2)*strength; img+= g[:,:,None]*np.array(col,float); return img
def ridge(y0,amp,rough,seed,n=513):
    r=np.random.default_rng(seed); pts=np.zeros(n); step=n-1; a=amp
    pts[0]=r.uniform(-amp,amp); pts[-1]=r.uniform(-amp,amp)
    while step>1:
        h=step//2
        for i in range(h,n-1,step): pts[i]=(pts[i-h]+pts[i+h])/2+r.uniform(-a,a)
        a*=rough; step=h
    xs=np.linspace(0,W,n); return [(x,y0+y) for x,y in zip(xs,pts)]
def layer(img,poly,col,blur=0):
    m=Image.new("L",(W,H),0); ImageDraw.Draw(m).polygon(poly+[(W,H),(0,H)],fill=255)
    if blur: m=m.filter(ImageFilter.GaussianBlur(blur))
    a=np.asarray(m,float)[:,:,None]/255; return img*(1-a)+a*np.array(col,float)
def circle(img,cx,cy,r,col,blur=2):
    m=Image.new("L",(W,H),0); ImageDraw.Draw(m).ellipse([cx-r,cy-r,cx+r,cy+r],fill=255)
    m=m.filter(ImageFilter.GaussianBlur(blur)); a=np.asarray(m,float)[:,:,None]/255
    return img*(1-a)+a*np.array(col,float)
def finish(img,name):
    yy,xx=np.mgrid[0:H,0:W]; d=np.sqrt(((xx-W/2)/W)**2+((yy-H/2)/H)**2)
    img*= (1-0.55*np.clip(d-0.25,0,1)**1.2)[:,:,None]
    img+=rng.normal(0,3,(H,W,1))
    Image.fromarray(np.clip(img,0,255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8)).save(name)

# A: golden particles
img=vgrad([(0,(22,10,6)),(0.5,(60,26,10)),(1,(30,12,6))])
img=glow(img,W*0.5,H*0.62,700,(200,110,40),0.9)
img=glow(img,W*0.5,H*0.62,250,(255,190,100),0.5)
for _ in range(45):
    cx,cy=rng.uniform(0,W),rng.uniform(0,H); r=rng.uniform(20,110)
    col=np.array([255,rng.uniform(170,215),rng.uniform(80,130)])
    m=Image.new("L",(W,H),0); ImageDraw.Draw(m).ellipse([cx-r,cy-r,cx+r,cy+r],fill=int(rng.uniform(25,70)))
    m=m.filter(ImageFilter.GaussianBlur(r*0.25)); a=np.asarray(m,float)[:,:,None]/255
    img=img+a*col
finish(img,"bgA.png")

# B: sunrise
img=vgrad([(0,(40,26,78)),(0.30,(120,60,120)),(0.48,(232,118,128)),(0.60,(255,178,95)),(0.66,(255,222,160)),(1,(255,222,160))])
hz=int(H*0.66)
img=glow(img,W/2,hz,900,(255,150,60),0.45)
img=glow(img,W/2,hz,260,(255,230,170),0.9)
img=circle(img,W/2,hz,150,(255,246,215),3)
for i,(cy,cx,w) in enumerate([(H*0.22,W*0.25,380),(H*0.30,W*0.78,300),(H*0.40,W*0.35,260)]):
    m=Image.new("L",(W,H),0); ImageDraw.Draw(m).ellipse([cx-w,cy-40,cx+w,cy+40],fill=90)
    m=m.filter(ImageFilter.GaussianBlur(25)); a=np.asarray(m,float)[:,:,None]/255
    img=img*(1-a)+a*np.array([255,190,170])
img=layer(img,ridge(hz-10,60,0.55,1),(170,80,110),2)
img=layer(img,ridge(hz+90,90,0.55,2),(110,45,85),2)
img=layer(img,ridge(hz+260,120,0.5,3),(62,24,60),2)
img=layer(img,ridge(hz+470,90,0.5,4),(32,12,36),2)
finish(img,"bgB.png")

# D: landscape with sun (golden hour)
img=vgrad([(0,(255,170,80)),(0.35,(255,200,120)),(0.55,(255,226,165)),(1,(255,226,165))])
sy=int(H*0.42)
img=glow(img,W/2,sy,800,(255,140,40),0.35)
img=glow(img,W/2,sy,300,(255,240,190),0.8)
img=circle(img,W/2,sy,170,(255,250,225),3)
# sun rays
m=Image.new("L",(W,H),0); d=ImageDraw.Draw(m)
for k in range(18):
    a0=k*20; import math
    pts=[(W/2,sy)]+[(W/2+2000*math.cos(math.radians(a)),sy+2000*math.sin(math.radians(a))) for a in (a0,a0+6)]
    d.polygon(pts,fill=28)
m=m.filter(ImageFilter.GaussianBlur(30)); a=np.asarray(m,float)[:,:,None]/255; img=img+a*255*0.6
img=layer(img,ridge(H*0.56,70,0.55,11),(214,150,110),3)
img=layer(img,ridge(H*0.62,80,0.5,12),(196,140,70),2)
img=layer(img,ridge(H*0.70,70,0.5,13),(150,120,45),2)
img=layer(img,ridge(H*0.80,60,0.45,14),(95,85,30),2)
# trees
for tx,ty,s in [(170,H*0.78,1.0),(260,H*0.79,0.7),(980,H*0.76,1.2),(1080,H*0.78,0.8)]:
    m=Image.new("L",(W,H),0); d=ImageDraw.Draw(m)
    d.rectangle([tx-8*s,ty-120*s,tx+8*s,ty+20],fill=255)
    for dx,dy,r in [(0,-200,95),(-60,-150,70),(60,-150,70),(0,-280,70)]:
        d.ellipse([tx+dx*s-r*s,ty+dy*s-r*s,tx+dx*s+r*s,ty+dy*s+r*s],fill=255)
    m=m.filter(ImageFilter.GaussianBlur(2)); a=np.asarray(m,float)[:,:,None]/255
    img=img*(1-a)+a*np.array([70,55,25])
img=layer(img,ridge(H*0.90,40,0.45,15),(55,45,18),2)
finish(img,"bgD.png")

# C: window with mountains
img=vgrad([(0,(250,196,150)),(0.45,(255,214,170)),(1,(255,214,170))])
img=glow(img,W*0.62,H*0.50,500,(255,235,190),0.7)
img=layer(img,ridge(H*0.47,140,0.6,21),(176,150,180),3)
img=layer(img,ridge(H*0.53,160,0.58,22),(128,110,152),2)
img=layer(img,ridge(H*0.60,130,0.55,23),(88,76,118),2)
img=layer(img,ridge(H*0.68,90,0.5,24),(56,52,82),2)
outside=img.copy()
# room
room=vgrad([(0,(58,34,22)),(1,(36,20,14))])
room=glow(room,W*0.5,H*0.5,900,(140,80,40),0.6)
x0,x1,y0,y1=140,W-140,330,1600
mask=np.zeros((H,W,1)); mask[y0:y1,x0:x1]=1
img=room*(1-mask)+outside*mask
im=Image.fromarray(np.clip(img,0,255).astype(np.uint8)); d=ImageDraw.Draw(im)
fr=(92,56,34); t=34
d.rectangle([x0-t,y0-t,x1+t,y0],fill=fr); d.rectangle([x0-t,y1,x1+t,y1+t],fill=fr)
d.rectangle([x0-t,y0,x0,y1],fill=fr); d.rectangle([x1,y0,x1+t,y1],fill=fr)
d.rectangle([W/2-12,y0,W/2+12,y1],fill=fr); d.rectangle([x0,int((y0+y1)/2)-12,x1,int((y0+y1)/2)+12],fill=fr)
d.rectangle([x0-90,y1+t,x1+90,y1+t+60],fill=(120,74,44))
# plant pot on sill
d.polygon([(860,y1+t),(1000,y1+t),(980,y1-110),(880,y1-110)],fill=(170,90,60))
for ang in range(-60,61,20):
    import math
    ex=930+170*math.sin(math.radians(ang)); ey=y1-110-200*math.cos(math.radians(ang))
    d.ellipse([ex-40,ey-70,ex+40,ey+70],fill=(70,100,50))
# curtains
for side in (0,1):
    for k in range(4):
        w=150-k*30
        if side==0: box=[0,0,w+k*0,H]; xa,xb=k*36,k*36+60
        else: xa,xb=W-k*36-60,W-k*36
        c=(170-k*18,100-k*12,64-k*8)
        d.rectangle([xa,0,xb,H],fill=c)
img=np.asarray(im,float)
# light shafts from window
m=Image.new("L",(W,H),0); ImageDraw.Draw(m).polygon([(x0,y1),(x1,y1),(W+300,H),(-300,H)],fill=40)
m=m.filter(ImageFilter.GaussianBlur(60)); a=np.asarray(m,float)[:,:,None]/255; img=img+a*np.array([255,200,140])
finish(img,"bgC.png")
