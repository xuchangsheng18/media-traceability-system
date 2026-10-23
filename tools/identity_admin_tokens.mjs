// Existing Node crypto only; no new runtime package or persistent token refresh.
import { constants, createPublicKey, verify } from 'node:crypto';
import { verifyIdToken } from './identity_oidc_browser.mjs';
import { pathToFileURL } from 'node:url';

export function verifyAccess(token, jwks, expected) {
  try {
    if (typeof token !== 'string' || token.length > 16384) throw new Error();
    const parts = token.split('.');
    if (parts.length !== 3 || parts.some(p => !/^[A-Za-z0-9_-]+$/.test(p) || Buffer.from(p, 'base64url').toString('base64url') !== p)) throw new Error();
    const header = JSON.parse(Buffer.from(parts[0], 'base64url'));
    const claims = JSON.parse(Buffer.from(parts[1], 'base64url'));
    const keys = jwks.keys.filter(k => k.kid === header.kid && k.kty === 'RSA' && k.use === 'sig' && (!k.alg || k.alg === 'RS256'));
    if (header.alg !== 'RS256' || typeof header.kid !== 'string' || keys.length !== 1) throw new Error();
    if (!verify('RSA-SHA256', Buffer.from(parts[0] + '.' + parts[1]), {
      key: createPublicKey({ key: keys[0], format: 'jwk' }), padding: constants.RSA_PKCS1_PADDING,
    }, Buffer.from(parts[2], 'base64url'))) throw new Error();
    const now = Math.floor(Date.now() / 1000);
    if (claims.iss !== expected.issuer || claims.azp !== 'media-trace-admin-tools' || claims.typ !== 'Bearer' ||
      !(claims.aud === 'media-trace-admin-tools' || (Array.isArray(claims.aud) && claims.aud.includes('media-trace-admin-tools'))) ||
      !Number.isSafeInteger(claims.exp) || !Number.isSafeInteger(claims.iat) || claims.exp <= now || claims.iat > now ||
      claims.exp <= claims.iat || claims.exp - claims.iat > 300 ||
      !Number.isSafeInteger(claims.auth_time) || claims.auth_time > now || now - claims.auth_time > 300 ||
      (claims.nbf !== undefined && (!Number.isSafeInteger(claims.nbf) || claims.nbf > now)) ||
      !Array.isArray(claims.amr) || !claims.amr.includes('pwd') || !claims.amr.includes('otp') ||
      !/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(claims.sub) ||
      typeof claims.sid !== 'string' || !/^[\x20-\x7E]{1,256}$/.test(claims.sid)) throw new Error();
    return { subject: claims.sub, expires_at: claims.exp, session_id: claims.sid };
  } catch { throw new Error('IDENTITY_MANAGEMENT_TOKEN_INVALID'); }
}

async function main() {
  let raw = '';
  for await (const chunk of process.stdin) { raw += chunk; if (raw.length > 131072) throw new Error(); }
  const input = JSON.parse(raw);
  const result = verifyAccess(input.token, input.jwks, input.expected);
  if (input.id_token !== undefined) verifyIdToken(input.id_token, input.jwks, {
    issuer: input.expected.issuer, audience: 'media-trace-admin-tools', nonce: input.expected.nonce, subject: result.subject,
  });
  process.stdout.write(JSON.stringify(result) + '\n');
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch(() => { process.stderr.write('IDENTITY_MANAGEMENT_TOKEN_INVALID\n'); process.exitCode = 1; });
}
