'use strict';
(() => {
  const root = document.body.dataset.root || '';
  const menuButton = document.querySelector('.menu-button');
  const navigation = document.querySelector('#navigation');
  menuButton.addEventListener('click', () => {
    const expanded = menuButton.getAttribute('aria-expanded') !== 'true';
    menuButton.setAttribute('aria-expanded', String(expanded));
    navigation.classList.toggle('open', expanded);
  });
  document.querySelector('.print-button').addEventListener('click', () => window.print());
  const searchInput = document.querySelector('#site-search');
  const searchResults = document.querySelector('#search-results');
  const records = (window.SEARCH_INDEX || []).map(record => ({...record, searchable: (record.title + ' ' + record.section + ' ' + record.text).toLowerCase()}));
  let searchTimer;
  function closeSearch() {
    searchResults.hidden = true;
    searchInput.setAttribute('aria-expanded', 'false');
  }
  function runSearch() {
    const query = searchInput.value.trim().toLowerCase();
    searchResults.replaceChildren();
    if (query.length < 2) { closeSearch(); return; }
    const tokens = query.split(/\s+/);
    const matched = records.filter(record => tokens.every(token => record.searchable.includes(token)));
    matched.sort((first, second) => Number(second.title.toLowerCase().includes(query)) - Number(first.title.toLowerCase().includes(query)));
    const notice = document.createElement('div');
    notice.className = 'search-notice';
    notice.setAttribute('role', 'status');
    notice.textContent = matched.length ? `${matched.length} matches · showing up to 40` : 'No matches. Try an ability, class, rule or material name.';
    searchResults.append(notice);
    for (const record of matched.slice(0, 40)) {
      const link = document.createElement('a');
      link.href = root + record.url;
      const title = document.createElement('strong'); title.textContent = record.title;
      const context = document.createElement('small'); context.textContent = record.section;
      link.append(title, context); searchResults.append(link);
    }
    searchResults.hidden = false;
    searchInput.setAttribute('aria-expanded', 'true');
  }
  searchInput.addEventListener('input', () => { clearTimeout(searchTimer); searchTimer = setTimeout(runSearch, 130); });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') { closeSearch(); navigation.classList.remove('open'); menuButton.setAttribute('aria-expanded', 'false'); }
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') { event.preventDefault(); searchInput.focus(); }
  });
  document.addEventListener('click', event => { if (!event.target.closest('.search-wrap')) closeSearch(); });
  document.querySelectorAll('[data-filter]').forEach(input => {
    const table = document.getElementById(input.dataset.filter);
    const rows = [...table.querySelectorAll('tbody tr')].map(row => ({row, text: row.textContent.toLowerCase()}));
    const count = input.closest('.table-controls').querySelector('.row-count');
    function filter() {
      const terms = input.value.toLowerCase().trim().split(/\s+/).filter(Boolean);
      let visible = 0;
      for (const entry of rows) {
        const matches = terms.every(term => entry.text.includes(term));
        entry.row.hidden = !matches;
        if (matches) visible++;
      }
      count.textContent = `${visible} of ${rows.length} entries`;
    }
    input.addEventListener('input', filter); filter();
  });
})();
