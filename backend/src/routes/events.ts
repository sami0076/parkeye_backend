import { Router } from "express";
import { requireAdmin } from "../middleware/auth.js";
import { z } from "zod";
import ical from "node-ical";
import { prisma } from "../db.js";

const router = Router();

const ImportSchema = z.object({
  icsUrl: z.string().url().optional(),
  icsText: z.string().optional(),
  source: z.string().optional(),
});

router.post("/import", requireAdmin, async (req, res) => {
  const parsed = ImportSchema.safeParse(req.body);
  if (!parsed.success) return res.status(400).json({ error: parsed.error.flatten() });
  const { icsUrl, icsText, source } = parsed.data;

  let events: ical.FullCalendarResponse | undefined;
  if (icsUrl) {
    events = await ical.fromURL(icsUrl);
  } else if (icsText) {
    events = ical.sync.parseICS(icsText);
  } else {
    return res.status(400).json({ error: "Provide icsUrl or icsText" });
  }

  const toCreate = Object.values(events)
    .filter((e) => e.type === "VEVENT")
    .map((e: any) => ({
      title: e.summary || "Event",
      start: new Date(e.start),
      end: new Date(e.end),
      reservedLots: [],
      source: source || icsUrl || "manual",
    }));

  const created = await prisma.$transaction(
    toCreate.map((data) => prisma.event.create({ data }))
  );

  res.json({ count: created.length });
});

router.get("/", async (_req, res) => {
  const events = await prisma.event.findMany({ orderBy: { start: "asc" } });
  res.json(events);
});

export default router;

