import os
import requests
import subprocess
from datetime import datetime, timezone
from dataclasses import asdict
from pathlib import Path
from urllib.parse import urlencode

from dotenv import dotenv_values, load_dotenv, set_key
from flask import Flask, Response, jsonify, render_template, request, send_file

from server.models.task_status import TaskStatus
from server.services.agenda_service import AgendaService
from server.services.catalog_service import CatalogService
from server.services.web_agenda_service import WebAgendaService
from server.services.process_runner import ProcessRunner
from server.discovery import MdnsAdvertiser, UdpDiscoveryResponder
from server.services.vpn_service import VpnService
from server.services.vpn_stream_resolver import VpnStreamResolver
from server.services.hls_relay import HlsRelay
from infrastructure.progress import ProgressReporter


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = Path(os.getenv("ENV_FILE", PROJECT_ROOT / ".env"))
if not ENV_PATH.is_absolute():
    ENV_PATH = PROJECT_ROOT / ENV_PATH
load_dotenv(ENV_PATH)

app = Flask(__name__)
status = TaskStatus()
runner = ProcessRunner(str(PROJECT_ROOT), status, os.getenv("LOG_LOCATION"))
PROGRESS_PATH = Path(os.getenv("PROGRESS_FILE", PROJECT_ROOT / "data/.update-futbollibre.progress.json"))
if not PROGRESS_PATH.is_absolute():
    PROGRESS_PATH = PROJECT_ROOT / PROGRESS_PATH
progress = ProgressReporter(str(PROGRESS_PATH))
runner.recover()
mdns = MdnsAdvertiser(port=8080)
udp_discovery = UdpDiscoveryResponder(http_port=8080)
vpn_service = VpnService(ENV_PATH)
TV_APP_VERSION_CODE = int(os.getenv("TV_APP_VERSION_CODE", "20"))
TV_APP_VERSION_NAME = os.getenv("TV_APP_VERSION_NAME", "2.0")
TV_APP_APK_PATH = Path(os.getenv("TV_APP_APK_PATH", PROJECT_ROOT / "output/futbol-tv-release.apk"))
if not TV_APP_APK_PATH.is_absolute():
    TV_APP_APK_PATH = PROJECT_ROOT / TV_APP_APK_PATH


def configured_path(env_name, fallback):
    value = os.getenv(env_name)
    return Path(value) if value else PROJECT_ROOT / fallback


def urls_env_path():
    path = Path(os.getenv("FUTBOL_LIBRE_URL_FILE", PROJECT_ROOT / "config/futbol_libre_urls.env"))
    return path if path.is_absolute() else PROJECT_ROOT / path


def current_futbol_urls():
    values = dotenv_values(urls_env_path())
    return values.get("FUTBOL_LIBRE_URL") or os.getenv("FUTBOL_LIBRE_URL", "")


def current_extra_futbol_url():
    values = dotenv_values(urls_env_path())
    return values.get("FUTBOL_LIBRE_EXTRA_URL") or os.getenv("FUTBOL_LIBRE_EXTRA_URL", "")


def agenda_service():
    return AgendaService(dotenv_values(ENV_PATH))


@app.get("/")
@app.get("/ejecutar")
def executor_page():
    search_query = os.getenv("SEARXNG_QUERY", "futbol libre")
    return render_template(
        "executor.html",
        current_url=current_futbol_urls(),
        current_extra_url=current_extra_futbol_url(),
        search_url=f"https://duckduckgo.com/?{urlencode({'q': search_query})}",
    )


@app.get("/canales")
def channels_page():
    try:
        service = CatalogService(
            configured_path("XML_FILE", "data/eventos.xml"),
            configured_path("M3U_FILE", "data/eventos.m3u"),
            configured_path("TV_EVENTS_FILE", "data/eventos.json"),
        )
        return render_template(
            "channels.html",
            events=service.groups(),
            source_dates=service.source_update_dates(),
            vpn_enabled=vpn_service.enabled,
        )
    except FileNotFoundError:
        return render_template(
            "channels.html",
            channels=[],
            source_dates={"xml": "No disponible", "m3u": "No disponible"},
            vpn_enabled=vpn_service.enabled,
        )


