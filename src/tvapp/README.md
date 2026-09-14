# Fútbol TV

Cliente Android TV/Android para el server local de fútbol.

## Flujo

La app descubre el servicio mDNS `_futbol._tcp`, consulta `/api/v1/events` y navega por:

`eventos -> fuentes -> preview -> pantalla completa`

Para probar el emulador sin mDNS se puede iniciar con un `server_url` explícito:

```bash
adb shell am start -n com.futbol.tv/.MainActivity \\
  --es server_url http://10.0.2.2:8080
```

## Instalación en una TV Android/Google TV

La TV y el servidor deben estar en la misma red local. En la TV, habilitá las opciones de desarrollador desde
`Configuración > Información > Compilación` y activá `Depuración por red` o `Depuración USB`.

Desde una Mac con ADB:

```bash
adb connect IP_DE_LA_TV:5555
adb install -r output/futbol-tv-release.apk
```

Si descargás el APK desde `/tvapp`, Android puede pedir habilitar `Permitir desde esta fuente` para el navegador o
explorador de archivos. La ubicación exacta de esa opción depende de la marca de la TV.
