# Instaladores

Cada instalador prepara el runtime disponible para el sistema, crea `.env` solo si no existe y ejecuta:

```text
docker compose -f docker/docker-compose.yml up --build -d
```

- Linux Debian/Ubuntu: `install-linux.sh`
- macOS: doble clic en `install-macos.command`
- Windows: doble clic en `install-windows.bat`

La primera instalación necesita permisos de administrador y acceso a Internet para instalar Docker Desktop/Engine y descargar las imágenes. Una vez iniciado, el servidor queda en `http://localhost:8080` y SearXNG en `http://localhost:8081`.

La primera carga del catálogo es manual. Desde la raíz del repositorio ejecutá:

```bash
docker compose -f docker/docker-compose.yml run --rm futbol ./update-futbollibre.sh
```

Repetí el mismo comando cuando quieras actualizar los eventos.
