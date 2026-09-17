"""Extracción del layout moderno basado en ``article.fl-event``."""


class FlEventStrategy:
    nombre = "fl-event"

    def extraer(self, driver):
        return driver.execute_script(
            """
            const resultado = [];
            const horaValida = /^([01]\\d|2[0-3]):[0-5]\\d$/;

            for (const bloque of document.querySelectorAll('article.fl-event')) {
                const horaNode = bloque.querySelector('.fl-event-time');
                const hora = (
                    horaNode?.dataset.originalTime ||
                    horaNode?.dataset.flOriginalTime ||
                    horaNode?.textContent || ''
                ).replace(/\\s+/g, ' ').trim();
                if (!horaValida.test(hora)) continue;

                const titulo = bloque.querySelector('.fl-event-title');
                if (!titulo) continue;
                const competencia = titulo.querySelector('.fl-event-competition');
                const partido = titulo.cloneNode(true);
                partido.querySelectorAll('.fl-event-competition').forEach(node => node.remove());
                const nombrePartido = partido.textContent.replace(/\\s+/g, ' ').trim();
                const nombreCompetencia = competencia
                    ? competencia.textContent.replace(/\\s+/g, ' ').trim().replace(/:$/, '')
                    : '';
                const nombre = nombreCompetencia && nombrePartido
                    ? `${nombreCompetencia}: ${nombrePartido}`
                    : nombrePartido || nombreCompetencia;
                if (!nombre) continue;

                const opciones = Array.from(bloque.querySelectorAll('.fl-event-channel[href]'))
                    .map(anchor => ({
                        url: anchor.href,
                        canal: anchor.textContent.replace(/\\s+/g, ' ').trim() || 'Opción'
                    }))
                    .filter(opcion => opcion.url);
                if (!opciones.length) continue;

                resultado.push({
                    nombre,
                    hora,
                    logo: (bloque.querySelector('.fl-event-image') || {}).src || '',
                    opciones
                });
            }
            return resultado;
            """
        ) or []
