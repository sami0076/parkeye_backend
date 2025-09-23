import { Router } from 'express';
import { prisma } from '../../lib/prisma.js';
import { requireAuth, requireRole } from '../middleware/rbac.js';

const router = Router();

// GET /permits/:user_id
router.get('/:user_id', async (req, res) => {
  const { user_id } = req.params;
  const user = await prisma.user.findUnique({ where: { id: user_id }, include: { permits: true } });
  if (!user) return res.status(404).json({ error: 'User not found' });
  const permits = user.permits.map((p) => ({
    id: p.id,
    type: p.type,
    allowed_lots: JSON.parse((p as any).allowedLots || '[]'),
    valid_times: JSON.parse((p as any).validTimes || '{}')
  }));
  res.json(permits);
});

// POST /permits (admin)
router.post('/', requireAuth, requireRole(['admin']), async (req, res) => {
  const { type, allowed_lots, valid_times } = req.body;
  if (!type || !Array.isArray(allowed_lots) || !valid_times) return res.status(400).json({ error: 'Invalid body' });
  const permit = await prisma.permit.create({ data: { type, allowedLots: JSON.stringify(allowed_lots), validTimes: JSON.stringify(valid_times) } });
  res.status(201).json({
    id: permit.id,
    type: permit.type,
    allowed_lots,
    valid_times
  });
});

export default router;

