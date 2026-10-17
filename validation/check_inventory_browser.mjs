import { spawn } from 'node:child_process';
import { existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const registry = JSON.parse(readFileSync(join(root, 'sources/data-inventory.json'), 'utf8'));
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
  await command('Emulation.setScriptExecutionDisabled', { value: true });
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
