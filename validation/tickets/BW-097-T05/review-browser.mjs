import { spawn } from 'node:child_process';
import { existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
const root=resolve(process.argv[2]);
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

try {
 const version=(await send('Browser.getVersion')).product;
 const target=await send('Target.createTarget',{url:'about:blank'});
 const {sessionId}=await send('Target.attachToTarget',{targetId:target.targetId,flatten:true});
 const command=(method,params={})=>send(method,params,sessionId);
 const evaluate=async expression=>{const r=await command('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw new Error(JSON.stringify(r.exceptionDetails));return r.result.value};
 await command('Page.enable');await command('Runtime.enable');await command('Network.enable');
 await command('Emulation.setDeviceMetricsOverride',{width:1800,height:1350,deviceScaleFactor:1,mobile:false});
 const loaded=once('Page.loadEventFired',sessionId);await command('Page.navigate',{url:pathToFileURL(join(root,'review.html')).href});await loaded;
 const counts=await evaluate('(async()=>{await still();await motion();return {fixtures:get("fixture").options.length,sequences:get("sequence").options.length,views:get("view").options.length}})()');
 check('all selectors populated',counts.fixtures===16&&counts.sequences===74&&counts.views===9,JSON.stringify(counts));
 check('candidate and source images render',await evaluate('get("candidate").width===772&&get("source").height===436'));
 check('actor-pair/zoom/light/AA/diagnostic changes render',await evaluate('(async()=>{get("fixture").selectedIndex=2;get("zoom").selectedIndex=1;get("light").selectedIndex=1;get("view").selectedIndex=6;await still();return get("measurement").textContent.includes("actors-overlap")})()'));
 check('pixel grid toggle and redraw',await evaluate('(async()=>{get("grid").checked=true;await still();return get("grid").checked&&get("candidate").width===772})()'));
 check('frame stepping updates actual sample',await evaluate('(async()=>{get("frame").value=0;get("step").click();await motion();return get("motionStatus").textContent.startsWith("1/31")})()'));
 check('playback advances',await evaluate('(async()=>{get("frame").value=0;get("play").click();await new Promise(r=>setTimeout(r,240));get("play").click();return Number(get("frame").value)>0})()'));
 await evaluate('(async()=>{get("fixture").selectedIndex=0;get("zoom").selectedIndex=0;get("light").selectedIndex=0;get("view").selectedIndex=8;get("grid").checked=false;get("sequence").selectedIndex=15;get("frame").value=16;await still();await motion()})()');
 const screenshot=await command('Page.captureScreenshot',{format:'png'});writeFileSync(join(root,'browser-review.png'),Buffer.from(screenshot.data,'base64'));
 check('no runtime or local resource errors',runtimeErrors.length===0&&failedRequests.length===0,JSON.stringify({runtimeErrors,failedRequests}));
 check('offline review has no external requests',externalRequests.length===0,JSON.stringify(externalRequests));
 const report={browser:version,checks,passed:checks.every(c=>c.passed),runtimeErrors,failedRequests,externalRequests};
 writeFileSync(join(root,'browser-review.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
 if(!report.passed)process.exitCode=1;
} finally {await send('Browser.close').catch(()=>{});browser.kill();await new Promise(resolve=>setTimeout(resolve,500));rmSync(profile,{recursive:true,force:true,maxRetries:5,retryDelay:200})}
