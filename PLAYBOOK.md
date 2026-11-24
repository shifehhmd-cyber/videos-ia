# Playbook del vídeo viral diario (lo sigue la tarea programada)

Todo en español. Sin gastar dinero ni créditos de pago (nada de Runway, Canva, Picsart, vidIQ, TinyFish de pago, etc.). Si algo falla, buscar otra vía gratis y seguir.

## 1. Tema
- WebSearch (mode "extended") de tendencias virales de los últimos días en TikTok / Reels / Shorts en español (que.es, metricool, elDiario, xataka, etc.).
- Elegir el de más potencial que se pueda contar SIN cara ni voz real y sin material con copyright (nada de clips de juegos, canciones o personas reales).
- No repetir nada de `temas_usados.md`.
- Comprobar 2-3 datos concretos del tema con búsquedas (no inventar cifras).

## 2. Vídeo
- Carpeta `reels/AAAA-MM-DD-slug/`. Escribir `bgs.py` con 3-4 fondos ilustrados 1200x2134 acordes al tema (ver ejemplos en `reels/2026-11-24-brain-stacking/bgs.py`). Dejar la zona central (y≈35-50%) sin detalles claros para que el texto se lea.
- Escribir `spec.json` (ver formato en `pipeline/make_video.py` y el ejemplo de brain stacking): 8-12 tarjetas, 20-40 s. Tarjeta 1 = gancho fuerte (pregunta o dato chocante en <2 s). Final con CTA (guárdalo / comenta / compártelo). Palabras en inglés: escribirlas fonéticamente en "say" y bien en "show". `music_seed` distinto cada día (día del año % 4 o similar). `band` 150-170 si hay fondos claros.
- `pip install edge-tts` si falta. Render: `python3 pipeline/make_video.py spec.json out` (usa el proxy http://127.0.0.1:41863; el host speech.platform.bing.com está permitido en el entorno "videos-ia"). Si edge-tts falla, NO usar voz robótica: reintentar y, si sigue fallando, informar en el resumen.
- Revisar `out/check_sheet.png` (leer la imagen): texto legible, cajas bien, sin cortes. Corregir y re-renderizar si hace falta. Comprobar que voz ≈ -15 LUFS y música ≈ -33 LUFS (lo imprime el script).
- Copiar `out/final.mp4` a `reel_<slug>.mp4`; portada `cover.jpg` (fotograma ~1.5 s). No subir a git la carpeta out/ (sí spec, bgs, mp4 final).

## 3. Publicación (PostOnce)
- Cuentas (comprobar con list_accounts): TikTok a80179b5-d91d-4c96-8a1a-289a94d559a9, Instagram 648ed7a5-214b-4e1f-91a5-7b9f43754136, YouTube 051cb7f1-166c-4e6d-9da8-f802c7455b2c.
- create_upload_url (vídeo y portada) → PUT con curl `--data-binary` y Content-Type → get_media para la URL pública.
- Horas (Europe/Madrid; convertir a UTC: CET = UTC+1 hasta el 29-mar-2027, luego CEST = UTC+2). Referencia de estudios para España: TikTok picos 13-15 h y 18-21 h; Instagram Reels 10 h y 15 h (mar/mié mejores); YouTube Shorts tarde 18-20 h. Por defecto: Instagram 13:00, TikTok 19:00, YouTube 20:00; ajustar si la búsqueda del día da otra cosa. Siempre en el futuro.
- Un create_post por red, `ai_generated: true` en platform_options, idempotency_key `<slug>-<fecha>-<red>`.
  - TikTok: texto corto + gancho + máx 5 hashtags; `video_cover_timestamp_ms`.
  - Instagram: texto más largo con emojis y 8-15 hashtags; thumbnail_url.
  - YouTube: platform_options.title (<100 caracteres, con #shorts) y descripción con 3-5 hashtags.

## 4. Cierre
- Añadir fila a `temas_usados.md`, commit y push a la rama `claude/motivational-reel-year-end-gf64bs`.
- Resumen final corto en español: tema, por qué, horas de publicación por red, IDs de los posts de PostOnce y enlace al vídeo (URL pública del mp4). Si alguna red da error, decirlo.
