---
name: futbol-developer-refactor
description: "Refactor Python systems with existing contracts by tracing callers, replacing procedural modules with cohesive classes, removing obsolete facades, and validating behavior."
---

# Desarrollo y refactorización estructural

Usar cuando un módulo Python mezcle configuración, infraestructura, dominio, persistencia y presentación, o cuando el usuario pida separar responsabilidades sin romper callers.

## Reglas de trabajo

- Leer primero `docs/ARCHITECTURE.md`, reglas locales y el estado del worktree. Buscar callers directos e indirectos con `rg` antes de renombrar o eliminar.
- Clasificar cada función como lógica real, adaptador o fachada. La fachada se elimina solo después de migrar todos sus callers; no conservar aliases “por si acaso”.
- Mover el comportamiento real al objeto dueño de la responsabilidad. No crear clases decorativas cuyos métodos solo llamen a las funciones que supuestamente reemplazan.
- Preferir una clase cohesiva por módulo; no superar una clase por archivo. Separar configuración, validación, dominio, scraping, publicación, persistencia y notificación cuando tengan ciclos de vida o dependencias distintas.
- Inyectar factories, clientes, relojes y persistencia en los servicios que los usan. No esconder dependencias en globals ni leer configuración dentro de cada método.
- Mantener los contratos observables: formatos, nombres de campos, query strings, User-Agent, orden de etapas, escritura atómica, cierre de recursos y semántica de errores.
- Hacer que el caso de uso principal sea una coordinación legible de etapas. Los detalles deben vivir en métodos de servicios concretos, no en un `run()` monolítico ni en helpers top-level.

## Logging operativo

- Configurar un logger por módulo y no usar `print` para diagnóstico operativo.
- Soportar `INFO`, `DEBUG` y `TRACE` (nivel 5 custom). `INFO` registra etapas y resultados; `DEBUG` decisiones y dependencias; `TRACE` elementos individuales detectados o descartados.
- Registrar contexto útil: sitio, URL, estrategia, cantidad, estado y excepción. No registrar secretos, tokens ni payloads sensibles.
- Diferenciar detección, disponibilidad y reproducibilidad. Encontrar un evento o `.m3u8` no equivale a tener un stream reproducible.

## Validación obligatoria

- Ejecutar compilación/importación, tests focalizados y suite mantenida.
- Barrer referencias residuales a nombres eliminados y contar clases/funciones top-level en los módulos afectados.
- Probar estados de error: dominio caído, CAPTCHA o HTML inválido, iframe inaccesible, URL sin stream, fallo de publicación y cierre de Selenium.
- Separar evidencia local de evidencia end-to-end contra sitios reales, TV, Threadfin o servicios externos.
- Reportar hechos verificados, cambios realizados y pendientes; no declarar una migración completa si quedan fachadas, callers sin actualizar o lógica duplicada.
