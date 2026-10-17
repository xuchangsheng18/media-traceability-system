import assert from 'node:assert/strict';
import { existsSync } from 'node:fs';
import { generateKeyPairSync, sign } from 'node:crypto';
import test from 'node:test';

const key = generateKeyPairSync('rsa', { modulusLength: 2048 });
const jwk = { ...key.publicKey.export({ format: 'jwk' }), kid: 'synthetic-key', alg: 'RS256' };
const expected = { issuer: 'https://identity.example.test/realms/synthetic', audience: 'probe', nonce: 'synthetic-nonce', subject: 'synthetic-user', now: 100 };
function jwt(changes = {}, header = {}) {
  const h = Buffer.from(JSON.stringify({ alg: 'RS256', kid: jwk.kid, ...header })).toString('base64url');
  const p = Buffer.from(JSON.stringify({ iss: expected.issuer, aud: expected.audience, nonce: expected.nonce, sub: expected.subject, exp: 110, iat: 90, ...changes })).toString('base64url');
  return h + '.' + p + '.' + sign('RSA-SHA256', Buffer.from(h + '.' + p), key.privateKey).toString('base64url');
}
async function verifier() {
  assert.ok(existsSync(new URL('./identity_oidc_browser.mjs', import.meta.url)), 'OIDC_BROWSER_VERIFIER_MISSING');
  return (await import('./identity_oidc_browser.mjs')).verifyIdToken;
}
test('valid ID token verifies signature and exact nonce identity', async () => {
  assert.equal((await verifier())(jwt(), { keys: [jwk] }, expected).sub, expected.subject);
});
for (const [name, changes] of [['nonce', { nonce: 'wrong' }], ['issuer', { iss: 'https://wrong.invalid' }],
  ['audience', { aud: 'wrong' }], ['subject', { sub: 'wrong' }], ['expired', { exp: 100 }], ['future', { nbf: 101 }]]) {
  test('rejects ' + name, async () => assert.throws(() => (globalThis.identityVerifier)(jwt(changes), { keys: [jwk] }, expected), /IDENTITY/));
}
test.before(async () => { globalThis.identityVerifier = await verifier(); });
test('rejects signature forgery and algorithm substitution', async () => {
  const verify = await verifier();
  const value = jwt();
  assert.throws(() => verify(value.slice(0, -12) + 'AAAAAAAAAAAA', { keys: [jwk] }, expected), /IDENTITY/);
  assert.throws(() => verify(jwt({}, { alg: 'none' }), { keys: [jwk] }, expected), /IDENTITY/);
  assert.throws(() => verify(value, { keys: [] }, expected), /IDENTITY/);
});
test('browser diagnostics redact credentials and callback URL query', async () => {
  const module = await import('./identity_oidc_browser.mjs');
  assert.equal(typeof module.safeError, 'function', 'PRIVATE_BROWSER_DIAGNOSTIC_MISSING');
  const value = module.safeError('failed synthetic-password https://localhost:18444/callback?code=private-code', ['synthetic-password']);
  assert.ok(!value.includes('synthetic-password') && !value.includes('private-code'));
});
