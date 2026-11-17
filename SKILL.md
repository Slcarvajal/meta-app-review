---
name: meta-app-review
description: Guía de punta a punta para sacar una app en Meta pidiendo acceso avanzado en el App Review (Facebook Login for Business con ads_read, ads_management, business_management, pages_*, Marketing API Access Tier; o Instagram API con Instagram Login con instagram_business_basic, manage_comments, manage_messages, manage_insights, content_publish). Diagnóstico, flujo de conexión, panel de Meta, llamada de prueba, grabación, armado de screencasts con subtítulos (video.py) y formulario, con lo que hace el agente, lo que hace la persona y las trampas que hacen rechazar. Úsala cuando alguien diga "app review", "revisión de la app", "acceso avanzado", "advanced access", "permisos de Meta", "permisos de Instagram", "que mis clientes conecten su cuenta", "Facebook Login for Business", "Instagram Login", "screencast para Meta" o "Meta me rechazó la app".
---

# meta-app-review

Sale de dos App Reviews reales hechos en noviembre de 2026: una app de
anuncios con Facebook Login for Business y una app de Instagram (comentarios,
mensajes, métricas y publicar). El panel se leyó el 2026-11-15 y la
documentación de Meta se contrastó el 2026-11-16 (fuentes en
`referencia.md`). Cuando algo viene del panel y no de la documentación, la
guía lo dice. **El panel de Meta en vivo manda sobre esta guía.**

## ¿Necesitas App Review?

- **Acceso estándar:** funciona solo para quien tiene un rol en la app
  (admin, desarrollador o tester) y para los activos del negocio dueño de la
  app. Para tu propia cuenta, no necesitas revisión.
- **Acceso avanzado:** lo necesita la app que maneja cuentas de **otros
  negocios** (Meta los llama "proveedor de tecnología"). Pide la
  verificación del negocio y el App Review.

Elige la ruta:

| Ruta | Para qué | Permisos típicos |
|---|---|---|
| **A · Facebook Login for Business** | Anuncios, páginas, portfolios comerciales | `ads_read`, `ads_management`, `business_management`, `pages_*`, Marketing API Access Tier |
| **B · Instagram API con Instagram Login** | DMs, comentarios, métricas y publicar en cuentas profesionales de Instagram | `instagram_business_basic`, `_manage_messages`, `_manage_comments`, `_manage_insights`, `_content_publish` |

