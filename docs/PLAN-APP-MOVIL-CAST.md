# Plan: app móvil para navegar y enviar videos a Fútbol TV

Documento de arranque para una aplicación nueva y separada de este repositorio.

## 1. Objetivo

Crear una app móvil que:

1. Navegue sitios web desde un navegador integrado.
2. Bloquee publicidad, pop-ups y trackers sin romper la reproducción.
3. Detecte videos reproducibles, principalmente MP4 y HLS (`.m3u8`).
4. Muestre las fuentes detectadas para que el usuario elija una.
5. Envíe el video seleccionado a una TV compatible.
6. Permita seguir navegando en el celular mientras la TV reproduce.
7. Deje el control de reproducción en la TV mediante el control remoto.

La app no debe actuar como proxy del video en el MVP. El celular manda la referencia del stream y los metadatos necesarios; la TV reproduce directamente.

## 2. Decisiones iniciales

### Plataforma

Empezar por Android. No empezar Android e iOS simultáneamente.

Motivos:

- Android permite un navegador embebido y servicios de red local con menos restricciones.
- La TV actual también es Android TV.
- iOS impone restricciones mayores para navegación embebida, detección de medios y comunicación local persistente.

iOS queda como fase posterior, solo después de probar el flujo Android completo.

### Reproducción

La TV reproduce directamente el stream. El celular no transcodifica, no reenvía segmentos y no mantiene un servidor HTTP para video.

Flujo esperado:

```text
Celular: navegador -> detector -> selección -> envío
                                               |
                                               v
TV: receptor -> reproductor Media3/ExoPlayer -> control remoto
```

### Ad blocker

Usar un motor de filtrado de requests, no un bloqueador DNS ni una VPN del teléfono.

Primera alternativa a evaluar:

- WebView Android.
- Motor compatible con EasyList/uBlock-style lists.
- Lista base EasyList.
- Lista regional si aporta cobertura.
- Reglas propias por sitio.
- Allowlist explícita para dominios de video, CDN, manifests, segmentos, imágenes de poster, cookies y endpoints necesarios.

No asumir que descargar una lista y hacer `contains(url)` alcanza. Hay que interpretar reglas, excepciones (`@@`), comodines, separadores de dominio y tipos de recurso.

Segunda alternativa, solo si WebView resulta insuficiente:

- GeckoView con integración de un bloqueador más completo.

No usar VPN/DNS como solución inicial: afecta todo el teléfono y puede romper streams o generar permisos y estados difíciles de explicar.

## 3. Riesgos que hay que falsar primero

### Riesgo A: el sitio no expone el stream al WebView

Un reproductor puede estar dentro de iframes, generarse con JavaScript o usar DRM. Detectar un elemento `<video>` no garantiza obtener una URL reproducible.

Prueba mínima: elegir cinco sitios representativos y registrar:

- URL de la página.
- iframe involucrado.
- requests de manifest.
- URL HLS o MP4 resultante.
- Referer, User-Agent, cookies y headers necesarios.
- Si la URL funciona fuera del navegador.

### Riesgo B: la TV no puede reproducir la URL enviada

La TV puede necesitar `User-Agent`, `Referer`, cookies o headers adicionales. Una URL visible en el celular no implica que el ExoPlayer pueda usarla.

El contrato de cast debe transportar los headers necesarios y preservar query strings y tokens sin truncarlos.

### Riesgo C: la URL expira

No enviar una URL al inicio de la navegación y reutilizarla indefinidamente. La URL debe capturarse cerca del momento de enviar a la TV.

Si expira durante la reproducción, el MVP debe informar el error. No agregar renovación automática hasta tener evidencia de que el sitio lo requiere.

### Riesgo D: el ad blocker rompe la página

El bloqueador debe poder desactivarse por sitio y debe registrar por qué bloqueó un request durante las pruebas.

Un resultado visualmente limpio no es suficiente si desaparece el botón de reproducción o se rompe la obtención del manifest.

### Riesgo E: no existe todavía un receptor compatible

La app móvil no puede enviar mágicamente un video a la app actual de Android TV si la TV no expone un contrato de recepción.

