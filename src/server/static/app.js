let poller;
const tailState = new WeakMap();

function setStatus(element, message, kind) {
  element.textContent = message;
  element.className = `status ${kind || ''}`;
}

function updateProgress(progress) {
  if (!progress) return;
  for (const stage of ['sites', 'streams']) {
    const percent = progress[stage]?.percent || 0;
    document.getElementById(`${stage}-progress`).value = percent;
    document.getElementById(`${stage}-progress-value`).textContent = `${percent}%`;
  }
}

function resetTail(tail) {
  tailState.delete(tail);
  tail.textContent = '';
}

function updateTail(tail, lines) {
  const incoming = lines || [];
  const previous = tailState.get(tail) || [];
  const distanceFromBottom = tail.scrollHeight - tail.scrollTop - tail.clientHeight;
  const wasFollowingBottom = distanceFromBottom <= 8;
  let next = incoming;

  if (previous.length && incoming.length) {
    let overlap = Math.min(previous.length, incoming.length);
    while (overlap > 0) {
      const matches = previous
        .slice(previous.length - overlap)
        .every((line, index) => line === incoming[index]);
      if (matches) break;
      overlap -= 1;
    }
    next = overlap ? previous.concat(incoming.slice(overlap)) : incoming;
  }

  if (next.join('\n') === previous.join('\n')) return;
  tailState.set(tail, next);
  tail.textContent = next.join('\n');

  if (wasFollowingBottom) {
    tail.scrollTop = tail.scrollHeight;
  }
}

function stopInlinePlayer(video) {
  if (!video) return;
  if (document.pictureInPictureElement === video && document.exitPictureInPicture) {
    document.exitPictureInPicture().catch(error => console.error('No se pudo cerrar Picture-in-Picture:', error));
  }
  video.pause();
  if (video._hls) {
    video._hls.destroy();
    delete video._hls;
  }
  video.removeAttribute('src');
  video.load();
  delete video.dataset.loaded;
}

function collapseSources(sourcesRow) {
  sourcesRow.querySelectorAll('.source-item[aria-expanded="true"]').forEach(source => {
    source.setAttribute('aria-expanded', 'false');
  });
  sourcesRow.querySelectorAll('.source-player-row').forEach(playerRow => {
    playerRow.hidden = true;
    stopInlinePlayer(playerRow.querySelector('video'));
  });
  sourcesRow.querySelectorAll('.player-button').forEach(button => { button.hidden = true; });
  sourcesRow.querySelectorAll('.vpn-button').forEach(button => { button.hidden = true; });
}

function toggleEvent(row) {
  const sourcesRow = row.nextElementSibling;
  const expanded = !sourcesRow.hidden;
  if (expanded) collapseSources(sourcesRow);
  sourcesRow.hidden = expanded;
  row.setAttribute('aria-expanded', String(!expanded));
}

function closeAllChannels(event) {
  if (event) event.stopPropagation();
  document.querySelectorAll('.event-card[aria-expanded]').forEach(row => {
    const sourcesRow = row.nextElementSibling;
    collapseSources(sourcesRow);
    sourcesRow.hidden = true;
    row.setAttribute('aria-expanded', 'false');
  });
}

function toggleSource(event, source) {
  event.stopPropagation();
  const playerRow = source.closest('.source-block').querySelector('.source-player-row');
  const expanded = !playerRow.hidden;
  if (expanded) {
    playerRow.hidden = true;
    stopInlinePlayer(playerRow.querySelector('video'));
  } else {
    playerRow.hidden = false;
    const video = playerRow.querySelector('video');
    const status = playerRow.querySelector('.player-status');
    const vpnButton = source.closest('.source-block').querySelector('.vpn-button');
    if (vpnButton) {
      vpnButton.hidden = false;
      syncVpnSwitch(vpnButton, video.dataset.route === 'vpn');
    }
    if (status) { status.hidden = true; status.textContent = ''; }
    ensureInlinePlayer(video, video.dataset.stream).catch(error => {
      if (status) { status.hidden = false; status.textContent = 'No se pudo cargar este canal. Probá otra fuente.'; }
      console.error(error);
    });
  }
  const playerButton = source.closest('.source-block').querySelector('.player-button');
  if (playerButton) playerButton.hidden = expanded;
  source.setAttribute('aria-expanded', String(!expanded));
}

