"""Chica ilustrada original (2D plano). Genera capas RGBA en chars/: body.png y head_m{0,1,2}_e{0,1}.png"""
from PIL import Image, ImageDraw, ImageFilter
import os
S=2; W,H=640*S,820*S
SKIN=(241,200,172); SKIN_SH=(226,176,148); HAIR=(74,44,30); HAIR_HI=(104,64,44)
COAT=(196,146,96); COAT_SH=(170,120,76); KNIT=(244,236,222); LIP=(196,82,92)
os.makedirs("chars",exist_ok=True)
def P(*pts):
    if isinstance(pts[0],tuple): return [(x*S,y*S) for x,y in pts]
    return [v*S for v in pts]
def save(im,n): im.resize((im.width//S,im.height//S),Image.LANCZOS).save("chars/"+n)
# ---- cuerpo + brazo que señala (arriba a la izquierda)
b=Image.new("RGBA",(W,H)); d=ImageDraw.Draw(b)
d.rounded_rectangle(P(285,300,365,420),20*S,fill=SKIN_SH)       # cuello
d.polygon(P((90,820),(120,520),(200,440),(450,440),(530,520),(560,820)),fill=COAT)  # abrigo
d.polygon(P((250,440),(325,600),(400,440)),fill=KNIT)           # jersey cuello vuelto
d.rounded_rectangle(P(262,410,388,470),30*S,fill=KNIT)
d.polygon(P((200,440),(325,620),(270,820),(230,820),(185,520)),fill=COAT_SH)   # solapas
d.polygon(P((450,440),(325,620),(380,820),(420,820),(465,520)),fill=COAT_SH)
for y in (680,760): d.ellipse(P(300,y,322,y+22),fill=(120,84,50)); d.ellipse(P(330,y,352,y+22),fill=(120,84,50))
# brazo izquierdo (de la chica, a la derecha de la imagen) relajado
d.polygon(P((530,520),(575,600),(590,820),(520,820),(500,600)),fill=COAT_SH)
save(b,"body.png")
# brazo que señala: capa aparte para animarlo (pivote en el hombro ~ (150,520))
a=Image.new("RGBA",(W,H)); d=ImageDraw.Draw(a)
d.polygon(P((175,470),(130,560),(40,420),(70,380)),fill=COAT)          # brazo hasta el codo hacia arriba-izquierda
d.polygon(P((40,420),(70,380),(40,250),(0,270)),fill=COAT)              # antebrazo
d.rounded_rectangle(P(0,240,48,285),12*S,fill=KNIT)                     # puño
d.ellipse(P(-2,190,52,250),fill=SKIN)                                   # mano
d.rounded_rectangle(P(14,120,36,210),11*S,fill=SKIN)                    # índice
d.ellipse(P(30,200,56,226),fill=SKIN_SH)                                # pulgar
save(a,"arm.png")
# ---- cabeza
def head(mouth,eyes):
    h=Image.new("RGBA",(W,H)); d=ImageDraw.Draw(h)
    d.ellipse(P(178,70,472,330),fill=HAIR)                              # volumen pelo
    d.polygon(P((182,230),(232,300),(240,420),(215,540),(160,560),(175,430)),fill=HAIR)   # mechón izq
    d.polygon(P((468,230),(418,300),(410,420),(435,540),(490,560),(475,430)),fill=HAIR)   # mechón dcho
    d.line(P(200,320,190,520),fill=HAIR_HI,width=4*S); d.line(P(452,320,462,520),fill=HAIR_HI,width=4*S)
    d.ellipse(P(222,130,428,370),fill=SKIN)                             # cara
    d.ellipse(P(208,235,240,290),fill=SKIN_SH); d.ellipse(P(410,235,442,290),fill=SKIN_SH)  # orejas
    d.ellipse(P(214,245,232,265),fill=(235,200,80))                     # pendiente
    d.ellipse(P(418,245,436,265),fill=(235,200,80))
    d.chord(P(205,80,445,300),180,360,fill=HAIR)                        # flequillo/coronilla
    d.polygon(P((222,190),(260,150),(330,165),(300,205)),fill=HAIR)     # mechón
    d.polygon(P((330,160),(420,170),(430,215),(380,190)),fill=HAIR)
    d.arc(P(250,110,360,190),200,300,fill=HAIR_HI,width=6*S)
    for cx in (285,365):                                                # cejas arqueadas
        d.arc(P(cx-30,208,cx+28,240),200,340,fill=HAIR,width=7*S)
    for cx in (285,365):
        if eyes:
            d.ellipse(P(cx-24,240,cx+24,276),fill=(255,255,255))
            d.ellipse(P(cx-15,242,cx+15,274),fill=(90,58,40)); d.ellipse(P(cx-8,248,cx+8,266),fill=(20,14,12))
            d.ellipse(P(cx+2,248,cx+8,254),fill=(255,255,255))
            d.arc(P(cx-26,236,cx+26,280),190,350,fill=(30,20,18),width=5*S)
            d.line(P(cx+20,244,cx+30,236),fill=(30,20,18),width=4*S)
        else:
            d.arc(P(cx-24,246,cx+24,274),10,170,fill=(30,20,18),width=5*S)
    d.ellipse(P(252,282,298,312),fill=(245,160,160,150)); d.ellipse(P(352,282,398,312),fill=(245,160,160,150))  # colorete
    d.arc(P(316,268,336,300),300,80,fill=SKIN_SH,width=4*S)              # nariz
    if mouth==0:
        d.chord(P(300,310,352,338),0,180,fill=LIP)
    elif mouth==1:
        d.ellipse(P(302,312,350,340),fill=LIP); d.ellipse(P(310,318,342,334),fill=(110,30,40))
    else:
        d.ellipse(P(300,308,352,354),fill=LIP); d.ellipse(P(308,314,344,348),fill=(110,30,40)); d.chord(P(312,330,340,352),180,360,fill=(220,110,120))
    return h
for m in range(3):
    for e in range(2): save(head(m,e),f"head_m{m}_e{e}.png")
# preview
pv=Image.new("RGBA",(640,820),(236,231,224,255))
for n in ("body.png","arm.png","head_m2_e1.png"): pv.alpha_composite(Image.open("chars/"+n))
pv.convert("RGB").save("chars/preview.png")
