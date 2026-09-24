---
name: futbol-future-agenda
description: Mantener o cambiar las pestañas de agenda deportiva futura sin mezclarla con la agenda de hoy generada por los sitios de streaming.
---

# Agenda futura de Fútbol Libre

- Leer `docs/ARCHITECTURE.md` y rastrear ambos productores antes de cambiar `/agenda`.
- Tratar `data/agenda_web.json` como la agenda de hoy: conserva sus reglas, su productor y `/api/v1/agenda`.
- Tratar `data/agenda_future.json` como una proyección independiente, actualizada una vez por día desde las fuentes configuradas de Clarín y TyC Sports.
- Exigir fecha y hora explícitas para cada evento futuro. No usar `EventClock.nearest()` ni convertir una hora nocturna en “mañana”.
- Excluir la fecha local actual de la fuente futura aunque la página externa la publique.
- Si la fuente cambia de contrato o falla, conservar el último archivo válido mediante escritura atómica y reportar el error; no publicar una agenda vacía.
- Fusionar fuentes por fecha/hora, equipos normalizados y torneo compatible. No deduplicar solo por título ni solo por horario; partidos distintos pueden comenzar juntos.
- Al fusionar un duplicado, conservar una fila y combinar los canales sin repetirlos. Exigir que todas las fuentes respondan antes de reemplazar el archivo válido.
- `/agenda` puede combinar ambos archivos solo en presentación: `Hoy` lee exclusivamente el archivo actual y las pestañas posteriores leen exclusivamente el futuro.
- Los filtros transversales deben operar en presentación sobre los días ya cargados; no deben fusionar ni reescribir los productores de agenda.
- Mantener días calendario vacíos visibles cuando la fuente no entregue eventos para ellos.
- Validar el parser con fixture determinista, el servicio futuro, las siete pestañas y una consulta real separada. La consulta real prueba extracción, no exactitud editorial de la fuente.
