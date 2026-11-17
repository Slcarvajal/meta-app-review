# meta-app-review

> **English:** an agent skill (Claude Code, Codex, any Agent Skills client) that walks you through Meta's App Review to get advanced access, for Facebook Login for Business (ads, pages) and Instagram Login (comments, messages, insights, publishing). The guide is in Spanish; every text you paste into Meta's form is in English. Install: `git clone https://github.com/Slcarvajal/meta-app-review ~/.claude/skills/meta-app-review`.

Una skill para que tu agente (Claude Code, Codex o cualquiera que lea Agent
Skills) te lleve por el App Review de Meta: pedir acceso avanzado para que
tus clientes conecten sus cuentas de anuncios o de Instagram a tu app.

Sale de dos revisiones reales de noviembre de 2026: una app de anuncios
(Facebook Login for Business) y una app de Instagram (comentarios, mensajes,
métricas y publicar).

## Qué hace

1. **Te dice si necesitas App Review** y qué ruta te toca.
2. **Abre el formulario el día 1**, para que veas todos los requisitos antes
   de construir (el error que más rondas cuesta).
3. **Revisa tu token y tu panel:** de qué app es, qué permisos tienes y
   cuántas llamadas tiene cada uno.
4. **Te guía en el código** del flujo de conexión y en las páginas públicas
   que Meta revisa.
5. **Llena el panel** (URLs, configuración, textos en inglés por permiso).
6. **Prepara la grabación:** una carpeta con los archivos y un guion paso a
   paso. Tú grabas.
7. **Arma los videos** con `video.py`: corta, tapa lo privado, une y pone
   subtítulos en inglés.
8. **Llena el formulario.** Tú marcas las declaraciones y das "Enviar".

## Instalar

Clona este repo en la carpeta de skills de tu agente:

```bash
# Claude Code
git clone https://github.com/Slcarvajal/meta-app-review ~/.claude/skills/meta-app-review
# Codex y otros agentes con Agent Skills
git clone https://github.com/Slcarvajal/meta-app-review ~/.agents/skills/meta-app-review
```

Después pídele a tu agente: "ayúdame con el App Review de Meta".

Para los videos necesitas Python 3.10 o más nuevo y `ffmpeg` con libass:
`brew install ffmpeg` (macOS), `sudo apt install ffmpeg` (Ubuntu/Debian) o
el build de gyan.dev (Windows).

## Archivos

| Archivo | Qué es |
|---|---|
| `SKILL.md` | La guía que lee el agente: orden, quién hace qué, trampas. |
| `referencia.md` | Lista del panel, textos en inglés por permiso, instrucciones para revisores, guiones y un `spec.json` de ejemplo. |
| `video.py` | Hojas de contacto, cuadros sueltos y armado de screencasts con subtítulos. Solo usa la librería estándar y ffmpeg. Nunca sube nada. |
| `test_video.py` | Tests de `video.py` (`python3 -m pytest test_video.py`). |
| `LICENSE` | MIT. |

## Límites

- Meta cambia el panel seguido. El panel se leyó el 2026-11-15 y la
  documentación de Meta se contrastó el 2026-11-16 (fuentes en
  `referencia.md`). El panel en vivo manda.
- Las declaraciones legales, la grabación, la llave secreta y el envío son
  tuyos. El agente solo marca una declaración si le dices "sí, márcalas", y
  nunca escribe contraseñas ni lee llaves.
- No es asesoría legal ni garantiza la aprobación.