Antes de construir toda la app móvil hay que implementar y probar un receptor mínimo en la TV o acordar un protocolo con el cliente actual.

## 4. Contrato móvil -> TV

Definirlo antes de construir la UI final.

### Descubrimiento

Orden recomendado:

1. Descubrimiento explícito por URL/IP.
2. mDNS en la red local.
3. Broadcast UDP como fallback, solo si funciona de forma comprobable.

La URL manual debe seguir siendo el método garantizado. No asumir que mDNS o UDP atravesarán routers, guest networks, VPNs o modos especiales de hotspot.

### Mensaje mínimo

```json
{
  "protocol": "futbol-cast-v1",
  "title": "Nombre del evento",
  "url": "https://example.test/video.m3u8?token=...",
  "mime_type": "application/vnd.apple.mpegurl",
  "headers": {
    "User-Agent": "...",
    "Referer": "https://example.test/"
  },
  "poster": "https://example.test/poster.jpg"
}
```

Reglas:

- No eliminar parámetros de la URL.
- No registrar tokens ni cookies en logs.
- Validar que la URL sea HTTP(S).
- Limitar el tamaño de títulos, headers y posters.
- Rechazar esquemas locales, `file://`, `javascript:` y destinos inválidos.
- Definir respuesta de aceptación, error y reproducción iniciada.

### Receptor de TV

La TV debe:

- recibir el mensaje;
- mostrar título y estado;
- crear el reproductor con URL y headers;
- permitir play, pausa, volumen, cambio de fuente, pantalla completa y atrás;
- informar errores de reproducción;
- mantener la reproducción aunque el celular vuelva a navegar;
- aceptar un nuevo video y decidir explícitamente si reemplaza el actual o entra en cola.

Primero implementar solo un video, sin cola ni multi-room.

## 5. Navegación de la app móvil

### Pantallas MVP

```text
Inicio
├── navegador
├── dispositivos
└── historial opcional

Navegador
├── barra de URL/búsqueda
├── atrás/adelante
├── recargar
├── bloqueo de anuncios activo
└── botón/lista de videos detectados

Videos detectados
├── título
├── tipo y calidad si se conoce
├── fuente/página
└── Enviar a TV

Dispositivos
├── buscar TVs
├── seleccionar TV
└── ingresar URL manual
```

La reproducción no debe ocupar ni bloquear la pantalla del navegador. El celular debe poder volver a la página, abrir otra pestaña o detectar otro video mientras la TV continúa reproduciendo.

La UI debe contemplar:

- estado sin dispositivos;
- video detectado pero no reproducible;
- stream sin headers suficientes;
- TV ocupada;
- URL vencida;
- error de red local;
- bloqueo del ad blocker que impide una función;
- botón para desactivar el bloqueo en el sitio actual.

## 6. Detección de medios

Implementar en capas y conservar evidencia de cada capa:

1. Elementos HTML `<video>` y `<source>`.
2. URLs visibles en atributos y scripts.
3. Interceptación de requests del WebView.
4. Detección de manifests HLS.
5. Inspección de iframes permitidos.
6. Reglas específicas solo para sitios que fallen en las capas generales.

Normalización permitida:

- desescapar `\\/` a `/`;
- resolver URLs relativas contra la página origen;
- conservar query strings, fragmentos relevantes y headers.

No:

- inventar una URL a partir del nombre del evento;
- declarar reproducible algo que solo fue detectado;
- eliminar una fuente porque no tiene poster;
- usar un stream de prueba como fallback silencioso.

Estados de una fuente:

```text
detected -> candidate -> validated -> sent -> playing | failed
```

## 7. Ad blocker: implementación propuesta

### Fase 1

- Cargar una lista conocida y versionada.
- Crear un parser testeable fuera de Android UI.
- Resolver reglas para host, URL, excepciones y recursos.
- Aplicar filtrado en `shouldInterceptRequest` o mecanismo equivalente.
- Registrar solo dominio, tipo de recurso y regla; nunca tokens completos.
- Medir latencia y cantidad de requests bloqueados.

### Fase 2

- Agregar reglas propias por sitio.
- Agregar allowlist de medios.
- Agregar botón de desactivar por dominio.
- Actualizar listas sin obligar a actualizar la APK.

