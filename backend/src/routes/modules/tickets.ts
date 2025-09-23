import { Router } from 'express';
import { prisma } from '../../lib/prisma.js';
import { requireAuth, requireRole } from '../middleware/rbac.js';

const router = Router();

// Phase 2 endpoints (stubs enabled for future)
router.post('/', requireAuth, requireRole(['enforcement', 'admin']), async (req, res) => {
  const { plate_hash, lot_id, rule_violated, photo_ref } = req.body as any;
  if (!plate_hash || !lot_id || !rule_violated) return res.status(400).json({ error: 'Missing fields' });
  const ticket = await prisma.ticket.create({ data: { plateHash: plate_hash, lotId: lot_id, ruleViolated: rule_violated, photoRef: photo_ref } });
  res.status(201).json(ticket);
});

router.get('/', requireAuth, requireRole(['enforcement', 'admin']), async (req, res) => {
  const status = (req.query.status as string) || 'open';
  const tickets = await prisma.ticket.findMany({ where: { status: status as any } });
  res.json(tickets);
});

export default router;

