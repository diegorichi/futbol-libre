# Plan de refactor del APK Fútbol TV

## Objetivo

Hacer que los cambios de navegación, layout y UI sean previsibles sin romper los contratos existentes entre el APK y el servidor.

## Estado de ejecución

- Fase 1: completada y validada.
- Fase 2A: implementada y validada por tests de geometría/estrategias; falta prueba visual en emulador/TV.
- Fase 2B: implementada a nivel de código. El Canvas vive en `ui/render/TvCanvasRenderer`, el input bruto en `input/TvScreenInputController` y `TvScreenView` quedó como adaptador Android de 105 líneas.
- Fase 4: completada y validada. Las 26 clases migradas están distribuidas por responsabilidad en `state`, `input`, `layout`, `ui.render`, `catalog`, `playback`, `discovery` y `ui.list`.

## Diagnóstico confirmado

- `MainActivity` coordinaba descubrimiento mDNS/UDP, carga de catálogo, actualización, estado de pantalla, navegación, touch, D-pad y reproducción.
- `TvScreenView` sólo compone la vista y delega Canvas/input; las listas, el Canvas y el input viven en sus respectivos componentes.
- La geometría compartida está en `TvLayoutMetrics`; la prueba automatizada no reemplaza una verificación visual real.
- `TvScreenView` selecciona una estrategia una sola vez: `TvCompactLayout` o `TvTelevisionLayout`. No recalcula el tipo de layout durante cada render.
- `TvNavigationController` ahora mantiene objetos `ScreenState` con comportamiento de transición y Back. `TvScreenState` fue eliminado; los efectos específicos de Back (PiP, preview, reproducción y update) viven en cada estado, no en `MainActivity`.
- La UI usa colores, márgenes y tamaños literales dispersos, sin tokens ni un único modelo de layout.
- Hay una sola prueba unitaria directa de navegación; no hay pruebas de Activity, layout ni flujo de reproducción.

## Contratos que no se modifican

- `/api/v1/events`, `/api/v1/app` y `/api/v1/discovery`.
- Descubrimiento por mDNS y fallback UDP en el puerto `45678`.
- `server_url` explícito y fallback de emulador `10.0.2.2:8080`.
- HLS directo, `PlaybackController`, selección de fuente y dual playback interno.
- D-pad, OK, Back, touch y actualización remota.

## Fase 1 — separación de responsabilidades

### 1. Estado, navegación y coordinación

- Modelar cada pantalla como un objeto `ScreenState`; no existe una clase mutable `TvScreenState`.
- Centralizar el estado actual y las transiciones de Back en `TvNavigationController`.
- Extraer catálogo/actualizaciones a `TvCatalogController`.
- Extraer reproducción, VPN y dual playback a `TvPlaybackCoordinator`.
- Extraer touch, scroll, D-pad y OK a `TvInputController`.
- Extraer binding de listas a `TvListBinder`.
- Probar transiciones válidas, límites y estados terminales.

### 2. Descubrimiento del servidor

- Extraer mDNS, timeout, fallback de emulador y broadcast UDP a `ServerDiscoveryController`.
- Mantener el callback de conexión en la Activity.
- Detener listeners, callbacks y sockets en `onDestroy`.
- No alterar URLs ni el orden de descubrimiento.

### 3. Validación de la fase

- Ejecutar tests unitarios del módulo.
- Compilar `assembleDebug`.
- Revisar referencias residuales a la lógica vieja.
- Verificar que no cambien los contratos del servidor.
- No declarar validación de TV física sin instalar y probar en una TV real.

## Fase 2 — UI y geometría

### Fase 2A — geometría y tokens — implementada

- Extraer `LayoutMetrics` y tokens de color, spacing y tamaños.
- Unificar rectángulo visual, hitbox y foco de cada control.
- Unificar el cálculo de filas y selección táctil de eventos y fuentes.
- Definir centrado, safe areas, targets mínimos, orientación y foco D-pad de forma determinista.
- Mantener touch, D-pad, Back y navegación existente.

### Fase 2B — componentes de pantalla — parcialmente implementada

