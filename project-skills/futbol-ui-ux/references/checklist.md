# Checklist Fútbol UI/UX

## Interacción

- [ ] La acción principal de cada pantalla se entiende sin leer documentación.
- [ ] Todos los botones tienen estado hover/focus/pressed/disabled apropiado.
- [ ] Web: foco visible y orden de teclado igual al orden visual.
- [ ] APK: D-pad/OK/Back siguen funcionando.
- [ ] APK: cada acción de touch tiene un control visible equivalente.
- [ ] No hay controles críticos menores de 44 px web o 48 dp Android.
- [ ] Hay una separación mínima de 8 px/dp entre controles adyacentes.
- [ ] Las acciones asíncronas muestran carga y evitan doble ejecución.
- [ ] Los errores indican qué pasó y qué puede hacer el usuario.

## Reproductor

- [ ] Evento, fuente, preview, fullscreen y PiP son estados distinguibles.
- [ ] Abrir inline y abrir ventana nueva son acciones separadas.
- [ ] El fallo HLS se muestra cerca del video y ofrece probar otra fuente.
- [ ] El toque fuera de un botón no inicia una acción crítica.
- [ ] Al cerrar o navegar atrás se detiene/libera el reproductor correcto.
- [ ] No se afirma que un stream funciona sin probarlo realmente.

## Responsive y layout

- [ ] No existe scroll horizontal en 320, 375 ni 414 px.
- [ ] El texto principal conserva al menos 16 px en la web.
- [ ] Las listas siguen siendo legibles en portrait y landscape.
- [ ] El video mantiene una proporción y no provoca saltos de layout evitables.
- [ ] Las barras fijas no tapan contenido ni foco.
- [ ] El APK usa insets del sistema cuando la pantalla tiene navegación inferior.

## Visual y accesibilidad

- [ ] El contraste del texto normal alcanza 4.5:1 en la paleta oscura.
- [ ] El color no es el único indicador de selección, error o disponibilidad.
- [ ] Los iconos sin texto visible tienen nombre accesible.
- [ ] Los logos decorativos no interrumpen la lectura accesible.
- [ ] No se agregan estilos decorativos que dificulten leer deportes, horarios o fuentes.
- [ ] El emoji ⚽ del loading se mantiene y solo se anima mientras se busca servidor.

## Evidencia

- [ ] Tests del proyecto ejecutados.
- [ ] Sintaxis JavaScript validada.
- [ ] APK compilado si el Android SDK está disponible.
- [ ] Prueba visual en navegador realizada o marcada como pendiente.
- [ ] Prueba física en teléfono/TV diferenciada de la compilación.
