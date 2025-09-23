import { Router } from 'express';
import { prisma } from '../../lib/prisma.js';
import { requireAuth, requireRole } from '../middleware/rbac.js';
import ical from 'node-ical';
import axios from 'axios';
import { io } from '../../index.js';
import { getEventsQueue } from '../../workers/eventIngest.js';

const router = Router();

// GET /events
router.get('/', async (_req, res) => {
  const events = await prisma.event.findMany({ orderBy: { start: 'asc' } });
  const parsed = events.map((e) => ({
    ...e,
    reservedLots: JSON.parse((e as any).reservedLots || '[]')
  }));
  res.json(parsed);
});

// POST /events/import
router.post('/import', requireAuth, requireRole(['admin']), async (_req, res) => {
  const url = process.env.ICS_FEED_URL;
  if (!url) return res.status(400).json({ error: 'ICS_FEED_URL not configured' });

  const q = getEventsQueue();
  if (!q) return res.status(202).json({ queued: false, reason: 'Redis not configured' });
  await q.add('import', {});
  io.emit('events:imported');
  res.json({ queued: true });
});

export default router;

