import { Router } from "express";
import { prisma } from "../db.js";
import { requireAdmin, requireAuth } from "../middleware/auth.js";
import { z } from "zod";

const router = Router();

router.get("/:userId", requireAuth, async (req, res) => {
  const { userId } = req.params;
  if (req.user!.id !== userId && req.user!.role !== "admin") return res.status(403).json({ error: "Forbidden" });
  const permits = await prisma.permit.findMany({ where: { userId } });
  res.json(permits);
});

const PermitSchema = z.object({
  userId: z.string().uuid(),
  type: z.string(),
  allowedLots: z.array(z.string()),
  validTimes: z.any(),
});

router.post("/", requireAdmin, async (req, res) => {
  const parsed = PermitSchema.safeParse(req.body);
  if (!parsed.success) return res.status(400).json({ error: parsed.error.flatten() });
  const permit = await prisma.permit.create({ data: parsed.data });
  res.status(201).json(permit);
});

export default router;

