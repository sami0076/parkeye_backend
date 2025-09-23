import { Router } from "express";
import { prisma } from "../db.js";
import { z } from "zod";
import type { Server } from "socket.io";
import { requireAdmin } from "../middleware/auth.js";
import { redis } from "../redis.js";

let io: Server | null = null;
export function attachSocket(server: Server) {
  io = server;
}

const router = Router();

router.get("/", async (_req, res) => {
  const lots = await prisma.lot.findMany();
  const occupancy = await redis.hgetall("lot:occupancy");
  const merged = lots.map((lot) => ({
    ...lot,
    currentOccupancy: occupancy[lot.id] ? Number(occupancy[lot.id]) : lot.currentOccupancy,
  }));
  res.json(merged);
});

const UpdateSchema = z.object({
  capacity: z.number().int().positive().optional(),
  currentOccupancy: z.number().int().min(0).optional(),
});

router.post("/:lotId/update", requireAdmin, async (req, res) => {
  const { lotId } = req.params;
  const parsed = UpdateSchema.safeParse(req.body);
  if (!parsed.success) return res.status(400).json({ error: parsed.error.flatten() });
  const data: Record<string, unknown> = {};
  if (parsed.data.capacity !== undefined) data.capacity = parsed.data.capacity;
  if (parsed.data.currentOccupancy !== undefined) data.currentOccupancy = parsed.data.currentOccupancy;
  const updated = await prisma.lot.update({ where: { id: lotId }, data });
  if (parsed.data.currentOccupancy !== undefined) {
    await redis.hset("lot:occupancy", lotId, String(parsed.data.currentOccupancy));
    io?.emit("lot:update", { lotId, currentOccupancy: parsed.data.currentOccupancy });
  }
  res.json(updated);
});

export default router;