### Criterio de aceptación

Para cada sitio de prueba:

- la página carga;
- los pop-ups conocidos no interrumpen;
- el video sigue visible;
- el manifest se detecta;
- la TV reproduce;
- desactivar el bloqueo restaura el comportamiento original.

## 8. Plan de trabajo para mañana

### Paso 1: crear proyecto separado

- Crear un repositorio nuevo para la app móvil.
- No mezclarlo con el proyecto del scraper ni con el APK actual.
- Registrar plataforma objetivo: Android primero.
- Elegir Kotlin + Jetpack Compose o XML según la experiencia del equipo.
- Separar módulos `browser`, `adblock`, `media-detection`, `cast`, `devices` y `ui`.

### Paso 2: prueba vertical mínima

Construir una app que:

- abra un sitio de prueba en WebView;
- detecte un MP4 conocido;
- permita escribir la URL manual de la TV;
- envíe título, URL y User-Agent;
- muestre en la TV un receptor mínimo;
- reproduzca con el control remoto.

No implementar todavía listas adblock, múltiples sitios ni login.

### Paso 3: probar contrato de recepción

- Definir transporte: HTTP local, WebSocket o intent/Deep Link.
- Probar URL MP4.
- Probar HLS sin headers.
- Probar HLS con User-Agent y Referer.
- Probar tokens en query string.
- Probar pérdida de conexión del celular después de enviar.

### Paso 4: detector real

- Agregar captura de requests.
- Presentar una lista de candidatos.
- Separar detección de validación.
- Mostrar motivo cuando una fuente falla.

### Paso 5: ad blocker

- Integrar parser/lista después de tener reproducción funcionando sin bloqueo.
- Probar primero con logging de decisiones.
- Activar bloqueo por defecto solo después de comparar con bloqueo desactivado.

### Paso 6: UX final

- Navegación independiente del estado de reproducción.
- Estado persistente de TV seleccionada.
- Reenvío de otro video sin cortar accidentalmente el actual.
- Foco y errores claros en la app TV.
- Historial o cola solo si el flujo básico lo necesita.

## 9. Qué no hacer al principio

- No hacer proxy del video desde el celular.
- No implementar iOS en paralelo.
- No intentar soportar todos los sitios con parsers específicos.
- No prometer compatibilidad con DRM.
- No usar screen mirroring como solución principal.
- No agregar login, cuentas o nube.
- No guardar cookies ni headers sensibles en logs.
- No considerar que “encontré `.m3u8`” equivale a “la TV reproduce”.

## 10. Skills recomendadas

Instalar o activar, si están disponibles para la sesión:

- `agent-vigilante`: revisar supuestos, contratos y falsación de resultados.
- Una skill de desarrollo Android/Kotlin/Jetpack Compose.
- Una skill de UX/UI móvil y navegación de reproductores.
- Una skill de testing Android y pruebas en dispositivos reales.
- `security-best-practices`: revisar WebView, URLs, headers, cookies y red local.
- `security-threat-model`: modelar ataques desde una página web o dispositivo de la LAN.
- `playwright`: pruebas reproducibles de páginas y detección de requests en navegador.
- `android-tv-release`: solo si se modifica el receptor de la app Android TV existente.
- `futbol-principal-architecture`: solo si el protocolo se integra con el servidor o APK actual.

No instalar skills por cantidad. La skill debe aportar instrucciones ejecutables al stack elegido.

## 11. Criterios de terminado del MVP

El MVP no está terminado porque la app compile. Debe demostrar en un dispositivo Android real y una TV real:

- navegación dentro de la app;
- detección de al menos un MP4 y un HLS;
- envío a la TV;
- reproducción directa en la TV;
- control remoto operativo;
- navegación posterior en el celular sin cortar la reproducción;
- headers y query strings conservados;
- ad blocker desactivable;
- error visible cuando un sitio no puede reproducirse;
- sin proxy de video en el celular;
- sin secretos en logs.

## 12. Conclusión operativa

La primera tarea no es diseñar toda la app. Es probar el contrato celular -> receptor TV con un MP4 y un HLS. Si ese contrato no funciona con headers y tokens, el resto de la app sería trabajo cosmético.
