import api from '../api/client';

// Fingerprint / Face ID sign-in through the phone's built-in passkey support (WebAuthn).
// The private key stays inside the phone; the server only ever gets the public key.

const STORE_KEY = 'summit_bio_cred';

function toBuf(b64u) {
  const pad = '='.repeat((4 - (b64u.length % 4)) % 4);
  const bin = atob((b64u + pad).replace(/-/g, '+').replace(/_/g, '/'));
  return Uint8Array.from(bin, (c) => c.charCodeAt(0)).buffer;
}

function toB64u(buf) {
  const bytes = new Uint8Array(buf);
  let bin = '';
  bytes.forEach((b) => { bin += String.fromCharCode(b); });
  return btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

export async function biometricSupported() {
  try {
    if (!window.isSecureContext || !window.PublicKeyCredential) return false;
    return await window.PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable();
  } catch {
    return false;
  }
}

export function hasBiometricOnThisDevice() {
  try {
    return !!localStorage.getItem(STORE_KEY);
  } catch {
    return false;
  }
}

export function forgetBiometricOnThisDevice() {
  try {
    localStorage.removeItem(STORE_KEY);
  } catch {
    /* storage unavailable */
  }
}

function friendly(err) {
  if (err?.response) return err;
  const name = err?.name || '';
  if (name === 'NotAllowedError' || name === 'AbortError') return new Error('Cancelled, or the fingerprint / face was not recognised.');
  if (name === 'InvalidStateError') return new Error('This device is already registered.');
  if (name === 'NotSupportedError' || name === 'SecurityError') return new Error('This browser or address does not support fingerprint sign-in.');
  return err instanceof Error ? err : new Error('Fingerprint sign-in is not available here.');
}

// Called from Settings while signed in; the password confirms it is really the owner.
export async function enableBiometric(password, label) {
  try {
    const { data: opts } = await api.post('/biometric/register/challenge');
    const credential = await navigator.credentials.create({
      publicKey: {
        challenge: toBuf(opts.challenge),
        rp: { name: 'Summit Bank', id: window.location.hostname },
        user: { id: toBuf(opts.user.id), name: opts.user.name, displayName: opts.user.display_name },
        pubKeyCredParams: [{ type: 'public-key', alg: -7 }, { type: 'public-key', alg: -257 }],
        authenticatorSelection: { authenticatorAttachment: 'platform', userVerification: 'required', residentKey: 'preferred' },
        excludeCredentials: opts.exclude.map((id) => ({ type: 'public-key', id: toBuf(id) })),
        attestation: 'none',
        timeout: 60000,
      },
    });
    const response = credential.response;
    if (!response.getPublicKey || !response.getPublicKeyAlgorithm) {
      throw new Error('This browser is too old for fingerprint sign-in. Please update it.');
    }
    const credentialId = toB64u(credential.rawId);
    await api.post('/biometric/register', {
      password,
      credential_id: credentialId,
      public_key: toB64u(response.getPublicKey()),
      algorithm: response.getPublicKeyAlgorithm(),
      client_data_json: toB64u(response.clientDataJSON),
      label,
    });
    localStorage.setItem(STORE_KEY, credentialId);
  } catch (err) {
    throw friendly(err);
  }
}

// Returns the access token for the account the fingerprint / face belongs to.
export async function signInWithBiometric() {
  try {
    const credentialId = localStorage.getItem(STORE_KEY);
    if (!credentialId) throw new Error('Turn on fingerprint sign-in in Settings first.');
    const { data } = await api.post('/biometric/login/challenge');
    const assertion = await navigator.credentials.get({
      publicKey: {
        challenge: toBuf(data.challenge),
        rpId: window.location.hostname,
        allowCredentials: [{ type: 'public-key', id: toBuf(credentialId) }],
        userVerification: 'required',
        timeout: 60000,
      },
    });
    const r = assertion.response;
    const res = await api.post('/biometric/login', {
      credential_id: toB64u(assertion.rawId),
      client_data_json: toB64u(r.clientDataJSON),
      authenticator_data: toB64u(r.authenticatorData),
      signature: toB64u(r.signature),
    });
    return res.data.access_token;
  } catch (err) {
    throw friendly(err);
  }
}
