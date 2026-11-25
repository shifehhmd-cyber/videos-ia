"""Anuncio de 15 s de Vanish Oxi Action Gold (nicho hogar/limpieza) con el estilo del vídeo de referencia:
fondo casi negro con brillo marrón, karaoke arriba (palabra clave en cursiva coral), pestañas de pasos y tarjetas UI animadas.
Uso: python3 render.py out_dir"""
import asyncio, math, os, subprocess, sys
import numpy as np, edge_tts
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
PIPE = os.path.join(HERE, "..", "..", "pipeline")
sys.path.insert(0, PIPE); import musiclib
F = lambda n, s: ImageFont.truetype(os.path.join(PIPE, "fonts", n), s)
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "out"); os.makedirs(OUT, exist_ok=True)
W, H, FPS, DUR = 1080, 1920, 30, 15.0
PROXY = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")

CORAL = (233, 124, 92); WHITE = (244, 238, 233); DIM = (110, 96, 90); GREEN = (78, 204, 130)
CARD = (27, 21, 19, 235); BORDER = (58, 45, 40); MUTED = (150, 136, 128); LIGHT = (246, 242, 237)

# ---------- guion: (lo que dice la voz, lo que se ve, ¿palabra clave?)
WORDS = [("¿Manchas", "¿Manchas", 1), ("que", "que", 0), ("ni", "ni", 0), ("a", "a", 0), ("sesenta", "60", 0), ("grados", "grados", 0), ("salen?", "salen?", 0),
         ("Vánish", "Vanish", 1), ("Oxi", "Oxi", 0), ("Ácshon", "Action", 0), ("Gold", "Gold", 1),
         ("las", "las", 0), ("elimina", "elimina", 0), ("a", "a", 0), ("solo", "solo", 0), ("veinte", "20", 1), ("grados.", "grados.", 0),
         ("Recupera", "Recupera", 0), ("el", "el", 0), ("blanco,", "blanco,", 1), ("sin", "sin", 0), ("lejía", "lejía", 1), ("y", "y", 0), ("con", "con", 0), ("antigrises.", "antigrises.", 1),
         ("Tus", "Tus", 0), ("blancos,", "blancos,", 0), ("otra", "otra", 0), ("vez", "vez", 0), ("blancos.", "blancos.", 1),
         ("Pídelo", "Pídelo", 1), ("ahora.", "ahora.", 0)]
SCENES = [0, 7, 11, 17, 25, 30]          # índice de palabra con el que empieza cada escena
CHUNKS = [(0, 3), (3, 7), (7, 11), (11, 15), (15, 17), (17, 20), (20, 22), (22, 25), (25, 27), (27, 30), (30, 32)]


async def tts():
    text = " ".join(w[0] for w in WORDS)
    for _ in range(4):
        try:
            c = edge_tts.Communicate(text, "es-ES-ElviraNeural", rate="+6%", boundary="WordBoundary", proxy=PROXY); wb = []
            with open(f"{OUT}/voz.mp3", "wb") as f:
                async for ch in c.stream():
                    if ch["type"] == "audio": f.write(ch["data"])
                    elif ch["type"] == "WordBoundary": wb.append((ch["offset"] / 1e7, (ch["offset"] + ch["duration"]) / 1e7, ch["text"]))
            if wb: return wb
        except Exception as e: print("retry", e)
    raise SystemExit("edge-tts falló")
WB = asyncio.run(tts())
assert len(WB) == len(WORDS), [w[2] for w in WB]
LEAD = 0.25
T = [(a + LEAD, b + LEAD) for a, b, _ in WB]
print("voz termina en", round(T[-1][1], 2))
SC_T = [T[i][0] - (0.25 if i else LEAD) for i in SCENES] + [DUR]

