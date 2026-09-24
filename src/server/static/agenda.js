(() => {
  const tabs = Array.from(document.querySelectorAll('[role="tab"][id^="agenda-tab-"]'));
  const panels = Array.from(document.querySelectorAll('.agenda-panel'));
  const filter = document.getElementById('agenda-filter');
  const browse = document.getElementById('agenda-browse');
  const results = document.getElementById('agenda-search-results');
  const summary = document.getElementById('agenda-search-summary');

  function normalize(value) {
    return value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('es');
  }

  function select(index, focus = false) {
    tabs.forEach((tab, tabIndex) => {
      const selected = tabIndex === index;
      tab.setAttribute('aria-selected', selected ? 'true' : 'false');
      tab.tabIndex = selected ? 0 : -1;
      const panel = document.getElementById(tab.getAttribute('aria-controls'));
      if (panel) panel.hidden = !selected;
    });
    if (focus && tabs[index]) tabs[index].focus();
  }

  tabs.forEach((tab, index) => {
    tab.addEventListener('click', () => select(index));
    tab.addEventListener('keydown', event => {
      let next = null;
      if (event.key === 'ArrowRight') next = (index + 1) % tabs.length;
      if (event.key === 'ArrowLeft') next = (index - 1 + tabs.length) % tabs.length;
      if (event.key === 'Home') next = 0;
      if (event.key === 'End') next = tabs.length - 1;
      if (next === null) return;
      event.preventDefault();
      select(next, true);
    });
  });

  if (!filter || !browse || !results || !summary) return;

  filter.addEventListener('input', () => {
    const query = normalize(filter.value.trim());
    results.replaceChildren();
    if (!query) {
      browse.hidden = false;
      results.hidden = true;
      summary.textContent = '';
      return;
    }

    browse.hidden = true;
    results.hidden = false;
    let count = 0;
    panels.forEach(panel => {
      const matches = Array.from(panel.querySelectorAll('.agenda-row'))
        .filter(row => normalize(row.dataset.search || row.textContent).includes(query));
      if (!matches.length) return;

      const section = document.createElement('section');
      const heading = document.createElement('h2');
      const list = document.createElement('div');
      heading.className = 'agenda-date';
      heading.textContent = panel.dataset.dayLabel;
      list.className = 'agenda-list';
      matches.forEach(row => list.append(row.cloneNode(true)));
      section.append(heading, list);
      results.append(section);
      count += matches.length;
    });

    if (!count) {
      const empty = document.createElement('p');
      empty.className = 'empty-state';
      empty.textContent = `No hay eventos que coincidan con “${filter.value.trim()}”.`;
      results.append(empty);
    }
    summary.textContent = count === 1 ? '1 evento encontrado.' : `${count} eventos encontrados.`;
  });
})();
