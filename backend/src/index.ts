import 'dotenv/config';
import express from 'express';
import http from 'http';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import { Server as SocketIOServer } from 'socket.io';
import { prisma } from './lib/prisma.js';
import { redis } from './lib/redis.js';
import { registerMetrics, metricsMiddleware } from './lib/metrics.js';
import { router } from './routes/index.js';
import { bootstrapDatabase } from './lib/bootstrap.js';
import { startEventWorker, getEventsQueue } from './workers/eventIngest.js';

const app = express();
app.use(helmet());
app.use(cors({ origin: '*'}));
app.use(express.json());
app.use(morgan('dev'));

// Health
app.get('/health', (_req, res) => {
  res.json({ status: 'ok' });
});

// Metrics
registerMetrics();
app.get('/metrics', metricsMiddleware);

// API routes
app.use('/api/v1', router);

const server = http.createServer(app);
export const io = new SocketIOServer(server, { cors: { origin: '*' } });

io.on('connection', (socket) => {
  socket.emit('welcome', { message: 'Connected to parking updates' });
});

const port = process.env.PORT ? Number(process.env.PORT) : 4000;

async function start() {
  await bootstrapDatabase();
  // Start background worker and schedule ICS import every 15 minutes
  startEventWorker();
  const q = getEventsQueue();
  if (q) {
    await q.add('import', {}, { repeat: { every: 15 * 60 * 1000 } });
  }
  server.listen(port, () => {
    console.log(`API listening on http://localhost:${port}`);
  });
}

start().catch((err) => {
  console.error('Fatal startup error', err);
  process.exit(1);
});

