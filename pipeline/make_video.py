#!/usr/bin/env python3
"""Genera un vídeo vertical 1080x1920 (Reel / Short / TikTok) a partir de un guion JSON.

Uso:
    python3 pipeline/make_video.py ruta/al/spec.json salida.mp4

Formato del spec (ver pipeline/example_spec.json):
{
  "series": "DATOS QUE NO SABÍAS",          # etiqueta pequeña arriba (opcional)
  "accent": "#FFD400",                       # color de las palabras *resaltadas*
  "slides": [
    {"text": "El *pulpo* tiene tres corazones", "image": "img1.png", "dur": 3.5},
    ...
  ],
  "cta": "Sígueme para más 👀"              # se añade como última diapositiva (opcional)
}

Las palabras entre *asteriscos* se pintan con el color de acento.
Las imágenes pueden faltar: entonces se usa un fondo degradado.
No necesita red: solo ffmpeg y Pillow.
"""
import json
import math
import os
import random
import shutil
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1920
FPS = 30
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr[-3000:])
        raise SystemExit(f"Falló: {' '.join(cmd[:6])}...")


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def cover(img, w, h):
    img = img.convert("RGB")
    s = max(w / img.width, h / img.height)
    img = img.resize((math.ceil(img.width * s), math.ceil(img.height * s)), Image.LANCZOS)
    x, y = (img.width - w) // 2, (img.height - h) // 2
    return img.crop((x, y, x + w, y + h))


def gradient_bg(seed):
    rnd = random.Random(seed)
    palettes = [((20, 20, 40), (90, 20, 120)), ((10, 30, 50), (0, 120, 140)),
                ((40, 10, 10), (160, 60, 20)), ((5, 5, 5), (60, 60, 80))]
    a, b = rnd.choice(palettes)
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3)))
    return img


def parse_words(text):
    """Devuelve lista de (palabra, resaltada)."""
    out, hl = [], False
    for tok in text.split():
        # el asterisco de apertura va al inicio de la palabra; el de cierre puede
        # ir seguido de puntuación ("*espacio*..." o "*tun*:")
        if tok.startswith("*") or tok.lstrip("\"'¿¡(").startswith("*"):
            hl = True
        closes = "*" in tok.lstrip("\"'¿¡(")[1:]
        out.append((tok.replace("*", ""), hl))
        if closes:
            hl = False
    return out


def wrap(words, font, maxw, draw):
    lines, cur = [], []
    for w in words:
        trial = " ".join(x for x, _ in cur + [w])
        if cur and draw.textlength(trial, font=font) > maxw:
            lines.append(cur)
            cur = [w]
        else:
            cur.append(w)
    if cur:
        lines.append(cur)
    return lines


def text_overlay(text, series, accent, idx, total):
    """PNG transparente con el texto centrado en una caja semitransparente."""
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    words = parse_words(text)
    size = 86 if len(text) < 60 else 72 if len(text) < 110 else 60
    font = ImageFont.truetype(FONT_BOLD, size)
    maxw = W - 160
    lines = wrap(words, font, maxw, d)
    lh = int(size * 1.25)
    block_h = lh * len(lines)
    top = int(H * 0.56) - block_h // 2
    widest = max(d.textlength(" ".join(w for w, _ in ln), font=font) for ln in lines)
    pad = 44
    box = [W / 2 - widest / 2 - pad, top - pad, W / 2 + widest / 2 + pad, top + block_h + pad - 10]
    d.rounded_rectangle(box, radius=36, fill=(0, 0, 0, 165))
    acc = hex_rgb(accent) + (255,)
    space = d.textlength(" ", font=font)
    for i, ln in enumerate(lines):
        lw = d.textlength(" ".join(w for w, _ in ln), font=font)
        x = W / 2 - lw / 2
        y = top + i * lh
        for w, hl in ln:
            d.text((x, y), w, font=font, fill=acc if hl else (255, 255, 255, 255),
                   stroke_width=3, stroke_fill=(0, 0, 0, 255))
            x += d.textlength(w, font=font) + space
    if series:
        sf = ImageFont.truetype(FONT_BOLD, 40)
        label = f"{series}  ·  {idx}/{total}"
        tw = d.textlength(label, font=sf)
        d.rounded_rectangle([W / 2 - tw / 2 - 28, 150, W / 2 + tw / 2 + 28, 222], radius=30, fill=acc)
        d.text((W / 2 - tw / 2, 162), label, font=sf, fill=(0, 0, 0, 255))
    return ov