function syncVpnSwitch(button, active) {
  button.setAttribute('aria-checked', String(active));
  button.classList.toggle('is-active', active);
  button.closest('.source-block').classList.toggle('vpn-active', active);
}

function toggleVpn(event, button) {
  event.stopPropagation();
  const block = button.closest('.source-block');
  const video = block.querySelector('video');
  const status = block.querySelector('.player-status');
  const active = button.getAttribute('aria-checked') !== 'true';
  const target = active
    ? '/api/v1/stream-relay/' + encodeURIComponent(button.dataset.eventId) + '/' + encodeURIComponent(button.dataset.sourceId)
    : video.dataset.directStream;
  stopInlinePlayer(video);
  video.dataset.stream = target;
  video.dataset.route = active ? 'vpn' : 'direct';
  syncVpnSwitch(button, active);
  ensureInlinePlayer(video, target).catch(error => {
    video.dataset.stream = video.dataset.directStream;
    video.dataset.route = 'direct';
    syncVpnSwitch(button, false);
    if (status) { status.hidden = false; status.textContent = active ? 'No se pudo cargar por VPN.' : 'No se pudo cargar este canal.'; }
    console.error(error);
  });
}

function ensureInlinePlayer(video, stream) {
  if (video.dataset.loaded === 'true') return Promise.resolve();
  video.muted = true;
  return new Promise((resolve, reject) => {
    if (video.canPlayType('application/vnd.apple.mpegurl')) {
      video.src = stream;
      video.addEventListener('loadedmetadata', resolve, {once: true});
      video.addEventListener('error', reject, {once: true});
      return;
    }
    if (!window.Hls || !Hls.isSupported()) return reject(new Error('HLS no soportado'));
    const hls = new Hls();
    video._hls = hls;
    hls.loadSource(stream);
    hls.attachMedia(video);
    hls.on(Hls.Events.MANIFEST_PARSED, resolve);
    hls.on(Hls.Events.ERROR, (_, data) => { if (data.fatal) reject(new Error('No se pudo cargar el stream')); });
  }).then(() => { video.dataset.loaded = 'true'; });
}

function openNewWindow(event, stream) {
  event.stopPropagation();
  const playerWindow = window.open('', '_blank');
  if (!playerWindow) {
    const status = event.currentTarget.closest('.source-block').querySelector('.player-status');
    if (status) { status.hidden = false; status.textContent = 'El navegador bloqueó la ventana. Permití ventanas emergentes para abrir el canal.'; }
    return;
  }

  const safeStream = JSON.stringify(stream).replace(/</g, '\\u003c');
  playerWindow.document.write(`<!doctype html><html><head><meta charset="utf-8"><title>Fútbol Libre</title>
    <style>html,body{height:100%;margin:0;background:#000}video{width:100%;height:100%;display:block}</style></head>
    <body><video id="player" controls autoplay muted playsinline></video>
    <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script><script>
      const video = document.getElementById('player');
      const stream = ${safeStream};
      video.muted = true;
      if (video.canPlayType('application/vnd.apple.mpegurl')) video.src = stream;
      else if (window.Hls && Hls.isSupported()) { const hls = new Hls(); hls.loadSource(stream); hls.attachMedia(video); }
      else document.body.textContent = 'Este navegador no soporta HLS.';
    </script></body></html>`);
  playerWindow.document.close();
}

function openPip(event, button) {
  const video = button.closest('.source-block').querySelector('video');
  openNewWindow(event, video.dataset.stream || button.dataset.stream);
}

function setExecutionButtonsDisabled(disabled) {
  ['run', 'run-extra'].forEach(id => {
    const button = document.getElementById(id);
    if (button) button.disabled = disabled;
  });
}

function pollStatus(status, tail) {
  fetch('/status').then(response => response.json()).then(data => {
    updateTail(tail, data.output);
    updateProgress(data.progress);
    if (data.is_running) {
      setStatus(status, data.message || 'Ejecutando...', '');
      return;
    }
    clearInterval(poller);
    setExecutionButtonsDisabled(false);
    setStatus(status, data.error ? data.message : 'Proceso terminado correctamente.', data.error ? 'error' : 'success');
  }).catch(() => {
    clearInterval(poller);
    setExecutionButtonsDisabled(false);
    setStatus(status, 'No se pudo consultar el estado.', 'error');
  });
}

