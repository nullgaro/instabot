# INSTABOT
![Icon](icon.png)

***Language***
- 🇪🇸 Español
- 🇺🇸 [English](https://github.com/nullgaro/instabot)

# Descripción

Instabot es un programa desarrollado en Python con la finalidad de automatizar al completo cualquier cuenta de Instagram de manera legal utilizando la API de Instagram para subir las publicaciones que han sido tomadas automáticamente de Reddit.

Cuenta con la posibilidad de manejar varias cuentas simultáneamente con la misma instancia, para una mayor organización y comodidad.

# Pasos previos

## Preparando la cuenta para poder automatizarla

1. Crea una [cuenta de Gmail](https://gmail.coms).

2. Crea una [cuenta de Instagram](https://instagram.com).

3. Crea una [cuenta de Facebook](https://facebook.com).

4. Crea una [pagina de Facebook](https://www.facebook.com/pages/creation/?ref_type=launch_point).

5. Crea una [cuenta de Imgur](https://imgur.com).

6. Cambia la cuenta de Imgur [a cuenta developer](https://api.imgur.com/oauth2/addclient) y le ponemos en Authorization callback URL: "https://oauth.pstmn.io/v1/browser-callback". **¡RECUERDA guardar el Client ID y el Client secret en el .users.json!**

7. A través de la aplicación de Instagram cambia la cuenta a Bussiness y enlaza con la página de facebook que te creaste anteriormente. **Hay que esperar unos minutos desde que te creas la página de Facebook. Aprovecha y ve a por un café**

8. Accede a [Facebook developers](https://developers.facebook.com/docs/instagram/) con tu cuenta de Facebook, crea una aplicación eligiendo la opción de "Otro" -> "Empresarial".
    1. Ve a Configurar -> Información básica y guardar el "Identificador de la aplicación" y el "Clave secreta de la aplicación" en el .users.json (id_api_insta y id_secret_api_insta).

9. Ve a [Explorador de la API Graph](https://developers.facebook.com/tools/explorer/)
    1. Dale los [permisos necesarios](https://developers.facebook.com/docs/instagram-api/guides/content-publishing#permisos):
        * ads_management
        * business_management
        * instagram_basic
        * instagram_content_publish
        * pages_read_engagement
    2. Genera un nuevo token y almacenarlo en .users.json -> instagram_token

## Preparando el entorno de del código

1. Rellena la informacion de `.users.json.example`. La información que sería 100% necesaria:
    * instagram_token
    * id_api_imgur
    * description
    * tags
    * subreddits

2. Pon el nombre del usuario que vas a usar en el `.env.example` en caso de que pongas varios usuarios continualos con una coma `USERNAME1,USERNAME2`.

3. Quita el sufijo `.example` de los archivos `.env.example` y `.users.json.example`.

3. Instala Python (solo testeado en la versión 3.10.10)

4. Instala [ffmpeg](https://www.ffmpeg.org/download.html) para tu sistema operativo

5. Abre una terminal y muevete al directorio del proyecto

6. Ejecuta `pip install -r requirements.txt`

7. Genera un nuevo Access token desde [Explorador de la API Graph](https://developers.facebook.com/tools/explorer/) e inmediatamente ejecuta `python3 setup.py` para conseguir el insta_id y un LLAT (Long Live Access Token).

# Ejecutar el programa

Para ejecutar el programa abre una terminal y ejecuta `python3 main.py &`, recomiendo añadir el `&` para permitir que el programa corra en segundo plano.

# Cómo funciona

El programa utiliza la API de Reddit para descargar el máximo de publicaciones permitidas (100 publicaciones) de los subreddits previamente anotados en el archivo `.users.json` y los filtra según si son validos para los requisitos de Instagram, los videos los formatea para que Instagram los acepte y todo lo descargado se almacena en una base de datos de SQLite.

A la hora de publicar las publicaciones se utiliza la libreria APScheduler para simular un crontab con las horas dadas en el archivo `.env` y las publicará para los usuarios que estén en este mismo archivo.

Debido a que Instagram requiere de una URL pública para tomar la publicación que se va a subir, utilizamos la API de Imgur para subirlas y que nos devuelva una URL que será la que le daremos a la API de Instagram.

# Resultados

Estos son los resultados que tuve en Octubre 2023:

![instabot-statistics](https://github.com/nullgaro/instabot/assets/90156486/7f9910bd-5b3c-48c0-b732-04fd333a340e)


## Condiciones de los archivos:

### Imágenes

```
    Hasta 8MB

    Formatos validos:
        image/jpg

    Ratio de aspecto: Debe estar entre 4:5 y 1.91:1


    Puede ir sin ajustar (Lo ajustará automaticamente instagram)

    Ancho mínimo: 320 px (Será escalado hacia arriba si hiciera falta)
    Ancho máximo: 1440 px (Será escalado hacia arriba si hiciera falta)

    Altura: Varia, depende del ancho y su ratio de aspecto
```

### Videos
```
    Hasta 100MB
    Entre 3 y 60 segundos
    Entre 23 y 60 FPS

    Ancho maximo 1920 px

    Ratio de aspecto entre 4:5 y 16:9

    Formatos validos:
        video/mp4
        video/mpeg
```