def sh(*a): subprocess.run(a, check=True)
def lufs(f):
    o = subprocess.run(["ffmpeg", "-hide_banner", "-i", f, "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    return float([l for l in o.splitlines() if l.strip().startswith("I:")][-1].split()[1])
ms = int(LEAD * 1000)
sh("ffmpeg", "-y", "-loglevel", "error", "-i", f"{OUT}/voz.mp3", "-af", f"aresample=44100,adelay={ms}|{ms},apad,atrim=0:{DUR},loudnorm=I=-15:TP=-1.5:LRA=11", "-ac", "2", f"{OUT}/voice.wav")
musiclib.piano(f"{OUT}/music.wav", DUR + 1, 2)
g = lufs(f"{OUT}/voice.wav") - 17 - lufs(f"{OUT}/music.wav")
sh("ffmpeg", "-y", "-loglevel", "error", "-i", f"{OUT}/music.wav", "-af", f"volume={g}dB,atrim=0:{DUR},afade=t=out:st={DUR-1.2}:d=1.2", f"{OUT}/music_n.wav")

# ---------- recursos
def ease(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3
def eob(x):  # ease-out-back
    x = min(max(x, 0), 1); c = 1.6; return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2
yy, xx = np.mgrid[0:H, 0:W]
bg = np.zeros((H, W, 3)) + np.array([9, 6, 5])
glow = np.exp(-(((xx - W * 0.5) / 620) ** 2 + ((yy - H * 0.42) / 900) ** 2))
bg += glow[:, :, None] * np.array([62, 27, 14])
bg += np.random.default_rng(3).normal(0, 1.6, (H, W, 1))
BG = Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8)).convert("RGBA")

src = Image.open(os.path.join(HERE, "producto_src.png")).convert("RGB").crop((262, 700, 918, 1862))
PROD = src

fK = F("Inter-Bold.ttf", 58); fKI = F("Playfair-BoldItalic.ttf", 64)
fSm = F("Inter-Bold.ttf", 26); fMd = F("Inter-Bold.ttf", 36); fLg = F("Inter-ExtraBold.ttf", 44)
fNum = F("Inter-ExtraBold.ttf", 190); fSerifBig = F("Playfair-BoldItalic.ttf", 300); fSerif = F("Playfair-BoldItalic.ttf", 120)
fSerifS = F("Playfair-BoldItalic.ttf", 40); fMono = F("JetBrainsMono.ttf", 24)

def spaced(d, xy, txt, font, fill, sp=3, anchor="l"):
    x, y = xy
    if anchor == "m":
        tot = sum(d.textlength(c, font=font) + sp for c in txt) - sp; x -= tot / 2
    for c in txt: d.text((x, y), c, font=font, fill=fill); x += d.textlength(c, font=font) + sp

def shadow_card(im, box, r=34, fill=CARD, border=BORDER, alpha=1.0, glow=None):
    x0, y0, x1, y1 = [int(v) for v in box]
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle((x0 + 4, y0 + 22, x1 - 4, y1 + 30), r, fill=(0, 0, 0, int(150 * alpha)))
    if glow: d.rounded_rectangle((x0 - 10, y0 - 10, x1 + 10, y1 + 10), r + 10, fill=glow[:3] + (int(glow[3] * alpha),))
    lay = lay.filter(ImageFilter.GaussianBlur(28)); im.alpha_composite(lay)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle((x0, y0, x1, y1), r, fill=fill[:3] + (int(fill[3] * alpha),), outline=border + (int(255 * alpha),) if border else None, width=2)
    im.alpha_composite(lay); return lay

def layer(im, fn, alpha=1.0, dy=0, scale=1.0, cx=W / 2, cy=H / 2, blur=0):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); fn(lay)
    if scale != 1.0:
        s = lay.resize((int(W * scale), int(H * scale)), Image.BICUBIC); lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        lay.alpha_composite(s, (int(cx - cx * scale), int(cy - cy * scale)))
    if blur: lay = lay.filter(ImageFilter.GaussianBlur(blur))
    if dy: lay = lay.transform(lay.size, Image.AFFINE, (1, 0, 0, 0, 1, -dy))
    if alpha < 1: a = lay.getchannel("A").point(lambda v: int(v * alpha)); lay.putalpha(a)
    im.alpha_composite(lay)

