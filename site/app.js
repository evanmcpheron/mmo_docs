(function () {
  'use strict';
  const storageKey = 'briarwake.manual.progress.v1';
  const allowedPhases = new Set(Array.from({ length: 32 }, (_, index) => String(index).padStart(2, '0')));
  const rootPath = document.body.dataset.root || './';
  const getStored = (key) => { try { return localStorage.getItem(key); } catch (_) { return null; } };
  const setStored = (key, value) => { try { localStorage.setItem(key, value); return true; } catch (_) { return false; } };
  const theme = getStored('briarwake.manual.theme');
  if (theme === 'light' || theme === 'dark') document.documentElement.dataset.theme = theme;
  document.getElementById('theme-toggle').addEventListener('click', () => {
    const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
    document.documentElement.dataset.theme = next;
    setStored('briarwake.manual.theme', next);
  });
  const menuButton = document.getElementById('menu-toggle');
  menuButton.addEventListener('click', () => {
    const expanded = menuButton.getAttribute('aria-expanded') !== 'true';
    menuButton.setAttribute('aria-expanded', String(expanded));
    document.getElementById('sidebar').classList.toggle('open', expanded);
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
      document.getElementById('sidebar').classList.remove('open');
      menuButton.setAttribute('aria-expanded', 'false');
    }
  });

  const searchInput = document.getElementById('search-input');
  if (searchInput) {
    const records = (window.BRIARWAKE_SEARCH || []).map(record => ({ ...record, haystack: [record.title, record.summary, record.text].join(' ').toLowerCase() }));
    searchInput.addEventListener('input', () => {
      const query = searchInput.value.trim().toLowerCase();
      const words = query.split(/\s+/).filter(Boolean);
      const results = document.getElementById('search-results');
      results.replaceChildren();
      if (!words.length) { document.getElementById('search-status').textContent = 'Enter one or more words.'; return; }
      const matches = records.filter(record => words.every(word => record.haystack.includes(word)));
      matches.sort((left, right) => Number(right.title.toLowerCase().includes(query)) - Number(left.title.toLowerCase().includes(query)) || left.title.localeCompare(right.title));
      document.getElementById('search-status').textContent = `${matches.length} matching pages. Showing up to 60.`;
      matches.slice(0, 60).forEach(record => {
        const item = document.createElement('li');
        const category = document.createElement('small'); category.textContent = record.category;
        const anchor = document.createElement('a'); anchor.href = rootPath + record.path; anchor.textContent = record.title;
        const summary = document.createElement('p'); summary.textContent = record.summary;
        item.append(category, anchor, summary); results.append(item);
      });
    });
  }

  const assetQuery = document.getElementById('asset-query');
  if (assetQuery) {
    const controls = ['asset-query', 'asset-type', 'asset-status', 'asset-phase'].map(id => document.getElementById(id));
    const rows = Array.from(document.querySelectorAll('[data-asset-row]'));
    const filterRows = () => {
      const [query, type, status, phase] = controls.map(control => control.value.trim());
      let count = 0;
      rows.forEach(row => {
        const visible = row.dataset.name.includes(query.toLowerCase()) && (!type || row.dataset.type === type) && (!status || row.dataset.status === status) && (!phase || Number(row.dataset.phase) === Number(phase));
        row.hidden = !visible; if (visible) count += 1;
      });
      document.getElementById('asset-count').textContent = `${count} of ${rows.length} registered assets`;
    };
    controls.forEach(control => { control.addEventListener('input', filterRows); control.addEventListener('change', filterRows); });
  }

  const checkboxes = Array.from(document.querySelectorAll('[data-phase-check]'));
  if (checkboxes.length) {
    const validateProgress = (value) => {
      if (!value || value.schemaVersion !== 1 || value.project !== 'Briarwake' || !Array.isArray(value.completed) || value.completed.length > 32 || value.completed.some(item => typeof item !== 'string' || !allowedPhases.has(item)) || new Set(value.completed).size !== value.completed.length) {
        throw new Error('Invalid Briarwake progress file. Expected schemaVersion 1 and unique phase IDs 00–31.');
      }
      return value.completed;
    };
    let completed = new Set();
    try { const saved = getStored(storageKey); if (saved) completed = new Set(validateProgress(JSON.parse(saved))); } catch (_) { document.getElementById('import-status').textContent = 'Stored progress could not be read. Import a valid exported file.'; }
    const payload = () => ({ schemaVersion: 1, project: 'Briarwake', completed: Array.from(completed).sort() });
    const refresh = () => {
      checkboxes.forEach(checkbox => { checkbox.checked = completed.has(checkbox.dataset.phaseCheck); });
      document.getElementById('progress-status').textContent = `${completed.size} of 32 phases checked locally. This is not game-test evidence.`;
    };
    const persist = () => {
      if (!setStored(storageKey, JSON.stringify(payload()))) document.getElementById('import-status').textContent = 'Browser storage is unavailable. Export progress before closing this page.';
      refresh();
    };
    checkboxes.forEach(checkbox => checkbox.addEventListener('change', () => {
      if (checkbox.checked) completed.add(checkbox.dataset.phaseCheck); else completed.delete(checkbox.dataset.phaseCheck);
      persist();
    }));
    document.getElementById('export-progress').addEventListener('click', () => {
      const blob = new Blob([JSON.stringify(payload(), null, 2) + '\n'], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a'); anchor.href = url; anchor.download = 'Briarwake-progress.json';
      document.body.append(anchor); anchor.click(); anchor.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      document.getElementById('import-status').textContent = 'Export created. Retain it before moving or updating the manual.';
    });
    document.getElementById('import-progress').addEventListener('change', async (event) => {
      const file = event.target.files[0]; if (!file) return;
      try {
        if (file.size > 100000) throw new Error('Progress file is too large.');
        const incoming = validateProgress(JSON.parse(await file.text()));
        if (!window.confirm('Replace this browser’s local checkmarks with the imported progress?')) return;
        completed = new Set(incoming); persist();
        document.getElementById('import-status').textContent = 'Progress imported. Existing local checkmarks were replaced.';
      } catch (error) {
        document.getElementById('import-status').textContent = error.message;
      } finally { event.target.value = ''; }
    });
    document.getElementById('reset-progress').addEventListener('click', () => {
      if (window.confirm('Clear all local phase checkmarks? Export first to keep a backup.')) { completed.clear(); persist(); }
    });
    refresh();
  }
}());
