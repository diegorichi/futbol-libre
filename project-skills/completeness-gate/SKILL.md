---
name: completeness-gate
description: "Control de completitud para flujos de trabajo: revisa faltantes al menos dos veces y obliga a reportarlos si el flujo se corta."
---

# Completeness Gate

Usá esta skill en tareas con varias partes, dependencias, migraciones,
integraciones o criterios de aceptación donde cerrar prematuramente puede dejar
trabajo omitido.

## Regla obligatoria

Revisá qué falta al menos dos veces, en momentos distintos:

1. **Antes de cerrar el plan o comenzar la ejecución:** contrastá la solicitud
   contra el inventario, consumidores, contratos, configuración, tests,
   documentación y criterios de aceptación.
2. **Antes de declarar terminado o detener el flujo:** repetí la revisión contra
   el estado actual, cambios realizados, validaciones, riesgos y pendientes.

La segunda revisión debe poder descubrir omisiones introducidas durante la
ejecución; no cuenta repetir la misma lista sin contrastar evidencia nueva.

## Si el flujo se corta

Si el usuario pide detenerse, aparece un bloqueo, falta autorización o se agota
el alcance, no ocultes los pendientes. Informá brevemente:

- qué quedó completado;
- qué falta exactamente, con archivo/componente cuando exista;
- por qué no se pudo continuar;
- qué decisión, acceso o evidencia permitiría retomarlo.

No declares éxito parcial como finalización. Si no hay faltantes, decilo
explícitamente y mencioná qué evidencia cerró la revisión.

## Evidencia mínima

Separá hechos verificados, inferencias y pendientes. Revisá también callers,
errores, estados vacíos, rollback, artefactos generados y basura no trackeada.
No borres ni marques obsoleto algo que todavía tenga consumidores sin una
transición y validación.

## Salida

Terminá con una sección corta `Control de completitud` que indique:

- revisión 1: resultado y faltantes;
- revisión 2: resultado y faltantes nuevos/resueltos;
- estado: `completo`, `parcial` o `bloqueado`;
- pendientes explícitos si el estado no es `completo`.