def check(d, cx, cy, p, r=22):
    if p <= 0: d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(80, 66, 60), width=3); return
    rr = r * eob(p); d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=GREEN)
    if p > 0.4:
        q = min(1, (p - 0.4) / 0.4); pts = [(cx - 10, cy + 1), (cx - 3, cy + 9), (cx + 11, cy - 8)]
        seg = [pts[0], pts[1]] if q < 0.45 else pts
        d.line(seg, fill=(12, 30, 20), width=5, joint="curve")

def shirt(d, cx, cy, s, col=(236, 232, 226)):
    P = [(-150, -110), (-60, -140), (-30, -120), (30, -120), (60, -140), (150, -110), (200, -30), (130, 0), (115, -30), (115, 150), (-115, 150), (-115, -30), (-130, 0), (-200, -30)]
    d.polygon([(cx + x * s, cy + y * s) for x, y in P], fill=col)
    d.arc((cx - 32 * s, cy - 150 * s, cx + 32 * s, cy - 95 * s), 0, 180, fill=(200, 194, 186), width=max(2, int(4 * s)))

def stain(im, cx, cy, s, a):
    if a <= 0.01: return
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    rng = np.random.default_rng(7)
    for k in range(9):
        ox, oy, rr = rng.uniform(-38, 38) * s, rng.uniform(-30, 30) * s, rng.uniform(18, 36) * s
        d.ellipse((cx + ox - rr, cy + oy - rr, cx + ox + rr, cy + oy + rr), fill=(132, 84, 44, int(210 * a)))
    lay = lay.filter(ImageFilter.GaussianBlur(5 * s)); im.alpha_composite(lay)

# ---------- karaoke superior
def caption(im, t):
    ci = max([i for i, (a, b) in enumerate(CHUNKS) if T[a][0] - 0.12 <= t] or [0])
    a, b = CHUNKS[ci]
    if t > T[b - 1][1] + 0.6 and ci == len(CHUNKS) - 1: return
    d = ImageDraw.Draw(im); parts = []
    for i in range(a, b):
        show, key = WORDS[i][1], WORDS[i][2]; f = fKI if key else fK
        parts.append((show, f, key, i))
    widths = [d.textlength(p[0], font=p[1]) for p in parts]; sp = 18
    x = W / 2 - (sum(widths) + sp * (len(parts) - 1)) / 2; y = 250
    for (s, f, key, i), w in zip(parts, widths):
        spoken = t >= T[i][0] - 0.05
        col = (CORAL if key else WHITE) if spoken else (DIM if not key else (120, 74, 60))
        d.text((x, y), s, font=f, fill=col, anchor="ls"); x += w + sp

# ---------- pestañas de pasos
TABS = ["MANCHA", "LAVADO", "RESULTADO"]
def tabs(im, active, a):
    if a <= 0: return
    d = ImageDraw.Draw(im); ws = [d.textlength(s, font=fSm) + 3 * len(s) + 78 for s in TABS]; gap = 14
    x = W / 2 - (sum(ws) + gap * 2) / 2; y = 360
    for i, (s, w) in enumerate(zip(TABS, ws)):
        on = i == active; done = i < active
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
        dl.rounded_rectangle((x, y, x + w, y + 58), 29, fill=(70, 34, 24, int(255 * a)) if on else (30, 24, 22, int(230 * a)),
                             outline=(CORAL if on else BORDER) + (int(255 * a),), width=2)
        cc = CORAL if on else (GREEN if done else (70, 60, 56))
        dl.ellipse((x + 14, y + 14, x + 44, y + 44), fill=cc + (int(255 * a),))
        dl.text((x + 29, y + 29), "✓" if False else str(i + 1), font=F("Inter-Bold.ttf", 20), fill=(20, 14, 12, int(255 * a)), anchor="mm")
        spaced(dl, (x + 56, y + 15), s, fSm, (WHITE if on else MUTED) + (int(255 * a),), sp=3)
        im.alpha_composite(lay); x += w + gap

