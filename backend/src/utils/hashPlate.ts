import crypto from 'crypto';

export function hashPlate(plate: string, salt?: string) {
  const effectiveSalt = salt || process.env.PLATE_SALT || 'dev-salt';
  const hash = crypto.createHmac('sha256', effectiveSalt).update(plate).digest('hex');
  return hash;
}

