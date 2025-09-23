import { Router } from 'express';
import { prisma } from '../../lib/prisma.js';
import { requireAuth } from '../middleware/rbac.js';
import { redis } from '../../lib/redis.js';

const router = Router();

// POST /recommendations
router.post('/', requireAuth, async (req, res) => {
  const { user_id, destination, eta } = req.body as { user_id: string; destination: { lat: number; lng: number }; eta?: number };
  if (!user_id || !destination) return res.status(400).json({ error: 'Missing user_id or destination' });

  const user = await prisma.user.findUnique({ where: { id: user_id }, include: { permits: true } });
  if (!user) return res.status(404).json({ error: 'User not found' });

  const lots = await prisma.lot.findMany();
  const now = new Date();

  const recommendations = await Promise.all(lots.map(async (lot) => {
    const cached = await redis.get(`lot:${lot.id}:occupancy`);
    const occupancy = cached ? Number(cached) : lot.currentOccupancy;
    const occupancyPct = Math.min(100, Math.round((occupancy / Math.max(lot.capacity, 1)) * 100));

    // Eligibility: permit must allow lot and time window must be valid
    const hasPermit = user.permits.some((p) => {
      const allowed = JSON.parse((p as any).allowedLots || '[]') as string[];
      return allowed.includes(lot.id);
    });
    const withinTime = true; // simplify MVP; later check p.validTimes vs now
    const eligible = hasPermit && withinTime;

    // Walk time placeholder: simple heuristic (no external API in MVP)
    const walk_time = 8; // minutes; replace with Mapbox/Google if token provided

    return {
      lot_id: lot.id,
      occupancy_pct: occupancyPct,
      walk_time,
      eligible,
      reserve_link: lot.reserveLink || null
    };
  }));

  // Rank by eligibility first, then lowest occupancy, then shortest walk
  const ranked = recommendations.sort((a, b) => {
    if (a.eligible !== b.eligible) return a.eligible ? -1 : 1;
    if (a.occupancy_pct !== b.occupancy_pct) return a.occupancy_pct - b.occupancy_pct;
    return a.walk_time - b.walk_time;
  });

  res.json(ranked);
});

export default router;

