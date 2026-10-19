import { spawn } from 'node:child_process';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../../..');
const output = resolve(process.argv[2] || 'supplementary-browser-run');
mkdirSync(output);
const observations = [];
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
 const target = await send('Target.createTarget', {url:'about:blank'});
 const attachment = await send('Target.attachToTarget', {targetId:target.targetId,flatten:true});
 const session = attachment.sessionId;
 await send('Page.enable',{},session);
 await send('Emulation.setDeviceMetricsOverride',{width:1280,height:900,deviceScaleFactor:1,mobile:false},session);
 await send('Runtime.enable',{},session);
 await send('Page.navigate',{url:'https://www.youtube.com/watch?v=ERA7-I5nPAU'},session);
 await new Promise(resolve => setTimeout(resolve,10000));

 for (const time of [3.2,30.2]) {
  const seek = await send('Runtime.evaluate',{expression:`(async()=>{const v=document.querySelector('video');v.muted=true;document.getElementById('movie_player').seekTo(${time},true);await Promise.race([v.play().catch(()=>{}),new Promise(resolve=>setTimeout(resolve,1500))]);const deadline=Date.now()+10000;let mediaTime=null;while(Date.now()<deadline){if(v.readyState>=2&&Math.abs(v.currentTime-${time})<5){mediaTime=await Promise.race([new Promise(resolve=>v.requestVideoFrameCallback((_,m)=>resolve(m.mediaTime))),new Promise(resolve=>setTimeout(()=>resolve(null),500))]);if(mediaTime!==null&&Math.abs(mediaTime-${time})<5)break;}await new Promise(resolve=>setTimeout(resolve,150));}v.pause();window.scrollTo(0,0);await new Promise(resolve=>setTimeout(resolve,400));const r=v.getBoundingClientRect();return {requestedTime:${time},mediaTime,time:v.currentTime,ready:v.readyState,paused:v.paused,videoWidth:v.videoWidth,videoHeight:v.videoHeight,rectangle:{x:r.x,y:r.y,width:r.width,height:r.height,scale:1}}})()`,awaitPromise:true,returnByValue:true},session);
  const state=seek.result.value;
  observations.push(state);
  process.stdout.write(JSON.stringify(state)+'\n');
  if (state.mediaTime === null || state.ready < 2 || Math.abs(state.mediaTime-time)>1) throw new Error('Decoded target frame unavailable; do not claim reference inspection.');
  await new Promise(resolve=>setTimeout(resolve,700));
  const screenshot=await send('Page.captureScreenshot',{format:'png',clip:state.rectangle,captureBeyondViewport:true},session);
  writeFileSync(resolve(output,'frame-'+Math.floor(time)+'.png'),Buffer.from(screenshot.data,'base64'));
 }
 writeFileSync(resolve(output,'observations.json'),JSON.stringify({source:'https://www.youtube.com/watch?v=ERA7-I5nPAU', inspected_at_utc:new Date().toISOString(), observations},null,2)+'\n');
} finally {
 await send('Browser.close');
 await new Promise(resolve => browser.once('exit',resolve));
 rmSync(profile,{recursive:true,force:true});
}