@app.get("/agenda")
def agenda_page():
    events = WebAgendaService(configured_path("AGENDA_FILE", "data/agenda_web.json")).events()
    grouped = {}
    for event in events:
        grouped.setdefault(event["date"], []).append(event)
    return render_template("agenda.html", agenda=grouped)


@app.get("/sistemas")
def systems_page():
    return render_template("systems.html")


@app.post("/update-url")
def update_url():
    data = request.get_json(silent=True) or {}
    new_url = (data.get("url") or "").strip()
    extra_url = (data.get("extra_url") or "").strip()
    only_extra = bool(data.get("only_extra"))
    if not new_url and not only_extra:
        return jsonify(success=False, error="URL no proporcionada."), 400
    if only_extra and not extra_url:
        return jsonify(success=False, error="La URL adicional es obligatoria."), 400
    if "," in extra_url:
        return jsonify(success=False, error="El sitio adicional debe ser una sola URL."), 400
    if runner.is_running() or status.snapshot()["is_running"]:
        current_status = status.snapshot()
        current_status["is_running"] = True
        current_status["output"] = runner.tail_output()
        current_status["progress"] = progress.snapshot()
        return jsonify(success=False, error="Ya hay una actualización en curso.", running=True, status=current_status), 409
    try:
        urls_file = urls_env_path()
        urls_file.parent.mkdir(parents=True, exist_ok=True)
        if not only_extra:
            set_key(str(urls_file), "FUTBOL_LIBRE_URL", new_url)
        if only_extra or extra_url:
            set_key(str(urls_file), "FUTBOL_LIBRE_EXTRA_URL", extra_url)
        progress.reset()
        arguments = ["--extra-only"] if only_extra else []
        if not runner.start("update-futbollibre.sh", arguments):
            return jsonify(success=False, error="Ya hay una actualización en curso."), 409
        return jsonify(success=True)
    except Exception as error:
        return jsonify(success=False, error=str(error)), 500


@app.get("/status")
def task_status():
    current_status = status.snapshot()
    current_status["output"] = runner.tail_output()
    current_status["progress"] = progress.snapshot()
    if runner.is_running():
        current_status["is_running"] = True
        if not current_status["message"]:
            current_status["message"] = "Actualización detectada en curso."
    return jsonify(current_status)


@app.post("/stop-update")
def stop_update():
    if not runner.stop():
        return jsonify(success=False, error="No hay una actualización corriendo."), 404
    progress.fail("Proceso detenido por el usuario.")
    return jsonify(success=True, message="Proceso detenido.")


@app.get("/grilla")
def grid_api():
    try:
        channels = CatalogService(
            configured_path("XML_FILE", "data/eventos.xml"),
            configured_path("M3U_FILE", "data/eventos.m3u"),
            configured_path("TV_EVENTS_FILE", "data/eventos.json"),
        ).channels()
        return jsonify([channel.__dict__ for channel in channels])
    except FileNotFoundError:
        return jsonify([])


def tv_channel_service():
    # Todas las interfaces leen el documento canónico; XML/M3U solo se
    # mantienen como proyecciones para Threadfin y consumidores legacy.
    return CatalogService(
        configured_path("XML_FILE", "data/eventos.xml"),
        configured_path("M3U_FILE", "data/eventos.m3u"),
        configured_path("TV_EVENTS_FILE", "data/eventos.json"),
    )


vpn_stream_resolver = VpnStreamResolver(tv_channel_service(), vpn_service, ENV_PATH)
vpn_relay = HlsRelay(vpn_service)


@app.get("/api/v1/health")
def tv_health():
    return jsonify({"ok": True, "service": "futbol-server", "api_version": "v1"})


def stream_capabilities():
    status = vpn_service.capability()
    return {
        "vpn_enabled": status["enabled"],
        "vpn_available": status["available"],
        "vpn_proxy_url": status["proxy_url"],
        "vpn_url_ttl_hours": status["ttl_hours"],
    }


@app.get("/api/v1/events")
def tv_events():
    try:
        events = [asdict(event) for event in tv_channel_service().events()]
        return jsonify({
            "api_version": "v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "refresh_after": 60,
            "streaming": stream_capabilities(),
            "events": events,
        })
    except FileNotFoundError:
        return jsonify({"api_version": "v1", "generated_at": None, "refresh_after": 60, "streaming": stream_capabilities(), "events": []})


