export async function unregisterAllSW() {
  if ('serviceWorker' in navigator) {
    const regs = await navigator.serviceWorker.getRegistrations();
    for (const r of regs) {
      try {
        await r.unregister();
      } catch {}
    }
    if ('caches' in window) {
      const keys = await caches.keys();
      for (const k of keys) {
        try {
          await caches.delete(k);
        } catch {}
      }
    }
  }
}
