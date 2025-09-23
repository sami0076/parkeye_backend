import { Queue, Worker, QueueScheduler, JobsOptions } from "bullmq";
import { redis } from "../redis.js";
import { prisma } from "../db.js";
import ical from "node-ical";

const connection = redis; // ioredis instance is compatible

export const EVENT_SYNC_QUEUE = "event-sync";
export const eventSyncQueue = new Queue(EVENT_SYNC_QUEUE, { connection });
export const eventSyncScheduler = new QueueScheduler(EVENT_SYNC_QUEUE, { connection });

export function scheduleEventSync(cron = "*/15 * * * *") {
  const opts: JobsOptions = { repeat: { cron }, removeOnComplete: true, removeOnFail: true };
  return eventSyncQueue.add("pull-ics", {}, opts);
}

export function startEventSyncWorker() {
  const worker = new Worker(
    EVENT_SYNC_QUEUE,
    async () => {
      // In a real setup, fetch list of feeds from DB/config
      const feeds: string[] = [];
      for (const feed of feeds) {
        const events = await ical.fromURL(feed);
        const toCreate = Object.values(events)
          .filter((e) => (e as any).type === "VEVENT")
          .map((e: any) => ({
            title: e.summary || "Event",
            start: new Date(e.start),
            end: new Date(e.end),
            reservedLots: [],
            source: feed,
          }));
        if (toCreate.length) {
          await prisma.$transaction(toCreate.map((data) => prisma.event.create({ data })));
        }
      }
    },
    { connection }
  );
  return worker;
}

