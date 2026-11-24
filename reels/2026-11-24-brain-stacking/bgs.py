import numpy as np, math
from PIL import Image, ImageDraw, ImageFilter
W,H=1200,2134; rng=np.random.default_rng(11)
def vgrad(stops):
    ys=np.linspace(0,1,H); img=np.zeros((H,W,3)); p=[s[0] for s in stops]; c=np.array([s[1] for s in stops],float)
    for k in range(3): img[:,:,k]=np.interp(ys,p,c[:,k])[:,None]
    return img
YY,XX=np.mgrid[0:H,0:W]
def glow(img,cx,cy,r,col,s): return img+(np.exp(-(((XX-cx)**2+(YY-cy)**2)/r**2))*s)[:,:,None]*np.array(col,float)
def paste(img,drawfn,blur=1.5):
    im=Image.fromarray(np.clip(img,0,255).astype(np.uint8)).convert("RGBA"); lay=Image.new("RGBA",(W,H),(0,0,0,0))
    drawfn(ImageDraw.Draw(lay)); lay=lay.filter(ImageFilter.GaussianBlur(blur))
    return np.asarray(Image.alpha_composite(im,lay).convert("RGB"),float)
def finish(img,name):
    d=np.sqrt(((XX-W/2)/W)**2+((YY-H/2)/H)**2); img=img*(1-0.6*np.clip(d-0.25,0,1)**1.2)[:,:,None]+rng.normal(0,3,(H,W,1))
    Image.fromarray(np.clip(img,0,255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7)).save(name)
# 1 móvil en la oscuridad
img=vgrad([(0,(8,10,30)),(1,(18,14,40))]); img=glow(img,W/2,H*0.62,520,(60,110,255),0.55); img=glow(img,W/2,H*0.62,260,(140,180,255),0.35)
def phone(d):
    x0,y0,x1,y1=W/2-230,H*0.62-430,W/2+230,H*0.62+430
    d.rounded_rectangle([x0-18,y0-18,x1+18,y1+18],60,fill=(20,20,28,255))
    d.rounded_rectangle([x0,y0,x1,y1],46,fill=(120,170,255,255))
    for i in range(6):
        yy=y0+60+i*130; d.rounded_rectangle([x0+30,yy,x1-30,yy+100],22,fill=(235,242,255,235))
        d.ellipse([x0+48,yy+22,x0+104,yy+78],fill=(255,80,90,255) if i%2==0 else (255,190,60,255))
        d.rounded_rectangle([x0+125,yy+28,x1-60,yy+44],8,fill=(150,165,200,255)); d.rounded_rectangle([x0+125,yy+58,x1-140,yy+72],8,fill=(190,200,225,255))
    for k in range(9):
        a=rng.uniform(0,6.28); r=rng.uniform(380,560); cx,cy=W/2+r*math.cos(a),H*0.62+r*math.sin(a)*1.2
        d.ellipse([cx-34,cy-34,cx+34,cy+34],fill=(255,60,80,220)); d.text((cx-9,cy-14),str(rng.integers(1,9)),fill=(255,255,255,255))
img=paste(img,phone,1.2); finish(img,"bg_phone.png")
# 2 escritorio con pila de libros y lámpara
img=vgrad([(0,(40,24,16)),(0.7,(58,34,20)),(0.71,(110,66,38)),(1,(80,46,26))]); img=glow(img,W*0.3,H*0.45,700,(255,170,80),0.65); img=glow(img,W*0.3,H*0.42,240,(255,220,150),0.5)
def desk(d):
    d.polygon([(W*0.3-170,H*0.38),(W*0.3+170,H*0.38),(W*0.3+90,H*0.30),(W*0.3-90,H*0.30)],fill=(230,170,80,255))
    d.rectangle([W*0.3-10,H*0.38,W*0.3+10,H*0.70],fill=(60,40,25,255)); d.ellipse([W*0.3-110,H*0.69,W*0.3+110,H*0.72],fill=(50,32,20,255))
    cols=[(176,64,52),(64,110,140),(222,170,80),(90,130,90),(150,90,140),(210,120,70),(70,80,130)]
    y=H*0.705
    for i,c in enumerate(cols):
        h=rng.uniform(60,95); w=rng.uniform(380,470); x=W*0.66+rng.uniform(-25,25)
        d.rounded_rectangle([x-w/2,y-h,x+w/2,y],8,fill=c+(255,)); d.rectangle([x-w/2+8,y-h+10,x+w/2-8,y-h+16],fill=(255,240,210,200)); y-=h
    d.rounded_rectangle([W*0.66-90,y-140,W*0.66+90,y-6],30,fill=(240,235,225,255)); d.ellipse([W*0.66+70,y-110,W*0.66+140,y-40],outline=(240,235,225,255),width=14)
