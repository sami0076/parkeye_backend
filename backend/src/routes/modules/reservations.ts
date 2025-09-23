import { Router } from 'express';
import { prisma } from '../../lib/prisma.js';
import { requireAuth } from '../middleware/rbac.js';

const router = Router();

// POST /reservations
router.post('/', requireAuth, async (req, res) => {
  const { user_id, lot_id, event_id } = req.body as { user_id: string; lot_id: string; event_id?: string };
  if (!user_id || !lot_id) return res.status(400).json({ error: 'Missing user_id or lot_id' });

  const lot = await prisma.lot.findUnique({ where: { id: lot_id } });
  if (!lot) return res.status(404).json({ error: 'Lot not found' });

  const reservedCount = await prisma.reservation.count({ where: { lotId: lot_id, status: 'reserved' } });
  if (reservedCount >= lot.capacity) return res.status(409).json({ error: 'Lot full' });

  const reservation = await prisma.reservation.create({ data: { userId: user_id, lotId: lot_id, eventId: event_id } });
  res.status(201).json(reservation);
});

// GET /reservations/:user_id
router.get('/:user_id', requireAuth, async (req, res) => {
  const { user_id } = req.params;
  const reservations = await prisma.reservation.findMany({ where: { userId: user_id }, orderBy: { createdAt: 'desc' } });
  res.json(reservations);
});

export default router;

