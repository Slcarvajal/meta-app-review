# meta-app-review · referencia

Cambia todo lo que va entre `<>` por los datos de tu app. Datos del panel
leídos el 2026-11-15; el panel en vivo manda.

Fuentes de Meta (leídas el 2026-11-16; ninguna muestra fecha de
actualización):
- [App Review: guía de envío](https://developers.facebook.com/documentation/resp-plat-initiatives/individual-processes/app-review/submission-guide.md):
  screencast, llamadas de prueba, credenciales y plazos.
- [App Review para la API de Instagram](https://developers.facebook.com/documentation/instagram-platform/app-review)
  y su [changelog](https://developers.facebook.com/documentation/instagram-platform/changelog.md).
- [Business Login for Instagram](https://developers.facebook.com/documentation/instagram-platform/instagram-api-with-instagram-login/business-login),
  [publicación de contenido](https://developers.facebook.com/documentation/instagram-platform/content-publishing)
  y [respuestas privadas](https://developers.facebook.com/documentation/instagram-platform/private-replies).
- [Facebook Login for Business](https://developers.facebook.com/documentation/facebook-login/facebook-login-for-business).
- Permisos: [ads_management](https://developers.facebook.com/docs/permissions/reference/ads_management/),
  [ads_read](https://developers.facebook.com/docs/permissions/reference/ads_read/),
  [business_management](https://developers.facebook.com/docs/permissions/reference/business_management/),
  [pages_read_engagement](https://developers.facebook.com/docs/permissions/reference/pages_read_engagement/).
- [Rate limiting de la Marketing API](https://developers.facebook.com/documentation/ads-commerce/marketing-api/overview/rate-limiting.md)
  y su [changelog](https://developers.facebook.com/documentation/ads-commerce/marketing-api/marketing-api-changelog.md).
- [System user tokens](https://developers.facebook.com/docs/business-management-apis/system-users/install-apps-and-generate-tokens).
- [Visión general de Instagram](https://developers.facebook.com/documentation/instagram-platform/overview):
  Unified Login, Instagram Login y Facebook Login.
- [Referencia de ad sets](https://developers.facebook.com/documentation/ads-commerce/marketing-api/reference/ad-account/adsets)
  y la página "Currency codes" de la Marketing API (offset por moneda).

Diferencias dentro de la propia documentación de Meta:
- El permiso de publicar sale como `instagram_business_content_publish` en
  Business Login y como `instagram_business_content_publishing` en la página
  de App Review. Usa el que muestre tu panel.
- `instagram_business_manage_insights` aparece en el panel, pero no en la
  lista de la página de App Review.
- El límite de publicaciones sale como 100 y como 50 en 24 h.
- Algunas páginas todavía dicen "Standard" y "Advanced" para el Marketing
  API Access Tier, y 1.500 llamadas en vez de 500.

**Qué tiene que mostrar el screencast de los permisos de anuncios**
(`ads_read`, `ads_management`, `business_management`, según la referencia):
el login completo de Facebook con el permiso concedido, el negocio entrando
a los datos de rendimiento, y esos datos en tu app (impresiones,
conversiones, gasto, clics, alcance). Para `pages_read_engagement`: el login,
la persona entrando al contenido de una publicación de su página, y ese
contenido en tu app.

## Panel

**Configuración de la app › Básica**
- Nombre visible: el nombre del producto. El cliente lo ve en el
  consentimiento.
- Dominios de la app: `<dominio>`.
- URL de la política de privacidad: `https://<dominio>/privacidad`.
- Eliminación de datos de usuario: "URL de devolución de llamada…" →
  `https://<dominio>/<ruta de borrado>`.
- Categoría: la que describe tu producto (por ejemplo "Negocios y páginas").
- Ícono: JPG o PNG de 512 a 1024 px.
- **Agregar plataforma › Sitio web** → `https://<dominio>/`. Sin esto no
  aparece el paso de instrucciones para revisores.

**Ruta A · Productos › Inicio de sesión con Facebook para empresas ›
Configurar**
- URI de redireccionamiento de OAuth válidos: `https://<dominio>/<callback>`,
  con el modo estricto encendido.
- URL de devolución de llamada para autorización cancelada:
  `https://<dominio>/<deauthorize>`.

**Ruta A · … › Configuraciones › Crear configuración**

| Paso | Elige | Nota |
|---|---|---|
| Nombre | "<Producto>: cuentas publicitarias" | Máximo 30 caracteres |
| Variación | General | |
| Token | De usuario del sistema | Exige un portfolio comercial. No se puede cambiar |
| Vencimiento | Nunca, salvo que tengas flujo de renovación | No se puede cambiar |
| Activos | Cuentas publicitarias, con "Activo requerido" | Suma "Páginas" si pides permisos de páginas |
| Permisos | `ads_read`, `ads_management`, `business_management` | Los de acceso estándar solo los ve quien tiene un rol en la app |

Copia el identificador de configuración a tu variable de `config_id`.

**Ruta B · Instagram › Configuración de la API con inicio de sesión de
Instagram**
- URL de redireccionamiento de OAuth y webhooks (comentarios, mensajes)
  apuntando a tu dominio.
- Los permisos nuevos se piden en el login solo en la instancia del
  revisor, hasta que Meta apruebe.

**Revisión de la app › Permisos y funciones**
- Mira la columna de llamadas. Un permiso en 0 no se puede pedir.
- Acciones requeridas › "Enviar comprobación de uso de datos": la hace la
  persona antes de la fecha.

**La llave secreta en el servidor** (la pega la persona; el agente no lee
llaves):

```bash
grep -q '^META_APP_SECRET=' <ruta>/.env && echo "ya está" || { read -rsp "secret: " S && echo "META_APP_SECRET=$S" >> <ruta>/.env && unset S && echo ok; }
```

Para comprobar la llave sin leerla, corre esto **donde la app ya carga su
`.env`** (por ejemplo dentro del contenedor). Lee las variables de entorno,
llama a `GET /<app_id>?fields=id,name` y solo imprime el nombre de la app;
la llave no queda en el historial de la terminal:

```bash
python3 -c 'import os,json,urllib.request as u;a=os.environ["META_APP_ID"];s=os.environ["META_APP_SECRET"];print(json.load(u.urlopen(f"https://graph.facebook.com/{a}?fields=id,name&access_token={a}|{s}"))["name"])'
```

## Textos por permiso (en inglés, uno propio por permiso)

### Ruta A

**ads_read.** Opción: "Proporciona el acceso a la API a los datos de
rendimiento de los anuncios para usarlos en paneles personalizados…".

> <Product> is the marketing tool of <Company>. Our clients are businesses that hire us to run their Meta ads. Each client connects its own ad account to <Product> with Facebook Login for Business, through a private link we send them, and chooses on the consent screen which business portfolio and ad account to share. <Product> uses ads_read to read the performance of that ad account (spend, reach, impressions, link clicks, CTR, leads and cost per result, per campaign, ad set and ad). <Product> shows this data to the client on a private dashboard and to our team in their reports. We only read the ad accounts the client granted, and we never sell or share this data.

**business_management.**

> <Product> connects to a client's business through Facebook Login for Business with a system-user token: the client logs in with their business portfolio, not a personal profile. <Product> uses business_management to read which business granted access (its name) and which ad accounts of that business were shared, so the client can pick the ad account <Product> works with, and so our admins can see which business each connection belongs to. <Product> does not change the client's business settings, users, roles or assets.

**ads_management.** Va con `pages_read_engagement` en la misma solicitud.

> Our team runs the client's campaigns from <Product>. With ads_management, <Product> creates campaigns, ad sets, ads and creatives in the client's ad account, and pauses or adjusts budgets when a team member asks. Every new object is created PAUSED, and a person approves each change in <Product> before it is sent to Meta; nothing is activated without that approval. Without this permission the team would have to repeat every change by hand in Ads Manager for each client.

**pages_read_engagement.** Escríbelo según el uso real. Ejemplo: leer la
página del cliente (nombre, publicaciones, seguidores) para elegir con qué
página se crean sus anuncios.

**Marketing API Access Tier.** Describe el volumen: cuántos clientes y
cuentas, y por qué el límite del nivel limitado no alcanza.

### Ruta B

**instagram_business_manage_comments** (una sola caja: uso más el bloque de
prueba).

> <Product> is used by businesses to manage the comments on their own Instagram posts and reels. We use instagram_business_manage_comments for two features, both only on media owned by the connected professional account. 1) Keyword comments to private replies: the business creates a campaign on one of its posts with a keyword (for example LINK). We receive comments through the comments webhook and, if the text contains the keyword, we send one private reply using the comment ID. 2) Manual moderation: a person on the business team sees the comments of a post and can reply in public, hide or show, or delete (after a confirmation step). Every moderation action is a click by a person; the app never moderates on its own.
>
> HOW TO TEST (no Instagram credentials needed):
> - Post with the automation already set up: <post link>
> - From your own Instagram account, comment the keyword LINK on that post. Within 30 seconds the private reply arrives in your inbox.
> - To test moderation, sign in to <Product> with the test login from the reviewer instructions and open the comments page.

**instagram_business_manage_insights.** Qué métricas lees (por ejemplo
`views`, `reach`, `saved`, `shares`, `total_interactions`,
`follower_count`), dónde las muestras y que son solo de la cuenta
conectada.

**instagram_business_content_publish.** La persona del negocio sube una
foto o un reel, escribe el texto y publica con un clic. Meta descarga el
archivo de una URL temporal que se borra al terminar. Nada se publica solo.

**instagram_business_manage_messages.** Qué mensajes lees y mandas, quién
los manda (una persona o una automatización que el negocio configura) y
dentro de qué ventana.

## Instrucciones para revisores (plantillas)

**Ruta A**

> <Product> is the internal tool of <Company>. The part a client uses is a private connect link, plus a private results dashboard. You can test both yourself:
>
> 1. Open this connect link (made for our test client, valid until <date>): <link>
> 2. Press "<connect button>" and log in with a Facebook account that is admin of a business portfolio with at least one ad account.
> 3. On the Facebook screen, choose the business portfolio and an ad account, then confirm.
> 4. Back in <Product>, the page shows the connected business and its ad accounts (business_management). Select one.
> 5. Open the test client's dashboard: <link>. <Product> reads the performance of the ad account you connected (ads_read).
>
> No payment is needed. Contact: <email>

**Ruta B**

> <Product> is a web app: <URL>. Each step gives the label in the app and its English meaning. The screencasts have English captions.
>
> TEST LOGIN FOR <Product> (not a Meta or Instagram account)
> - URL: <URL>/login
> - Email: <reviewer email>
> - Password: <written by the owner>
>
> This user can see our Instagram professional account @<account>, which is already connected. You do not need to connect any account, and we do not share Instagram credentials. If there is an account selector, choose @<account>.
>
> A. <permission>: <steps>
> B. <permission>: <steps>

## Guiones de grabación (plantillas para la persona)

**Ruta A**

0. Oculta lo privado. Navegador en pantalla completa, sin favoritos.
1. Empieza a grabar la pantalla completa.
2. Abre `<link de conexión nuevo>`. Espera 3 s. Pulsa el botón de conectar.
3. En Facebook: el negocio › solo la cuenta de prueba › Continuar.
4. De vuelta en la app: elige la cuenta. Espera 3 s.
5. Abre el dashboard. Cada pestaña, 3 s.
6. (Para `ads_management`) Crea una campaña **en pausa** desde la app y
   ábrela en Ads Manager.
7. Para la grabación.

**Ruta B (computador y celular a la vez)**

0. Navegador en pantalla completa, sin favoritos ni otras pestañas.
   Celular con una cuenta personal, no la del negocio.
1. Graba las dos pantallas.
2. Ajustes de la app › conectar una cuenta profesional que nunca se
   conectó › cursor 3 s sobre los permisos › Permitir.
3. Publica una foto y un reel desde la app y abre cada post en Instagram.
4. Celular: comenta dos veces en un post del negocio ("What time do you
   open?" y "spam test").
5. Menos de 30 s después, en la app: responde el primero, oculta el segundo
   y bórralo.
6. Celular: recarga el post (se ve la respuesta, el spam no).
7. La página de métricas: 3 s en cada sección.
8. Para las dos grabaciones.

## spec.json (ejemplo)

Rutas relativas al JSON. Los tiempos de los subtítulos son del video
armado. `\\N` parte la línea. `tapar` usa píxeles de la toma original:
`[x, y, ancho, alto]`.

```json
{
  "salida": "videos-meta",
  "segmentos": {
    "login": ["toma1.mp4", 1.5, 27.5],
    "dash":  ["toma1.mp4", 29.5, 55.0]
  },
  "tapar": {
    "login": [[0, 1900, 1200, 60]]
  },
  "videos": {
    "app_ads_read": {
      "partes": ["login", "dash"],
      "subtitulos": [
        [0, 5, "The client opens the private connect link."],
        [5, 15, "Facebook asks which business portfolio and ad account to share,\\Nand shows what the app will be able to do."],
        [15, 26, "Back in the app: the connected business and its ad account."],
        [26, 51.5, "ads_read: the app reads the performance of that ad account.\\NRead only."]
      ]
    }
  }
}
```
