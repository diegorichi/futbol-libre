# Auditoría y continuidad: VPN / relay web

## Estado verificado

- El checkout está en la rama `codex/adding-vpn-for-web`.
- `HEAD` es `e968a34`, que coincide con `origin/codex/adding-vpn` y `origin/main`.
- Hay cambios locales sin commit relacionados con el relay web.
- La rama base ya contiene el flujo VPN de Android TV y el ruteo selectivo
  probado en el LXC.
- Los cambios web siguen sin commit y todavía no forman parte de main.

## Cambios web locales detectados

- `src/server/services/hls_relay.py`: proxy de playlists, segmentos y URI de
  claves HLS; reescribe las referencias del playlist.
- `src/server/api_service.py`: agrega `/api/v1/stream-relay/...` y publica
  botones web cuando `STREAM_VPN_ENABLED` está activo.
- `src/server/templates/channels.html`, `src/server/static/app.js` y
  `src/server/static/app.css`: botón `Usar VPN` y reproducción inline.
- `src/server/models/channel.py` y
  `src/server/services/channel_service.py`: propagan `event_id` y `source_id`.
- `tests/test_hls_relay.py`: pruebas unitarias de reescritura y recurso
  inexistente.

## Estado posterior de la implementación

1. El endpoint devuelve 404 para VPN deshabilitada o recurso inexistente, 404
   para evento/fuente inexistentes, 503 para errores del resolver y 502 para
   errores aguas arriba.
2. `HlsRelay._resources` deduplica URLs, elimina entradas vencidas y mantiene
   un máximo de 4096 recursos con TTL de 600 segundos.
3. El updater invalida atómicamente el cache VPN después de publicar con éxito;
   si falla la actualización, conserva el cache anterior.
4. Hay pruebas Flask del endpoint para manifest, headers y errores 404/503/502,
   además de pruebas unitarias del relay.
5. No hay prueba real desde un navegador con HLS.js ni prueba de una playlist
   con variantes, `EXT-X-KEY`, `EXT-X-MAP`, URLs absolutas y relativas.
5. No está verificado aquí el comportamiento con varios clientes simultáneos,
   reinicio del servidor, vencimiento de cache ni caída de WireGuard durante
   una reproducción.
6. La documentación ya describe el relay como implementado, pero los cambios
   siguen sin commit.
7. El relay consume ancho de banda y memoria del servidor. No es un simple
   cambio de URL ni una prueba de reproducción directa desde el navegador.

## Validación ejecutada

```text
PYTHONPATH=src pytest -q
36 passed, 1 failed
```

El fallo es `TvApiContractTest.test_upcoming_events_are_not_expandable` y
depende de que el catálogo actual contenga eventos futuros; no demuestra que
el relay funcione.

También pasaron `compileall` y `git diff --check`. No se ejecutó una prueba
real contra un sitio, una TV ni un navegador con HLS.js.

## Plan para continuar

1. Agregar una prueba de playlist HLS completa con variantes, claves, mapa y
   URLs relativas/absolutas.
2. Probar en el LXC con VPN selectiva: IP directa del servidor, IP del proxy,
   scraping VPN y reproducción web simultánea con reproducción TV directa.
3. Verificar reinicio, caída de `vpn0`, expiración de URL y concurrencia antes
   de afirmar que el relay está terminado.
4. Recién entonces revisar el diff, decidir qué cambios conservar, crear un
   commit separado y actualizar la documentación.

## Regla de continuidad

No hacer `git reset`, `git checkout` ni borrar estos cambios sin confirmar
primero si pertenecen al usuario. Si se abandona el relay, debe hacerse una
reversión deliberada de los archivos listados arriba y comprobar que la rama
vuelve a contener únicamente la feature VPN de Android TV.
