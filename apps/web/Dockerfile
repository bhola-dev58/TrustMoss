# ─────────────────────────────────────────────
# TrustMoss Web — Production-ready Dockerfile
# Multi-stage: build with Node, serve with Nginx
# ─────────────────────────────────────────────

# ── Stage 1: Node builder ─────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies (layer-cached)
COPY package.json package-lock.json ./
RUN npm ci --frozen-lockfile

# Copy source and build
COPY . .
RUN npm run build


# ── Stage 2: Nginx static server ─────────────
FROM nginx:1.27-alpine AS runtime

LABEL org.opencontainers.image.title="TrustMoss Web"
LABEL org.opencontainers.image.description="TrustMoss Dashboard UI"

# Remove default nginx config; add custom SPA config
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:3000 || exit 1

CMD ["nginx", "-g", "daemon off;"]
