import 'dotenv/config';
import bcrypt from 'bcryptjs';
import { prisma } from './lib/prisma.js';

async function main() {
  const passwordHash = await bcrypt.hash('password123', 10);

  const admin = await prisma.user.upsert({
    where: { email: 'admin@campus.edu' },
    update: {},
    create: { email: 'admin@campus.edu', passwordHash, campusId: 'A0001', role: 'admin' }
  });

  const student = await prisma.user.upsert({
    where: { email: 'student@campus.edu' },
    update: {},
    create: { email: 'student@campus.edu', passwordHash, campusId: 'S12345', role: 'student' }
  });

  const lotA = await prisma.lot.upsert({
    where: { id: 'lot-a' },
    update: {},
    create: { id: 'lot-a', capacity: 100, gpsBounds: JSON.stringify({ type: 'Polygon', coordinates: [] }), lotType: 'surface', rules: JSON.stringify({}), currentOccupancy: 20 }
  });
  const lotB = await prisma.lot.upsert({
    where: { id: 'lot-b' },
    update: {},
    create: { id: 'lot-b', capacity: 200, gpsBounds: JSON.stringify({ type: 'Polygon', coordinates: [] }), lotType: 'garage', rules: JSON.stringify({}), currentOccupancy: 120 }
  });

  const permit = await prisma.permit.create({
    data: { type: 'student', allowedLots: JSON.stringify([lotA.id, lotB.id]), validTimes: JSON.stringify({ weekday: { start: '06:00', end: '22:00' } }), users: { connect: [{ id: student.id }] } }
  });

  const event = await prisma.event.create({ data: { title: 'Basketball Game', start: new Date(Date.now() + 3600_000), end: new Date(Date.now() + 3_600_000 * 3), reservedLots: JSON.stringify([lotB.id]) } });

  console.log({ admin, student, lotA, lotB, permit, event });
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});

