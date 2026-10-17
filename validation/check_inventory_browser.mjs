import { spawn } from 'node:child_process';
import { existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const registry = JSON.parse(readFileSync(join(root, 'sources/data-inventory.json'), 'utf8'));
const roadmap = JSON.parse(readFileSync(join(root, 'sources/development-roadmap.json'), 'utf8'));
const phasePath = phase => `guide/roadmap-${phase.id.replace(/^phase-/, '')}.html`;
const epicPhase = new Map(roadmap.epics.map(epic => [epic.id, roadmap.phases.find(phase => phase.id === epic.phase)]));
const epicHref = id => `${phasePath(epicPhase.get(id)).split('/').pop()}#${id}`;
const referencePages = ['milestones', 'decisions', 'coverage', 'maintenance'].map(name => `guide/roadmap-${name}.html`);
const executable = process.env.BRIARWAKE_CHROME_BIN || [
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser',
].find(existsSync);
if (!executable) throw new Error('Set BRIARWAKE_CHROME_BIN to an installed Chrome or Chromium executable.');
const profile = mkdtempSync(join(tmpdir(), 'briarwake-inventory-qa-'));
const browser = spawn(executable, [
  '--headless', '--disable-gpu', '--disable-background-networking', '--disable-component-update',
  '--disable-sync', '--disable-breakpad', '--no-first-run', '--no-default-browser-check',
  '--remote-debugging-pipe', `--user-data-dir=${profile}`, 'about:blank',
], { stdio: ['ignore', 'ignore', 'ignore', 'pipe', 'pipe'] });
let sequence = 0;
let buffer = '';
const pending = new Map();
const listeners = new Map();
const checks = [];
const runtimeErrors = [];
const failedRequests = [];
const externalRequests = [];

function check(name, passed, detail = '') {
  checks.push({ name, passed: Boolean(passed), ...(detail ? { detail } : {}) });
}

function send(method, params = {}, sessionId) {
  return new Promise((resolveResult, reject) => {
    const id = ++sequence;
    const timer = setTimeout(() => { pending.delete(id); reject(new Error(`Timed out: ${method}`)); }, 15000);
    pending.set(id, { resolveResult, reject, timer });
    browser.stdio[3].write(JSON.stringify({ id, method, params, ...(sessionId ? { sessionId } : {}) }) + '\0');
  });
}

browser.stdio[4].setEncoding('utf8');
browser.stdio[4].on('data', chunk => {
  buffer += chunk;
  let end;
  while ((end = buffer.indexOf('\0')) >= 0) {
    const message = JSON.parse(buffer.slice(0, end));
    buffer = buffer.slice(end + 1);
    if (message.id && pending.has(message.id)) {
      const request = pending.get(message.id);
      pending.delete(message.id);
      clearTimeout(request.timer);
      if (message.error) request.reject(new Error(JSON.stringify(message.error)));
      else request.resolveResult(message.result);
    }
    if (message.method === 'Runtime.exceptionThrown') runtimeErrors.push(message.params.exceptionDetails.text);
    if (message.method === 'Network.loadingFailed') failedRequests.push(message.params.errorText);
    if (message.method === 'Network.requestWillBeSent' && /^https?:/.test(message.params.request.url)) externalRequests.push(message.params.request.url);
    for (const listener of listeners.get(message.method) || []) listener(message);
  }
});

function once(method, sessionId) {
  return new Promise((resolveEvent, reject) => {
    const timer = setTimeout(() => { remove(); reject(new Error(`Timed out waiting for ${method}`)); }, 15000);
    const handlers = listeners.get(method) || new Set();
    listeners.set(method, handlers);
    function remove() { clearTimeout(timer); handlers.delete(handler); }
    function handler(message) {
      if (message.sessionId === sessionId) { remove(); resolveEvent(message.params); }
    }
    handlers.add(handler);
  });
}

let browserVersion = '';
try {
  browserVersion = (await send('Browser.getVersion')).product;
  const target = await send('Target.createTarget', { url: 'about:blank' });
  const { sessionId } = await send('Target.attachToTarget', { targetId: target.targetId, flatten: true });
  const command = (method, params = {}) => send(method, params, sessionId);
  const evaluate = async expression => {
    const result = await command('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
    if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
    return result.result.value;
  };
  const navigate = async path => {
    const loaded = once('Page.loadEventFired', sessionId);
    await command('Page.navigate', { url: pathToFileURL(join(root, path.split('#')[0])).href + (path.includes('#') ? '#' + path.split('#')[1] : '') });
    await loaded;
  };
  const captureRoadmap = async name => {
    const screenshot = await command('Page.captureScreenshot', { format: 'png' });
    writeFileSync(join(tmpdir(), `briarwake-roadmap-${name}.png`), Buffer.from(screenshot.data, 'base64'));
  };
  const scrollRoadmap = id => evaluate(`document.getElementById(${JSON.stringify(id)}).scrollIntoView({behavior:'instant'})`);
  const clickNavigation = async expression => {
    const loaded = once('Page.loadEventFired', sessionId);
    await evaluate(expression);
    await loaded;
  };
  await command('Page.enable');
  await command('Runtime.enable');
  await command('Network.enable');
  await command('Network.emulateNetworkConditions', { offline: true, latency: 0, downloadThroughput: 0, uploadThroughput: 0 });
  await command('Emulation.setDeviceMetricsOverride', { width: 1440, height: 1100, deviceScaleFactor: 1, mobile: false });
  await navigate('guide/data-inventory.html');
  check('Actual offline file URL navigation and inventory rendering', await evaluate(`location.protocol === 'file:' && document.querySelector('h1').textContent === 'Data Inventory'`));
  check('All category tables render in alphabetical order', await evaluate(`['enums','interfaces','schemas'].every(category => {
    const names = [...document.querySelector('#inventory-' + category).tBodies[0].rows].map(row => row.cells[0].textContent);
    return names.length > 0 && names.every((name,index) => index === 0 || names[index-1].toLowerCase() <= name.toLowerCase());
  })`));
  check('Every rendered canonical schema matches the authoritative registry', await evaluate(`(() => {
    const expected = ${JSON.stringify(registry.entries.map(entry => ({ id: entry.id, schema: entry.definition })))};
    return expected.every(entry => {
      const code = document.getElementById(entry.id)?.querySelector('.definition pre code');
      return code && JSON.stringify(JSON.parse(code.textContent)) === JSON.stringify(entry.schema);
    });
  })()`));
  for (const [category, query] of [['enums', 'QuestStatus'], ['interfaces', 'CharacterCreationDraft'], ['schemas', 'ability_command_v2']]) {
    check(`Existing local filter: ${category}`, await evaluate(`(() => {
      const input = document.querySelector('[data-filter="inventory-${category}"]');
      input.value = ${JSON.stringify(query)}; input.dispatchEvent(new Event('input'));
      const rows = [...document.querySelector('#inventory-${category}').tBodies[0].rows];
      const visible = rows.filter(row => !row.hidden);
      const passed = visible.some(row => row.cells[0].textContent === ${JSON.stringify(query)}) && visible.length < rows.length && visible.every(row => row.textContent.toLowerCase().includes(${JSON.stringify(query.toLowerCase())}));
      input.value = ''; input.dispatchEvent(new Event('input')); return passed;
    })()`));
  }
  check('Offline global search finds the canonical inventory anchor', await evaluate(`(async () => {
    const input = document.querySelector('#site-search'); input.value = 'QuestProgressRecord'; input.dispatchEvent(new Event('input'));
    await new Promise(resolve => setTimeout(resolve, 250));
    return [...document.querySelectorAll('#search-results a')].some(link => link.textContent.includes('QuestProgressRecord') && link.href.endsWith('data-inventory.html#quest-progress-record'));
  })()`));
  await evaluate(`document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape'}))`);
  check('Desktop inventory has no body overflow', await evaluate('document.documentElement.scrollWidth <= innerWidth'));
  await navigate('guide/character-creation.html#data');
  check('Feature Data section is last in the article and uses normal layout', await evaluate(`(() => {
    const section = document.querySelector('.data-inventory');
    return section === document.querySelector('.article-body').lastElementChild && !['fixed','absolute'].includes(getComputedStyle(section).position) && section.querySelector('h2').textContent === 'Data';
  })()`));
  await clickNavigation(`document.querySelector('[data-inventory-id="quest-progress-record"] a').click()`);
  check('Feature link opens the correct canonical entry', await evaluate(`location.hash === '#quest-progress-record' && document.querySelector(':target').id === 'quest-progress-record'`));
  await clickNavigation(`document.querySelector('#quest-progress-record a[href="character-creation.html#data"]').click()`);
  check('Inventory backlink opens feature Data', await evaluate(`location.pathname.endsWith('/guide/character-creation.html') && location.hash === '#data'`));
  await navigate('guide/data-inventory.html');
  await command('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 1, mobile: true });
  check('Mobile inventory has no body overflow', await evaluate('document.documentElement.scrollWidth <= innerWidth'));
  await evaluate(`document.querySelector('.menu-button').click()`);
  check('Mobile navigation includes and opens Data Inventory', await evaluate(`document.querySelector('#navigation').classList.contains('open') && document.querySelector('[data-inventory-nav]').textContent === 'Data Inventory'`));
  await evaluate(`document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape'}))`);
  await evaluate(`new Promise(resolve => setTimeout(resolve, 250))`);
  check('Escape closes mobile navigation', await evaluate(`!document.querySelector('#navigation').classList.contains('open') && document.querySelector('#navigation').getBoundingClientRect().right <= 0`));
  const screenshot = await command('Page.captureScreenshot', { format: 'png' });
  writeFileSync(join(tmpdir(), 'briarwake-inventory-mobile.png'), Buffer.from(screenshot.data, 'base64'));
  await navigate('guide/development-roadmap.html');
  check('Offline roadmap hub is compact and links every phase instead of embedding epic details', await evaluate(`(() => {
    const expected = ${JSON.stringify(roadmap.phases.map(phasePath))};
    return location.protocol === 'file:' && document.querySelector('h1').textContent === 'Briarwake Development Roadmap'
      && !document.querySelector('.roadmap-epic') && !document.querySelector('.roadmap-epic-body')
      && expected.every(path => [...document.querySelectorAll('.article-body a')].some(link => link.href.endsWith(path)));
  })()`));
  check('Mobile roadmap hub has no body overflow', await evaluate('document.documentElement.scrollWidth <= innerWidth'));
  await captureRoadmap('mobile');
  await evaluate(`document.querySelector('.menu-button').click()`);
  check('Roadmap navigation is prominent and marks the hub current', await evaluate(`(() => {
    const link = document.querySelector('[data-roadmap-nav]');
    return link.previousElementSibling.classList.contains('nav-home') && link.getAttribute('aria-current') === 'page' && document.querySelector('#navigation').classList.contains('open');
  })()`));
  await evaluate(`document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape'}))`);
  check('Offline global search points to the canonical phase epic', await evaluate(`(async () => {
    const input = document.querySelector('#site-search'); input.value = ${JSON.stringify(roadmap.epics[0].id)}; input.dispatchEvent(new Event('input'));
    await new Promise(resolve => setTimeout(resolve, 250));
    return [...document.querySelectorAll('#search-results a')].some(link => link.href.endsWith(${JSON.stringify(epicHref(roadmap.epics[0].id))}));
  })()`));
  await evaluate(`document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape'}))`);
  check('Hub legacy epic anchor offers a direct canonical link', await evaluate(`(() => {
    const node = document.getElementById(${JSON.stringify(roadmap.epics[0].id)});
    return node?.matches('a') && node.href.endsWith(${JSON.stringify(epicHref(roadmap.epics[0].id))});
  })()`));
  await clickNavigation(`document.getElementById(${JSON.stringify(roadmap.epics[0].id)}).click()`);
  check('Legacy hub epic navigation reaches its canonical phase target', await evaluate(`location.pathname.endsWith(${JSON.stringify(phasePath(roadmap.phases[0]))}) && location.hash === ${JSON.stringify('#' + roadmap.epics[0].id)} && document.querySelector(':target').classList.contains('roadmap-epic')`));
  await command('Emulation.setDeviceMetricsOverride', { width: 1440, height: 1100, deviceScaleFactor: 1, mobile: false });
  await navigate('guide/development-roadmap.html');
  check('Desktop roadmap hub has no body overflow', await evaluate('document.documentElement.scrollWidth <= innerWidth'));
  await captureRoadmap('desktop');
  await scrollRoadmap('progress');
  await captureRoadmap('progress');
  await scrollRoadmap('sequence');
  await captureRoadmap('sequence');
  let renderedEpicCount = 0;
  for (const [index, phase] of roadmap.phases.entries()) {
    const epics = roadmap.epics.filter(epic => epic.phase === phase.id);
    await navigate(phasePath(phase));
    const phaseState = await evaluate(`(() => {
      const expected = ${JSON.stringify(epics.map(epic => ({ id: epic.id, title: epic.title, criteria: epic.acceptance_criteria })))};
      return {
        count: document.querySelectorAll('.roadmap-epic').length,
        correct: expected.every(epic => {
          const node = document.getElementById(epic.id);
          return node && node.classList.contains('roadmap-epic') && node.textContent.includes(epic.title) && epic.criteria.every(criterion => node.textContent.includes(criterion));
        }),
        overflow: document.documentElement.scrollWidth > innerWidth,
        current: [...document.querySelectorAll('.roadmap-nav a[aria-current="page"]')].some(link => link.href === location.href),
        hub: [...document.querySelectorAll('.roadmap-nav a')].some(link => link.href.endsWith('guide/development-roadmap.html')),
        previous: ${index === 0 ? 'true' : `[...document.querySelectorAll('.roadmap-phase-nav a')].some(link => link.href.endsWith(${JSON.stringify(phasePath(roadmap.phases[index - 1]))}))`},
        next: ${index + 1 === roadmap.phases.length ? 'true' : `[...document.querySelectorAll('.roadmap-phase-nav a')].some(link => link.href.endsWith(${JSON.stringify(phasePath(roadmap.phases[index + 1]))}))`},
      };
    })()`);
    renderedEpicCount += phaseState.count;
    check(`Phase ${index + 1} contains only its authoritative epics and all acceptance criteria`, phaseState.correct && phaseState.count === epics.length, `${phaseState.count} epics`);
    check(`Phase ${index + 1} has current local navigation, hub return and adjacent phases`, phaseState.current && phaseState.hub && phaseState.previous && phaseState.next);
    check(`Phase ${index + 1} has no desktop overflow`, !phaseState.overflow);
  }
  check('All authoritative epics render once across the phase pages', renderedEpicCount === roadmap.epics.length, `${renderedEpicCount} / ${roadmap.epics.length}`);
  const crossPhaseEpic = roadmap.epics.find(epic => epic.hard_dependencies.some(id => epicPhase.get(id).id !== epic.phase));
  const crossPhasePrerequisite = crossPhaseEpic.hard_dependencies.find(id => epicPhase.get(id).id !== crossPhaseEpic.phase);
  await navigate(phasePath(epicPhase.get(crossPhaseEpic.id)) + '#' + crossPhaseEpic.id);
  check('Cross-phase hard dependency links point directly to canonical targets', await evaluate(`(() => {
    const node = document.getElementById(${JSON.stringify(crossPhaseEpic.id)});
    return [...node.querySelectorAll('a')].some(link => link.href.endsWith(${JSON.stringify(epicHref(crossPhasePrerequisite))}));
  })()`));
  await clickNavigation(`document.getElementById(${JSON.stringify(crossPhaseEpic.id)}).querySelector('a[href="${epicHref(crossPhasePrerequisite)}"]').click()`);
  check('Cross-phase dependency navigation lands on the referenced epic', await evaluate(`location.hash === ${JSON.stringify('#' + crossPhasePrerequisite)} && document.querySelector(':target').classList.contains('roadmap-epic')`));
  for (const path of referencePages) {
    await navigate(path);
    check(`${path.split('/').pop()} renders offline with current roadmap navigation`, await evaluate(`document.querySelector('.article-body').textContent.trim().length > 300 && [...document.querySelectorAll('.roadmap-nav a[aria-current="page"]')].some(link => link.href === location.href) && document.documentElement.scrollWidth <= innerWidth`));
  }
  await navigate(phasePath(roadmap.phases[0]));
  await captureRoadmap('phase-desktop');
  await scrollRoadmap(roadmap.epics[0].id);
  await captureRoadmap('epic');
  await command('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 1, mobile: true });
  for (const path of [...roadmap.phases.map(phasePath), ...referencePages]) {
    await navigate(path);
    check(`Mobile ${path.split('/').pop()} has no body overflow`, await evaluate('document.documentElement.scrollWidth <= innerWidth'));
  }
  await navigate(phasePath(roadmap.phases[0]));
  await captureRoadmap('phase-mobile');
  await command('Emulation.setDeviceMetricsOverride', { width: 1440, height: 1100, deviceScaleFactor: 1, mobile: false });
  await command('Emulation.setEmulatedMedia', { media: 'print' });
  check('Phase print keeps its article content and hides website navigation', await evaluate(`getComputedStyle(document.querySelector('.article-body')).display !== 'none' && getComputedStyle(document.querySelector('.sidebar')).display === 'none' && document.querySelector('h1').getBoundingClientRect().height > 0`));
  check('Collapsed phase epics expose acceptance criteria in print', await evaluate(`(() => {
    document.querySelectorAll('.roadmap-epic').forEach(node => { node.open = false; });
    const bodies = [...document.querySelectorAll('.roadmap-epic-body')];
    return bodies.length > 0 && bodies.every(node => node.getBoundingClientRect().height > 0 && getComputedStyle(node).display !== 'none');
  })()`));
  await captureRoadmap('print');
  await command('Emulation.setEmulatedMedia', { media: '' });
  await command('Emulation.setScriptExecutionDisabled', { value: true });
  await navigate('guide/development-roadmap.html#' + roadmap.epics[0].id);
  check('Legacy hub epic anchors remain usable without JavaScript', await evaluate(`document.querySelector(':target')?.id === ${JSON.stringify(roadmap.epics[0].id)} && document.querySelector(':target').href.endsWith(${JSON.stringify(epicHref(roadmap.epics[0].id))})`));
  await captureRoadmap('nojs');
  for (const phase of roadmap.phases) {
    const epics = roadmap.epics.filter(epic => epic.phase === phase.id);
    await navigate(phasePath(phase) + '#' + epics[0].id);
    check(`No-JavaScript ${phase.id} deep link and native disclosures expose epic criteria`, await evaluate(`(() => {
      const expected = ${JSON.stringify(epics.map(epic => ({ id: epic.id, criterion: epic.acceptance_criteria[0] })))};
      document.querySelectorAll('.article-body details').forEach(node => { node.open = true; });
      return document.querySelector(':target')?.id === ${JSON.stringify(epics[0].id)} && expected.every(epic => {
        const node = document.getElementById(epic.id);
        return node && node.textContent.includes(epic.criterion) && node.getBoundingClientRect().height > 0;
      });
    })()`));
  }
  await navigate(phasePath(roadmap.phases[0]) + '#' + roadmap.epics[0].id);
  await captureRoadmap('nojs-epic');
  await navigate('guide/data-inventory.html');
  check('Inventory entries remain readable with JavaScript disabled', await evaluate(`document.querySelector('#quest-progress-record').textContent.includes(${JSON.stringify(registry.entries.find(entry => entry.id === 'quest-progress-record').definition_status)}) && document.querySelector('#inventory-enums').tBodies[0].rows.length > 0`));
  check('Canonical properties and enum members disclose without JavaScript', await evaluate(`(() => {
    const quest = document.querySelector('#quest-progress-record .definition');
    const grade = document.querySelector('#item-grade .definition');
    quest.open = true; grade.open = true;
    return quest.querySelector('table').textContent.includes('quest_id') && quest.textContent.includes('Required') && grade.textContent.includes('masterwork');
  })()`));
  await navigate('classes/mage.html#data');
  check('Class Data remains readable with JavaScript disabled', await evaluate(`document.querySelector('.data-inventory').textContent.includes('ArcanistCombatState') && document.querySelectorAll('.data-inventory').length === 1`));
  check('No page JavaScript exceptions', runtimeErrors.length === 0, JSON.stringify(runtimeErrors));
  check('No failed local requests or external page dependencies', failedRequests.length === 0 && externalRequests.length === 0, JSON.stringify({ failedRequests, externalRequests }));
} catch (error) {
  check('Browser automation completed', false, error.message);
} finally {
  await new Promise(resolveExit => {
    const timer = setTimeout(() => { browser.kill('SIGKILL'); resolveExit(); }, 2000);
    browser.once('exit', () => { clearTimeout(timer); resolveExit(); });
    browser.kill();
  });
  for (const request of pending.values()) clearTimeout(request.timer);
  rmSync(profile, { recursive: true, force: true, maxRetries: 3, retryDelay: 100 });
}
const report = {
  browser: browserVersion,
  method: 'Installed headless Chrome via DevTools pipe, actual local file navigation with network emulation offline; isolated temporary profile.',
  passed: checks.filter(check => check.passed).length,
  failed: checks.filter(check => !check.passed).length,
  checks,
};
writeFileSync(join(root, 'validation/data-inventory-browser-checks.json'), JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify(report, null, 2));
process.exitCode = report.failed ? 1 : 0;
