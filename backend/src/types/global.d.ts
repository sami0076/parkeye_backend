declare namespace NodeJS {
  interface ProcessEnv {
    DATABASE_URL: string;
    REDIS_URL: string;
    JWT_SECRET: string;
    MAPBOX_TOKEN?: string;
    ICS_FEED_URL?: string;
    PLATE_SALT?: string;
    NODE_ENV?: 'development' | 'production' | 'test';
  }
}

