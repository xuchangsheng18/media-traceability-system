import { constants, createPublicKey, verify } from 'node:crypto';
import { lstatSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

let sensitiveValues = [];
export function safeError(message, values) {
  let text = String(message);
  for (const value of values) if (typeof value === 'string' && value) text = text.split(value).join('<redacted>');
  return text.replace(/https?:\/\/\S+/g, '<url>').split('\n').slice(0, 2).join(':').slice(0, 240);
}

export function verifyIdToken(token, jwks, expected) {
  try {
    if (typeof token !== 'string' || token.length > 16384) throw new Error();
    const pieces = token.split('.');
    if (pieces.length !== 3) throw new Error();
    const header = JSON.parse(Buffer.from(pieces[0], 'base64url'));
    const claims = JSON.parse(Buffer.from(pieces[1], 'base64url'));
    const keys = jwks.keys.filter(k => k.kid === header.kid && k.kty === 'RSA');
    if (header.alg !== 'RS256' || typeof header.kid !== 'string' || keys.length !== 1) throw new Error();
    const key = createPublicKey({ key: keys[0], format: 'jwk' });
    if (!verify('RSA-SHA256', Buffer.from(pieces[0] + '.' + pieces[1]),
      { key, padding: constants.RSA_PKCS1_PADDING }, Buffer.from(pieces[2], 'base64url'))) throw new Error();
    const now = expected.now ?? Math.floor(Date.now() / 1000);
    if (claims.iss !== expected.issuer || claims.nonce !== expected.nonce || claims.sub !== expected.subject ||
      !(claims.aud === expected.audience || (Array.isArray(claims.aud) && claims.aud.includes(expected.audience))) ||
      !Number.isSafeInteger(claims.exp) || claims.exp <= now ||
      (claims.nbf !== undefined && (!Number.isSafeInteger(claims.nbf) || claims.nbf > now)) ||
      (claims.iat !== undefined && (!Number.isSafeInteger(claims.iat) || claims.iat > now))) throw new Error();
    return claims;
  } catch { throw new Error('IDENTITY_ID_TOKEN_VERIFICATION_FAILED'); }
}

function privateJson(path) {
  const info = lstatSync(path);
  if (!info.isFile() || (info.mode & 0o077) || info.uid !== process.getuid() || info.size > 65536) throw new Error('IDENTITY_PRIVATE_CONFIG_INVALID');
  return JSON.parse(readFileSync(path, 'utf8'));
}

async function main(path) {
  const config = privateJson(path);
  sensitiveValues = [config.username, config.password, config.token, config.expected?.nonce, config.expected?.subject];
  if (config.action === 'verify') {
    verifyIdToken(config.token, config.jwks, config.expected);
    process.stdout.write('{"status":"PASS"}\n');
    return;
  }
  const base = dirname(resolve(path));
  if (config.action !== 'login' || !resolve(config.browser_home).startsWith(base + '/') ||
    dirname(resolve(config.callback_file)) !== base ||
    !config.authorization_url.startsWith('https://172.16.58.179:18443/realms/') ||
    config.redirect_uri !== 'https://localhost:18444/identity-test/callback') throw new Error('IDENTITY_BROWSER_BOUNDARY_INVALID');
  const require = createRequire(new URL('../frontend/package.json', import.meta.url));
  const { chromium } = require('@playwright/test');
  const context = await chromium.launchPersistentContext(resolve(config.browser_home, 'chromium'), {
    headless: true, ignoreHTTPSErrors: false, env: { ...process.env, HOME: resolve(config.browser_home) },
  });
  try {
    const page = await context.newPage();
    let callback;
    let completeCallback;
    const callbackReady = new Promise(resolve => { completeCallback = resolve; });
    // Observe the genuine IdP redirect. Playwright routes only the first URL in
    // a redirect chain; this collector neither fabricates an IdP response nor
    // treats the temporary callback page as an implemented business frontend.
    page.on('response', response => {
      if (![302, 303].includes(response.status()) || !response.url().startsWith('https://172.16.58.179:18443/realms/')) return;
      const location = response.headers().location;
      if (!location) return;
      const url = new URL(location, response.url());
      if (url.origin + url.pathname !== config.redirect_uri) return;
      if (url.searchParams.getAll('code').length !== 1 || url.searchParams.getAll('state').length !== 1) return;
      callback = { code: url.searchParams.get('code'), state: url.searchParams.get('state') };
      sensitiveValues.push(callback.code, callback.state);
      completeCallback();
    });
    await page.goto(config.authorization_url, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.locator('input[name="username"]').fill(config.username);
    await page.locator('input[name="password"]').fill(config.password);
    await page.locator('#kc-login').click();
    let timer;
    try {
      await Promise.race([callbackReady, new Promise((_, reject) => { timer = setTimeout(async () => {
        const text = await page.locator('body').innerText().catch(() => '');
        const codes = text.match(/\bERR_[A-Z_]+\b|\b404 Not Found\b/g) || [];
        reject(new Error('IDENTITY_CALLBACK_TIMEOUT:' + codes.join(',')));
      }, 5000); })]);
    } finally { clearTimeout(timer); }
    if (!callback) {
      const finalUrl = new URL(page.url());
      const keys = [...finalUrl.searchParams.keys()].map(k => ['state', 'code', 'iss', 'session_state', 'error'].includes(k) ? k : 'other');
      throw new Error('IDENTITY_CALLBACK_MISSING:keys=' + keys.join(',') + ';raw_slash=' + finalUrl.search.includes('/'));
    }
    writeFileSync(config.callback_file, JSON.stringify(callback), { mode: 0o600, flag: 'wx' });
    process.stdout.write('{"status":"PASS","flow":"authorization_code_pkce"}\n');
  } finally { await context.close(); }
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main(process.argv[2]).catch(error => {
    const detail = sensitiveValues.length ? safeError(error.message, sensitiveValues) : 'PRIVATE_CONFIGURATION_INVALID';
    process.stderr.write('IDENTITY_BROWSER_PROBE_FAILED:' + detail + '\n');
    process.exitCode = 1;
  });
}
