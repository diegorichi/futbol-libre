# Streaming por VPN

## Alcance actual

El modo VPN es opcional y se habilita con `.env`:

```text
STREAM_VPN_ENABLED=0
STREAM_VPN_INTERFACE="vpn0"
STREAM_VPN_CONFIG="/etc/wireguard/vpn0.conf"
STREAM_VPN_PROXY_HOST="192.168.0.149"
STREAM_VPN_PROXY_PORT=8888
STREAM_VPN_TTL_HOURS=4
```

Cuando el flag está desactivado, el servidor no exige WireGuard ni Tinyproxy.
Cuando se solicita una URL VPN, levanta `vpn0`, verifica configuración,
interfaz, handshake, listener del proxy y salida externa del proxy. El Chrome
usado para ese scraping también se configura con Tinyproxy. La disponibilidad se publica junto con el
contrato de `/api/v1/app`, `/api/v1/discovery` y `/api/v1/events`.

Las URLs VPN son dinámicas y no forman parte del `eventos.json` canónico. Se
guardan en `data/.vpn-stream-cache.json` con `fetched_at` y un vencimiento
calculado como `fetched_at + STREAM_VPN_TTL_HOURS`.

## Flujo previsto para TV

```text
URL directa: TV -> proveedor
URL VPN:     TV -> Tinyproxy local -> Proton -> proveedor
```

El scraping VPN y la reproducción VPN deben usar la misma salida de Proton,
porque algunos proveedores firman el token para la IP de salida.

## Ruteo

El servidor administra `vpn0` solo durante una operación VPN. El `vpn0` debe
usar `Table=off` y una tabla/rule exclusiva para el usuario del proceso
Tinyproxy. No debe instalar una ruta por defecto global en el LXC.

La idea de la configuración de WireGuard es esta; el UID real se debe obtener
en el LXC con `id -u tinyproxy` y reemplazar en ambas reglas:

```ini
[Interface]
Table = off
PostUp = ip route add default dev %i table 51820; ip rule add uidrange UID-UID table 51820 priority 100
PreDown = ip rule del uidrange UID-UID table 51820 priority 100; ip route del default dev %i table 51820
```

También hay que confirmar que Tinyproxy corre con ese usuario:

```bash
systemctl show -p User tinyproxy
```

Si `User=` está vacío, se debe revisar el usuario efectivo del proceso antes
de aplicar `uidrange`. El `DNS=` de la configuración actual no debe cambiar el
resolver global del LXC; hay que quitarlo o aislarlo antes de probar convivencia
con tráfico directo.
Eso sirve para una prueba manual, pero no permite todavía convivencia limpia
entre tráfico directo y VPN. La solución prevista es policy routing o un
namespace de red para Tinyproxy y el scraping VPN. La aplicación no debe subir
ni bajar el túnel global.

## Operación manual en Debian

Con `/etc/wireguard/vpn0.conf` instalado, la activación normal la hace el
servidor al resolver una URL. Para una prueba manual:

```bash
sudo wg-quick up vpn0
sudo wg show vpn0
curl -4 https://api.ipify.org
```

Para desactivarlo:

```bash
sudo wg-quick down vpn0
curl -4 https://api.ipify.org
```

No se debe habilitar `wg-quick@vpn0` de forma persistente mientras la
configuración siga siendo full-tunnel.

El flag `STREAM_VPN_ENABLED` habilita la feature y autoriza al servidor a
administrar WireGuard y publicar el proxy. Si queda en `false`, el servidor no
usa ni verifica la VPN.

## Relay HLS web

La web usa el endpoint local de relay por evento y fuente. El servidor
resuelve el stream y obtiene el manifest y sus segmentos mediante Tinyproxy;
las URLs HLS se reescriben para que el navegador vuelva al relay.
No hay transcodificación, pero el servidor retransmite el tráfico del video y
por eso consume ancho de banda equivalente al stream.

La URL web solo contiene el event_id y source_id. El servidor busca la URL VPN
en el cache y la regenera mediante Selenium si venció o no existe. Las
referencias a playlists, segmentos y claves se registran internamente y se
sirven por rutas locales del mismo evento y fuente.