**Para una integración nueva de Instagram,** Meta recomienda hoy la
[Instagram API with Unified Login](https://developers.facebook.com/documentation/instagram-platform/instagram-api-with-unified-login):
la persona entra con Instagram o con Facebook, sin página de Facebook. A
Instagram Login la presenta como la opción de las integraciones que ya
existen. Esta guía se probó con Instagram Login: el App Review es el mismo
proceso, pero lee la página de Unified Login antes de construir.

Las plantillas de texto, la lista del panel y los guiones están en
[`referencia.md`](referencia.md).

## Regla de oro: abre el formulario antes de construir

El día 1, antes de escribir código o grabar, ve a Revisión de la app ›
Permisos y funciones › "Solicitar acceso avanzado" en cada permiso, y entra
a "Continuar con la solicitud" › Uso permitido. Cada tarjeta lista sus
requisitos, y algunos solo aparecen ahí:

- **Un permiso con 0 llamadas no se puede pedir.** Meta pide al menos una
  llamada correcta por permiso **en los 30 días antes de enviar**, y el botón
  "Solicitar acceso avanzado" queda gris hasta que la registra. La
  documentación dice que la registra en hasta 2 días; el panel decía hasta
  24 h. Haz la primera llamada real de cada permiso apenas tengas la app
  arriba.
- **Dependencias:** según la referencia de permisos, `ads_management` y
  `business_management` dependen de `pages_read_engagement` y
  `pages_show_list`. El formulario dice cuál exige en tu solicitud: en una
  app real, `ads_management` pidió `pages_read_engagement` en la misma
  solicitud.
- Insights y comentarios de Instagram exigen `instagram_business_basic` en
  la misma solicitud.
- **Marketing API Access Tier:** desde 2026 los niveles se llaman Limited y
  Full (antes Standard y Advanced). Full pide 500 o más llamadas a la
  Marketing API en los últimos 15 días y menos de 15 % de error en las
  últimas 500. Para subir de nivel ya no se pide screencast.
- **Comentarios de Instagram** (lo pide la tarjeta del panel, no la
  documentación): el video muestra a un usuario comentando y la respuesta de
  la cuenta (o el DM) **en menos de 30 s**. La descripción lleva el enlace a
  un post con la automatización ya activa y la palabra que el revisor debe
  comentar. Nunca des credenciales de Instagram.

El borrador no se envía solo: se puede armar y desarmar sin riesgo.

## Quién hace qué

| El agente | La persona dueña de la app |
|---|---|
| Diagnóstico del token, código del flujo, panel de Meta (textos, URLs, configuración), prueba en seco, una carpeta con los archivos de prueba y el guion, armado de los videos, borrador del formulario, subida de videos, instrucciones para revisores | Verificación del negocio, la llave secreta de la app, **toda casilla de declaración** ("Acepto…", "Confirmo…", "Certifico…"), el cuestionario de tratamiento de datos, la comprobación de uso de datos, el clic de consentimiento en Facebook o Instagram, **la grabación**, la contraseña del usuario revisor y **Enviar para revisión** |

- Las declaraciones son legales. El agente no las marca sin un "sí,
  márcalas" explícito. Aun con ese sí, el navegador puede bloquear el clic:
  entonces se las pasa a la persona en una lista.
- El agente nunca escribe una contraseña ni lee una llave. Deja el marcador
  en el cuadro y la persona escribe encima. La llave secreta la pega la
  persona en el servidor.
- Mientras la persona graba, el agente no toca su navegador. Le da pasos
  numerados y espera.
- Todo lo demás lo hace el agente, y le dice a la persona solo cuándo le
  toca. Junta los clics de la persona en un solo mensaje.

## Orden

### 0 · Diagnóstico (15 min)

1. Si la app ya usa un token: `GET /debug_token?input_token=T&access_token=T`
   dice de qué app es (`app_id`), su tipo y sus `scopes`. Nunca imprimas el
   token.
2. Panel de la app: modo, tipo de app, productos, verificación del negocio,
   **acciones requeridas** y **llamadas por permiso** en "Permisos y
   funciones". La comprobación de uso de datos vence: si vence, Meta
   restringe la API, también en producción.
3. Abre el borrador (regla de oro). Guarda una tabla: permiso, nivel,
   llamadas y qué se pide. Un permiso en 0 es el camino crítico.

### 1 · Código del flujo de conexión

**Ruta A · Facebook Login for Business:**

- Un **link de conexión por cliente**, secreto: guarda solo su hash, que
  venza y se pueda revocar.
- Login con `config_id` (reemplaza a `scope`, que no se usa),
  `response_type=code` y `override_default_response_type=true`. Con token
  de usuario del sistema de integración, el login solo se pide desde web.
- Tipo de token: el de **usuario del sistema de integración** no vence por
  defecto y sirve para servidor a servidor; el de usuario es de vida corta.
- `state` OAuth de un solo uso y con vencimiento. El token del link va en
  una cookie HttpOnly, para que nunca viaje a Facebook.
- Canje del código en el backend y `debug_token` para validar que el token
  es de tu app.
- En cada llamada a Meta, usa el token del cliente para sus cuentas.

**Ruta B · Instagram Login:**

- El negocio conecta su cuenta profesional desde los ajustes de tu app
  (`https://www.instagram.com/oauth/authorize`). Solo web. Una app usa
  Facebook Login o Instagram Login, no las dos.
- **El token largo dura 60 días.** El código vale 1 hora y una sola vez, y
  se canjea por un token **corto**. El backend canjea ese token corto por el
  largo con `GET graph.instagram.com/access_token?grant_type=ig_exchange_token`.
  Guarda solo el largo: el corto es de vida corta y no se renueva. El largo se
  renueva con `refresh_access_token` cuando tiene al menos 24 h y antes de
  vencer. Sin renovación, la conexión muere a los 60 días.
- **No pidas en el login un permiso que siga en estándar** si se conectan
  cuentas sin rol en la app: Meta rechaza su login. Activa los permisos
  nuevos solo en la instancia que usa el revisor hasta que Meta apruebe.
- Publicar: Meta descarga el archivo desde una URL tuya, pública en ese
  momento, temporal y difícil de adivinar. Después vienen el contenedor,
  `status_code` y `media_publish`.
  - Imágenes: solo JPEG.
  - El contenedor vence a las 24 h. Meta sugiere consultar el estado una
    vez por minuto, hasta 5 minutos.
  - Límite: la documentación dice 100 publicaciones por API en 24 h en un
    lugar y 50 en otro. Consulta `/<IG_ID>/content_publishing_limit`.
  - Desde junio de 2026, `is_ai_generated=true` pone la etiqueta de IA.
- Métricas: usa `views`. `impressions`, `plays` y `video_views` ya no
  existen (2025).
- Borrar posts por la API (Delete Media, diciembre de 2025, permiso
  `instagram_manage_contents`) **solo existe con Instagram API with
  Facebook Login**. Con Instagram Login, los posts se borran a mano.
- Respuesta privada a un comentario: dentro de 7 días del comentario y un
  solo mensaje. Otro mensaje solo si la persona responde, y dentro de 24 h.
- Moderar: responder, ocultar o mostrar, y borrar con confirmación. Cada
  acción es un clic de una persona.

**Las dos rutas:**

- Token cifrado en reposo, nunca devuelto por tu API ni escrito en un log.
  Ojo: muchas librerías HTTP ponen la URL con el query en sus errores.
- Páginas públicas: política de privacidad, instrucciones de borrado y
  callbacks `signed_request` (HMAC-SHA256 con la llave secreta) de borrado
  y de desautorización.
- La política de privacidad cubre todo lo que pides (publicar, moderar,
  métricas). Revisa la URL que está en el panel, no solo la de tu app.
- Los textos dicen exactamente lo que pides y recibes. No prometas datos
  que no llegan (trampa 1).
- Todo apagado mientras falte una variable: el id y la llave secreta de la
  app en las dos rutas, y el `config_id` solo en la ruta A (Instagram Login
  no lo usa).

### 2 · Panel de Meta

La lista está en `referencia.md` § Panel. Hazlo **después** del deploy:
Meta valida que las URLs respondan.

### 3 · Prueba en seco y llamada de prueba

1. Conecta una cuenta propia por el flujo real. Sin reconectar, el token no
   trae los permisos nuevos.
2. Haz **una llamada real por permiso** con ese token. Desbloquea los
   botones en 0 (regla de oro).
3. Si la prueba escribe en Meta (crea una campaña, publica un post), mira
   el resultado en Ads Manager o en Instagram. Ejemplo real: Meta maneja
   las monedas sin decimales (COP, JPY, CLP…) en unidades enteras, y un ×100
   fijo de "centavos" multiplicó un presupuesto.
4. **Deja lista la demo del revisor** y pruébala desde otra cuenta. Si el
   revisor comenta y no le llega el DM, rechaza.

### 4 · Grabación (la persona)

**Reglas de Meta para el screencast:**
- 1080p o más. Meta sugiere bajar el ancho del monitor a 1440 o menos.
- La interfaz en inglés si se puede. Si no, subtítulos y notas que
  expliquen cada botón.
- Sin audio: los revisores no lo escuchan.
- Usa el mouse en vez del teclado, con el cursor más grande.
- Muestra el login completo y el momento en que la persona da cada permiso.
  Cierra antes la sesión de cualquier cuenta de prueba.
- Un permiso sin screencast no se aprueba.

**Cómo grabar:**

- **Grabador de pantalla:**
  - macOS: Cmd+Shift+5 › "Grabar toda la pantalla".
  - Windows: Herramienta Recortes › Grabar, o Win+Alt+R (Xbox Game Bar).
  - Linux con GNOME (Wayland): tecla Imprimir pantalla › ícono de video ›
    pantalla completa. `ffmpeg -f x11grab` graba en negro en Wayland.
  - Celular: la grabación de pantalla del sistema.
- **El agente prepara una carpeta** con la foto y el video de prueba, el
  guion en un `.txt` y los textos para copiar. El guion va en un solo
  mensaje, numerado, con "espera 3 s" en cada pantalla.
- **El consentimiento tiene que verse completo.** Si la cuenta ya estaba
  conectada, Instagram muestra una pantalla corta sin la lista de permisos.
  Conecta otra cuenta profesional que nunca se conectó.
- **Comentarios:** graba el computador y el celular a la vez. Desde una
  cuenta personal se comenta, y en menos de 30 s se responde, se oculta y
  se borra desde la app.
- Una toma por flujo basta. Los videos por permiso salen del corte. Si
  falta un tramo, graba solo ese tramo.
- La persona oculta lo privado (correo, chats). Lo que se cuele (una URL
  interna, un correo) se tapa con `tapar` de `video.py`.

### 5 · Armar los videos (`video.py`, el agente)

Necesita Python 3.10+ y `ffmpeg` con libass (el de Homebrew, apt o
gyan.dev lo trae).

```bash
V=<carpeta de la skill>/video.py
python3 -I $V hoja toma.mp4 --cada 2 --salida hoja.png      # ubica los cortes
python3 -I $V cuadro toma.mp4 --en 13 --recorte 700:300:300:820   # lee un texto chico
python3 -I $V armar spec.json                               # tramos, tapas, unión y subtítulos
python3 -I $V hoja salida/app_permiso.mp4 --cada 0.5        # revisa el video armado entero
```

- **Un video por permiso.** Cada uno empieza con el login y el
  consentimiento, y después muestra ese permiso en uso.
- Subtítulos en inglés, una idea por tramo. Si la interfaz no está en
  inglés, nombra cada botón con su traducción: "Publicar" (Publish).
- **Revisa el video armado, no la toma.** Los grabadores hacen cuadros de
  duración variable y un corte se puede correr cerca de 1 s. Corre `hoja`
  sobre la salida con `--cada 0.5` antes de subirlo.
- El ejemplo de `spec.json` está en `referencia.md`.

### 6 · Formulario

- **Tarjeta por permiso:** un solo cuadro de texto, el video y una casilla
  "Si se aprueba, confirmo…". No hay campos aparte para los pasos de prueba:
  van dentro del texto y en las instrucciones para revisores. Sin la
  casilla, "Guardar" no guarda.
- **Un texto propio por permiso,** en inglés. Meta pide no copiar y pegar.
- **Renovación:** cada solicitud vuelve a revisar los permisos que ya
  tienes. Hay una casilla "Certifico que…" por cada uno. El primer
  interruptor de esa página es el modo de la app: no lo toques.
- **Configuración de apps:** el ícono (512 a 1024 px) y una plataforma
  "Sitio web" en Configuración › Básica. Sin la plataforma no aparece el
  paso de instrucciones para revisores.
- **Tratamiento de datos:** la primera vez lo llena la persona. En la
  siguiente solicitud Meta trae las respuestas anteriores: confirma que
  siguen siendo ciertas.
- **Instrucciones para revisores:** dale al revisor una forma de probar sin
  tocar clientes reales.
  - Ruta A: un link de conexión de un cliente de prueba, con vencimiento
    largo, y el link de su dashboard.
  - Ruta B: un usuario de tu app (no de Meta ni de Instagram) que ya ve la
    cuenta de prueba conectada.
  - Si la interfaz no está en inglés, cada paso da la etiqueta y su
    traducción.
- **"Enviar para revisión":** abre una confirmación con la casilla
  "Confirmo y acepto…" de la persona. Después no se puede editar ni
  cancelar. La documentación dice que la decisión llega en una semana (casi
  siempre en 2 o 3 días); para una app de Instagram, en noviembre de 2026,
  el panel dijo unos 20 días.
- Meta prueba con sus propias cuentas de prueba. Nunca pongas las
  credenciales de tu cuenta personal de Facebook o Instagram.
- **Envío parcial:** si un permiso todavía está en 0, manda los que estén
  listos y deja ese para otra solicitud. Quita su sección de las
  instrucciones.
- **Mientras Meta revisa, no toques** la instancia del revisor, la demo
  activa ni el usuario revisor.

## Trampas que hacen perder una ronda

1. **El token de usuario del sistema no es la persona.** En Facebook Login
   for Business con "token de usuario del sistema", `/me` devuelve un
   usuario del sistema del negocio del cliente, con `client_business_id`.
   El nombre de la persona nunca llega: muestra el nombre del negocio, y no
   prometas datos personales en la política.
2. **Una configuración de FLfB no cambia** su tipo de token ni su
   vencimiento. Para sumar Páginas, crea otra configuración.
3. **"60 días (recomendado)"** exige un flujo de renovación. Sin él, elige
   "Nunca", o las conexiones mueren calladas a los 60 días. El token largo
   de Instagram Login siempre dura 60 días: ahí la renovación es obligatoria.
4. **FLfB pide `public_profile` en acceso avanzado.** Es gratis y sin
   revisión, pero trae una declaración y el cuestionario de tratamiento de
   datos.
5. **La comprobación de uso de datos vence** y restringe toda la API.
6. **El botón "Upgrade"** del Marketing API Access Tier mete el permiso al
   borrador. Se quita con la papelera.
7. **0 llamadas = botón gris** hasta que Meta registra la primera llamada:
   hasta 2 días según la documentación (el panel decía 24 h).
8. **Un permiso estándar en el login** rompe el login de toda cuenta sin
   rol en la app.
9. **Comentarios en estándar:** Meta manda los webhooks de comentarios solo
   de cuentas con rol en la app. Si "no llegan comentarios" de un cliente,
   mira primero el nivel del permiso (observado, no confirmado por Meta).
10. **La demo del revisor apagada** es rechazo seguro.
11. **Consentimiento corto** en una cuenta ya conectada: no muestra los
    permisos.
12. **Monedas:** cada moneda tiene un "offset" en la Marketing API (página
    Currency codes). USD tiene 100: un 1 es 0,01 USD. COP, JPY y KRW
    tienen 1: un 1 es un peso, un yen o un won. En una app real, un ×100
    fijo de "centavos" multiplicó un presupuesto en COP.
13. **Versiones:** en Graph API la más nueva es v27.0 y v21.0 se retira el
    2027-01-21. En la Marketing API, v27.0 salió el 2026-11-04, v24.0 venció
    el 2026-11-10 y v25.0 vence el 2027-02-23. Revisa los changelogs antes
    de enviar.

## Más rápido

- **Día 1, en paralelo:** el diagnóstico, el borrador del formulario, el
  código y la primera llamada real de cada permiso en 0.
- **Un solo deploy,** con los textos ya alineados con el tipo de token.
- **Una carpeta y una sola sesión de grabación** con el guion completo.
- **Un solo mensaje con todo lo de la persona** al final: casillas,
  contraseña del revisor y la confirmación del envío.
- **Si un permiso no está listo:** dos solicitudes. La primera con lo que
  ya funciona.
