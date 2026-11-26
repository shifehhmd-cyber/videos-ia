import numpy as np, math
from PIL import Image, ImageDraw, ImageFilter, ImageFont
W,H=1200,2134; rng=np.random.default_rng(41); YY,XX=np.mgrid[0:H,0:W]
FA=lambda s: ImageFont.truetype("/home/user/videos-ia/pipeline/fonts/Anton.ttf",s)
FI=lambda s: ImageFont.truetype("/home/user/videos-ia/pipeline/fonts/Inter-ExtraBold.ttf",s)
def vgrad(a,b):
    t=np.linspace(0,1,H)[:,None,None]; return np.array(a,float)*(1-t)+np.array(b,float)*t*np.ones((H,W,3))
def glow(img,cx,cy,r,col,s): return img+(np.exp(-(((XX-cx)**2+(YY-cy)**2)/r**2))*s)[:,:,None]*np.array(col,float)
def paste(img,fn,blur=1.0):
    im=Image.fromarray(np.clip(img,0,255).astype(np.uint8)).convert("RGBA"); l=Image.new("RGBA",(W,H)); fn(ImageDraw.Draw(l))
    return np.asarray(Image.alpha_composite(im,l.filter(ImageFilter.GaussianBlur(blur))).convert("RGB"),float)
def fin(img,n):
    d=np.sqrt(((XX-W/2)/W)**2+((YY-H/2)/H)**2); img=img*(1-0.6*np.clip(d-0.25,0,1))[:,:,None]+rng.normal(0,3,(H,W,1))
    Image.fromarray(np.clip(img,0,255).astype(np.uint8)).save(n)
# 1 móvil con mensaje reenviado
img=glow(vgrad((10,14,30),(22,12,30)),W/2,H*0.74,600,(255,80,80),0.4)
def ph(d):
    x0,y0,x1,y1=W/2-260,1180,W/2+260,2134; d.rounded_rectangle([x0-16,y0-16,x1+16,y1+60],60,fill=(20,20,26)); d.rounded_rectangle([x0,y0,x1,y1+40],46,fill=(232,226,218))
    for k in range(3):
        yy=y0+80+k*230; d.rounded_rectangle([x0+30,yy,x1-60,yy+190],28,fill=(255,255,255))
        d.text((x0+56,yy+20),"↪ Reenviado muchas veces" if False else "REENVIADO",font=FI(30),fill=(150,150,160))
        d.rounded_rectangle([x0+56,yy+80,x1-110,yy+100],8,fill=(190,190,200)); d.rounded_rectangle([x0+56,yy+124,x1-200,yy+144],8,fill=(190,190,200))
    d.ellipse([x1-90,y0-70,x1+70,y0+90],fill=(230,50,60)); d.text((x1-30,y0-60),"!",font=FA(120),fill=(255,255,255))
img=paste(img,ph); fin(img,"bg_phone.png")
# 2 lupa sobre titular
img=glow(vgrad((18,20,26),(8,10,14)),W/2,H*0.72,600,(255,210,120),0.35)
def lupa(d):
    d.rounded_rectangle([170,1250,1030,1800],24,fill=(245,242,235))
    d.text((220,1290),"¡ÚLTIMA HORA!",font=FA(110),fill=(30,30,30))
    for k in range(6): d.rounded_rectangle([220,1450+k*55,980-(k%3)*120,1475+k*55],10,fill=(170,165,160))
    d.ellipse([560,1480,900,1820],outline=(40,40,48),width=34); d.line([(860,1780),(1040,1990)],fill=(40,40,48),width=50)
img=paste(img,lupa); fin(img,"bg_lupa.png")
# 3 verificado / falso sellos
img=glow(vgrad((14,22,20),(8,12,12)),W/2,H*0.74,600,(80,220,150),0.35)
def sellos(d):
    d.rounded_rectangle([170,1300,560,1520],20,outline=(230,60,70),width=14); d.text((215,1325),"FALSO",font=FA(140),fill=(230,60,70))
    d.rounded_rectangle([590,1600,1110,1820],20,outline=(60,200,130),width=14); d.text((640,1625),"VERIFICADO",font=FA(110),fill=(60,200,130))
img=paste(img,sellos); fin(img,"bg_check.png")
# 4 urna
img=glow(vgrad((16,14,34),(8,8,18)),W/2,H*0.76,650,(120,150,255),0.4)
def urna(d):
    d.polygon([(330,1500),(870,1500),(930,2050),(270,2050)],fill=(225,232,245)); d.rectangle([330,1460,870,1520],fill=(200,210,230)); d.rectangle([500,1478,700,1496],fill=(40,40,60))
    d.polygon([(520,1260),(690,1240),(710,1480),(540,1500)],fill=(255,255,255)); d.text((560,1320),"29N",font=FA(70),fill=(60,70,120))
img=paste(img,urna); fin(img,"bg_urna.png")