# ---------- escenas
def sc_hook(im, t, t0, t1):
    p = ease((t - t0) / 0.45); out = ease((t - (t1 - 0.3)) / 0.3)
    temp = int(20 + 40 * ease((t - t0 - 0.2) / 1.4))
    def f1(lay):
        shadow_card(lay, (130, 520, 950, 860))
        d = ImageDraw.Draw(lay)
        spaced(d, (180, 565), "LAVADORA · PROGRAMA ALGODÓN", fSm, MUTED, sp=3)
        d.rounded_rectangle((760, 556, 905, 600), 22, fill=(60, 24, 22)); d.ellipse((778, 571, 792, 585), fill=(235, 90, 80))
        d.text((802, 578), "Caliente", font=F("Inter-Bold.ttf", 22), fill=(235, 120, 110), anchor="lm")
        d.text((178, 790), str(temp), font=fNum, fill=WHITE, anchor="ls")
        d.text((178 + d.textlength(str(temp), font=fNum) + 8, 700), "°C", font=F("Inter-ExtraBold.ttf", 80), fill=CORAL, anchor="ls")
        # barra
        d.rounded_rectangle((560, 760, 900, 776), 8, fill=(50, 40, 36)); d.rounded_rectangle((560, 760, 560 + 340 * (temp - 20) / 40, 776), 8, fill=CORAL)
        spaced(d, (560, 720), "TEMPERATURA", F("Inter-Bold.ttf", 20), MUTED, sp=3)
    layer(im, f1, alpha=p * (1 - out), dy=(1 - p) * 60)
    p2 = ease((t - t0 - 0.5) / 0.5)
    def f2(lay):
        shadow_card(lay, (130, 900, 950, 1380))
        d = ImageDraw.Draw(lay); shirt(d, 330, 1150, 0.95)
        spaced(d, (560, 960), "PRENDA", fSm, MUTED, sp=3)
        d.text((560, 1000), "Camiseta blanca", font=fMd, fill=WHITE)
        spaced(d, (560, 1090), "ESTADO TRAS LAVAR", fSm, MUTED, sp=3)
        d.rounded_rectangle((560, 1130, 870, 1182), 26, fill=(60, 24, 22)); d.text((715, 1156), "Mancha sigue ahí", font=F("Inter-Bold.ttf", 24), fill=(240, 130, 115), anchor="mm")
        d.rounded_rectangle((560, 1210, 870, 1262), 26, fill=(44, 38, 36)); d.text((715, 1236), "Tono grisáceo", font=F("Inter-Bold.ttf", 24), fill=MUTED, anchor="mm")
    def f2b(lay): f2(lay); stain(lay, 320, 1170, 0.95, 1)
    layer(im, f2b, alpha=p2 * (1 - out), dy=(1 - p2) * 60)

def product_card(lay, box, glow_a=1.0, small=False):
    x0, y0, x1, y1 = box
    shadow_card(lay, box, r=36, fill=LIGHT + (255,), border=None, glow=(233, 124, 92, int(70 * glow_a)))
    pw = x1 - x0 - 60; ph = int(PROD.height * pw / PROD.width)
    if not small: ph = min(ph, int((y1 - y0) * 0.66)); pw = int(PROD.width * ph / PROD.height)
    else: ph = int((y1 - y0) - 40); pw = int(PROD.width * ph / PROD.height)
    im2 = PROD.resize((pw, ph), Image.LANCZOS).convert("RGBA")
    m = Image.new("L", (pw, ph), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, pw - 1, ph - 1), 24, fill=255); im2.putalpha(m)
    px = int((x0 + x1) / 2 - pw / 2) if not small else x0 + 20
    lay.alpha_composite(im2, (px, y0 + 22))
    return ph

def sc_product(im, t, t0, t1):
    p = eob((t - t0) / 0.55); a = ease((t - t0) / 0.3); out = ease((t - (t1 - 0.25)) / 0.25)
    def f(lay):
        box = (200, 470, 880, 1500); ph = product_card(lay, box)
        d = ImageDraw.Draw(lay); y = 470 + 22 + ph + 34
        d.rounded_rectangle((240, y, 420, y + 40), 20, fill=(226, 240, 230)); d.ellipse((256, y + 14, 268, y + 26), fill=(40, 160, 90))
        d.text((278, y + 20), "Ropa blanca", font=F("Inter-Bold.ttf", 21), fill=(30, 110, 60), anchor="lm")
        d.text((240, y + 62), "Vanish Oxi Action Gold", font=fLg, fill=(26, 20, 18))
        d.text((240, y + 120), "Gel concentrado · 690 ml · sin lejía", font=F("Inter-Bold.ttf", 26), fill=(130, 118, 110))
    layer(im, f, alpha=a * (1 - out), scale=0.85 + 0.15 * p, cx=540, cy=985)

