# Fútbol Libre

Servidor local y cliente Android TV para consultar eventos deportivos y reproducir sus fuentes.

## Estructura

- `src/server/`: API Flask, interfaz web y descubrimiento mDNS.
- `src/futbol_pipeline.py`: coordinación del scraping y generación de `eventos.m3u`, `eventos.xml` y `eventos.json`.
- `src/tvapp/`: proyecto Android TV.
- `output/`: APK listo para instalar en el TV.

## Requisitos

- Docker Desktop (Mac/Windows) o Docker Engine (Linux) para la instalación recomendada.
- La instalación nativa con `install.sh` requiere Debian/Ubuntu, Python 3, `ffmpeg`, Google Chrome y ChromeDriver/Selenium.
- Para la app: Android SDK, Java y `adb`.
- El servidor y el TV deben estar en la misma red local.

## Configuración

Copiar `.env.example` a `.env` y ajustar las rutas, URLs y credenciales necesarias:

```bash
cp .env.example .env
```

`.env` contiene configuración local y secretos; no debe versionarse.

## Instalar el servidor

### Instalación recomendada con Docker

En Mac, Windows o Linux:

```bash
cp .env.example .env
docker compose up --build -d
```

La primera actualización se ejecuta manualmente, una vez que los contenedores estén arriba:

```bash
docker compose run --rm futbol ./update-futbollibre.sh
```

El catálogo queda guardado en un volumen Docker. Para actualizarlo nuevamente, repetí ese comando.

En un servidor Debian/Ubuntu:

```bash
./install.sh
```

El instalador crea el entorno en `/opt/futbol`, instala dependencias y registra las tareas diarias de actualización.

## Correr el servidor

Desde la raíz del proyecto:

```bash
./server.sh
```

El servidor escucha en el puerto `8080`:

- Web: `http://IP_DEL_SERVIDOR:8080/`
- Salud TV: `http://IP_DEL_SERVIDOR:8080/api/v1/health`
- Eventos TV: `http://IP_DEL_SERVIDOR:8080/api/v1/events`

La app descubre automáticamente el servidor mediante mDNS (`_futbol._tcp`). Si no funciona el descubrimiento, se puede iniciar la app indicando manualmente la URL del servidor.

Para ejecutar la actualización manual de eventos:

```bash
./update-futbollibre.sh
```

## Correr la app en el TV

### Instalar el APK incluido

Con `adb` habilitado y el TV conectado:

```bash
adb connect IP_DEL_TV:5555
adb install -r output/futbol-tv-release.apk
```

Abrir `Fútbol TV` desde el TV. El servidor debe estar corriendo y ambos dispositivos deben compartir la red local.

Si la TV no permite instalar el APK:

1. Abrí `Configuración > Sistema/Preferencias del dispositivo > Información` y presioná varias veces sobre `Compilación` para habilitar las opciones de desarrollador.
2. Activá `Depuración por red` o `Depuración USB` y permití instalar desde la aplicación usada para descargar el APK.

La ruta y el nombre pueden variar según el fabricante. La página `/tvapp` muestra la misma advertencia antes de descargar.

### Generar un APK nuevo

```bash
cd src/tvapp
./gradlew assembleRelease
cp app/build/outputs/apk/release/app-release.apk ../../output/futbol-tv-release.apk
```

El APK generado queda también en `src/tvapp/app/build/outputs/apk/release/`, pero esa carpeta es un artefacto de Gradle y está ignorada por Git. El archivo distribuible es `output/futbol-tv-release.apk`.

## Instalación y actualización desde el servidor

Con el servidor corriendo en la red local, desde el navegador de la TV se puede abrir:

```text
http://IP_DEL_SERVIDOR:8080/tvapp
```

La página permite descargar el APK. La TV pide autorización y confirmación antes de instalarlo.

Las versiones instaladas consultan `/api/v1/app`. Si el servidor anuncia un `version_code` mayor, la app muestra la actualización, descarga `/downloads/futbol-tv.apk` y abre el instalador de Android para que el usuario confirme.

Al publicar una versión nueva hay que incrementar `versionCode` y `versionName` en `src/tvapp/app/build.gradle`, compilar y copiar el APK:

```bash
cp src/tvapp/app/build/outputs/apk/release/app-release.apk output/futbol-tv-release.apk
```

### Probar en emulador

```bash
adb shell am start -n com.futbol.tv/.MainActivity \
  --es server_url http://10.0.2.2:8080
```

## FFmpeg externo

Configuración recomendada:

```text
-hide_banner -loglevel error -reconnect 1 -reconnect_at_eof 1 -reconnect_streamed 1 -reconnect_delay_max 2000 -i [URL] -c copy -map 0 -f mpegts -fflags +genpts pipe:1
```

User-Agent recomendado:

```text
Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36
```
