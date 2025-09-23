import { Router } from "express";
import { z } from "zod";
import { prisma } from "../db.js";
import { requireAuth } from "../middleware/auth.js";

const router = Router();

const CreateSchema = z.object({
  lot_id: z.string().uuid(),
  event_id: z.string().uuid().optional(),
});

router.post("/", requireAuth, async (req, res) => {
  const parsed = CreateSchema.safeParse(req.body);
  if (!parsed.success) return res.status(400).json({ error: parsed.error.flatten() });
  const { lot_id, event_id } = parsed.data;

  const lot = await prisma.lot.findUnique({ where: { id: lot_id } });
  if (!lot) return res.status(404).json({ error: "Lot not found" });

  const activeCount = await prisma.reservation.count({ where: { lotId: lot_id, status: "reserved" } });
  if (activeCount >= lot.capacity) return res.status(409).json({ error: "Lot at capacity" });

  const reservation = await prisma.reservation.create({ data: {
    lotId: lot_id,
    eventId: event_id,
    userId: req.user!.id,
  }});
  res.status(201).json(reservation);
});

router.get("/:userId", requireAuth, async (req, res) => {
  const { userId } = req.params;
  if (req.user!.id !== userId && req.user!.role !== "admin") return res.status(403).json({ error: "Forbidden" });
  const reservations = await prisma.reservation.findMany({ where: { userId }, orderBy: { createdAt: "desc" } });
  res.json(reservations);
});

export default router;