def make_audio(path, dur, seed, n_slides):
    """Pad ambiental sintetizado + 'whoosh' suave en cada cambio de diapositiva."""
    rnd = random.Random(seed)
    roots = [110.0, 98.0, 130.81, 123.47, 146.83]
    r = rnd.choice(roots)
    chord = [r, r * 1.2599, r * 1.4983, r * 2]  # acorde mayor + octava
    expr = "+".join(f"0.08*sin(2*PI*{f:.2f}*t)*(0.6+0.4*sin(2*PI*0.{i+2}*t))" for i, f in enumerate(chord))
    # pulso de bajo cada ~0.5s para dar ritmo
    expr += f"+0.10*sin(2*PI*{r/2:.2f}*t)*exp(-6*mod(t,0.5))"
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
         f"aevalsrc='{expr}':s=44100:d={dur}",
         "-af", f"afade=t=in:d=1,afade=t=out:st={max(dur-1.5,0)}:d=1.5,lowpass=f=2500,volume=1.4",
         "-c:a", "aac", "-b:a", "160k", path])


def build(spec, out):
    tmp = tempfile.mkdtemp(prefix="mkvid_")
    base_dir = os.path.dirname(os.path.abspath(spec["_path"]))
    accent = spec.get("accent", "#FFD400")
    slides = list(spec["slides"])
    if spec.get("cta"):
        slides.append({"text": spec["cta"], "image": slides[0].get("image"), "dur": 2.5})
    total = len(slides)
    segs = []
    for i, s in enumerate(slides):
        dur = float(s.get("dur", 3.5))
        img_path = s.get("image")
        if img_path and not os.path.isabs(img_path):
            img_path = os.path.join(base_dir, img_path)
        if img_path and os.path.exists(img_path):
            bg = cover(Image.open(img_path), int(W * 1.15), int(H * 1.15))
        else:
            bg = gradient_bg(i).resize((int(W * 1.15), int(H * 1.15)))
        # oscurece un poco para legibilidad
        bg = Image.blend(bg, Image.new("RGB", bg.size, (0, 0, 0)), 0.18)
        bgp = os.path.join(tmp, f"bg{i}.png")
        bg.save(bgp)
        ovp = os.path.join(tmp, f"ov{i}.png")
        text_overlay(s["text"], spec.get("series"), accent, i + 1, total).save(ovp)
        frames = int(dur * FPS)
        zin = i % 2 == 0
        z = f"'1+0.0009*on'" if zin else f"'1.13-0.0009*on'"
        seg = os.path.join(tmp, f"seg{i}.mp4")
        fade_out = max(dur - 0.25, 0)
        run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", bgp, "-loop", "1", "-i", ovp,
             "-filter_complex",
             f"[0:v]zoompan=z={z}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={FPS}[bg];"
             f"[1:v]format=rgba,fade=t=in:st=0:d=0.3:alpha=1[ov];"
             f"[bg][ov]overlay=0:0:shortest=1,fade=t=in:st=0:d=0.2,fade=t=out:st={fade_out}:d=0.25,format=yuv420p[v]",
             "-map", "[v]", "-t", str(dur), "-r", str(FPS), "-c:v", "libx264", "-preset", "veryfast",
             "-crf", "20", seg])
        segs.append((seg, dur))
    lst = os.path.join(tmp, "list.txt")
    with open(lst, "w") as f:
        for seg, _ in segs:
            f.write(f"file '{seg}'\n")
    total_dur = sum(d for _, d in segs)
    joined = os.path.join(tmp, "joined.mp4")
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", joined])
    audio = os.path.join(tmp, "a.m4a")
    make_audio(audio, total_dur, spec.get("seed", 1), total)
    ar, ag, ab = hex_rgb(accent)
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", joined, "-i", audio,
         "-f", "lavfi", "-i", f"color=c=0x{ar:02x}{ag:02x}{ab:02x}:s={W}x14:r={FPS}",
         "-filter_complex",
         f"[0:v]drawbox=x=0:y=ih-14:w=iw:h=14:color=black@0.5:t=fill[b];"
         f"[b][2:v]overlay=x='-W+W*t/{total_dur:.3f}':y=H-14:shortest=1[v]",
         "-map", "[v]", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
         "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", "-shortest", out])
    # portada (primer fotograma con texto, ~1s)
    cover_path = os.path.splitext(out)[0] + "_cover.jpg"
    run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "1.0", "-i", out, "-frames:v", "1", "-q:v", "3", cover_path])
    shutil.rmtree(tmp, ignore_errors=True)
    print(json.dumps({"video": out, "cover": cover_path, "duration": round(total_dur, 2),
                      "size_bytes": os.path.getsize(out)}))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    with open(sys.argv[1]) as f:
        spec = json.load(f)
    spec["_path"] = sys.argv[1]
    build(spec, sys.argv[2])
