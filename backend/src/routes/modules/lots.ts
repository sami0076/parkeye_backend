import { Router } from 'express';
import { prisma } from '../../lib/prisma.js';
import { redis } from '../../lib/redis.js';
import { io } from '../../index.js';
import { requireAuth, requireRole } from '../middleware/rbac.js';

const router = Router();

// GET /lots
router.get('/', async (_req, res) => {
  const lots = await prisma.lot.findMany();
  // Merge cached occupancy if present
  const enriched = await Promise.all(
    lots.map(async (lot) => {
      const cached = await redis.get(`lot:${lot.id}:occupancy`);
      return {
        ...lot,
        gpsBounds: JSON.parse((lot as any).gpsBounds || '{}'),
        rules: JSON.parse((lot as any).rules || '{}'),
        currentOccupancy: cached ? Number(cached) : lot.currentOccupancy
      };
    })
  );
  res.json(enriched);
});

// POST /lots/:lot_id/update
router.post('/:lot_id/update', requireAuth, requireRole(['admin']), async (req, res) => {
  const { lot_id } = req.params;
  const { capacity, occupancy } = req.body as { capacity?: number; occupancy?: number };

  const existing = await prisma.lot.findUnique({ where: { id: lot_id } });
  if (!existing) return res.status(404).json({ error: 'Lot not found' });

  if (typeof capacity === 'number') {
    await prisma.lot.update({ where: { id: lot_id }, data: { capacity } });
  }
  if (typeof occupancy === 'number') {
    await prisma.lot.update({ where: { id: lot_id }, data: { currentOccupancy: occupancy } });
    await prisma.occupancyReading.create({ data: { lotId: lot_id, occupancy } });
    await redis.set(`lot:${lot_id}:occupancy`, String(occupancy), 'EX', 60);
    io.emit('lot:update', { lot_id, occupancy });
  }

  const updated = await prisma.lot.findUnique({ where: { id: lot_id } });
  res.json({
    ...updated,
    gpsBounds: JSON.parse((updated as any)?.gpsBounds || '{}'),
    rules: JSON.parse((updated as any)?.rules || '{}')
  });
});

export default router;

