import numpy as np, math
from PIL import Image, ImageDraw, ImageFilter, ImageFont
W,H=1200,2134; rng=np.random.default_rng(31); YY,XX=np.mgrid[0:H,0:W]
FA=lambda s: ImageFont.truetype("/home/user/videos-ia/pipeline/fonts/Anton.ttf",s)
def vgrad(a,b):
    t=np.linspace(0,1,H)[:,None,None]; return np.array(a,float)*(1-t)+np.array(b,float)*t*np.ones((H,W,3))
def glow(img,cx,cy,r,col,s): return img+(np.exp(-(((XX-cx)**2+(YY-cy)**2)/r**2))*s)[:,:,None]*np.array(col,float)
def paste(img,fn,blur=1.2):
    im=Image.fromarray(np.clip(img,0,255).astype(np.uint8)).convert("RGBA"); l=Image.new("RGBA",(W,H)); fn(ImageDraw.Draw(l))
    return np.asarray(Image.alpha_composite(im,l.filter(ImageFilter.GaussianBlur(blur))).convert("RGB"),float)
def fin(img,n):
    d=np.sqrt(((XX-W/2)/W)**2+((YY-H/2)/H)**2); img=img*(1-0.6*np.clip(d-0.25,0,1))[:,:,None]+rng.normal(0,3,(H,W,1))
    Image.fromarray(np.clip(img,0,255).astype(np.uint8)).save(n)
def person(d,cx,base,s=1.0,col=(14,10,24)):
    d.ellipse([cx-60*s,base-640*s,cx+60*s,base-520*s],fill=col)
    d.polygon([(cx-120*s,base-500*s),(cx+120*s,base-500*s),(cx+150*s,base-200*s),(cx+90*s,base),(cx-90*s,base),(cx-150*s,base-200*s)],fill=col)
    d.rounded_rectangle([cx-60*s,base-540*s,cx+60*s,base-480*s],20,fill=col)
# 1 silueta con aura
img=vgrad((10,6,26),(30,10,50)); img=glow(img,W/2,H*0.74,420,(160,90,255),0.9); img=glow(img,W/2,H*0.74,230,(255,180,255),0.5)
img=paste(img,lambda d: person(d,W/2,2050,1.1)); fin(img,"bg_aura.png")
# 2 barra de experiencia de videojuego
img=glow(vgrad((8,14,30),(14,8,30)),W/2,H*0.75,600,(60,200,255),0.4)
def xp(d):
    d.text((300,1250),"+100 AURA",font=FA(150),fill=(120,230,255))
    d.rounded_rectangle([160,1500,1040,1580],40,outline=(120,230,255),width=8); d.rounded_rectangle([176,1516,800,1564],28,fill=(120,230,255))
    d.text((160,1610),"LVL 99",font=FA(80),fill=(255,255,255))
img=paste(img,xp,0.8); fin(img,"bg_xp.png")
# 3 batalla de aura: dos siluetas y público
img=glow(vgrad((24,8,20),(10,6,14)),W*0.3,H*0.75,360,(255,90,120),0.7); img=glow(img,W*0.7,H*0.75,360,(90,160,255),0.7)
def bat(d):
    person(d,W*0.3,2000,0.95); person(d,W*0.7,2000,0.95)
    d.text((W/2-60,1500),"VS",font=FA(130),fill=(255,255,255))
    for k in range(14): x=40+k*85; person(d,x,2134+120,0.35,(6,4,10))
img=paste(img,bat); fin(img,"bg_battle.png")
# 4 calle nocturna con luces (cierre)
img=vgrad((12,10,30),(40,16,40))
for k in range(18): img=glow(img,rng.uniform(0,W),rng.uniform(H*0.55,H*0.95),rng.uniform(40,110),[(255,200,120),(255,120,180),(140,180,255)][k%3],0.6)
img=paste(img,lambda d: person(d,W/2,2134,1.0,(8,6,14)),2); fin(img,"bg_street.png")
