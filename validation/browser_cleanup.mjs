import { rm } from 'node:fs/promises';

function signalBrowserGroup(browser, signal) {
  try {
    process.kill(-browser.pid, signal);
  } catch (error) {
    if (error.code !== 'ESRCH') throw error;
  }
}

function waitForExit(browser, timeout) {
  if (browser.exitCode !== null || browser.signalCode !== null) return Promise.resolve(true);
  return new Promise(resolve => {
    const onExit = () => { clearTimeout(timer); resolve(true); };
    const timer = setTimeout(() => {
      browser.removeListener('exit', onExit);
      resolve(false);
    }, timeout);
    browser.once('exit', onExit);
  });
}

export async function cleanupBrowser(browser, profile) {
  if (browser.pid) {
    signalBrowserGroup(browser, 'SIGTERM');
    if (!await waitForExit(browser, 2000)) {
      signalBrowserGroup(browser, 'SIGKILL');
      if (!await waitForExit(browser, 5000)) throw new Error('Browser did not exit after SIGKILL');
    }
    // A launcher can exit before the Chrome children that still own the profile.
    signalBrowserGroup(browser, 'SIGKILL');
  }
  await rm(profile, { recursive: true, force: true, maxRetries: 10, retryDelay: 100 });
}
