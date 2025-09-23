import jwt from "jsonwebtoken";
import { config } from "../config.js";
import { Role } from "@prisma/client";
import type { Request, Response, NextFunction } from "express";

export interface AuthUser {
  id: string;
  role: Role;
  campusId: string;
  email: string;
}

declare global {
  namespace Express {
    interface Request {
      user?: AuthUser;
    }
  }
}

export function requireAuth(req: Request, res: Response, next: NextFunction) {
  const header = req.headers.authorization;
  if (!header) return res.status(401).json({ error: "Missing Authorization" });
  const token = header.replace(/^Bearer\s+/i, "");
  try {
    const payload = jwt.verify(token, config.jwtSecret) as AuthUser;
    req.user = payload;
    next();
  } catch {
    return res.status(401).json({ error: "Invalid token" });
  }
}

export function requireAdmin(req: Request, res: Response, next: NextFunction) {
  if (!req.user) return res.status(401).json({ error: "Unauthenticated" });
  if (req.user.role !== "admin") return res.status(403).json({ error: "Forbidden" });
  next();
}

