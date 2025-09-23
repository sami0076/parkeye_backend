import { Queue, Worker, QueueScheduler } from 'bullmq';
import axios from 'axios';
import ical from 'node-ical';
import { prisma } from '../lib/prisma.js';
import { redis } from '../lib/redis.js';

export function getEventsQueue(): Queue | null {
  if (!process.env.REDIS_URL) return null;
  const connection = { url: process.env.REDIS_URL } as any;
  try {
    const q = new Queue('events', { connection });
    new QueueScheduler('events', { connection });
    return q;
  } catch {
    return null;
  }
}

export function startEventWorker(): Worker | null {
  if (!process.env.REDIS_URL) return null;
  const connection = { url: process.env.REDIS_URL } as any;
  try {
    const worker = new Worker(
      'events',
      async () => {
        const url = process.env.ICS_FEED_URL;
        if (!url) return;
        const result = await axios.get(url, { responseType: 'text' });
        const data = ical.sync.parseICS(result.data);
        const ops = [] as Promise<any>[];
        for (const key of Object.keys(data)) {
          const ev = data[key];
          if (ev.type !== 'VEVENT') continue;
          const reservedLots: string[] = [];
          const title: string = ev.summary || 'Event';
          const start: Date = ev.start as Date;
          const end: Date = ev.end as Date;
          ops.push(
            prisma.event.upsert({
              where: { id: key },
              update: { title, start, end, reservedLots },
              create: { id: key, title, start, end, reservedLots }
            })
          );
        }
        await Promise.all(ops);
      },
      { connection }
    );
    return worker;
  } catch {
    return null;
  }
}

