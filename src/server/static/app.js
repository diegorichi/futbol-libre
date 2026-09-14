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
  const playerRow = source.nextElementSibling;
  const expanded = !playerRow.hidden;
  if (expanded) {
    playerRow.hidden = true;
    stopInlinePlayer(playerRow.querySelector('video'));
  } else {
    playerRow.hidden = false;
    const video = playerRow.querySelector('video');
    ensureInlinePlayer(video, video.dataset.stream).catch(error => console.error(error));
  }
  source.setAttribute('aria-expanded', String(!expanded));
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

function openPip(event, stream, videoId) {
  event.stopPropagation();
  const video = document.getElementById(videoId);
  video.closest('.source-player-row, .stream-row').hidden = false;
  ensureInlinePlayer(video, stream)
    .then(() => video.play())
    .then(() => video.requestPictureInPicture())
    .catch(error => console.error('No se pudo abrir Picture-in-Picture:', error));
}

function pollStatus(button, status, tail) {
  fetch('/status').then(response => response.json()).then(data => {
    updateTail(tail, data.output);
    updateProgress(data.progress);
    if (data.is_running) {
      setStatus(status, data.message || 'Ejecutando...', '');
      return;
    }
    clearInterval(poller);
    button.disabled = false;
    setStatus(status, data.error ? data.message : 'Proceso terminado correctamente.', data.error ? 'error' : 'success');
  }).catch(() => {
    clearInterval(poller);
    button.disabled = false;
    setStatus(status, 'No se pudo consultar el estado.', 'error');
  });
}

function updateUrl() {
  const button = document.getElementById('run');
  const status = document.getElementById('status');
  const tail = document.getElementById('tail');
  const url = document.getElementById('url').value.trim();
  const extraUrl = document.getElementById('extra-url').value.trim();
  if (!url) return setStatus(status, 'La URL es obligatoria.', 'error');
  button.disabled = true;
  resetTail(tail);
  fetch('/update-url', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({url, extra_url: extraUrl}) })
    .then(response => response.json().then(data => ({ok: response.ok, data})))
    .then(result => {
      if (!result.ok && result.data.running) {
        updateTail(tail, result.data.status.output || []);
        updateProgress(result.data.status.progress);
        poller = setInterval(() => pollStatus(button, status, tail), 1000);
        throw new Error('Ya hay un proceso corriendo; mostrando su log.');
      }
      if (!result.ok) throw new Error(result.data.error || 'No se pudo iniciar.');
      poller = setInterval(() => pollStatus(button, status, tail), 1000);
    }).catch(error => {
      if (!error.message.startsWith('Ya hay un proceso')) {
        button.disabled = false;
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
  button.disabled = true;
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
        poller = setInterval(() => pollStatus(button, status, tail), 1000);
        throw new Error('Ya hay un proceso corriendo; mostrando su log.');
      }
      if (!result.ok) throw new Error(result.data.error || 'No se pudo iniciar.');
      poller = setInterval(() => pollStatus(button, status, tail), 1000);
    }).catch(error => {
      if (!error.message.startsWith('Ya hay un proceso')) {
        button.disabled = false;
        setStatus(status, error.message, 'error');
      }
    });
}

function stopUpdate() {
  const runButton = document.getElementById('run');
  const stopButton = document.getElementById('stop');
  const status = document.getElementById('status');
  stopButton.disabled = true;
  fetch('/stop-update', {method: 'POST'})
    .then(response => response.json().then(data => ({ok: response.ok, data})))
    .then(result => {
      stopButton.disabled = false;
      if (!result.ok) return setStatus(status, result.data.error, 'error');
      runButton.disabled = false;
      setStatus(status, result.data.message, 'success');
      if (poller) clearInterval(poller);
    }).catch(() => { stopButton.disabled = false; setStatus(status, 'No se pudo detener el proceso.', 'error'); });
}

window.addEventListener('DOMContentLoaded', () => {
  const runButton = document.getElementById('run');
  const status = document.getElementById('status');
  const tail = document.getElementById('tail');
  fetch('/status').then(response => response.json()).then(data => {
    if (data.is_running) {
      runButton.disabled = true;
      updateTail(tail, data.output);
      updateProgress(data.progress);
      poller = setInterval(() => pollStatus(runButton, status, tail), 1000);
    }
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
