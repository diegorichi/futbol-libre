"""Compatibilidad con la estructura anterior basada en ``#menu``."""


class MenuStrategy:
    nombre = "menu"

    def extraer(self, driver):
        return driver.execute_script(
            """
            return Array.from(document.querySelectorAll('#menu > li.toggle-submenu')).map(li => ({
                nombre: li.querySelector(':scope > div span')
                    ? li.querySelector('div span').textContent.trim() : '',
                hora: li.querySelector(':scope > div time')
                    ? li.querySelector(':scope > div time').textContent.trim() : '00:00',
                logo: li.querySelector(':scope > div img')
                    ? li.querySelector(':scope > div img').src : '',
                opciones: Array.from(li.querySelectorAll('a.submenu-item[href]')).map(a => ({
                    url: a.href,
                    canal: a.querySelector('span')
                        ? a.querySelector('span').textContent.trim() : 'Opción'
                }))
            }));
            """
        ) or []
