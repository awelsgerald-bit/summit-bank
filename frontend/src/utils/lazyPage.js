import { lazy } from 'react';

// Pages load the first time they are opened, and start loading earlier when a link is hovered,
// touched or focused, so a tap on a menu item usually opens an already-downloaded page.
const loaders = new Map();

function loadWithRetry(loader) {
  return () =>
    loader().then(
      (mod) => {
        try {
          sessionStorage.removeItem('summit_chunk_reload');
        } catch {
          // storage can be blocked; nothing to clean up
        }
        return mod;
      },
      (err) => {
        // After a new release the old files are gone. Reload once to pick up the new ones.
        try {
          if (!sessionStorage.getItem('summit_chunk_reload')) {
            sessionStorage.setItem('summit_chunk_reload', '1');
            window.location.reload();
            return new Promise(() => {});
          }
        } catch {
          // fall through to the error
        }
        throw err;
      }
    );
}

export function page(path, loader) {
  const wrapped = loadWithRetry(loader);
  loaders.set(path, wrapped);
  return lazy(wrapped);
}

export function preloadRoute(path) {
  const loader = loaders.get(path);
  if (loader) loader().catch(() => {});
}

export function preloadWhenIdle(paths) {
  const run = () => paths.forEach(preloadRoute);
  if (typeof window.requestIdleCallback === 'function') window.requestIdleCallback(run, { timeout: 4000 });
  else setTimeout(run, 2500);
}