@app.post("/api/v1/stream-url")
def vpn_stream_url():
    payload = request.get_json(silent=True) or {}
    event_id = str(payload.get("event_id") or "").strip()
    source_id = str(payload.get("source_id") or "").strip()
    if not event_id or not source_id:
        return jsonify({"ok": False, "error": "event_id y source_id son obligatorios."}), 400
    status = vpn_service.status()
    if not status["enabled"]:
        return jsonify({"ok": False, "error": "Streaming VPN deshabilitado."}), 404
    try:
        result = vpn_stream_resolver.resolve(event_id, source_id, force=bool(payload.get("force")))
        return jsonify({"ok": True, **result, "proxy_url": status["proxy_url"]})
    except LookupError as error:
        return jsonify({"ok": False, "error": str(error)}), 404
    except RuntimeError as error:
        return jsonify({"ok": False, "error": str(error)}), 503


@app.get("/api/v1/stream-relay/<event_id>/<source_id>")
@app.get("/api/v1/stream-relay/<event_id>/<source_id>/<resource_id>")
def stream_relay(event_id, source_id, resource_id=None):
    if not vpn_service.enabled:
        return jsonify({"ok": False, "error": "Streaming VPN deshabilitado."}), 404
    try:
        result = vpn_stream_resolver.resolve(event_id, source_id)
        body, content_type = vpn_relay.fetch(event_id, source_id, result["url"], resource_id)
        response = Response(body, content_type=content_type)
        response.headers["Cache-Control"] = "no-store"
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response
    except LookupError as error:
        return jsonify({"ok": False, "error": str(error)}), 404
    except RuntimeError as error:
        return jsonify({"ok": False, "error": str(error)}), 503
    except (ValueError, requests.RequestException) as error:
        return jsonify({"ok": False, "error": str(error)}), 502


@app.get("/api/v1/agenda")
def web_agenda():
    events = WebAgendaService(configured_path("AGENDA_FILE", "data/agenda_web.json")).events()
    return jsonify({"api_version": "v1", "generated_at": datetime.now(timezone.utc).isoformat(), "events": events})


@app.get("/api/v1/discovery")
def tv_discovery():
    return jsonify({"name": "Futbol Server", "api_version": "v1", "events_path": "/api/v1/events", "streaming": stream_capabilities()})


@app.get("/tvapp")
def tv_app_page():
    return render_template("tvapp.html", version=TV_APP_VERSION_NAME)


@app.get("/api/v1/app")
def tv_app_info():
    return jsonify({
        "api_version": "v1",
        "version_code": TV_APP_VERSION_CODE,
        "version_name": TV_APP_VERSION_NAME,
        "apk_url": "/downloads/futbol-tv.apk",
        "changelog": "Actualización de Fútbol TV",
        "streaming": stream_capabilities(),
    })


@app.get("/downloads/futbol-tv.apk")
def tv_app_download():
    if not TV_APP_APK_PATH.is_file():
        return jsonify({"ok": False, "error": "APK no disponible"}), 404
    return send_file(TV_APP_APK_PATH, as_attachment=True, download_name="futbol-tv.apk", mimetype="application/vnd.android.package-archive")


@app.post("/system-update/<target>")
def system_update(target):
    try:
        if target == "ntfy":
            message = agenda_service().update_ntfy()
        elif target == "sites":
            result = subprocess.run(
                [str(PROJECT_ROOT / "update-futbol-libre-sites.sh")],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
            if result.returncode:
                error = result.stderr.strip() or result.stdout.strip() or "Error desconocido."
                return jsonify(success=False, error=error), 502
            message = result.stdout.strip() or "Sitios actualizados."
        else:
            return jsonify(success=False, error="Sistema no soportado."), 404
        return jsonify(success=True, message=message)
    except Exception as error:
        return jsonify(success=False, error=str(error)), 502


if __name__ == "__main__":
    mdns.start()
    udp_discovery.start()
    try:
        app.run(host="0.0.0.0", port=8080)
    finally:
        mdns.stop()
        udp_discovery.stop()
