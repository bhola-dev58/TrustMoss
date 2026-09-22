# ─────────────────────────────────────────────
# TrustMoss Web — Next.js 14+ App Router Dockerfile
# Multi-stage standalone output build
# ─────────────────────────────────────────────

# ── Stage 1: Install dependencies ─────────────
FROM node:26-alpine AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

# ── Stage 2: Build the Next.js application ────
FROM node:26-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production
ENV DOCKER_BUILD=1

RUN npm run build

# ── Stage 3: Production runner ────────────────
FROM node:26-alpine AS runtime
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy standalone build and static assets
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Ensure server.js, public, and static are accessible whether Next outputs standalone flat or nested
RUN if [ -f apps/web/server.js ]; then \
      ln -sf apps/web/server.js server.js; \
      mkdir -p apps/web/.next apps/web/public; \
      cp -rn .next/static apps/web/.next/ 2>/dev/null || true; \
      cp -rn public/* apps/web/public/ 2>/dev/null || true; \
    fi && \
    chown -R nextjs:nodejs /app

USER nextjs

EXPOSE 3000

HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=5 \
    CMD wget --quiet --tries=1 --spider http://127.0.0.1:3000/api/health || exit 1

CMD ["sh", "-c", "if [ -f server.js ]; then exec node server.js; elif [ -f apps/web/server.js ]; then exec node apps/web/server.js; else echo 'CRITICAL: server.js not found in /app. Listing /app:'; ls -laR /app; exit 1; fi"]