- Separar componentes de pantalla: header, listas, preview, controles y estados.
- Separar la selección de renderers concretos por `ScreenState`.
- Reducir la responsabilidad de `TvScreenView` a composición, ciclo de vida y delegación de input.

## Fase 4 — organización de paquetes

- Separar las 26 clases migradas por responsabilidad: `state`, `navigation`, `input`, `layout`, `render`, `catalog`, `playback`, `discovery` y `list`.
- Ajustar visibilidad e imports sin mover contratos externos.
- Compilar y revisar referencias residuales después de cada grupo.

## Fase 3 — reproducción y ciclo de vida

- Verificar en dispositivo el coordinador de reproducción ya extraído.
- Mantener explícita la diferencia entre dual playback interno y PiP del sistema Android.
- Agregar pruebas de cambio de fuente, cierre, pausa, reanudación y error.

## Criterio de finalización

La Fase 1 se considera completa: compila, pasan los tests, `MainActivity` ya no implementa mDNS/UDP, catálogo, actualización, reproducción ni traducción de input directamente; el estado está centralizado y los contratos externos siguen sin cambios.

## Evidencia de esta iteración

- `MainActivity.java`: 378 líneas; coordina ciclo de vida y composición.
- `TvScreenView.java`: 105 líneas; sólo composición de listas, ciclo de vida y delegación.
- `ui/render/TvCanvasRenderer.java`: renderiza estados, textos, botones, listas visuales, preview y variantes compactas.
- `input/TvScreenInputController.java`: recibe D-pad, touch, scroll, gestos y hit-testing de controles de preview.
- `catalog/TvCatalogController.java`: catálogo, logos y actualización.
- `catalog/TvCatalogControllerListener.java`: adapta callbacks de catálogo, actualización y logos sin listener anónimo en la Activity.
- `input/TvInputController.java`: despacha input a handlers por estado; `onConfirm`, `onDpad`, `scroll` y `tap` ya no contienen el router completo de pantallas.
- Los contratos `Host.state()` y `TvNavigationController.current()` transportan `ScreenState`; no hay `int state()` en los hosts.
- `TvCanvasStateRenderer` concentra la selección del renderer por estado; `TvScreenView` ya no tiene la cadena principal de dibujo por estado.
- `goTo` recibe `ScreenState` en todos los hosts y en `TvNavigationController`; no queda `goTo(int)`.
- `playback/TvPlaybackCoordinator.java`: reproducción, VPN y dual playback.
- `input/TvInputController.java`: touch semántico, scroll, D-pad y OK.
- `ui/list/TvListBinder.java`: binding y visibilidad de RecyclerViews.
- `ui/layout/TvLayoutProfile.java`, `TvCompactLayout.java`, `TvTelevisionLayout.java`: estrategia de layout instanciada al crear la vista.
- `state/ScreenState.java`, `ScreenStates.java`, `TvNavigationController.java`: patrón State y navegación por objetos, no por enteros.
- `ScreenState` expone `eventListVisible()`, `sourceListVisible()`, `isPipList()`, `isSearching()`, `isPreview()` e `isDual()`; los consumidores ya no comparan estados concretos para esas decisiones.
- `ui/render/TvCanvasStateRenderer.java` y renderers concretos: dispatch visual por estado.
- Preview recuperado: muestra evento y fuente/canal activos, conserva cambio de canal arriba/abajo, usa iconos geométricos para fullscreen/PiP y aplica el rojo VPN de la web (`#7f1d1d`). Renderer y hit-testing comparten `TvLayoutMetrics.PreviewLayout`.
- `./gradlew testDebugUnitTest assembleDebug`: correcto.
- `./gradlew lintDebug`: correcto; se agregaron capacidades TV opcionales, banner y opt-in explícito de Media3.
- `git diff --check`: correcto.
- Falta todavía validación visual en emulador/TV; la compilación no prueba centrado ni foco en hardware.
- La validación visual en emulador/TV sigue pendiente. En este host no están disponibles `adb`, `emulator` ni `avdmanager`; la compilación no prueba centrado, foco ni targets táctiles en hardware.
