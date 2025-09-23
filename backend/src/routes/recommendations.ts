import { Router } from "express";
import { z } from "zod";
import { prisma } from "../db.js";
import { redis } from "../redis.js";

const router = Router();

const ReqSchema = z.object({
  user_id: z.string().uuid(),
  destination: z.object({ lat: z.number(), lng: z.number() }),
  eta: z.string().optional(),
});

router.post("/", async (req, res) => {
  const parsed = ReqSchema.safeParse(req.body);
  if (!parsed.success) return res.status(400).json({ error: parsed.error.flatten() });
  const { user_id } = parsed.data;

  const [user, lots, permits] = await Promise.all([
    prisma.user.findUnique({ where: { id: user_id } }),
    prisma.lot.findMany(),
    prisma.permit.findMany({ where: { userId: user_id } }),
  ]);
  if (!user) return res.status(404).json({ error: "User not found" });

  const allowedLots = new Set<string>();
  for (const p of permits) p.allowedLots.forEach((l) => allowedLots.add(l));

  const occupancy = await redis.hgetall("lot:occupancy");

  const recommendations = lots.map((lot) => {
    const current = occupancy[lot.id] ? Number(occupancy[lot.id]) : lot.currentOccupancy;
    const pct = lot.capacity > 0 ? Math.min(100, Math.round((current / lot.capacity) * 100)) : 0;
    return {
      lot_id: lot.id,
      current_occupancy_pct: pct,
      walk_time: null,
      eligibility: allowedLots.has(lot.id),
      reserve_link: null,
    };
  });

  recommendations.sort((a, b) => a.current_occupancy_pct - b.current_occupancy_pct);
  res.json(recommendations);
});

export default router;