def sc_20(im, t, t0, t1):
    a = ease((t - t0) / 0.35); out = ease((t - (t1 - 0.25)) / 0.25)
    k = ease((t - t0 - 0.2) / 1.3); temp = int(round(60 - 40 * k))
    def f(lay):
        d = ImageDraw.Draw(lay)
        tw = d.textlength(str(temp), font=fSerifBig)
        d.text((W / 2 - 40, 830), str(temp), font=fSerifBig, fill=CORAL, anchor="ms")
        d.text((W / 2 - 40 + tw / 2 - 5, 700), "°C", font=F("Playfair-BoldItalic.ttf", 110), fill=CORAL, anchor="ls")
        spaced(d, (W / 2, 875), "ELIMINA MANCHAS · LAVADO EN FRÍO", fSm, MUTED, sp=4, anchor="m")
        shadow_card(lay, (170, 960, 910, 1420))
        d = ImageDraw.Draw(lay); shirt(d, 370, 1210, 0.82, col=(236 + int(14 * k), 232 + int(18 * k), 226 + int(24 * k)))
        spaced(d, (590, 1010), "MANCHA", fSm, MUTED, sp=3)
        d.text((590, 1050), "Eliminando…" if k < 1 else "Eliminada", font=fMd, fill=WHITE if k < 1 else GREEN)
        d.rounded_rectangle((590, 1130, 860, 1146), 8, fill=(50, 40, 36)); d.rounded_rectangle((590, 1130, 590 + 270 * k, 1146), 8, fill=GREEN)
        spaced(d, (590, 1190), "TEMPERATURA", fSm, MUTED, sp=3)
        d.text((590, 1230), f"{temp} °C", font=fMd, fill=WHITE)
    def g(lay): f(lay); stain(lay, 360, 1225, 0.8, 1 - k)
    layer(im, g, alpha=a * (1 - out), dy=(1 - a) * 50)

ROWS = [("01", "Recupera el blanco", "Blancos que vuelven a ser blancos", 19), ("02", "Sin lejía", "Blanqueador para ropa blanca", 21), ("03", "+ Anti-grises", "Adiós al tono apagado", 24)]
def sc_list(im, t, t0, t1):
    out = ease((t - (t1 - 0.25)) / 0.25)
    for j, (n, ti, sub, wi) in enumerate(ROWS):
        ts = T[wi - (2 if j == 0 else 1)][0] - 0.15; a = ease((t - ts) / 0.35)
        if a <= 0: continue
        pc = (t - T[wi][0]) / 0.45
        def f(lay, j=j, n=n, ti=ti, sub=sub, pc=pc):
            y = 560 + j * 190
            shadow_card(lay, (110, y, 970, y + 150), r=28)
            d = ImageDraw.Draw(lay); d.text((150, y + 75), n, font=F("Playfair-BoldItalic.ttf", 54), fill=CORAL, anchor="lm")
            d.text((250, y + 50), ti, font=F("Inter-Bold.ttf", 40), fill=WHITE, anchor="lm")
            d.text((250, y + 100), sub, font=F("Inter-Bold.ttf", 24), fill=MUTED, anchor="lm")
            check(d, 910, y + 75, pc)
        layer(im, f, alpha=a * (1 - out), dy=(1 - a) * 40)
    a2 = ease((t - T[24][1]) / 0.4)
    if a2 > 0:
        def g(lay):
            shadow_card(lay, (110, 1150, 970, 1270), r=28); d = ImageDraw.Draw(lay)
            spaced(d, (150, 1180), "RESULTADO", F("Inter-Bold.ttf", 20), MUTED, sp=3)
            d.text((150, 1215), "Blanco ", font=F("Inter-Bold.ttf", 32), fill=WHITE)
            d.text((150 + d.textlength("Blanco ", font=F("Inter-Bold.ttf", 32)), 1212), "recuperado", font=F("Playfair-BoldItalic.ttf", 36), fill=GREEN)
            q = ease((t - T[24][1]) / 0.8); pts = [(600 + i * 34, 1240 - 60 * (i / 10) ** 1.4 - 6 * math.sin(i)) for i in range(11)]
            n = max(2, int(len(pts) * q)); d.line(pts[:n], fill=GREEN, width=4, joint="curve")
        layer(im, g, alpha=a2 * (1 - out), dy=(1 - a2) * 30)

