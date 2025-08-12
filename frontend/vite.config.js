import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { VitePWA } from 'vite-plugin-pwa';

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      selfDestroying: true,
      registerType: 'autoUpdate',
      workbox: { clientsClaim: true, skipWaiting: true },
    }),
  ],
  build: { sourcemap: true },
});

// build trigger to redeploy updated vercel configuration
