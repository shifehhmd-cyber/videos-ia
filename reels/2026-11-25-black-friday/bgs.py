import numpy as np, math
from PIL import Image, ImageDraw, ImageFilter, ImageFont
W,H=1200,2134; rng=np.random.default_rng(21); YY,XX=np.mgrid[0:H,0:W]
FB=ImageFont.truetype("/home/user/videos-ia/pipeline/fonts/Anton.ttf",150)
def vgrad(a,b):
    t=np.linspace(0,1,H)[:,None,None]; return np.array(a,float)*(1-t)+np.array(b,float)*t*np.ones((H,W,3))
def glow(img,cx,cy,r,col,s): return img+(np.exp(-(((XX-cx)**2+(YY-cy)**2)/r**2))*s)[:,:,None]*np.array(col,float)
def paste(img,fn,blur=1.2):
    im=Image.fromarray(np.clip(img,0,255).astype(np.uint8)).convert("RGBA"); l=Image.new("RGBA",(W,H)); fn(ImageDraw.Draw(l))
    return np.asarray(Image.alpha_composite(im,l.filter(ImageFilter.GaussianBlur(blur))).convert("RGB"),float)
def fin(img,n):
    d=np.sqrt(((XX-W/2)/W)**2+((YY-H/2)/H)**2); img=img*(1-0.6*np.clip(d-0.25,0,1))[:,:,None]+rng.normal(0,3,(H,W,1))
    Image.fromarray(np.clip(img,0,255).astype(np.uint8)).save(n)
# 1 bolsas de compra
img=glow(vgrad((20,14,30),(50,16,40)),W/2,H*0.75,700,(255,60,90),0.45)
def bags(d):
    for x,y,w,h,c in [(150,1350,330,420,(230,60,80)),(470,1300,300,470,(250,200,70)),(760,1380,320,390,(240,240,245))]:
        d.arc([x+w*0.28,y-110,x+w*0.72,y+60],180,360,fill=(40,30,40),width=16); d.rectangle([x,y,x+w,y+h],fill=c)
        d.rectangle([x,y,x+w,y+30],fill=tuple(max(0,v-40) for v in c))
    d.text((520,1480),"%",font=FB,fill=(40,30,40))
img=paste(img,bags); fin(img,"bg_bags.png")
# 2 etiqueta de precio tachado
img=glow(vgrad((26,20,18),(12,10,10)),W/2,H*0.72,600,(255,200,80),0.35)
def tag(d):
    d.polygon([(330,1250),(870,1250),(950,1420),(870,1590),(330,1590)],fill=(250,240,220)); d.ellipse([835,1395,875,1445],fill=(26,20,18))
    d.text((380,1280),"99€",font=FB,fill=(150,140,130)); d.line([(370,1420),(700,1330)],fill=(230,50,60),width=14)
    d.text((380,1440),"",font=FB,fill=(230,50,60))
img=paste(img,tag); fin(img,"bg_tag.png")
# 3 móvil con SMS sospechoso
img=glow(vgrad((10,14,34),(20,16,44)),W/2,H*0.72,600,(70,120,255),0.5)
def ph(d):
    x0,y0,x1,y1=W/2-240,1150,W/2+240,2050; d.rounded_rectangle([x0-16,y0-16,x1+16,y1+16],60,fill=(20,20,26)); d.rounded_rectangle([x0,y0,x1,y1],46,fill=(235,238,245))
    for k in range(3):
        yy=y0+80+k*190; d.rounded_rectangle([x0+30,yy,x1-80,yy+150],30,fill=(210,215,228)); d.rounded_rectangle([x0+60,yy+40,x1-140,yy+60],8,fill=(150,160,180)); d.rounded_rectangle([x0+60,yy+90,x1-220,yy+110],8,fill=(150,160,180))
    d.polygon([(x1-60,y0+40),(x1+60,y0+250),(x1-180,y0+250)],fill=(250,200,40)); d.rectangle([x1-68,y0+110,x1-52,y0+190],fill=(30,30,30)); d.ellipse([x1-70,y0+205,x1-50,y0+225],fill=(30,30,30))
img=paste(img,ph); fin(img,"bg_phone.png")
# 4 calendario 27
img=glow(vgrad((30,12,20),(12,8,14)),W/2,H*0.72,650,(255,70,90),0.4)
def cal(d):
    x0,y0=330,1200; d.rounded_rectangle([x0,y0,x0+540,y0+600],40,fill=(250,248,245)); d.rounded_rectangle([x0,y0,x0+540,y0+150],40,fill=(225,55,70)); d.rectangle([x0,y0+110,x0+540,y0+150],fill=(225,55,70))
    for k in (120,420): d.rounded_rectangle([x0+k-14,y0-50,x0+k+14,y0+50],12,fill=(60,50,55))
    f=ImageFont.truetype("/home/user/videos-ia/pipeline/fonts/Anton.ttf",300); d.text((x0+120,y0+190),"27",font=f,fill=(30,24,26))
img=paste(img,cal); fin(img,"bg_cal.png")
