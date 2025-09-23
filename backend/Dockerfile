FROM node:20-alpine AS base

WORKDIR /app

COPY package.json package-lock.json* .npmrc* ./

RUN npm install --no-audit --no-fund

COPY tsconfig.json ./
COPY prisma ./prisma
RUN npx prisma generate

COPY src ./src

RUN npm run build

ENV NODE_ENV=production

EXPOSE 4000

CMD ["npm", "run", "start"]

