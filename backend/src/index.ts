import express from "express";
import http from "http";
import cors from "cors";
import { Server } from "socket.io";
import { config } from "./config.js";
import { prisma } from "./db.js";
import { redis } from "./redis.js";

import authRouter from "./routes/auth.js";
import permitsRouter from "./routes/permits.js";
import lotsRouter, { attachSocket } from "./routes/lots.js";
import eventsRouter from "./routes/events.js";
import recommendationsRouter from "./routes/recommendations.js";
import reservationsRouter from "./routes/reservations.js";

const app = express();
const server = http.createServer(app);
const io = new Server(server, { cors: { origin: "*" } });

attachSocket(io);

app.use(cors());
app.use(express.json());

app.get("/health", async (_req, res) => {
  try {
    await prisma.$queryRaw`SELECT 1`;
    await redis.ping();
    res.json({ ok: true });
  } catch (e) {
    res.status(500).json({ ok: false, error: String(e) });
  }
});

app.use("/auth", authRouter);
app.use("/api/v1/permits", permitsRouter);
app.use("/api/v1/lots", lotsRouter);
app.use("/api/v1/events", eventsRouter);
app.use("/api/v1/recommendations", recommendationsRouter);
app.use("/api/v1/reservations", reservationsRouter);

server.listen(config.port, () => {
  // eslint-disable-next-line no-console
  console.log(`Server listening on :${config.port}`);
});

