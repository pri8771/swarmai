# syntax=docker/dockerfile:1.7
# Operator console — static Vite build served by nginx with API reverse-proxy.
FROM node:22.14.0-bookworm-slim AS build

WORKDIR /console
COPY apps/console/package.json apps/console/package-lock.json ./
RUN npm ci
COPY apps/console/ ./
RUN npm run build

FROM nginx:1.27.4-alpine AS runtime

RUN apk add --no-cache wget \
  && rm -f /etc/nginx/conf.d/default.conf

COPY deploy/console/nginx.conf /etc/nginx/conf.d/console.conf
COPY deploy/console/docker-entrypoint.sh /docker-entrypoint.d/40-swarm-runtime-config.sh
COPY --from=build /console/dist /usr/share/nginx/html

RUN chmod 755 /docker-entrypoint.d/40-swarm-runtime-config.sh \
  && chown -R nginx:nginx /usr/share/nginx/html

EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=5 \
  CMD wget -qO- http://127.0.0.1:8080/healthz || exit 1