function updateUrl() {
  const button = document.getElementById('run');
  const status = document.getElementById('status');
  const tail = document.getElementById('tail');
  const url = document.getElementById('url').value.trim();
  if (!url) return setStatus(status, 'La URL es obligatoria.', 'error');
  setExecutionButtonsDisabled(true);
  resetTail(tail);
  fetch('/update-url', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({url}) })
    .then(response => response.json().then(data => ({ok: response.ok, data})))
    .then(result => {
      if (!result.ok && result.data.running) {
        updateTail(tail, result.data.status.output || []);
        updateProgress(result.data.status.progress);
        poller = setInterval(() => pollStatus(status, tail), 1000);
        throw new Error('Ya hay un proceso corriendo; mostrando su log.');
      }
      if (!result.ok) throw new Error(result.data.error || 'No se pudo iniciar.');
      poller = setInterval(() => pollStatus(status, tail), 1000);
    }).catch(error => {
      if (!error.message.startsWith('Ya hay un proceso')) {
        setExecutionButtonsDisabled(false);
        setStatus(status, error.message, 'error');
      }
    });
}

function processExtra() {
  const button = document.getElementById('run-extra');
  const status = document.getElementById('status');
  const tail = document.getElementById('tail');
  const extraUrl = document.getElementById('extra-url').value.trim();
  if (!extraUrl) return setStatus(status, 'La URL adicional es obligatoria.', 'error');
  setExecutionButtonsDisabled(true);
  resetTail(tail);
  fetch('/update-url', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({extra_url: extraUrl, only_extra: true})
  })
    .then(response => response.json().then(data => ({ok: response.ok, data})))
    .then(result => {
      if (!result.ok && result.data.running) {
        updateTail(tail, result.data.status.output || []);
        updateProgress(result.data.status.progress);
        poller = setInterval(() => pollStatus(status, tail), 1000);
        throw new Error('Ya hay un proceso corriendo; mostrando su log.');
      }
      if (!result.ok) throw new Error(result.data.error || 'No se pudo iniciar.');
      poller = setInterval(() => pollStatus(status, tail), 1000);
    }).catch(error => {
      if (!error.message.startsWith('Ya hay un proceso')) {
        setExecutionButtonsDisabled(false);
        setStatus(status, error.message, 'error');
      }
    });
}

function stopUpdate() {
  const stopButton = document.getElementById('stop');
  const status = document.getElementById('status');
  stopButton.disabled = true;
  fetch('/stop-update', {method: 'POST'})
    .then(response => response.json().then(data => ({ok: response.ok, data})))
    .then(result => {
      stopButton.disabled = false;
      if (!result.ok) return setStatus(status, result.data.error, 'error');
      setExecutionButtonsDisabled(false);
      setStatus(status, result.data.message, 'success');
      if (poller) clearInterval(poller);
    }).catch(() => { stopButton.disabled = false; setStatus(status, 'No se pudo detener el proceso.', 'error'); });
}

window.addEventListener('DOMContentLoaded', () => {
  const status = document.getElementById('status');
  const tail = document.getElementById('tail');
  fetch('/status').then(response => response.json()).then(data => {
    if (data.is_running) {
      setExecutionButtonsDisabled(true);
      updateTail(tail, data.output);
      updateProgress(data.progress);
      poller = setInterval(() => pollStatus(status, tail), 1000);
  }
});

window.addEventListener('pagehide', () => {
  document.querySelectorAll('video').forEach(stopInlinePlayer);
});
});

function updateSystem(target, button) {
  const status = document.getElementById('system-status');
  button.disabled = true;
  fetch(`/system-update/${target}`, {method: 'POST'})
    .then(response => response.json().then(data => ({ok: response.ok, data})))
    .then(result => {
      button.disabled = false;
      setStatus(status, result.data.message || result.data.error, result.ok ? 'success' : 'error');
    }).catch(() => { button.disabled = false; setStatus(status, 'No se pudo actualizar el sistema.', 'error'); });
}
