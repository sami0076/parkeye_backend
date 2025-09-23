import { prisma } from './prisma.js';

export async function bootstrapDatabase() {
  // Ensure extension exists (requires superuser; for MVP we skip and rely on image)
  // Create a hypertable alternative for OccupancyReading if desired later via SQL
  await prisma.$connect();
}