def sc_compare(im, t, t0, t1):
    a = ease((t - t0) / 0.35); out = ease((t - (t1 - 0.2)) / 0.2); k = ease((t - t0 - 0.35) / 1.0)
    def f(lay):
        shadow_card(lay, (110, 520, 970, 1360)); d = ImageDraw.Draw(lay)
        spaced(d, (160, 570), "RESULTADO · ROPA BLANCA", fSm, MUTED, sp=3)
        d.rounded_rectangle((805, 560, 925, 602), 21, fill=(24, 60, 40)); d.text((865, 581), "Listo", font=F("Inter-Bold.ttf", 22), fill=GREEN, anchor="mm")
        # antes / después con barrido
        bx0, by0, bx1, by1 = 160, 640, 920, 1180
        d.rounded_rectangle((bx0, by0, bx1, by1), 26, fill=(40, 33, 30))
        cut = bx0 + (bx1 - bx0) * (1 - k)
        before = Image.new("RGBA", (W, H), (0, 0, 0, 0)); db = ImageDraw.Draw(before); shirt(db, 540, 930, 1.35, col=(176, 170, 160))
        after = Image.new("RGBA", (W, H), (0, 0, 0, 0)); da = ImageDraw.Draw(after); shirt(da, 540, 930, 1.35, col=(252, 252, 255))
        m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).rectangle((cut, 0, W, H), fill=255)
        lay.alpha_composite(before); after.putalpha(Image.composite(after.getchannel("A"), Image.new("L", (W, H), 0), m)); lay.alpha_composite(after)
        d.line((cut, by0 + 10, cut, by1 - 10), fill=CORAL, width=4); d.ellipse((cut - 16, (by0 + by1) / 2 - 16, cut + 16, (by0 + by1) / 2 + 16), fill=CORAL)
        d.text((190, 1150), "Antes", font=fSerifS, fill=MUTED, anchor="ls"); d.text((890, 1150), "Después", font=fSerifS, fill=WHITE, anchor="rs")
        d.text((160, 1250), "Tus blancos,", font=F("Inter-Bold.ttf", 44), fill=WHITE, anchor="ls")
        d.text((160 + d.textlength("Tus blancos, ", font=F("Inter-Bold.ttf", 44)), 1252), "otra vez blancos", font=F("Playfair-BoldItalic.ttf", 50), fill=CORAL, anchor="ls")
    layer(im, f, alpha=a * (1 - out), dy=(1 - a) * 50)

