import express from 'express';
import path from 'path';
import { createServer as createViteServer } from 'vite';

/**
 * This server ONLY serves the React frontend (dev via Vite middleware, or
 * static files in production). It does NOT proxy or implement any
 * prediction logic -- the frontend calls the real Python FastAPI backend
 * directly (see src/services/api.ts, configured via VITE_API_BASE_URL).
 *
 * Run the FastAPI backend separately: see backend/README.md.
 */
async function startServer() {
  const app = express();
  const PORT = Number(process.env.PORT) || 3000;

  app.get('/health', (_req, res) => {
    res.json({ status: 'ok', service: 'Yield Engine frontend server' });
  });

  if (process.env.NODE_ENV !== 'production') {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: 'spa',
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), 'dist');
    app.use(express.static(distPath));
    app.get('*', (_req, res) => {
      res.sendFile(path.join(distPath, 'index.html'));
    });
  }

  app.listen(PORT, '0.0.0.0', () => {
    console.log(`Yield Engine frontend running on http://0.0.0.0:${PORT}`);
    console.log(`Make sure the FastAPI backend is running separately (see backend/README.md)`);
  });
}

startServer();
