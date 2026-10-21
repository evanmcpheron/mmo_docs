import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { existsSync, mkdtempSync, mkdirSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { test } from 'node:test';
import { setTimeout as delay } from 'node:timers/promises';
import { cleanupBrowser } from './browser_cleanup.mjs';

const writer = `
  const { mkdirSync, writeFileSync } = require('node:fs');
  const { join } = require('node:path');
  const profile = process.argv[1];
  process.on('SIGTERM', () => {});
  setInterval(() => {
    mkdirSync(join(profile, 'Default'), { recursive: true });
    writeFileSync(join(profile, 'Default', 'state'), 'active');
  }, 5);
  console.log('ready');
`;

function fixture(t, script) {
  const root = mkdtempSync(join(tmpdir(), 'briarwake-cleanup-test-'));
  const profile = join(root, 'profile');
  mkdirSync(profile);
  const browser = spawn(process.execPath, ['-e', script, profile], {
    detached: true, stdio: ['ignore', 'pipe', 'inherit'],
  });
  t.after(async () => {
    try { process.kill(-browser.pid, 'SIGKILL'); }
    catch (error) { if (error.code !== 'ESRCH') throw error; }
    if (browser.exitCode === null && browser.signalCode === null) await once(browser, 'exit');
    rmSync(root, { recursive: true, force: true, maxRetries: 10, retryDelay: 100 });
  });
  return { browser, profile };
}

test('forced shutdown waits for actual exit before removing a live profile', { timeout: 10000 }, async t => {
  const { browser, profile } = fixture(t, writer);
  await once(browser.stdout, 'data');
  await cleanupBrowser(browser, profile);
  assert.equal(browser.signalCode, 'SIGKILL');
  assert.equal(existsSync(profile), false);
  await delay(100);
  assert.equal(existsSync(profile), false);
});

test('cleanup stops profile-writing descendants after their launcher exits', { timeout: 10000 }, async t => {
  const launcher = `
    const { spawn } = require('node:child_process');
    const child = spawn(process.execPath, ['-e', ${JSON.stringify(writer)}, process.argv[1]], {
      stdio: ['ignore', 'pipe', 'ignore'],
    });
    process.on('SIGTERM', () => process.exit(0));
    child.stdout.once('data', () => console.log('ready'));
  `;
  const { browser, profile } = fixture(t, launcher);
  await once(browser.stdout, 'data');
  await cleanupBrowser(browser, profile);
  assert.equal(browser.exitCode, 0);
  assert.equal(existsSync(profile), false);
  await delay(100);
  assert.equal(existsSync(profile), false);
});

test('an already exited browser can release its profile without another exit event', { timeout: 2000 }, async t => {
  const { browser, profile } = fixture(t, 'process.exit(0)');
  await once(browser, 'exit');
  await cleanupBrowser(browser, profile);
  assert.equal(existsSync(profile), false);
});

test('profile removal failures remain observable after browser shutdown', { timeout: 2000 }, async t => {
  const { browser } = fixture(t, 'process.exit(0)');
  await once(browser, 'exit');
  await assert.rejects(cleanupBrowser(browser, null), { code: 'ERR_INVALID_ARG_TYPE' });
});
