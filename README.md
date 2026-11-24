# videos-ia

Pipeline automático de vídeos cortos (Reels / Shorts / TikTok) con IA:

1. Busca un nicho/tema en tendencia.
2. Escribe un guion corto con gancho.
3. Genera imágenes de fondo con IA (Runway).
4. Monta el vídeo vertical 1080x1920 con texto animado, barra de progreso y música sintetizada (`pipeline/make_video.py`).
5. Lo sube y programa en Instagram, YouTube y TikTok a la hora de más actividad (PostOnce).

El procedimiento completo está en [PLAYBOOK.md](PLAYBOOK.md). Cada día se guarda el guion en `content/` y un registro en `log/`.

Requisitos locales: `ffmpeg` y `Pillow`.
