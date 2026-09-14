---
name: futbol-ui-ux
description: "Revisar y mejorar la experiencia visual e interacción de Fútbol Libre en la web Flask/Jinja y en el APK Android TV/teléfono."
---

# Fútbol Libre UI/UX

Skill específica para este repositorio. Aplicarla cuando se cambie la interfaz web, la navegación del APK, los controles del reproductor, el responsive, el touch o la presentación de estados.

## Contexto del producto

- La web usa Flask/Jinja, HTML, CSS y JavaScript sin framework frontend.
- La web sirve operación del servidor, agenda, canales y reproducción HLS.
- El APK usa Java, `TvScreenView` con Canvas y listas nativas; funciona con D-pad/OK/Back en TV y touch/swipe en teléfono.
- El flujo principal es: evento → fuente → preview → reproducción → PiP/segundo evento.
- La identidad actual es oscura, sobria y deportiva: fondo azul oscuro, tarjetas azul grisáceas y acento turquesa.
- El emoji ⚽ del estado de búsqueda es intencional y debe conservarse salvo pedido explícito.

## Criterios prioritarios

1. No romper el flujo de reproducción ni los contratos existentes (`/api/v1/events`, `/api/v1/agenda`, APK y streams).
2. Cada acción importante debe ser visible, operable y tener feedback: tocar, enfocar, cargar, error, éxito y estado deshabilitado.
3. Web: usar controles HTML semánticos, foco visible, `aria-current`, nombres accesibles y no depender de hover.
4. Web móvil: evitar scroll horizontal; mantener texto base de 16 px; targets cómodos (idealmente 44 px o más); dejar al menos 8 px entre acciones.
5. APK: conservar D-pad/OK/Back y ofrecer una acción táctil visible equivalente; usar targets de al menos 48 dp y no hacer que un tap ambiguo ejecute una acción crítica.
6. Gestos: usar swipe vertical para listas; no bloquear Back ni otros gestos del sistema; no hacer que una acción crítica dependa solo de swipe.
7. Safe areas: no fijar offsets arbitrarios si se pueden obtener insets reales; no ocultar contenido detrás de barras del sistema o del reproductor.
8. Contraste: texto normal ≥ 4.5:1; el color no debe ser el único indicador de estado; los iconos de controles deben tener nombre accesible.
9. Animación: debe comunicar un cambio; preferir transform/opacity; respetar `prefers-reduced-motion`; no mantener repaints o timers cuando la pantalla no los necesita.
10. Mantener una sola dirección visual. No agregar glassmorphism, 3D, auroras, gradientes decorativos ni fuentes externas sin una necesidad comprobable.

## Revisión por superficie

### Web

- Separar visualmente entry points y procesos distintos.
- Usar `button`, `a`, `input`, `details` y `summary` antes que `div[role=button]`.
- Mantener los logs cerrados por defecto si son secundarios, pero expandibles sin perder el estado.
- En canales, distinguir evento, fuente, abrir inline y abrir ventana nueva.
- Mostrar el error del reproductor cerca del reproductor, con una recuperación concreta.
- Probar 320/375/414 px y desktop. Confirmar que las tarjetas, navegación, video y acciones no desborden.

### APK

- Las acciones de preview deben verse como botones, no como instrucciones entre corchetes.
- El área tocable debe coincidir con lo que se dibuja; un toque fuera no debe activar reproducción accidentalmente.
- Mantener selección/foco visible para TV y estado pressed/selected para touch.
- Describir eventos y fuentes con `contentDescription` cuando se dibujen como vistas nativas.
- Diferenciar preview, fullscreen y DUAL/PiP; Back debe volver un nivel predecible.
- El loading ⚽ se conserva, pero su animación solo corre durante `SEARCHING`.

## Validación

- Revisar `git status` antes de editar y preservar cambios no relacionados.
- Ejecutar `python3 -m pytest -q tests`, `node --check src/server/static/app.js` y `git diff --check`.
- Compilar el APK con `ANDROID_HOME` configurado: `cd src/tvapp && ./gradlew test assembleDebug`.
- Separar evidencia determinista de evidencia real: compilación/tests no prueban que un stream funcione ni que el layout sea correcto en una TV o teléfono físico.
- No publicar ni reemplazar el APK distribuible sin autorización explícita.

Para el checklist detallado de una revisión, leer [references/checklist.md](references/checklist.md).
