# Playbook diario — vídeos virales con IA

Este documento es lo que sigue la tarea programada cada día. Todo se hace sin intervención.

## Cuentas (PostOnce)

| Plataforma | Cuenta | account_id |
|---|---|---|
| YouTube (Shorts) | Radar IA | `051cb7f1-166c-4e6d-9da8-f802c7455b2c` |
| Instagram (Reels) | jellyfish.452834 | `648ed7a5-214b-4e1f-91a5-7b9f43754136` |
| TikTok | OUTFIT INSPO | `a80179b5-d91d-4c96-8a1a-289a94d559a9` |

Si `mcp__PostOnce__list_accounts` muestra otros IDs o alguna cuenta inactiva, usar los nuevos y anotarlo en `log/`.

## Horarios (hora de España, Europe/Madrid)

- **Instagram Reels**: 13:00 entre semana, 12:00 fines de semana.
- **TikTok**: 19:30 (L-V), 18:00 (S-D).
- **YouTube Shorts**: 20:30 todos los días.

Programar siempre con `publish_at` en ISO-8601 con el desfase correcto
(invierno CET = `+01:00`, verano CEST = `+02:00`). Si al ejecutar ya pasó una franja,
usar la siguiente hora en punto disponible del mismo día.

## Paso 1 — Buscar un nicho viral (10 min máx.)

1. `WebSearch` (modo standard) de tendencias del día: p. ej.
   "tendencias TikTok hoy España", "trending Reels this week", "noticias IA hoy".
2. Elegir **un** tema que cumpla:
   - Encaja en formato *faceless* de texto + imágenes (curiosidades, misterios, noticias de IA,
     datos de historia/espacio/animales, psicología, "cosas que no sabías de X", top 3/5).
   - Es verificable: los datos deben salir de fuentes fiables. **Nunca inventar datos.**
   - No repetir un tema de los últimos 14 días (ver `log/`).
   - Nada de marcas, personas reales en situaciones falsas, salud/finanzas como consejo, ni política.
3. Rotación sugerida si no hay nada claro: Lunes IA/tecnología · Martes misterios ·
   Miércoles animales · Jueves espacio · Viernes psicología · Sábado historia · Domingo top 5.

## Paso 2 — Guion

- 4-6 diapositivas + CTA, total 14-25 s. Primera frase = **gancho** (pregunta o dato chocante).
- Máx. ~90 caracteres por diapositiva. Palabras clave entre `*asteriscos*` (se resaltan).
- Sin emojis en el texto del vídeo (la fuente no los dibuja); en los pies de texto sí.
- Guardar en `content/AAAA-MM-DD/spec.json` (formato en `pipeline/example_spec.json`).

## Paso 3 — Imágenes (Runway)

- 3 imágenes por vídeo con `mcp__Runway__generate_image`, `model: "p-image-ideogram"`,
  `ratio: "9:16"`, `imageSize: "1K"` (2 créditos/imagen). Prompt en inglés, fotográfico,
  terminar con "no text". Reutilizar imágenes entre diapositivas.
- Esperar con `mcp__Runway__get_task` hasta `SUCCEEDED`. **No descargar con curl** (el CDN de Runway
  está bloqueado por la red): el resultado de `get_task` incluye una línea
  `[Image: source: /root/.claude/projects/.../tool-results/mcp-Runway-blob-XXXX.jpg]`;
  copiar ese archivo con `cp` a `content/AAAA-MM-DD/imgN.jpg`.
- Si Runway falla o no quedan créditos: seguir sin imágenes (el script usa degradados) y anotarlo.

## Paso 4 — Renderizar

```bash
python3 pipeline/make_video.py content/AAAA-MM-DD/spec.json content/AAAA-MM-DD/video.mp4
```

Comprobar un fotograma con `ffmpeg -ss 2 -i video.mp4 -frames:v 1 f.png` y mirarlo con Read.
Los `.mp4` / `.png` / `.jpg` no se suben a git (ver `.gitignore`).

## Paso 5 — Subir y programar (PostOnce)

1. `mcp__PostOnce__create_upload_url` (video/mp4) → `curl -X PUT -H "Content-Type: video/mp4" --data-binary @video.mp4 "<signedUrl>"`.
   Igual con la portada (`image/jpeg`).
2. Con la `media_id` de cada subida, obtener la URL pública (`mcp__PostOnce__get_media`).
3. Crear **tres posts separados** con `mcp__PostOnce__create_post` (uno por cuenta y hora),
   `platform_options: {"ai_generated": true}` y `idempotency_key` = `AAAA-MM-DD-<plataforma>`.
   - YouTube: `title` (≤ 70 car., con gancho + `#shorts`) en `platform_options.title`; descripción con 3-5 hashtags.
   - Instagram: pie con gancho + pregunta para comentarios + 5-10 hashtags en español.
   - TikTok: pie corto + **máx. 5 hashtags**.
4. Verificar con `mcp__PostOnce__get_post` que quedan en `scheduled`.

### Si PostOnce rechaza la publicación (prueba gratuita agotada u otro bloqueo)

Desde el 25-11 la prueba gratuita de PostOnce (10 posts) está agotada. Antes de crear posts, comprobar con
`mcp__PostOnce__list_posts` si los últimos posts quedaron en `paused` con el error de "free trial".
Si sigue bloqueado: no crear posts nuevos; renderizar igualmente el vídeo y enviárselo al usuario con
`SendUserFile` junto con los pies de texto listos para copiar (Instagram, TikTok, YouTube) y las horas
recomendadas, para que lo suba a mano. Anotarlo en el log.

## Paso 6 — Registro

Añadir `log/AAAA-MM-DD.md` con: tema, fuentes, IDs de los posts, horas, créditos Runway restantes
y cualquier problema. Revisar ayer con `mcp__PostOnce__get_post_analytics` si hay datos y anotar
qué funcionó, para elegir mejor el tema de hoy. Hacer commit y push a la rama de trabajo.
