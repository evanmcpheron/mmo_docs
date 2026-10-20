import { spawn } from 'node:child_process';
import { existsSync,mkdtempSync,writeFileSync,rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join,resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
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


const directory=resolve(process.argv[2]);
try {
 const version=await send('Browser.getVersion');
 const target=await send('Target.createTarget',{url:'about:blank'});
 const {sessionId}=await send('Target.attachToTarget',{targetId:target.targetId,flatten:true});
 const command=(method,params={})=>send(method,params,sessionId);
 const evaluate=async expression=>{
  const result=await command('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});
  if(result.exceptionDetails)throw new Error(JSON.stringify(result.exceptionDetails));return result.result.value;
 };
 await command('Page.enable');await command('Runtime.enable');await command('Network.enable');
 await command('Emulation.setDeviceMetricsOverride',{width:1700,height:1000,deviceScaleFactor:2,mobile:false});
 const loaded=once('Page.loadEventFired',sessionId);
 await command('Page.navigate',{url:pathToFileURL(join(directory,'review.html')).href});await loaded;
 await evaluate('draw()');
 check('viewer initialized',await evaluate('document.getElementById("left").width===1536'));
 check('step increments one sample',await evaluate('document.getElementById("step").click();Number(slider.value)===1'));
 const samples=await evaluate(`(async()=>{const observations=[];
  for(let index=0;index<data.sequences.length;index+=2){selector.value=index;slider.value=32;await draw();
  observations.push({pair:index/2,label:data.sequences[index].id,frame:Number(slider.value),width:document.getElementById('right').width})}return observations})()`);
 check('every retained pair decodes',samples.length>0 && samples.every(s=>s.frame===32&&s.width>0));
 await evaluate('selector.value=0;slider.value=0;draw()');
 const screen=await command('Page.captureScreenshot',{format:'png'});
 writeFileSync(join(directory,'viewer.png'),Buffer.from(screen.data,'base64'));
 writeFileSync(join(directory,'browser-review.json'),JSON.stringify({browser:version,checks,samples,runtimeErrors,failedRequests,externalRequests},null,2));
 console.log(JSON.stringify({checks,runtimeErrors,failedRequests,externalRequests,samples:samples.length}));
} finally {await send('Browser.close').catch(()=>{});browser.kill();if(browser.exitCode===null)await new Promise(resolve=>browser.once("exit",resolve));rmSync(profile,{recursive:true,force:true,maxRetries:5,retryDelay:100})}
