export const config = {
  port: parseInt(process.env.PORT || "4000", 10),
  jwtSecret: process.env.JWT_SECRET || "dev-secret",
  databaseUrl: process.env.DATABASE_URL || "postgres://postgres:postgres@localhost:5432/campus_parking",
  redisUrl: process.env.REDIS_URL || "redis://localhost:6379",
  mapboxToken: process.env.MAPBOX_TOKEN || "",
};

