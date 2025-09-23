import client from 'prom-client';
import { Request, Response } from 'express';

export function registerMetrics() {
  client.collectDefaultMetrics();
}

export async function metricsMiddleware(_req: Request, res: Response) {
  res.set('Content-Type', client.register.contentType);
  res.end(await client.register.metrics());
}