def sc_cta(im, t, t0, t1):
    a = ease((t - t0) / 0.4)
    def f(lay):
        d = ImageDraw.Draw(lay)
        d.text((W / 2, 700), "Pídelo ahora", font=fSerif, fill=CORAL, anchor="ms")
        d.text((W / 2, 770), "y recupera el blanco de tu ropa", font=F("Playfair-BoldItalic.ttf", 40), fill=WHITE, anchor="ms")
        box = (150, 860, 930, 1110)
        shadow_card(lay, box, r=30, fill=LIGHT + (255,), border=None)
        product_card_small(lay, box)
    layer(im, f, alpha=a, dy=(1 - a) * 50)
    # botón + cursor
    b = ease((t - t0 - 0.5) / 0.4)
    if b > 0:
        press = t > T[-1][1] + 0.05; s = 0.96 if (press and t < T[-1][1] + 0.25) else 1.0
        def g(lay):
            d = ImageDraw.Draw(lay); cx, cy = W / 2, 1270; w, h = 300 * s, 54 * s
            d.rounded_rectangle((cx - w, cy - h, cx + w, cy + h), int(h), fill=CORAL)
            d.text((cx, cy), "Comprar ahora", font=F("Inter-ExtraBold.ttf", int(42 * s)), fill=(255, 250, 246), anchor="mm")
            q = ease((t - t0 - 0.7) / 0.6); mx, my = 760 - 150 * q, 1460 - 150 * q
            d.polygon([(mx, my), (mx, my + 52), (mx + 13, my + 40), (mx + 24, my + 62), (mx + 33, my + 58), (mx + 22, my + 36), (mx + 40, my + 36)], fill=WHITE, outline=(20, 14, 12))
            if press:
                r = 20 + 80 * ease((t - T[-1][1]) / 0.5); al = int(160 * (1 - ease((t - T[-1][1]) / 0.5)))
                d.ellipse((mx - r, my - r, mx + r, my + r), outline=(255, 255, 255, al), width=4)
            spaced(d, (W / 2, 1390), "ENLACE EN LA BIO", fSm, MUTED, sp=4, anchor="m")
        layer(im, g, alpha=b, dy=(1 - b) * 30)

def product_card_small(lay, box):
    x0, y0, x1, y1 = box; ph = y1 - y0 - 40; pw = int(PROD.width * ph / PROD.height)
    p = PROD.resize((pw, ph), Image.LANCZOS).convert("RGBA"); lay.alpha_composite(p, (x0 + 24, y0 + 20))
    d = ImageDraw.Draw(lay); tx = x0 + 24 + pw + 30
    d.text((tx, y0 + 60), "Vanish Oxi Action", font=F("Inter-ExtraBold.ttf", 38), fill=(26, 20, 18))
    d.text((tx, y0 + 108), "Gold · 690 ml", font=F("Inter-ExtraBold.ttf", 38), fill=(26, 20, 18))
    d.text((tx, y0 + 168), "Elimina manchas a 20 °C", font=F("Inter-Bold.ttf", 26), fill=(130, 118, 110))

SCN = [sc_hook, sc_product, sc_20, sc_list, sc_compare, sc_cta]
TAB = [0, 0, 1, 2, 2, 2]

ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                       "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", f"{OUT}/video_noaudio.mp4"], stdin=subprocess.PIPE)
for fi in range(int(DUR * FPS)):
    t = fi / FPS; si = max(i for i in range(len(SCN)) if SC_T[i] <= t or i == 0)
    im = BG.copy()
    tabs(im, TAB[si], ease((t - SC_T[1]) / 0.4) * (1 - ease((t - SC_T[5]) / 0.3)))
    SCN[si](im, t, SC_T[si], SC_T[si + 1])
    caption(im, t)
    if t < 0.15: im = Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 255)), im, t / 0.15)
    ff.stdin.write(im.convert("RGB").tobytes())
ff.stdin.close(); ff.wait()
sh("ffmpeg", "-y", "-loglevel", "error", "-i", f"{OUT}/video_noaudio.mp4", "-i", f"{OUT}/voice.wav", "-i", f"{OUT}/music_n.wav", "-filter_complex",
   "[1:a][2:a]amix=inputs=2:normalize=0,alimiter=limit=0.89[a]", "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", str(DUR), "-movflags", "+faststart", f"{OUT}/final.mp4")
ims = []
for i in range(len(SCN)):
    tt = SC_T[i + 1] - 0.4
    sh("ffmpeg", "-y", "-loglevel", "error", "-ss", f"{tt:.2f}", "-i", f"{OUT}/final.mp4", "-frames:v", "1", "-vf", "scale=360:640", f"{OUT}/_f.png"); ims.append(Image.open(f"{OUT}/_f.png").copy())
sheet = Image.new("RGB", (360 * 3, 640 * 2))
for i, x in enumerate(ims): sheet.paste(x, ((i % 3) * 360, (i // 3) * 640))
sheet.save(f"{OUT}/check_sheet.png")
print("OK escenas", [round(x, 2) for x in SC_T], "voz", lufs(f"{OUT}/voice.wav"), "música", lufs(f"{OUT}/music_n.wav"))