img=paste(img,desk,1.5); finish(img,"bg_books.png")
# 3 libreta + piezas de puzle sobre mesa
img=vgrad([(0,(190,140,95)),(1,(150,100,64))]); img=glow(img,W*0.5,H*0.35,800,(255,220,170),0.4)
def note(d):
    d.rounded_rectangle([170,520,1030,1500],20,fill=(70,50,40,90)); d.rounded_rectangle([150,490,1010,1470],20,fill=(252,248,238,255))
    for k in range(13): d.line([210,600+k*64,960,600+k*64],fill=(170,200,230,255),width=4)
    d.line([300,500,300,1460],fill=(240,140,140,255),width=4)
    for k in range(9): d.ellipse([130,560+k*100,175,605+k*100],fill=(120,90,70,255))
    pts=[(500,1560),(1080,1080),(1110,1110),(530,1590)]; d.polygon(pts,fill=(255,200,60,255)); d.polygon([(500,1560),(530,1590),(470,1610)],fill=(240,210,170,255))
    cols=[(80,140,200),(230,110,90),(120,180,110),(240,190,80)]
    for i in range(6):
        cx,cy=rng.uniform(150,1050),rng.uniform(1650,2000); s=rng.uniform(80,120); c=cols[i%4]
        d.rectangle([cx-s,cy-s,cx+s,cy+s],fill=c+(255,)); d.ellipse([cx+s-30,cy-30,cx+s+30,cy+30],fill=c+(255,)); d.ellipse([cx-30,cy-s-30,cx+30,cy-s+30],fill=c+(255,))
img=paste(img,note,1.5); finish(img,"bg_notebook.png")
# 4 ventana nocturna serena con luna
sky=vgrad([(0,(14,18,48)),(0.5,(40,46,96)),(1,(80,70,120))]); sky=glow(sky,W*0.65,H*0.30,300,(200,210,255),0.5)
mask=np.zeros((H,W,1)); x0,x1,y0,y1=160,W-160,330,1580; mask[y0:y1,x0:x1]=1
room=vgrad([(0,(30,22,30)),(1,(18,14,20))]); room=glow(room,W*0.2,H*0.85,600,(255,150,70),0.45)
img=room*(1-mask)+sky*mask
def win(d):
    for _ in range(60):
        x,y=rng.uniform(x0,x1),rng.uniform(y0,y0+700); r=rng.uniform(1.5,4); d.ellipse([x-r,y-r,x+r,y+r],fill=(255,255,240,220))
    d.ellipse([W*0.65-90,H*0.30-90,W*0.65+90,H*0.30+90],fill=(250,245,220,255))
    import random; random.seed(4); pts=[(x0,1300)]
    for k in range(9): pts.append((x0+k*(x1-x0)/8,1150+random.uniform(-90,90)))
    pts+= [(x1,y1),(x0,y1)]; d.polygon(pts,fill=(36,36,70,255))
    fr=(70,48,40,255); t=32
    d.rectangle([x0-t,y0-t,x1+t,y0],fill=fr); d.rectangle([x0-t,y1,x1+t,y1+t],fill=fr); d.rectangle([x0-t,y0,x0,y1],fill=fr); d.rectangle([x1,y0,x1+t,y1],fill=fr)
    d.rectangle([W/2-11,y0,W/2+11,y1],fill=fr); d.rectangle([x0,(y0+y1)/2-11,x1,(y0+y1)/2+11],fill=fr)
    d.rectangle([x0-90,y1+t,x1+90,y1+t+60],fill=(96,66,50,255))
    # taza y libro en el alféizar
    d.rounded_rectangle([260,y1+t-150,420,y1+t],24,fill=(235,225,210,255)); d.ellipse([400,y1+t-120,470,y1+t-50],outline=(235,225,210,255),width=14)
    d.rounded_rectangle([600,y1+t-60,950,y1+t],8,fill=(176,64,52,255)); d.rounded_rectangle([620,y1+t-110,930,y1+t-60],8,fill=(64,110,140,255))
img=paste(img,win,1.5); img=glow(img,W*0.5,H*0.95,500,(255,160,80),0.2); finish(img,"bg_night.png")
