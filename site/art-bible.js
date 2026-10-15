(function () {
  'use strict';
  const one = (scope, selector) => scope.querySelector(selector);
  const all = (scope, selector) => Array.from(scope.querySelectorAll(selector));
  all(document, '.pixel-viewer').forEach(viewer => {
    const stage = one(viewer, '.pixel-stage');
    one(viewer, '[data-zoom]').addEventListener('change', event => {
      const zoom = Number(event.target.value);
      stage.style.width = `${Number(viewer.dataset.width) * zoom}px`;
      stage.style.height = `${Number(viewer.dataset.height) * zoom}px`;
      stage.style.setProperty('--zoom', zoom);
    });
    for (const [selector, className] of [['[data-pixel-grid]', 'show-pixels'], ['[data-tile-grid]', 'show-tiles']]) {
      one(viewer, selector).addEventListener('change', event => stage.classList.toggle(className, event.target.checked));
    }
    one(viewer, '[data-checker]').addEventListener('change', event => stage.classList.toggle('no-checker', !event.target.checked));
  });
  all(document, '[data-copy]').forEach(button => button.addEventListener('click', async () => {
    let copied = false;
    try {
      if (navigator.clipboard) { await navigator.clipboard.writeText(button.dataset.copy); copied = true; }
    } catch (_) { /* File URLs may deny the asynchronous clipboard permission. */ }
    if (!copied) {
      const field = document.createElement('textarea');
      field.value = button.dataset.copy;
      field.style.position = 'fixed'; field.style.left = '-10000px';
      document.body.append(field); field.select();
      try { copied = document.execCommand('copy'); } catch (_) { copied = false; }
      field.remove(); button.focus();
    }
    const status = one(button.closest('section'), '.copy-status');
    status.textContent = copied ? `Copied ${button.dataset.copy}` : `Copy this value: ${button.dataset.copy}`;
  }));
  all(document, '[data-animation]').forEach(viewer => {
    const sheet = one(viewer, '.animation-source');
    const canvas = one(viewer, 'canvas');
    const context = canvas.getContext('2d');
    const stage = one(viewer, '.animation-stage');
    let frame = 0, facing = 4, speed = 1, playing = false, timer;
    const draw = () => {
      if (!sheet.complete || !sheet.naturalWidth) return;
      context.imageSmoothingEnabled = false;
      context.clearRect(0, 0, 64, 64);
      context.drawImage(sheet, frame * 64, facing * 64, 64, 64, 0, 0, 64, 64);
      one(viewer, '[data-frame-label]').textContent = `Frame ${frame + 1} of 6 · sheet frame ${facing * 6 + frame + 1} of 48 · ${['N','NE','E','SE','S','SW','W','NW'][facing]} · 100 ms${playing ? ' · playing' : ' · paused'}`;
      viewer.classList.add('ready');
    };
    const pause = () => { playing = false; clearTimeout(timer); draw(); };
    const tick = () => { if (!playing) return; frame = (frame + 1) % 6; draw(); timer = setTimeout(tick, 100 / speed); };
    one(viewer, '[data-play]').addEventListener('click', () => { if (!playing) { playing = true; draw(); timer = setTimeout(tick, 100 / speed); } });
    one(viewer, '[data-pause]').addEventListener('click', pause);
    all(viewer, '[data-step]').forEach(button => button.addEventListener('click', () => { pause(); frame = (frame + Number(button.dataset.step) + 6) % 6; draw(); }));
    one(viewer, '[data-facing]').addEventListener('change', event => { facing = Number(event.target.value); frame = 0; draw(); });
    one(viewer, '[data-speed]').addEventListener('change', event => { speed = Number(event.target.value); if (playing) { clearTimeout(timer); timer = setTimeout(tick, 100 / speed); } });
    one(viewer, '[data-animation-zoom]').addEventListener('change', event => {
      const zoom = Number(event.target.value); stage.style.width = `${64 * zoom}px`; stage.style.height = `${64 * zoom}px`; stage.style.setProperty('--zoom', zoom);
    });
    one(viewer, '[data-registration]').addEventListener('change', event => { one(stage, '.registration-marker').hidden = !event.target.checked; });
    one(viewer, '[data-animation-checker]').addEventListener('change', event => stage.classList.toggle('no-checker', !event.target.checked));
    one(viewer, '[data-animation-grid]').addEventListener('change', event => stage.classList.toggle('show-pixels', event.target.checked));
    one(viewer, '[data-animation-tile-grid]').addEventListener('change', event => stage.classList.toggle('show-tiles', event.target.checked));
    document.addEventListener('visibilitychange', () => { if (document.hidden) pause(); });
    sheet.addEventListener('load', draw); draw();
  });
  const condition = one(document, '[data-condition]');
  if (condition) {
    const image = one(document, '[data-condition-image]');
    const slider = one(document, '[data-before-after]');
    const wrapper = document.createElement('div'); wrapper.className = 'condition-comparison';
    image.before(wrapper); wrapper.append(image);
    const day = image.cloneNode(); day.removeAttribute('data-condition-image'); day.className = 'day-overlay'; day.alt = ''; day.setAttribute('aria-hidden','true'); wrapper.append(day);
    const label = () => { one(document, '[data-condition-label]').textContent = `${condition.value} · ${slider.value}% day comparison`; };
    condition.addEventListener('change', () => { image.src = `assets/light-${condition.value}.png`; image.alt = `Same scene in ${condition.value} conditions`; label(); });
    slider.addEventListener('input', () => { day.style.opacity = Number(slider.value) / 100; label(); });
  }
  const crowd = one(document, '[data-crowd]');
  if (crowd) crowd.addEventListener('change', () => {
    const image = one(document, '[data-crowd-image]'); image.src = `assets/crowd-${crowd.value}.png`; image.alt = `Static readability study with ${crowd.value} actors`;
  });
  all(document, '[data-item]').forEach(button => button.addEventListener('click', () => {
    all(document, '[data-item]').forEach(item => item.setAttribute('aria-pressed', String(item === button)));
    one(document, '[data-item-detail]').textContent = `${button.dataset.item} · 16×16 native icon · proposed reference · category identity comes from silhouette.`;
  }));
  all(document, '[data-print]').forEach(button => button.addEventListener('click', () => window.print()));
  const search = one(document, '#art-search');
  if (search) search.addEventListener('input', () => {
    const terms = search.value.toLocaleLowerCase().trim().split(/\s+/).filter(Boolean);
    const result = one(document, '#art-search-results'); result.replaceChildren();
    const matches = terms.length ? (window.BRIARWAKE_ART_SEARCH || []).filter(p => terms.every(t => `${p.title} ${p.summary} ${p.text}`.toLocaleLowerCase().includes(t))) : [];
    matches.slice(0, 33).forEach(p => { const item = document.createElement('li'); const anchor = document.createElement('a'); anchor.href = p.path; anchor.textContent = p.title; const description = document.createElement('small'); description.textContent = p.summary; item.append(anchor, description); result.append(item); });
    one(document, '#art-search-status').textContent = terms.length ? `${matches.length} matching chapters` : 'Search works locally, including offline.';
  });
}());
