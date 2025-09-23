import { Redis } from 'ioredis';

type CacheLike = {
  get(key: string): Promise<string | null>;
  set(key: string, value: string, mode?: string, ttlSeconds?: number): Promise<'OK' | null>;
};

class InMemoryCache implements CacheLike {
  private store = new Map<string, { value: string; expiresAt?: number }>();
  async get(key: string) {
    const item = this.store.get(key);
    if (!item) return null;
    if (item.expiresAt && Date.now() > item.expiresAt) {
      this.store.delete(key);
      return null;
    }
    return item.value;
  }
  async set(key: string, value: string, mode?: string, ttlSeconds?: number) {
    const entry: { value: string; expiresAt?: number } = { value };
    if (mode === 'EX' && typeof ttlSeconds === 'number') {
      entry.expiresAt = Date.now() + ttlSeconds * 1000;
    }
    this.store.set(key, entry);
    return 'OK';
  }
}

let client: CacheLike;
const redisUrl = process.env.REDIS_URL;
if (redisUrl) {
  try {
    const r = new Redis(redisUrl);
    // attach minimal wrappers to satisfy CacheLike
    client = {
      get: (key: string) => r.get(key),
      set: (key: string, value: string, mode?: string, ttlSeconds?: number) => {
        if (mode === 'EX' && typeof ttlSeconds === 'number') {
          return r.set(key, value, 'EX', ttlSeconds);
        }
        return r.set(key, value);
      }
    };
    r.on('error', () => {
      // degrade to memory if error persists
      client = new InMemoryCache();
    });
  } catch {
    client = new InMemoryCache();
  }
} else {
  client = new InMemoryCache();
}

export const redis: CacheLike = client;

